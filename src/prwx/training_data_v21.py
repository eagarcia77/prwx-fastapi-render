from __future__ import annotations

import io
import json
import math
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np
import pandas as pd
import requests

PR_BBOX = (18.65, -67.35, 17.80, -65.15)  # north, west, south, east
NCEI_DATA_URL = "https://www.ncei.noaa.gov/access/services/data/v1"

S3_BASES = {
    "gfs": "https://noaa-gfs-bdp-pds.s3.amazonaws.com",
    "gefs": "https://noaa-gefs-pds.s3.amazonaws.com",
    "nam_pr": "https://noaa-nam-pds.s3.amazonaws.com",
}

DEFAULT_GRIB_PATTERNS = (
    r":TMP:2 m above ground:",
    r":DPT:2 m above ground:",
    r":RH:2 m above ground:",
    r":UGRD:10 m above ground:",
    r":VGRD:10 m above ground:",
    r":GUST:surface:",
    r":APCP:surface:",
    r":PRMSL:mean sea level:",
    r":PWAT:entire atmosphere",
    r":CAPE:surface:",
    r":CIN:surface:",
)


@dataclass(frozen=True)
class Location:
    location_id: str
    lat: float
    lon: float
    name: str = ""
    island: str = "Puerto Rico"
    elevation_m: float | None = None


@dataclass(frozen=True)
class GribObject:
    source: str
    date: str
    cycle: int
    forecast_hour: int
    member: str | None
    bucket_base: str
    key: str

    @property
    def url(self) -> str:
        return f"{self.bucket_base.rstrip('/')}/{self.key}"

    @property
    def idx_url(self) -> str:
        return f"{self.url}.idx"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def bbox_param(bbox: Sequence[float] = PR_BBOX) -> str:
    if len(bbox) != 4:
        raise ValueError("bbox must contain north, west, south, east")
    return ",".join(f"{float(value):.5f}".rstrip("0").rstrip(".") for value in bbox)


def _to_float(value: Any) -> float | None:
    try:
        if value is None or pd.isna(value):
            return None
        text = str(value).strip()
        if not text or text.lower() in {"nan", "none", "null"}:
            return None
        return float(text)
    except Exception:
        return None


def _encoded_tenths(value: Any, missing: set[str] | None = None) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    main = text.split(",", 1)[0].strip()
    if missing and main in missing:
        return None
    try:
        raw = int(main)
    except Exception:
        return _to_float(main)
    return raw / 10.0


def _parse_wnd(value: Any) -> tuple[float | None, float | None]:
    if value is None:
        return None, None
    parts = str(value).split(",")
    if len(parts) < 4:
        return None, None
    direction = _to_float(parts[0])
    if direction is not None and direction >= 999:
        direction = None
    speed_raw = _to_float(parts[3])
    speed_ms = None if speed_raw is None or speed_raw >= 9999 else speed_raw / 10.0
    return direction, speed_ms


def _parse_precip_group(value: Any) -> tuple[int | None, float | None]:
    if value is None:
        return None, None
    parts = str(value).split(",")
    if len(parts) < 2:
        return None, None
    period = _to_float(parts[0])
    depth = _to_float(parts[1])
    if period is None or depth is None or depth >= 9999:
        return None, None
    return int(period), (depth / 10.0) / 25.4  # ISD depth tenths of mm -> inches


def _relative_humidity_from_temp_dew(temp_c: float | None, dew_c: float | None) -> float | None:
    if temp_c is None or dew_c is None:
        return None
    try:
        a, b = 17.625, 243.04
        numerator = math.exp((a * dew_c) / (b + dew_c))
        denominator = math.exp((a * temp_c) / (b + temp_c))
        return float(max(0.0, min(100.0, 100.0 * numerator / denominator)))
    except Exception:
        return None


def fetch_ncei_global_hourly(
    start_date: str,
    end_date: str,
    *,
    bbox: Sequence[float] = PR_BBOX,
    timeout: int = 180,
    session: requests.Session | None = None,
) -> pd.DataFrame:
    client = session or requests.Session()
    params = {
        "dataset": "global-hourly",
        "startDate": start_date,
        "endDate": end_date,
        "bbox": bbox_param(bbox),
        "format": "csv",
        "includeAttributes": "false",
        "includeStationName": "true",
        "includeStationLocation": "true",
    }
    response = client.get(NCEI_DATA_URL, params=params, timeout=timeout)
    response.raise_for_status()
    text = response.text.strip()
    if not text:
        return pd.DataFrame()
    return pd.read_csv(io.StringIO(text), low_memory=False)


def normalize_ncei_global_hourly(raw: pd.DataFrame, *, island: str = "Puerto Rico") -> pd.DataFrame:
    if raw.empty:
        return pd.DataFrame()
    rows: list[dict[str, Any]] = []
    precip_columns = [column for column in ("AA1", "AA2", "AA3", "AA4") if column in raw.columns]

    for _, source_row in raw.iterrows():
        temp_c = _encoded_tenths(source_row.get("TMP"), {"+9999", "-9999", "9999"})
        dew_c = _encoded_tenths(source_row.get("DEW"), {"+9999", "-9999", "9999"})
        slp_hpa = _encoded_tenths(source_row.get("SLP"), {"99999", "+99999", "-99999"})
        wind_dir, wind_ms = _parse_wnd(source_row.get("WND"))
        precip: dict[int, float] = {}
        for column in precip_columns:
            period, amount = _parse_precip_group(source_row.get(column))
            if period is not None and amount is not None:
                precip[period] = max(precip.get(period, 0.0), amount)

        station = str(source_row.get("STATION") or source_row.get("station") or "").strip()
        valid_time = source_row.get("DATE") or source_row.get("date")
        lat = _to_float(source_row.get("LATITUDE"))
        lon = _to_float(source_row.get("LONGITUDE"))
        elevation = _to_float(source_row.get("ELEVATION"))
        if not station or valid_time is None or lat is None or lon is None:
            continue

        row = {
            "valid_time_utc": pd.to_datetime(valid_time, errors="coerce", utc=True),
            "station_id": station,
            "location_id": station,
            "station_name": str(source_row.get("NAME") or "").strip(),
            "island": island,
            "lat": lat,
            "lon": lon,
            "elevation_m": elevation,
            "observed_temp_f": None if temp_c is None else temp_c * 9.0 / 5.0 + 32.0,
            "observed_dewpoint_f": None if dew_c is None else dew_c * 9.0 / 5.0 + 32.0,
            "observed_relative_humidity": _relative_humidity_from_temp_dew(temp_c, dew_c),
            "observed_pressure_hpa": slp_hpa,
            "observed_wind_direction_deg": wind_dir,
            "observed_wind_speed_mph": None if wind_ms is None else wind_ms * 2.2369362921,
            "observed_precip_1h_in": precip.get(1),
            "observed_precip_6h_in": precip.get(6),
            "observed_precip_24h_in": precip.get(24),
            "observation_source": "NOAA/NCEI Global Hourly ISD",
        }
        gust = _to_float(source_row.get("GUST"))
        if gust is not None and gust < 900:
            row["observed_wind_gust_mph"] = gust * 2.2369362921
        rows.append(row)

    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out = out[out["valid_time_utc"].notna()].copy()
    out["valid_time_utc"] = pd.to_datetime(out["valid_time_utc"], utc=True).dt.floor("h")
    numeric = [column for column in out.columns if column.startswith("observed_") or column in {"lat", "lon", "elevation_m"}]
    agg: dict[str, str] = {column: "mean" for column in numeric}
    for column in out.columns:
        if column not in agg and column not in {"valid_time_utc", "station_id"}:
            agg[column] = "first"
    out = out.groupby(["station_id", "valid_time_utc"], as_index=False).agg(agg)

    augmented: list[pd.DataFrame] = []
    for _, group in out.groupby("station_id", sort=False):
        group = group.sort_values("valid_time_utc").copy()
        group = group.set_index("valid_time_utc")
        one_hour = pd.to_numeric(group.get("observed_precip_1h_in"), errors="coerce")
        if one_hour is not None:
            roll6 = one_hour.rolling("6h", min_periods=4).sum()
            roll24 = one_hour.rolling("24h", min_periods=18).sum()
            if "observed_precip_6h_in" in group:
                group["observed_precip_6h_in"] = pd.to_numeric(group["observed_precip_6h_in"], errors="coerce").combine_first(roll6)
            else:
                group["observed_precip_6h_in"] = roll6
            if "observed_precip_24h_in" in group:
                group["observed_precip_24h_in"] = pd.to_numeric(group["observed_precip_24h_in"], errors="coerce").combine_first(roll24)
            else:
                group["observed_precip_24h_in"] = roll24
        augmented.append(group.reset_index())
    return pd.concat(augmented, ignore_index=True) if augmented else out


def locations_from_observations(observations: pd.DataFrame) -> list[Location]:
    if observations.empty:
        return []
    required = {"station_id", "lat", "lon"}
    missing = required - set(observations.columns)
    if missing:
        raise ValueError(f"Observation table lacks location columns: {sorted(missing)}")
    locations: list[Location] = []
    for station_id, group in observations.groupby("station_id"):
        first = group.iloc[0]
        locations.append(
            Location(
                location_id=str(station_id),
                lat=float(first["lat"]),
                lon=float(first["lon"]),
                name=str(first.get("station_name") or ""),
                island=str(first.get("island") or "Puerto Rico"),
                elevation_m=_to_float(first.get("elevation_m")),
            )
        )
    return locations


def build_grib_object(source: str, date: str, cycle: int, forecast_hour: int, member: str | None = None) -> GribObject:
    date = str(date).replace("-", "")
    cycle = int(cycle)
    forecast_hour = int(forecast_hour)
    if cycle not in {0, 6, 12, 18}:
        raise ValueError("cycle must be one of 00, 06, 12, 18 UTC")
    hh = f"{cycle:02d}"

    if source == "gfs":
        key = f"gfs.{date}/{hh}/atmos/gfs.t{hh}z.pgrb2.0p25.f{forecast_hour:03d}"
        return GribObject(source, date, cycle, forecast_hour, None, S3_BASES["gfs"], key)
    if source in {"gefs_mean", "gefs_spread"}:
        filename = "geavg" if source == "gefs_mean" else "gespr"
        key = f"gefs.{date}/{hh}/atmos/pgrb2sp25/{filename}.t{hh}z.pgrb2s.0p25.f{forecast_hour:03d}"
        return GribObject(source, date, cycle, forecast_hour, filename, S3_BASES["gefs"], key)
    if source == "gefs_member":
        member = (member or "p01").lower()
        if member == "c00":
            filename = "gec00"
        elif re.fullmatch(r"p\d{2}", member):
            filename = f"ge{member}"
        else:
            raise ValueError("GEFS member must be c00 or p01-p30")
        key = f"gefs.{date}/{hh}/atmos/pgrb2sp25/{filename}.t{hh}z.pgrb2s.0p25.f{forecast_hour:03d}"
        return GribObject(source, date, cycle, forecast_hour, member, S3_BASES["gefs"], key)
    if source == "nam_pr":
        key = f"nam.{date}/nam.t{hh}z.priconest.hiresf{forecast_hour:02d}.tm00.grib2"
        return GribObject(source, date, cycle, forecast_hour, None, S3_BASES["nam_pr"], key)
    raise ValueError(f"Unsupported NOAA model source: {source}")


def parse_idx(text: str) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        parts = line.split(":", 2)
        if len(parts) < 3:
            continue
        try:
            message_no = int(parts[0])
            offset = int(parts[1])
        except ValueError:
            continue
        entries.append({"message": message_no, "offset": offset, "description": parts[2], "line": line})
    return entries


def select_idx_ranges(
    entries: Sequence[dict[str, Any]],
    *,
    patterns: Sequence[str] = DEFAULT_GRIB_PATTERNS,
    content_length: int | None = None,
) -> list[tuple[int, int | None, str]]:
    regexes = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
    selected: list[tuple[int, int | None, str]] = []
    for index, entry in enumerate(entries):
        line = str(entry.get("line") or entry.get("description") or "")
        if not any(regex.search(line) for regex in regexes):
            continue
        start = int(entry["offset"])
        if index + 1 < len(entries):
            end: int | None = int(entries[index + 1]["offset"]) - 1
        elif content_length is not None:
            end = int(content_length) - 1
        else:
            end = None
        selected.append((start, end, line))
    return selected


def download_grib_subset(
    grib: GribObject,
    destination: str | Path,
    *,
    patterns: Sequence[str] = DEFAULT_GRIB_PATTERNS,
    timeout: int = 180,
    session: requests.Session | None = None,
) -> dict[str, Any]:
    client = session or requests.Session()
    idx_response = client.get(grib.idx_url, timeout=timeout)
    idx_response.raise_for_status()
    entries = parse_idx(idx_response.text)
    if not entries:
        raise RuntimeError(f"No GRIB index entries found: {grib.idx_url}")

    head = client.head(grib.url, timeout=timeout, allow_redirects=True)
    content_length = _to_float(head.headers.get("Content-Length")) if head.ok else None
    ranges = select_idx_ranges(entries, patterns=patterns, content_length=int(content_length) if content_length else None)
    if not ranges:
        raise RuntimeError(f"No requested meteorological fields found in {grib.idx_url}")

    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    bytes_written = 0
    with destination.open("wb") as output:
        for start, end, _ in ranges:
            range_value = f"bytes={start}-" if end is None else f"bytes={start}-{end}"
            response = client.get(grib.url, headers={"Range": range_value}, timeout=timeout)
            if response.status_code not in {200, 206}:
                response.raise_for_status()
            output.write(response.content)
            bytes_written += len(response.content)

    return {
        "source": grib.source,
        "date": grib.date,
        "cycle": grib.cycle,
        "forecast_hour": grib.forecast_hour,
        "member": grib.member,
        "object_url": grib.url,
        "index_url": grib.idx_url,
        "destination": str(destination),
        "selected_messages": len(ranges),
        "bytes_written": bytes_written,
        "downloaded_at_utc": utc_now_iso(),
    }


def _safe_codes_get(eccodes: Any, gid: Any, key: str, default: Any = None) -> Any:
    try:
        return eccodes.codes_get(gid, key)
    except Exception:
        return default


def _grib_field_name(short_name: str, level_type: str, level: float | int | None) -> str | None:
    short = short_name.lower()
    level_value = float(level) if level is not None else None
    if short in {"2t", "t", "tmp"} and level_type == "heightAboveGround" and level_value == 2:
        return "temp_f"
    if short in {"2d", "dpt", "d2m"} and level_type == "heightAboveGround" and level_value == 2:
        return "dewpoint_f"
    if short in {"r", "rh"} and level_type == "heightAboveGround" and level_value == 2:
        return "relative_humidity"
    if short in {"10u", "u", "ugrd"} and level_type == "heightAboveGround" and level_value == 10:
        return "u10_ms"
    if short in {"10v", "v", "vgrd"} and level_type == "heightAboveGround" and level_value == 10:
        return "v10_ms"
    if short in {"gust", "gustsfc"}:
        return "wind_gust_mph"
    if short in {"tp", "apcp"}:
        return "precip_in"
    if short in {"prmsl", "msl"}:
        return "pressure_hpa"
    if short in {"pwat", "pwat1"}:
        return "pwat_kg_m2"
    if short == "cape" and level_type in {"surface", "heightAboveGround"}:
        return "cape_jkg"
    if short == "cin" and level_type in {"surface", "heightAboveGround"}:
        return "cin_jkg"
    return None


def _convert_grib_value(field_name: str, value: float) -> float:
    if field_name in {"temp_f", "dewpoint_f"}:
        return (value - 273.15) * 9.0 / 5.0 + 32.0
    if field_name == "wind_gust_mph":
        return value * 2.2369362921
    if field_name == "precip_in":
        return value / 25.4
    if field_name == "pressure_hpa":
        return value / 100.0
    return value


def extract_grib_points(
    path: str | Path,
    locations: Sequence[Location],
    *,
    source: str,
    run_time_utc: datetime | None = None,
    forecast_hour: int | None = None,
) -> pd.DataFrame:
    try:
        import eccodes  # type: ignore
    except Exception as exc:
        raise RuntimeError(
            "GRIB extraction requires the optional training dependencies. Install requirements-training.txt."
        ) from exc

    prefix = source
    rows: dict[tuple[str, pd.Timestamp], dict[str, Any]] = {}
    with Path(path).open("rb") as handle:
        while True:
            gid = eccodes.codes_grib_new_from_file(handle)
            if gid is None:
                break
            try:
                short_name = str(_safe_codes_get(eccodes, gid, "shortName", ""))
                level_type = str(_safe_codes_get(eccodes, gid, "typeOfLevel", ""))
                level = _safe_codes_get(eccodes, gid, "level", None)
                field_name = _grib_field_name(short_name, level_type, level)
                if not field_name:
                    continue

                validity_date = int(_safe_codes_get(eccodes, gid, "validityDate", 0) or 0)
                validity_time = int(_safe_codes_get(eccodes, gid, "validityTime", 0) or 0)
                if validity_date:
                    valid_dt = datetime.strptime(f"{validity_date:08d}{validity_time:04d}", "%Y%m%d%H%M").replace(tzinfo=timezone.utc)
                elif run_time_utc is not None:
                    valid_dt = run_time_utc + timedelta(hours=int(forecast_hour or 0))
                else:
                    continue

                for location in locations:
                    nearest = eccodes.codes_grib_find_nearest(gid, float(location.lat), float(location.lon))[0]
                    value = float(nearest["value"])
                    converted = _convert_grib_value(field_name, value)
                    key = (location.location_id, pd.Timestamp(valid_dt))
                    row = rows.setdefault(
                        key,
                        {
                            "location_id": location.location_id,
                            "station_id": location.location_id,
                            "station_name": location.name,
                            "island": location.island,
                            "lat": location.lat,
                            "lon": location.lon,
                            "elevation_m": location.elevation_m,
                            "valid_time_utc": pd.Timestamp(valid_dt),
                        },
                    )
                    row[f"{prefix}_{field_name}"] = converted
                    row[f"{prefix}_grid_distance_km"] = float(nearest.get("distance", np.nan))
                    if run_time_utc is not None:
                        row[f"{prefix}_run_time_utc"] = pd.Timestamp(run_time_utc)
                    if forecast_hour is not None:
                        row[f"{prefix}_lead_hours"] = int(forecast_hour)
            finally:
                eccodes.codes_release(gid)
    return pd.DataFrame(list(rows.values()))


def merge_training_sources(observations: pd.DataFrame, model_frames: Sequence[pd.DataFrame]) -> pd.DataFrame:
    if observations.empty:
        raise ValueError("Observations are required before model predictors can be merged.")
    base = observations.copy()
    base["valid_time_utc"] = pd.to_datetime(base["valid_time_utc"], utc=True).dt.floor("h")
    if "location_id" not in base.columns:
        base["location_id"] = base["station_id"].astype(str)

    for frame in model_frames:
        if frame is None or frame.empty:
            continue
        current = frame.copy()
        current["valid_time_utc"] = pd.to_datetime(current["valid_time_utc"], utc=True).dt.floor("h")
        if "location_id" not in current.columns:
            current["location_id"] = current["station_id"].astype(str)
        lead_columns = [column for column in current.columns if column.endswith("_lead_hours")]
        sort_columns = ["location_id", "valid_time_utc"] + lead_columns
        current = current.sort_values(sort_columns, kind="stable")
        current = current.drop_duplicates(["location_id", "valid_time_utc"], keep="first")
        keep = [
            column
            for column in current.columns
            if column in {"location_id", "valid_time_utc"}
            or column.startswith(("gfs_", "gefs_", "nam_pr_", "mrms_", "goes_", "nws_", "ndbc_"))
        ]
        base = base.merge(current[keep], on=["location_id", "valid_time_utc"], how="left")
    return base.sort_values(["location_id", "valid_time_utc"], kind="stable").reset_index(drop=True)


def write_manifest(path: str | Path, payload: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str), encoding="utf-8")


def manifest_summary(paths: Iterable[str | Path]) -> dict[str, Any]:
    manifests: list[dict[str, Any]] = []
    for raw_path in paths:
        path = Path(raw_path)
        if not path.exists() or path.stat().st_size == 0:
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["manifest_path"] = str(path)
            manifests.append(payload)
        except Exception:
            continue
    return {
        "manifests": manifests,
        "count": len(manifests),
        "sources": sorted({str(item.get("source")) for item in manifests if item.get("source")}),
        "total_rows": int(sum(int(item.get("rows", 0) or 0) for item in manifests)),
        "total_bytes": int(sum(int(item.get("bytes_written", 0) or 0) for item in manifests)),
    }
