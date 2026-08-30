from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

VERSION = "3.6.0"
MODEL_CODE = "AURORA-3D"
MODEL_NAME = "AURORA Caribe 3D Command Center"
MODEL_FULL_NAME = "AURORA Caribe-Atlántico 3D Atmospheric Intelligence"
ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"

PR_CENTER = {"name": "Puerto Rico", "lat": 18.2208, "lon": -66.5901, "z": 0.16}

MUNICIPAL_NODES = [
    {"name": "San Juan", "lat": 18.4655, "lon": -66.1057, "risk": 61, "layer": "metro_north"},
    {"name": "Ponce", "lat": 18.0111, "lon": -66.6141, "risk": 54, "layer": "south_urban"},
    {"name": "Juana Díaz", "lat": 18.0525, "lon": -66.5063, "risk": 49, "layer": "south_central"},
    {"name": "San Germán", "lat": 18.0816, "lon": -67.0449, "risk": 43, "layer": "west_interior"},
    {"name": "Fajardo", "lat": 18.3258, "lon": -65.6524, "risk": 58, "layer": "east_coast"},
    {"name": "Mayagüez", "lat": 18.2011, "lon": -67.1396, "risk": 51, "layer": "west_coast"},
    {"name": "Arecibo", "lat": 18.4724, "lon": -66.7157, "risk": 46, "layer": "north_coast"},
    {"name": "Caguas", "lat": 18.2341, "lon": -66.0485, "risk": 52, "layer": "central_valley"},
]

DUST_STREAMS = [
    {"id": "sahara_core", "name": "Pulso Sahara-Atlántico", "altitude_km": 3.8, "intensity": 0.72, "points": [[-22, 17], [-35, 16], [-48, 15.5], [-58, 16.1], [-66.2, 18.1]]},
    {"id": "sal_north", "name": "Borde norte SAL", "altitude_km": 4.6, "intensity": 0.48, "points": [[-30, 22], [-44, 21.5], [-57.5, 20.8], [-66, 19.2]]},
    {"id": "deep_caribbean", "name": "Corredor Caribe profundo", "altitude_km": 2.7, "intensity": 0.38, "points": [[-38, 10], [-50, 11], [-61.5, 13], [-68, 15]]},
]

TROPICAL_STREAMS = [
    {"id": "atlantic_wave", "name": "Onda tropical experimental", "risk": 44, "points": [[-45, 12.5], [-51, 13.3], [-58, 15.2], [-64, 17.4], [-66.6, 18.2]]},
    {"id": "north_recurve", "name": "Corredor de recurvatura norte", "risk": 31, "points": [[-52, 20.5], [-58, 21.4], [-64, 22.2], [-69, 23.0]]},
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def model_identity() -> dict[str, Any]:
    return {
        "model_code": MODEL_CODE,
        "model_name": MODEL_NAME,
        "full_name": MODEL_FULL_NAME,
        "version": VERSION,
        "design_language": "holographic_3d_command_center",
        "scope": "Puerto Rico, Caribe, Atlántico tropical, polvo del Sahara y trayectorias tropicales",
        "status": "experimental_visual_intelligence",
        "official_warning_policy": "No emite avisos oficiales. Validar con NHC, NWS San Juan, agencias de salud y manejo de emergencias.",
    }


def scene_layers() -> dict[str, Any]:
    return {
        "version": VERSION,
        "layers": [
            {"id": "caribbean_globe", "name": "Globo/océano 3D", "type": "base_3d"},
            {"id": "puerto_rico_nodes", "name": "Torres municipales IA", "type": "risk_nodes"},
            {"id": "sahara_dust_streams", "name": "Polvo del Sahara volumétrico", "type": "aerosol_stream"},
            {"id": "tropical_trajectory_streams", "name": "Trayectorias tropicales 3D", "type": "storm_stream"},
            {"id": "risk_dome", "name": "Domo de riesgo AURORA", "type": "holographic_dome"},
            {"id": "atmospheric_grid", "name": "Rejilla atmosférica Caribe-Atlántico", "type": "spatial_grid"},
        ],
    }


def scene_payload() -> dict[str, Any]:
    return {
        "model": model_identity(),
        "generated_at_utc": utc_now_iso(),
        "reference_point": PR_CENTER,
        "municipal_nodes": MUNICIPAL_NODES,
        "dust_streams": DUST_STREAMS,
        "tropical_streams": TROPICAL_STREAMS,
        "scene": {
            "camera": {"position": [0, 8.5, 13.5], "target": [0, 0, 0]},
            "coordinate_frame": {"lon_min": -72, "lon_max": -58, "lat_min": 10, "lat_max": 24},
            "visual_mode": "aurora_holographic_3d",
            "animation": {
                "dust_particle_speed": 0.006,
                "storm_orbit_speed": 0.009,
                "node_pulse_speed": 0.018,
                "auto_rotate": True,
            },
        },
        "summary_es": "Escena 3D experimental de AURORA con polvo del Sahara, trayectorias tropicales, nodos municipales y domo de riesgo sobre Puerto Rico.",
        "disclaimer": "Visualización experimental. No sustituye avisos oficiales meteorológicos, de salud o manejo de emergencias.",
    }


def status() -> dict[str, Any]:
    return {
        "status": "ok",
        "model": model_identity(),
        "scene_endpoint": "/aurora-caribe/3d/scene",
        "layers_endpoint": "/aurora-caribe/3d/layers",
        "desktop_component": "desktop/aurora-3d-command-center.js",
        "style_component": "desktop/aurora-3d.css",
        "three_js_mode": "browser_client_rendering_with_css_fallback",
    }


def report() -> dict[str, Any]:
    payload = scene_payload()
    return {
        "model": payload["model"],
        "headline": "AURORA 3D Command Center integra mapas, polvo del Sahara, trayectorias tropicales y riesgo municipal en una experiencia holográfica.",
        "capabilities": [
            "Mapa 3D no tradicional del Caribe y Atlántico",
            "Flujos volumétricos para polvo del Sahara",
            "Trayectorias tropicales con animación",
            "Torres municipales por riesgo IA",
            "Domo de riesgo sobre Puerto Rico",
            "Fallback accesible si WebGL o Three.js no cargan",
        ],
        "payload_preview": {
            "municipal_nodes": len(payload["municipal_nodes"]),
            "dust_streams": len(payload["dust_streams"]),
            "tropical_streams": len(payload["tropical_streams"]),
        },
        "disclaimer": payload["disclaimer"],
    }
