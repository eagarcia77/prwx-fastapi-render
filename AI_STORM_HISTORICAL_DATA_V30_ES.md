# PR-WX v3.0.0 — Datos históricos para entrenar IA de trayectorias hacia Puerto Rico

## Propósito

Esta versión añade una ruta de datos históricos para entrenar un modelo experimental de inteligencia artificial que estime acercamiento de sistemas tropicales hacia Puerto Rico. El objetivo no es reemplazar los productos oficiales del National Hurricane Center ni del National Weather Service, sino mejorar el análisis interno del dashboard con datos históricos verificables.

## Fuentes históricas incluidas

1. NOAA/NHC HURDAT2 Atlantic Hurricane Database.
2. NOAA/NCEI IBTrACS North Atlantic CSV como fuente de validación cruzada.
3. NOAA/NCEI African Easterly Wave Climatology para una etapa posterior de ondas tropicales.
4. NOAA/PSL NCEP/NCAR Reanalysis para vaguadas, ondas y ambiente sinóptico.
5. ERA5 Copernicus/ECMWF como fuente opcional de mayor resolución.

## Archivos añadidos

```text
src/prwx/storm_historical_ingest_v30.py
src/prwx/storm_historical_train_v30.py
api/ai_storm_historical_router.py
scripts/38_download_historical_storm_data_v30.py
scripts/39_train_storm_historical_ai_v30.py
desktop/storm-history-panel.js
tests/test_storm_historical_v30.py
```

## Comandos principales

Descargar HURDAT2 y construir la tabla histórica:

```bash
python scripts/38_download_historical_storm_data_v30.py
```

Entrenar el modelo experimental si el dataset está listo:

```bash
python scripts/39_train_storm_historical_ai_v30.py --train
```

Ejecutar una prueba pequeña aunque no cumpla los umbrales de investigación:

```bash
python scripts/39_train_storm_historical_ai_v30.py --build --train --force
```

## Archivos generados

```text
data/training/raw/hurdat2_atlantic_latest.txt
data/training/storm_tracks_atlantic_training.csv
data/processed/storm_historical_training_v30.json
data/processed/storm_historical_sources_v30.json
models/storm_pr_trajectory_ai_v30.joblib
data/processed/storm_pr_trajectory_ai_v30.json
```

## Variables objetivo

- `target_min_distance_72h_km`
- `target_approach_500km_72h`
- `target_approach_300km_72h`
- `target_direct_pr_150km_72h`
- `target_high_wind_near_pr_72h`

## Variables predictoras iniciales

- Latitud y longitud del sistema.
- Intensidad máxima en nudos.
- Presión mínima estimada.
- Distancia a Puerto Rico.
- Rumbo hacia Puerto Rico.
- Tendencia de viento en seis horas.
- Tendencia de presión en seis horas.
- Tendencia de distancia a Puerto Rico.
- Mes y hora codificados como variables cíclicas.

## Próxima etapa recomendada

La próxima etapa debe integrar variables ambientales de reanálisis: viento de dirección en 850/700/500 hPa, altura geopotencial, vorticidad, humedad, OLR y anomalías de presión. Estas variables son necesarias para modelar mejor ondas tropicales y vaguadas, porque HURDAT2 se concentra en ciclones tropicales clasificados.

## Regla de seguridad

El modelo es experimental. Las decisiones de emergencia, cierres, desalojos, avisos y comunicación pública deben seguir siempre al NHC, NWS San Juan y las agencias oficiales de manejo de emergencias.
