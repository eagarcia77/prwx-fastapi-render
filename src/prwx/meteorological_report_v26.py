from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from prwx.caribbean_model_v20 import MODEL_NAME, MODEL_VERSION, TARGET_SPECS
from prwx.caribbean_sources import source_registry, sources_for_area

REPORT_VERSION = "2.6.0"
REPORT_TITLE = "Informe meteorológico Caribe-Atlántico"

ADDITIONAL_ATLANTIC_TRAINING_SOURCES: list[dict[str, Any]] = [
    {
        "id": "era5_reanalysis",
        "name": "ERA5 hourly reanalysis",
        "agency": "Copernicus/ECMWF",
        "kind": "historical_reanalysis",
        "coverage": ("Puerto Rico", "Caribbean", "Atlantic", "global"),
        "resolution": "global hourly reanalysis",
        "cadence": "historical archive",
        "role": "Retrospective training, climatology and independent atmospheric context.",
        "operational_use": "training_next",
        "status": "supported_next",
        "notes": "Use for backtesting and not as a real-time official warning source.",
    },
    {
        "id": "oisst",
        "name": "NOAA Daily Optimum Interpolation Sea Surface Temperature",
        "agency": "NOAA/NCEI",
        "kind": "sea_surface_temperature",
        "coverage": ("Caribbean", "Atlantic", "global oceans"),
        "resolution": "0.25 degree daily SST grid",
        "cadence": "daily",
        "role": "Sea-surface temperature predictor for tropical-wave and cyclone environment.",
        "operational_use": "training_and_analysis_next",
        "status": "supported_next",
        "notes": "Use as ocean-energy input and for seasonal/tropical context.",
    },
]


def extended_source_registry() -> list[dict[str, Any]]:
    existing = source_registry()
    existing_ids = {item.get("id") for item in existing}
    out = list(existing)
    for item in ADDITIONAL_ATLANTIC_TRAINING_SOURCES:
        if item["id"] not in existing_ids:
            out.append(item)
    return out


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def model_feature_matrix() -> list[dict[str, Any]]:
    return [
        {
            "domain": "Atmósfera sinóptica",
            "sources": ["gfs", "gefs"],
            "features": ["temperatura", "viento", "presión", "humedad", "precipitación", "incertidumbre de ensamble"],
            "targets_supported": ["temperatura", "lluvia 1h/6h/24h", "viento", "presión", "humedad"],
            "training_role": "Base de predicción determinística y probabilística para Caribe y Atlántico.",
        },
        {
            "domain": "Ciclones tropicales",
            "sources": ["nhc", "hafs"],
            "features": ["trayectoria", "cono", "intensidad", "distancia al centro", "radio de vientos", "lluvia asociada"],
            "targets_supported": ["ráfagas", "lluvia acumulada", "riesgo tropical", "incertidumbre de trayectoria"],
            "training_role": "Contexto oficial y dinámico para sistemas activos o potenciales.",
        },
        {
            "domain": "Océano y energía tropical",
            "sources": ["oisst", "gfs_wave", "ndbc"],
            "features": ["temperatura superficial del mar", "oleaje", "período", "viento marino", "presión marina"],
            "targets_supported": ["riesgo marino", "exposición costera", "ambiente favorable a desarrollo tropical"],
            "training_role": "Mejora el análisis de ondas tropicales, ciclones y condiciones marítimas.",
        },
        {
            "domain": "Reanálisis y verificación histórica",
            "sources": ["era5_reanalysis", "ncei_isd", "mrms_caribbean", "tjua_nexrad"],
            "features": ["observaciones horarias", "QPE de lluvia", "radar", "reanálisis atmosférico", "orografía"],
            "targets_supported": list(TARGET_SPECS.keys()),
            "training_role": "Entrenamiento retrospectivo, backtesting y calibración local.",
        },
        {
            "domain": "Puerto Rico operacional",
            "sources": ["nws_sju_grid", "nam_pr_nest", "mrms_caribbean", "tjua_nexrad", "goes19"],
            "features": ["grilla oficial local", "radar", "satélite", "precipitación", "calor", "viento", "topografía"],
            "targets_supported": ["impacto municipal", "riesgo de inundación", "calor", "lluvia intensa", "viento costero"],
            "training_role": "Ajuste fino por municipio, incluyendo Juana Díaz, Ponce, San Juan y San Germán.",
        },
    ]


def training_plan_payload(
    model_status: dict[str, Any] | None = None,
    training_status: dict[str, Any] | None = None,
) -> dict[str, Any]:
    model_status = model_status or {}
    training_status = training_status or {}
    return {
        "report_version": REPORT_VERSION,
        "generated_at_utc": utc_now_iso(),
        "model": {
            "name": MODEL_NAME,
            "version": MODEL_VERSION,
            "current_status": model_status.get("status", "unknown"),
            "production_validated": bool(model_status.get("production_validated", False)),
        },
        "training_decision": {
            "recommendation": "train_new_caribbean_atlantic_model",
            "reason": (
                "El modelo existente PR-CARIBE ya define la base técnica, pero necesita entrenamiento "
                "retrospectivo real, validación independiente y ampliación de fuentes para Caribe y Atlántico."
            ),
            "use_bootstrap_only_for_code_validation": True,
            "use_real_training_for_operational_candidate": True,
        },
        "minimum_real_training_dataset": {
            "rows_research_ready": 5000,
            "rows_operational_candidate": 50000,
            "minimum_days_research_ready": 90,
            "minimum_days_operational_candidate": 365,
            "minimum_stations_research_ready": 8,
            "minimum_stations_operational_candidate": 25,
            "minimum_islands_or_territories": 5,
            "targets": list(TARGET_SPECS.keys()),
        },
        "phases": [
            {
                "phase": "1. Inventario y normalización",
                "actions": [
                    "Crear manifiestos por fuente, ciclo de corrida y hora válida.",
                    "Estandarizar unidades: pulgadas, mph, °F, hPa, %, nudos y coordenadas WGS84.",
                    "Separar datos de Puerto Rico, Caribe insular, mar Caribe, Golfo de México y Atlántico tropical.",
                ],
            },
            {
                "phase": "2. Ensamblaje histórico",
                "actions": [
                    "Unir observaciones NCEI/estaciones con GFS, GEFS, HAFS/NHC, OISST, ERA5, MRMS y radar.",
                    "Evitar fuga de información: ninguna observación futura debe entrar como predictor.",
                    "Guardar una tabla por hora válida y localización.",
                ],
            },
            {
                "phase": "3. Entrenamiento del modelo",
                "actions": [
                    "Entrenar modelos por variable: temperatura, lluvia 1h/6h/24h, viento, ráfagas, humedad y presión.",
                    "Comparar modelos de árbol, regresión regularizada, ensamble y calibración por cuantiles.",
                    "Separar el periodo de validación por años completos y temporadas de huracanes.",
                ],
            },
            {
                "phase": "4. Validación meteorológica",
                "actions": [
                    "Comparar contra climatología, persistencia, GFS crudo, GEFS medio y pronóstico oficial.",
                    "Evaluar lluvia extrema, eventos tropicales, calor, viento costero y falsas alarmas.",
                    "Requerir revisión humana antes de etiquetar como candidato operacional.",
                ],
            },
            {
                "phase": "5. Integración al dashboard",
                "actions": [
                    "Publicar informe meteorológico, estado del modelo y matriz de fuentes por API.",
                    "Mostrar incertidumbre y limitaciones junto con cada resultado.",
                    "Mantener el aviso de que PR-WX no reemplaza fuentes oficiales.",
                ],
            },
        ],
        "current_training_status": training_status,
    }


def readiness_label(training_status: dict[str, Any] | None = None) -> str:
    training_status = training_status or {}
    table = training_status.get("training_table", {})
    readiness = table.get("readiness", {}) if isinstance(table, dict) else {}
    if readiness.get("production_validated"):
        return "validado para producción"
    if readiness.get("operational_candidate"):
        return "candidato operacional pendiente de revisión humana"
    if readiness.get("research_ready"):
        return "listo para investigación"
    return "entrenamiento histórico requerido"


def build_report_payload(
    model_status: dict[str, Any] | None = None,
    training_status: dict[str, Any] | None = None,
) -> dict[str, Any]:
    model_status = model_status or {}
    training_status = training_status or {}
    matrix = model_feature_matrix()
    plan = training_plan_payload(model_status, training_status)
    sources = extended_source_registry()
    return {
        "title": REPORT_TITLE,
        "report_version": REPORT_VERSION,
        "generated_at_utc": utc_now_iso(),
        "scope": {
            "region": "Puerto Rico, Caribe, Golfo de México y Atlántico tropical/subtropical occidental",
            "purpose": "Informe meteorológico, análisis de fuentes y ruta de entrenamiento para un modelo híbrido Caribe-Atlántico.",
            "not_official_warning": True,
        },
        "model_analysis": {
            "current_model_name": MODEL_NAME,
            "current_model_version": MODEL_VERSION,
            "current_model_status": model_status,
            "readiness_label": readiness_label(training_status),
            "decision": plan["training_decision"],
        },
        "source_registry": sources,
        "applicable_sources": {
            "Puerto Rico": sources_for_area("Puerto Rico"),
            "Caribe": sources_for_area("Caribe"),
            "Atlantic": sources_for_area("Atlantic"),
        },
        "feature_matrix": matrix,
        "training_plan": plan,
        "report_markdown": build_report_markdown(model_status, training_status, matrix, plan),
        "disclaimer": (
            "Producto experimental PR-WX. Las alertas públicas y decisiones de emergencia deben seguir "
            "NOAA/NWS, NHC, la Red Sísmica de Puerto Rico y las agencias oficiales de manejo de emergencias."
        ),
    }


def build_report_markdown(
    model_status: dict[str, Any] | None = None,
    training_status: dict[str, Any] | None = None,
    matrix: list[dict[str, Any]] | None = None,
    plan: dict[str, Any] | None = None,
) -> str:
    model_status = model_status or {}
    training_status = training_status or {}
    matrix = matrix or model_feature_matrix()
    plan = plan or training_plan_payload(model_status, training_status)
    matrix_lines = []
    for item in matrix:
        matrix_lines.append(
            f"- **{item['domain']}**: fuentes {', '.join(item['sources'])}; "
            f"uso: {item['training_role']}"
        )
    phase_lines = []
    for phase in plan["phases"]:
        phase_lines.append(f"### {phase['phase']}")
        phase_lines.extend([f"- {action}" for action in phase["actions"]])

    return f"""# {REPORT_TITLE} v{REPORT_VERSION}

## Resumen ejecutivo
PR-WX debe avanzar de un tablero meteorológico experimental a un sistema con informe meteorológico estructurado y modelo híbrido Caribe-Atlántico. El modelo existente **{MODEL_NAME} {MODEL_VERSION}** ya ofrece una base técnica, pero el análisis indica que todavía requiere entrenamiento retrospectivo real, validación independiente y revisión meteorológica antes de cualquier uso operacional. La recomendación técnica es entrenar un nuevo ciclo del modelo utilizando GFS, GEFS, HAFS/NHC, ERA5, OISST, MRMS, radar, NWS San Juan y observaciones históricas. El informe debe presentar lluvia, viento, calor, humedad, presión, riesgo de inundación, riesgo tropical, incertidumbre y limitaciones. El producto no sustituye a las fuentes oficiales.

## Estado del modelo
- Estado actual: `{model_status.get('status', 'unknown')}`
- Etiqueta de preparación: **{readiness_label(training_status)}**
- Validado para producción: `{bool(model_status.get('production_validated', False))}`
- Recomendación: **{plan['training_decision']['recommendation']}**

## Matriz de fuentes y variables
{chr(10).join(matrix_lines)}

## Ruta de entrenamiento
{chr(10).join(phase_lines)}

## Criterios mínimos antes de uso operacional
- Mínimo de 50,000 filas reales para candidato operacional.
- Mínimo de 365 días de cobertura histórica.
- Mínimo de 25 estaciones o puntos de verificación.
- Cobertura de al menos 5 islas, territorios o subregiones.
- Evaluación separada para lluvia, viento, calor, presión, humedad y riesgo tropical.
- Backtesting por temporadas de huracanes y por eventos extremos.
- Comparación contra climatología, persistencia, GFS crudo, GEFS medio y pronóstico oficial.
- Revisión humana meteorológica antes de publicar como candidato operacional.

## Integración al dashboard
El dashboard debe añadir una sección llamada **Informe meteorológico Caribe-Atlántico**. Esta sección debe leer los endpoints `/weather/report/caribbean-atlantic`, `/weather/report/caribbean-atlantic.md`, `/caribbean/model/training-plan` y `/caribbean/model/feature-matrix`. También debe mostrar el estado del modelo y un aviso visible de que el resultado es experimental. Para municipios de Puerto Rico, el informe municipal existente se mantiene en `/weather/report/{{municipality}}`.

## Limitación institucional
PR-WX es una herramienta experimental, educativa e institucional. Las alertas públicas, evacuaciones, cierres, avisos de tormenta, huracán, inundación o tsunami deben seguir las agencias oficiales. El sistema puede ayudar a organizar información, pero no debe presentarse como fuente oficial de emergencia.
"""
