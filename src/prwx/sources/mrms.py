from __future__ import annotations

MRMS_QPE_IMAGESERVER = "https://mapservices.weather.noaa.gov/raster/rest/services/obs/mrms_qpe/ImageServer"


def mrms_qpe_identify_url(lat: float, lon: float, tolerance: int = 2) -> str:
    """Build an ArcGIS ImageServer identify URL for MRMS QPE.

    This returns a URL that can be opened with requests or in a browser. For production,
    prefer a GIS workflow that clips rasters to Puerto Rico and samples all grid cells.
    """
    geometry = f"{lon},{lat}"
    return (
        f"{MRMS_QPE_IMAGESERVER}/identify?"
        f"f=json&geometry={geometry}&geometryType=esriGeometryPoint&"
        f"returnGeometry=false&tolerance={tolerance}"
    )
