from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable


@dataclass(frozen=True)
class WeatherSource:
    id: str
    name: str
    agency: str
    kind: str
    coverage: tuple[str, ...]
    resolution: str
    cadence: str
    role: str
    operational_use: str
    status: str
    notes: str = ""


SOURCES: tuple[WeatherSource, ...] = (
    WeatherSource(
        id="nws_sju_grid",
        name="NWS San Juan Digital Forecast Grid",
        agency="NOAA/NWS",
        kind="official_forecast",
        coverage=("Puerto Rico", "U.S. Virgin Islands"),
        resolution="~2.5 km grid",
        cadence="updated by WFO forecast operations",
        role="Primary official local guidance and calibration reference for Puerto Rico",
        operational_use="active",
        status="supported",
    ),
    WeatherSource(
        id="nam_pr_nest",
        name="NAM Puerto Rico Nest",
        agency="NOAA/NCEP",
        kind="regional_nwp",
        coverage=("Puerto Rico regional domain",),
        resolution="2.5 km",
        cadence="4 cycles/day; hourly guidance to about 60 h",
        role="High-resolution short-range predictor for Puerto Rico",
        operational_use="ingestion_next",
        status="supported",
        notes="Use priconest products; do not substitute CONUS-only HRRR.",
    ),
    WeatherSource(
        id="gfs",
        name="Global Forecast System",
        agency="NOAA/NCEP",
        kind="global_nwp",
        coverage=("Puerto Rico", "Caribbean", "Atlantic", "global"),
        resolution="~13 km native global guidance",
        cadence="00/06/12/18 UTC",
        role="Deterministic large-scale atmospheric backbone",
        operational_use="ingestion_next",
        status="supported",
    ),
    WeatherSource(
        id="gefs",
        name="Global Ensemble Forecast System",
        agency="NOAA/NCEP",
        kind="global_ensemble",
        coverage=("Puerto Rico", "Caribbean", "Atlantic", "global"),
        resolution="~25 km ensemble guidance",
        cadence="00/06/12/18 UTC",
        role="Forecast uncertainty, probability and scenario spread",
        operational_use="ingestion_next",
        status="supported",
    ),
    WeatherSource(
        id="mrms_caribbean",
        name="MRMS Caribbean QPE",
        agency="NOAA/NWS/NSSL",
        kind="radar_qpe",
        coverage=("Puerto Rico", "Caribbean MRMS domain"),
        resolution="high-resolution radar-derived mosaics",
        cadence="near real time; accumulation products 15 min to 72 h",
        role="Observed/estimated rainfall and flood nowcasting input",
        operational_use="active",
        status="supported",
    ),
    WeatherSource(
        id="tjua_nexrad",
        name="TJUA NEXRAD Cayey",
        agency="NOAA/NWS",
        kind="weather_radar",
        coverage=("Puerto Rico", "nearby waters"),
        resolution="radar volume scans",
        cadence="near real time",
        role="Convection, rainfall intensity and storm motion around Puerto Rico",
        operational_use="ingestion_next",
        status="supported",
    ),
    WeatherSource(
        id="goes19",
        name="GOES-19 / GOES-East ABI",
        agency="NOAA/NESDIS",
        kind="satellite",
        coverage=("Puerto Rico", "Caribbean", "Tropical Atlantic"),
        resolution="multi-spectral ABI imagery",
        cadence="Puerto Rico/Caribbean sectors commonly update every 10 min",
        role="Cloud, water-vapor, convection and tropical-wave nowcasting",
        operational_use="ingestion_next",
        status="supported",
    ),
    WeatherSource(
        id="nhc",
        name="National Hurricane Center official products",
        agency="NOAA/NWS/NHC",
        kind="tropical_guidance",
        coverage=("Caribbean", "North Atlantic"),
        resolution="storm products",
        cadence="event-driven operational advisories",
        role="Official tropical cyclone tracks, hazards and advisories",
        operational_use="active_or_next",
        status="supported",
    ),
    WeatherSource(
        id="hafs",
        name="Hurricane Analysis and Forecast System",
        agency="NOAA/NCEP",
        kind="tropical_nwp",
        coverage=("active tropical cyclones affecting Atlantic/Caribbean"),
        resolution="storm-following high-resolution nests",
        cadence="active-storm cycles",
        role="Tropical cyclone track, intensity, rainfall and rapid-intensification guidance",
        operational_use="conditional_next",
        status="supported",
    ),
    WeatherSource(
        id="gfs_wave",
        name="GFS-Wave / WAVEWATCH III",
        agency="NOAA/NCEP",
        kind="marine_nwp",
        coverage=("Puerto Rico", "Caribbean", "Atlantic", "global oceans"),
        resolution="global/regional nested wave grids",
        cadence="00/06/12/18 UTC",
        role="Wave height, period, swell and marine hazard guidance",
        operational_use="ingestion_next",
        status="supported",
    ),
    WeatherSource(
        id="ndbc",
        name="National Data Buoy Center",
        agency="NOAA/NWS/NDBC",
        kind="marine_observation",
        coverage=("Puerto Rico", "Caribbean", "Atlantic"),
        resolution="station/buoy observations",
        cadence="near real time by station",
        role="Marine verification, wind, waves, pressure and sea state",
        operational_use="training_and_verification_next",
        status="supported",
    ),
    WeatherSource(
        id="ncei_isd",
        name="NCEI Integrated Surface Database",
        agency="NOAA/NCEI",
        kind="historical_observation",
        coverage=("Puerto Rico", "Caribbean", "global stations"),
        resolution="hourly/synoptic station observations",
        cadence="historical archive updated daily",
        role="Primary long-term training and verification observations",
        operational_use="training_next",
        status="supported",
    ),
)


EXCLUDED_CORE_MODELS = (
    {
        "id": "hrrr_operational",
        "reason": "Operational HRRR core domains are CONUS and Alaska; experimental Caribbean graphics must not be treated as the operational Puerto Rico backbone.",
    },
)


def source_registry() -> list[dict]:
    return [asdict(source) for source in SOURCES]


def sources_for_area(area: str) -> list[dict]:
    key = area.casefold().strip()
    selected: list[WeatherSource] = []
    for source in SOURCES:
        coverage = " ".join(source.coverage).casefold()
        if key in {"pr", "puerto rico"} and "puerto rico" in coverage:
            selected.append(source)
        elif key in {"caribbean", "caribe"} and ("caribbean" in coverage or "global" in coverage or "atlantic" in coverage):
            selected.append(source)
        elif key in coverage:
            selected.append(source)
    return [asdict(source) for source in selected]


def source_ids(items: Iterable[WeatherSource] = SOURCES) -> set[str]:
    return {item.id for item in items}
