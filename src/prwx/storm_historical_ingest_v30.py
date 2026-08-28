from __future__ import annotations

import json
import math
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import requests

HISTORICAL_INGEST_VERSION = "3.0.0"
ROOT = Path(__file__).resolve().parents[2]
TRAINING = ROOT / "data" / "training"
RAW = TRAINING / "raw"
PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"

HURDAT_INDEX_URL = "https://www.nhc.noaa.gov/data/hurdat/"
IBTRACS_NA_CSV_URL = "https://www.ncei.noaa.gov/data/international-best-track-archive-for-climate-stewardship-ibtracs/v04r01/access/csv/ibtracs.NA.list.v04r01.csv"
AEWC_ACCESS_URL = "https://www.ncei.noaa.gov/data/african-easterly-wave-climatology/access/"
NCEP_REANALYSIS_URL = "https://psl.noaa.gov/data/reanalysis/"
ERA5_URL = "https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels"

TRAINING_TABLE = TRAINING / "storm_tracks_atlantic_training.csv"
TRAINING_META = PROCESSED / "storm_historical_training_v30.json"
SOURCES_META = PROCESSED / "storm_historical_sources_v30.json"

PR_REFERENCE = {"name": "Puerto Rico", "lat": 18.22, "lon": -66.59}


@dataclass(frozen=True)
class HistoricalSource:
    id: str
    name: str
    agency: str
    url: str
    role: str
    status: str
    notes: str


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def source_catalog() -> list[dict[str, str]]:
    sources = [
        HistoricalSource(
            "hurdat2_atlantic",
            "Atlantic hurricane database HURDAT2",
            "NOAA/NHC",
            HURDAT_INDEX_URL,
            "Primary Atlantic best-track training source for tropical depressions, storms and hurricanes.",
            "downloadable",
            "The downloader discovers the current HURDAT2 Atlantic text file from the NHC index before parsing.",
        ),
        HistoricalSource(
            "ibtracs_na",
            "IBTrACS North Atlantic CSV",
            "NOAA/NCEI",
            IBTRACS_NA_CSV_URL,
            "Independent/global best-track archive and future cross-check source.",
            "optional_large_download",
            "Used for validation and extension after the HURDAT2 baseline is working.",
        ),
        HistoricalSource(
            "aewc",
            "African Easterly Wave Climatology",
            "NOAA/NCEI",
            AEWC_ACCESS_URL,
            "Historical easterly-wave reference for wave-like disturbances.",
            "optional_next_stage",
            "Useful for wave/trough training but not needed to begin cyclone track training.",
        ),
        HistoricalSource(
            "ncep_reanalysis",
            "NCEP/NCAR Reanalysis",
            "NOAA/PSL",
            NCEP_REANALYSIS_URL,
            "Environmental steering-flow and synoptic context for troughs/waves.",
            "optional_gridded_next_stage",
            "Needed for 500/700/850-hPa wind, pressure, vorticity and moisture features.",
        ),
        HistoricalSource(
            "era5",
            "ERA5 hourly reanalysis",
            "Copernicus/ECMWF",
            ERA5_URL,
            "Higher-resolution environmental predictors and backtesting context.",
            "optional_credentials_required",
            "Requires Copernicus CDS access and is not downloaded by default in Render.",
        ),
    ]
    return [asdict(source) for source in sources]


def _ensure_dirs() -> None:
    for path in (TRAINING, RAW, PROCESSED, REPORTS):
        path.mkdir(parents=True, exist_ok=True)


def _download_text(url: str, timeout: int = 60) -> str:
    response = requests.get(url, timeout=timeout, headers={"User-Agent": "PR-WX-Historical-Trainer/3.0"})
    response.raise_for_status()
    return response.text


def discover_hurdat2_url() -> str:
    index = _download_text(HURDAT_INDEX_URL)
    matches = re.findall(r'href="([^"]*hurdat2-[^"]*atl[^"]*\.txt)"', index, flags=re.I)
    if not matches:
        matches = re.findall(r'href="([^"]*hurdat2-[^"]*\.txt)"', index, flags=re.I)
    if not matches:
        raise RuntimeError("No HURDAT2 text file was discovered in the NHC HURDAT index.")
    href = matches[-1]
    if href.startswith("http"):
        return href
    return HURDAT_INDEX_URL.rstrip("/") + "/" + href.lstrip("/")


def download_hurdat2() -> Path:
    _ensure_dirs()
    url = discover_hurdat2_url()
    text = _download_text(url, timeout=120)
    out = RAW / "hurdat2_atlantic_latest.txt"
    out.write_text(text, encoding="utf-8")
    (RAW / "hurdat2_atlantic_latest.url.txt").write_text(url + "\n", encoding="utf-8")
    return out


def _latlon(value: str) -> float:
    item = str(value).strip().upper()
    if not item:
        return math.nan
    sign = -1 if item.endswith(("S", "W")) else 1
    try:
        return sign * float(item[:-1])
    except ValueError:
        return math.nan


def _haversine_km(lat1: float, lon1: float, lat2: float = PR_REFERENCE["lat"], lon2: float = PR_REFERENCE["lon"]) -> float:
    radius = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(a))


def _bearing_to_pr(lat: float, lon: float) -> float:
    lat1, lat2 = math.radians(lat), math.radians(PR_REFERENCE["lat"])
    dlon = math.radians(PR_REFERENCE["lon"] - lon)
    y = math.sin(dlon) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    return (math.degrees(math.atan2(y, x)) + 360) % 360


def parse_hurdat2(path: Path | None = None) -> pd.DataFrame:
    source = path or RAW / "hurdat2_atlantic_latest.txt"
    if not source.exists():
        source = download_hurdat2()
    rows: list[dict[str, Any]] = []
    storm_id = storm_name = ""
    storm_records = 0
    for raw_line in source.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        parts = [part.strip() for part in line.split(",")]
        if re.match(r"^[A-Z]{2}\d{6}$", parts[0] if parts else ""):
            storm_id = parts[0]
            storm_name = parts[1] if len(parts) > 1 else "UNNAMED"
            try:
                storm_records = int(parts[2])
            except Exception:
                storm_records = 0
            continue
        if len(parts) < 7 or not storm_id:
            continue
        date_s, time_s = parts[0], parts[1]
        try:
            valid = datetime.strptime(date_s + time_s.zfill(4), "%Y%m%d%H%M").replace(tzinfo=timezone.utc)
        except Exception:
            continue
        lat, lon = _latlon(parts[4]), _latlon(parts[5])
        if math.isnan(lat) or math.isnan(lon):
            continue
        try:
            wind = float(parts[6])
        except Exception:
            wind = math.nan
        try:
            pressure = float(parts[7]) if len(parts) > 7 and parts[7] not in {"", "-999"} else math.nan
        except Exception:
            pressure = math.nan
        rows.append(
            {
                "source": "hurdat2_atlantic",
                "storm_id": storm_id,
                "storm_name": storm_name,
                "storm_records_declared": storm_records,
                "valid_time_utc": valid.isoformat(),
                "year": valid.year,
                "month": valid.month,
                "day": valid.day,
                "hour": valid.hour,
                "record_id": parts[2] if len(parts) > 2 else "",
                "status": parts[3] if len(parts) > 3 else "",
                "lat": lat,
                "lon": lon,
                "max_wind_kt": wind,
                "min_pressure_mb": pressure,
                "distance_to_pr_km": _haversine_km(lat, lon),
                "bearing_to_pr_deg": _bearing_to_pr(lat, lon),
            }
        )
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    frame = frame.sort_values(["storm_id", "valid_time_utc"]).reset_index(drop=True)
    frame["storm_sequence"] = frame.groupby("storm_id").cumcount()
    frame["wind_trend_6h_kt"] = frame.groupby("storm_id")["max_wind_kt"].diff().fillna(0)
    frame["pressure_trend_6h_mb"] = frame.groupby("storm_id")["min_pressure_mb"].diff().fillna(0)
    frame["distance_trend_6h_km"] = frame.groupby("storm_id")["distance_to_pr_km"].diff().fillna(0)
    return frame


def build_pr_trajectory_training_table(frame: pd.DataFrame | None = None) -> pd.DataFrame:
    data = frame if frame is not None else parse_hurdat2()
    if data.empty:
        return data
    rows: list[dict[str, Any]] = []
    for storm_id, group in data.groupby("storm_id", sort=False):
        group = group.sort_values("valid_time_utc").reset_index(drop=True)
        for idx, row in group.iterrows():
            future = group.iloc[idx : min(idx + 13, len(group))]  # current + 72 h at 6 h intervals
            min_distance = float(future["distance_to_pr_km"].min())
            closest_idx = int(future["distance_to_pr_km"].idxmin())
            hours_to_closest = max(0, (closest_idx - idx) * 6)
            out = row.to_dict()
            out.update(
                {
                    "target_min_distance_72h_km": min_distance,
                    "target_hours_to_closest_72h": hours_to_closest,
                    "target_approach_500km_72h": int(min_distance <= 500),
                    "target_approach_300km_72h": int(min_distance <= 300),
                    "target_direct_pr_150km_72h": int(min_distance <= 150),
                    "target_high_wind_near_pr_72h": int(min_distance <= 300 and float(row.get("max_wind_kt") or 0) >= 50),
                }
            )
            rows.append(out)
    table = pd.DataFrame(rows)
    if table.empty:
        return table
    # Candidate feature set for AI training.
    table["month_sin"] = table["month"].map(lambda m: math.sin(2 * math.pi * float(m) / 12))
    table["month_cos"] = table["month"].map(lambda m: math.cos(2 * math.pi * float(m) / 12))
    table["hour_sin"] = table["hour"].map(lambda h: math.sin(2 * math.pi * float(h) / 24))
    table["hour_cos"] = table["hour"].map(lambda h: math.cos(2 * math.pi * float(h) / 24))
    return table


def write_training_table(download: bool = True) -> dict[str, Any]:
    _ensure_dirs()
    if download or not (RAW / "hurdat2_atlantic_latest.txt").exists():
        source_path = download_hurdat2()
    else:
        source_path = RAW / "hurdat2_atlantic_latest.txt"
    parsed = parse_hurdat2(source_path)
    training = build_pr_trajectory_training_table(parsed)
    training.to_csv(TRAINING_TABLE, index=False)
    meta = training_readiness(training)
    meta.update(
        {
            "version": HISTORICAL_INGEST_VERSION,
            "generated_at_utc": utc_now_iso(),
            "raw_hurdat2_path": str(source_path),
            "training_table": str(TRAINING_TABLE),
            "sources": source_catalog(),
        }
    )
    TRAINING_META.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    SOURCES_META.write_text(json.dumps({"sources": source_catalog(), "generated_at_utc": utc_now_iso()}, indent=2, ensure_ascii=False), encoding="utf-8")
    return meta


def training_readiness(table: pd.DataFrame | None = None) -> dict[str, Any]:
    if table is None:
        if TRAINING_TABLE.exists() and TRAINING_TABLE.stat().st_size:
            table = pd.read_csv(TRAINING_TABLE)
        else:
            table = pd.DataFrame()
    rows = int(len(table))
    storms = int(table["storm_id"].nunique()) if rows and "storm_id" in table.columns else 0
    years = int(table["year"].nunique()) if rows and "year" in table.columns else 0
    approaches_500 = int(table["target_approach_500km_72h"].sum()) if rows and "target_approach_500km_72h" in table.columns else 0
    direct_150 = int(table["target_direct_pr_150km_72h"].sum()) if rows and "target_direct_pr_150km_72h" in table.columns else 0
    useful = rows >= 2500 and storms >= 50 and years >= 30 and approaches_500 >= 25
    operational_candidate = rows >= 10000 and storms >= 150 and years >= 70 and approaches_500 >= 100 and direct_150 >= 10
    return {
        "available": rows > 0,
        "rows": rows,
        "storms": storms,
        "years": years,
        "approach_500km_cases": approaches_500,
        "direct_150km_cases": direct_150,
        "research_ready": useful,
        "operational_candidate": operational_candidate,
        "production_validated": False,
        "note": "This builds an experimental PR approach training table from official best-track history. Operational use requires independent meteorological backtesting.",
    }


def status() -> dict[str, Any]:
    meta = {}
    if TRAINING_META.exists() and TRAINING_META.stat().st_size:
        try:
            meta = json.loads(TRAINING_META.read_text(encoding="utf-8"))
        except Exception:
            meta = {}
    return {
        "version": HISTORICAL_INGEST_VERSION,
        "training_table_exists": TRAINING_TABLE.exists(),
        "training_table": str(TRAINING_TABLE),
        "training_table_size_bytes": TRAINING_TABLE.stat().st_size if TRAINING_TABLE.exists() else 0,
        "raw_hurdat2_exists": (RAW / "hurdat2_atlantic_latest.txt").exists(),
        "sources": source_catalog(),
        "readiness": training_readiness(),
        "metadata": meta,
    }


def sample_schema() -> dict[str, Any]:
    return {
        "required_targets": [
            "target_min_distance_72h_km",
            "target_approach_500km_72h",
            "target_approach_300km_72h",
            "target_direct_pr_150km_72h",
        ],
        "core_features": [
            "lat",
            "lon",
            "max_wind_kt",
            "min_pressure_mb",
            "distance_to_pr_km",
            "bearing_to_pr_deg",
            "wind_trend_6h_kt",
            "pressure_trend_6h_mb",
            "distance_trend_6h_km",
            "month_sin",
            "month_cos",
            "hour_sin",
            "hour_cos",
        ],
        "optional_next_stage_features": [
            "gfs_850_steering_u",
            "gfs_850_steering_v",
            "gfs_500_height_anomaly",
            "gefs_track_spread_km",
            "era5_vorticity_700hpa",
            "olr_anomaly",
            "aewc_wave_id",
            "saharan_air_layer_index",
        ],
    }
