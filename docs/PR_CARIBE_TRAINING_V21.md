# PR-CARIBE WX — Pipeline histórico v2.1

## Objetivo

Esta fase construye un dataset meteorológico real para entrenar PR-CARIBE WX con observaciones de Puerto Rico y predictores de modelos que sí cubren la región. El pipeline separa cuatro responsabilidades: observación, descarga de modelos, extracción espacial y ensamblaje final.

## 1. Dependencias de entrenamiento

Las dependencias operacionales de Render se mantienen livianas. Para trabajar con archivos GRIB2 localmente instale el perfil de entrenamiento:

```bash
python -m pip install -r requirements-training.txt
python -m pip install -e .
```

`eccodes` se utiliza para leer mensajes GRIB2 y extraer el valor más cercano a cada estación de observación.

## 2. Observaciones históricas NCEI

El colector consulta NOAA/NCEI Global Hourly por bloques mensuales y utiliza el bounding box de Puerto Rico.

```bash
python scripts/23_collect_ncei_pr.py --start 2023-01-01 --end 2026-08-12
```

Salida por defecto:

```text
data/training/observations_ncei_pr.parquet
```

Manifiesto:

```text
data/training/manifests/ncei_pr.json
```

El normalizador convierte temperatura y punto de rocío a Fahrenheit, viento a mph, presión a hPa y precipitación a pulgadas. También calcula humedad relativa a partir de temperatura y punto de rocío cuando ambos están disponibles. La precipitación de 6 y 24 horas se completa mediante acumulación móvil cuando existe suficiente cobertura horaria.

## 3. Modelos NOAA

El colector `scripts/24_collect_model_archive_pr.py` admite:

- `gfs`
- `gefs_mean`
- `gefs_spread`
- `gefs_member`
- `nam_pr`

Ejemplo GFS:

```bash
python scripts/24_collect_model_archive_pr.py \
  --source gfs \
  --date 2026-08-12 \
  --cycle 0 \
  --forecast-hours 0,3,6,9,12,18,24
```

Ejemplo NAM Puerto Rico Nest:

```bash
python scripts/24_collect_model_archive_pr.py \
  --source nam_pr \
  --date 2026-08-12 \
  --cycle 0 \
  --forecast-hours 0-24
```

Ejemplo GEFS ensemble mean:

```bash
python scripts/24_collect_model_archive_pr.py \
  --source gefs_mean \
  --date 2026-08-12 \
  --cycle 0 \
  --forecast-hours 0,3,6,9,12,18,24
```

## 4. Descarga selectiva GRIB2

El pipeline no descarga el GRIB2 completo cuando existe un archivo `.idx`. Primero descarga el índice, identifica los mensajes meteorológicos necesarios y luego solicita solamente sus rangos de bytes.

Los campos iniciales son:

- temperatura a 2 m;
- punto de rocío a 2 m;
- humedad relativa a 2 m;
- componentes U/V del viento a 10 m;
- ráfagas;
- precipitación acumulada;
- presión reducida al nivel del mar;
- agua precipitable;
- CAPE;
- CIN.

Esto reduce de forma importante el volumen de transferencia para GFS, GEFS y NAM.

## 5. Ubicaciones de extracción

Por defecto, los puntos para el modelo se derivan de las estaciones reales encontradas en `observations_ncei_pr.parquet`. Esto evita inventar coordenadas y permite comparar el pronóstico con una observación real en el mismo punto.

También se puede proporcionar un archivo propio mediante:

```bash
--locations ruta/al/archivo.csv
```

El archivo debe contener `location_id` o `station_id`, `lat` y `lon`.

## 6. Ensamblaje

Después de recopilar observaciones y varias corridas de modelos:

```bash
python scripts/25_build_pr_caribbean_training.py
```

Salida canónica:

```text
data/training/pr_caribbean_training.parquet
```

Para un mismo punto y hora válida, si existen varias corridas del mismo modelo, el ensamblador conserva la predicción con menor `lead_hours`, lo que aproxima el principio operacional de utilizar la corrida más reciente disponible.

## 7. Preparación

Consulte:

```text
GET /caribbean/training/status
GET /caribbean/model/readiness
```

`/caribbean/training/status` informa si ya existen observaciones, tabla final, manifiestos y filas. `/caribbean/model/readiness` calcula los umbrales mínimos de investigación y candidato operacional.

## 8. Entrenamiento

Cuando el dataset tenga suficiente cobertura:

```bash
python scripts/22_train_pr_caribbean_v20.py
```

El entrenamiento exitoso no equivale a validación meteorológica. `production_validated` permanece en `false` hasta completar backtesting independiente.

## 9. Estrategia de backfill

No conviene comenzar descargando todo el Caribe. La secuencia recomendada es:

1. Puerto Rico: observaciones NCEI de varios años.
2. GFS en estaciones de Puerto Rico.
3. NAM Puerto Rico Nest en las mismas estaciones.
4. GEFS mean/spread y, posteriormente, miembros seleccionados.
5. MRMS para precipitación observada y eventos intensos.
6. Validación por estación y zona climática.
7. Ampliación a USVI y luego islas adicionales del Caribe.

## 10. Proveniencia

Cada colector produce un manifiesto JSON con fuente, fecha, corrida, horas de pronóstico, número de filas, bytes descargados, errores y ruta del producto. Los datos grandes de entrenamiento y los GRIB2 quedan fuera de Git mediante `.gitignore`; los manifiestos pequeños pueden conservarse para reproducibilidad.

## 11. Regla operacional

PR-CARIBE WX nunca debe utilizar un predictor fuera de su dominio documentado. Las alertas oficiales de NOAA/NWS San Juan y NHC conservan prioridad sobre cualquier salida experimental del modelo.
