# PR-WX v2.9.0 — Mapa IA de trayectoria de tormentas hacia Puerto Rico

Esta versión añade un segundo mapa interactivo con IA para analizar trayectorias de huracanes, tormentas tropicales, ondas tropicales y vaguadas hacia Puerto Rico.

## Propósito

El objetivo es combinar datos oficiales disponibles, trayectoria histórica, distancia a Puerto Rico, dirección, intensidad, probabilidad experimental de acercamiento y confianza del análisis para apoyar un informe meteorológico más certero.

## Endpoints principales

```text
/ai/storm-tracks/status
/ai/storm-tracks/analysis
/ai/storm-tracks/map
/ai/storm-tracks/map.geojson
/ai/storm-tracks/training/status
/ai/storm-tracks/training/plan
/ai/storm-tracks/training/plan.md
/ai/storm-tracks/event/{event_id}
```

## Fuentes que debe usar el entrenamiento IA

- NHC advisories and GIS
- HURDAT2 best track
- GFS
- GEFS
- HAFS
- GOES-East
- ERA5
- OISST
- Alertas de NWS San Juan

## Dataset de entrenamiento recomendado

```text
data/training/storm_tracks_atlantic_training.csv
```

o:

```text
data/training/storm_tracks_atlantic_training.parquet
```

El dataset debe incluir latitud, longitud, tiempo, intensidad, presión, velocidad de traslación, dirección, distancia a Puerto Rico, dispersión de ensamble, SST, cizalladura vertical, humedad, precipitable water, variables satelitales y etiqueta de impacto a Puerto Rico.

## Comandos

```bash
python scripts/37_ai_storm_track_map_v29.py
```

Para entrenar si existe dataset real:

```bash
python scripts/37_ai_storm_track_map_v29.py --train
```

Para prueba experimental pequeña:

```bash
python scripts/37_ai_storm_track_map_v29.py --train --force
```

## Regla de seguridad

El mapa no sustituye al National Hurricane Center, NWS San Juan ni manejo de emergencias. Todo resultado IA debe validarse con productos oficiales antes de tomar decisiones públicas.
