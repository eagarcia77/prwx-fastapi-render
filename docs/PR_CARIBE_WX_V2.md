# PR-CARIBE WX Hybrid v2.0

## Propósito

PR-CARIBE WX Hybrid v2.0 es la nueva capa meteorológica experimental de PR-WX para Puerto Rico y el Caribe. No pretende sustituir un modelo físico de predicción numérica de la atmósfera ni las advertencias oficiales. Su propósito es combinar modelos y observaciones que sí cubren la región, aprender sesgos locales y producir pronósticos municipales y regionales con incertidumbre explícita.

## Principio de diseño

El sistema no debe asumir que un modelo disponible para Estados Unidos continental es válido para Puerto Rico. Cada fuente se incorpora solamente cuando su dominio operacional documentado cubre la ubicación solicitada.

La arquitectura se divide en cuatro niveles:

1. Fuentes oficiales y observaciones.
2. Normalización espacial y temporal.
3. Ensemble de aprendizaje automático para corrección y fusión local.
4. Producto operacional con pronóstico, incertidumbre, riesgos y fuentes oficiales.

## Fuentes previstas

### Puerto Rico

- NWS San Juan Digital Forecast Grid: referencia oficial local y calibración.
- NAM Puerto Rico Nest: predictor regional de alta resolución para corto plazo.
- GFS: patrón sinóptico y circulación de gran escala.
- GEFS: incertidumbre y probabilidades de ensemble.
- MRMS Caribbean: lluvia observada/estimada y nowcasting de precipitación.
- Radar TJUA/NEXRAD: convección, intensidad y movimiento de precipitación.
- GOES-East/GOES-19: nubosidad, vapor de agua, convección y ondas tropicales.
- NHC: fuente oficial para ciclones tropicales.
- HAFS: predictor condicional cuando existe un ciclón tropical activo.
- GFS-Wave/WAVEWATCH III y NDBC: oleaje, viento marino y verificación costera.
- NCEI Integrated Surface Database: observaciones históricas para entrenamiento y validación.

### Caribe

El núcleo regional utiliza GFS, GEFS, GOES-East, NHC/HAFS, GFS-Wave y observaciones de superficie/marinas disponibles. Para cada isla o territorio se pueden incorporar productos oficiales locales adicionales cuando exista un proveedor documentado.

### Fuente excluida como núcleo operacional

HRRR operacional no se utiliza como columna vertebral para Puerto Rico. Cualquier producto experimental del Caribe debe mantenerse separado de la cadena operacional hasta que tenga cobertura, disponibilidad y validación apropiadas.

## Variables objetivo

La versión 2.0 admite entrenamiento independiente para:

- temperatura;
- lluvia acumulada de 1, 6 y 24 horas;
- velocidad del viento;
- ráfagas;
- humedad relativa;
- presión atmosférica.

Cada variable genera una estimación central y un intervalo P10-P90 basado inicialmente en la dispersión entre miembros del ensemble de aprendizaje automático.

## Predictores

El modelo acepta variables de las familias `nws_`, `nam_pr_`, `gfs_`, `gefs_`, `mrms_`, `tjua_`, `goes_`, `nhc_`, `hafs_`, `gfs_wave_`, `ndbc_`, además de elevación, distancia a costa, pendiente, orientación, fracción de terreno, temperatura del mar, polvo, humedad precipitable y variables temporales cíclicas.

Nunca se utilizan columnas `observed_`, `verified_`, `target_` o `error_` como predictores para evitar fuga de información.

## Dataset de entrenamiento

Ruta canónica:

```text
data/training/pr_caribbean_training.csv
```

Cada fila debe representar un punto/estación y una hora válida. Como mínimo debe incluir:

```text
valid_time_utc
station_id
island
lat
lon
elevation_m
```

Debe contener uno o más predictores meteorológicos y las observaciones objetivo correspondientes, por ejemplo:

```text
gfs_temp_f
nam_pr_temp_f
nws_temp_f
gefs_temp_mean_f
mrms_qpe_24h_in
observed_temp_f
observed_precip_24h_in
```

## Criterios automáticos de preparación

Los umbrales siguientes son controles mínimos de ingeniería y no equivalen a validación meteorológica:

### Investigación

- 5,000 filas o más;
- 90 días o más;
- 8 estaciones o más;
- al menos 2 variables objetivo entrenables.

### Candidato operacional

- 50,000 filas o más;
- 365 días o más;
- 25 estaciones o más;
- 5 islas o territorios o más;
- al menos 4 variables objetivo entrenables.

Un dataset que supera estos umbrales sigue teniendo `production_validated = false` hasta completar validación independiente.

## Entrenamiento

```bash
python scripts/22_train_pr_caribbean_v20.py
```

Para una prueba de ingeniería con un dataset todavía limitado:

```bash
python scripts/22_train_pr_caribbean_v20.py --allow-research-only
```

El segundo comando no autoriza uso operacional.

El modelo se guarda en:

```text
models/pr_caribe_wx_v20.joblib
```

La auditoría del entrenamiento se guarda en:

```text
data/processed/pr_caribe_wx_v20_training.json
```

## Validación requerida antes de producción

La validación real debe utilizar cortes cronológicos y pruebas fuera de muestra. Además del conjunto general, se deben reservar eventos completos que el entrenamiento no haya visto.

Se deben evaluar por separado:

- costa norte;
- costa sur;
- oeste;
- este;
- Cordillera Central;
- Vieques y Culebra cuando los datos lo permitan;
- Islas Vírgenes y otras islas del Caribe incorporadas al entrenamiento;
- temporada seca;
- temporada húmeda;
- ondas tropicales;
- episodios de polvo del Sahara;
- calor extremo;
- lluvias convectivas de corta duración;
- inundaciones;
- ciclones tropicales.

Para temperatura, viento, humedad y presión se deben reportar como mínimo MAE, RMSE y sesgo. Para precipitación se deben añadir posteriormente métricas por umbral y probabilísticas, incluyendo Brier Score, confiabilidad y CRPS cuando se incorpore un ensemble probabilístico completo.

## API

### Estado del modelo

```text
GET /caribbean/model/status
```

### Preparación del dataset

```text
GET /caribbean/model/readiness
```

### Fuentes y dominios

```text
GET /caribbean/model/sources
```

### Informe meteorológico municipal

```text
GET /weather/report/{municipality}
```

Ejemplo:

```text
GET /weather/report/San Juan
```

## Regla de seguridad

PR-CARIBE WX puede resumir, corregir y comparar información meteorológica, pero nunca reemplaza ni cancela una advertencia oficial. Para alertas, huracanes y decisiones de seguridad, la interfaz debe mantener visibles las fuentes oficiales NOAA/NWS San Juan, NHC y las agencias correspondientes de manejo de emergencias.

## Próximas fases

1. Construir el archivo histórico real de entrenamiento con observaciones y pronósticos archivados.
2. Añadir ingestión automática de NAM Puerto Rico Nest, GFS, GEFS, GOES y datos marinos.
3. Entrenar y registrar el primer modelo de investigación con datos reales.
4. Ejecutar backtesting independiente por estación, zona climática y evento.
5. Añadir calibración probabilística de lluvia y viento.
6. Extender el entrenamiento gradualmente al Caribe sin degradar la precisión específica de Puerto Rico.
7. Integrar el API de PR-CARIBE WX en las experiencias Desktop, Mobile y entornos educativos/VR que necesiten el informe del tiempo.
