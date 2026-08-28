# PR-WX v2.7 - Inteligencia Artificial para entrenar el modelo del Caribe y el Atlántico

## Propósito

Esta versión añade una capa de inteligencia artificial para analizar datos meteorológicos, evaluar si el dataset histórico es suficiente y entrenar un modelo experimental para Puerto Rico, Caribe, Golfo de México y Atlántico tropical/subtropical.

El sistema no usa servicios pagados ni una API externa de IA. La inteligencia artificial se implementa con un motor local de aprendizaje automático basado en `scikit-learn`, validación cronológica, análisis de calidad de datos y ensamble multiobjetivo.

## Componentes añadidos

```text
src/prwx/ai_training_engine_v27.py
api/ai_training_router.py
scripts/35_ai_analyze_and_train_caribbean_atlantic_v27.py
tests/test_ai_training_v27.py
```

## Endpoints nuevos

```text
/ai/model/status
/ai/model/analyze
/ai/model/training-plan
/ai/model/training-plan.md
/ai/model/feature-matrix
/ai/model/train-status
/ai/model/report
```

El endpoint de entrenamiento existe, pero está protegido:

```text
POST /ai/model/train
```

Para permitir entrenamiento desde el servidor se debe activar esta variable de entorno:

```text
PRWX_ENABLE_RUNTIME_TRAINING=true
```

Por seguridad y estabilidad, se recomienda entrenar desde la computadora o un ambiente dedicado, no desde Render Free.

## Comando recomendado

Primero analizar:

```bash
python scripts/35_ai_analyze_and_train_caribbean_atlantic_v27.py
```

Luego entrenar si el dataset está listo:

```bash
python scripts/35_ai_analyze_and_train_caribbean_atlantic_v27.py --train
```

Si se desea forzar un entrenamiento experimental pequeño:

```bash
python scripts/35_ai_analyze_and_train_caribbean_atlantic_v27.py --train --force
```

## Dataset esperado

El motor busca estos archivos:

```text
data/training/pr_caribbean_atlantic_training.parquet
data/training/pr_caribbean_atlantic_training.csv
data/training/pr_caribbean_training.parquet
data/training/pr_caribbean_training.csv
```

Debe incluir, como mínimo:

```text
valid_time_utc
lat
lon
station_id o grid_id
territory, island, country o basin
variables de fuentes oficiales: gfs_, gefs_, nam_pr_, nws_, mrms_, goes_, nhc_, hafs_, ndbc_, sst_
objetivos observados: observed_temp_f, observed_precip_24h_in, observed_wind_speed_mph, etc.
```

## Criterios mínimos

Para investigación:

```text
5,000 filas
90 días de cobertura
8 estaciones o puntos de verificación
12 variables predictoras útiles
2 objetivos entrenables
```

Para candidato operacional experimental:

```text
50,000 filas
365 días de cobertura
25 estaciones o puntos de verificación
5 territorios, islas o subregiones
25 variables predictoras útiles
4 objetivos entrenables
validación independiente requerida
```

## Modelo IA

El motor entrena un ensamble con:

```text
Ridge
RandomForest
ExtraTrees
HistGradientBoosting
```

Los objetivos incluyen:

```text
temperatura
lluvia 1h, 6h y 24h
viento sostenido
ráfagas
humedad relativa
presión
```

La incertidumbre se estima con percentiles P10, media y P90 usando el desacuerdo entre los miembros del ensamble.

## Advertencia operacional

Este componente es experimental. No reemplaza a NOAA, NWS, NHC, Red Sísmica ni manejo de emergencias. Toda predicción debe validarse con fuentes oficiales y revisión meteorológica antes de usarse para decisiones públicas.
