# PR-WX v3.1.0 — Entrenamiento IA con datos históricos desde GitHub Actions

Esta versión añade un flujo manual de GitHub Actions para descargar datos históricos oficiales, construir la tabla de entrenamiento y entrenar el modelo experimental de trayectoria hacia Puerto Rico sin subir archivos grandes al repositorio.

## Fuente histórica principal

- NOAA/NHC HURDAT2 Atlantic best track.

## Fuentes de validación y próxima etapa

- NOAA/NCEI IBTrACS.
- African Easterly Wave Climatology.
- NCEP/NCAR Reanalysis.
- ERA5.

## Workflow nuevo

```text
.github/workflows/train-storm-historical-ai-v31.yml
```

Nombre visible en GitHub Actions:

```text
Train Storm Trajectory AI
```

## Qué hace

1. Instala Python y dependencias del proyecto.
2. Descarga HURDAT2 desde NOAA/NHC.
3. Construye `data/training/storm_tracks_atlantic_training.csv`.
4. Entrena `models/storm_pr_trajectory_ai_v30.joblib` si se solicita.
5. Genera `reports/storm_training_artifact_manifest_v31.json`.
6. Sube un artifact ZIP llamado `prwx-storm-ai-training-v31`.

## Cómo correrlo

1. Entra al repositorio en GitHub.
2. Selecciona `Actions`.
3. Selecciona `Train Storm Trajectory AI`.
4. Presiona `Run workflow`.
5. Deja activos:
   - `build_dataset = true`
   - `train_model = true`
   - `force_training = true`
6. Espera que termine.
7. Descarga el artifact `prwx-storm-ai-training-v31`.

## Qué contiene el artifact

```text
artifact_bundle/data_training/storm_tracks_atlantic_training.csv
artifact_bundle/data_training/hurdat2_atlantic_latest.url.txt
artifact_bundle/data_processed/storm_historical_training_v30.json
artifact_bundle/data_processed/storm_historical_sources_v30.json
artifact_bundle/data_processed/storm_pr_trajectory_ai_v30.json
artifact_bundle/models/storm_pr_trajectory_ai_v30.joblib
artifact_bundle/reports/storm_training_artifact_manifest_v31.json
```

## Por qué no se sube todo directo al repo

Los datos históricos y modelos pueden crecer mucho. Se manejan como artifacts de workflow para no llenar GitHub con archivos grandes y para mantener el repositorio limpio.

## Uso local alterno

```bash
python scripts/38_download_historical_storm_data_v30.py
python scripts/39_train_storm_historical_ai_v30.py --train --force
python scripts/40_summarize_storm_training_artifacts_v31.py
```

## Regla de seguridad

El modelo es experimental. Las decisiones operacionales y avisos públicos sobre tormentas, huracanes, ondas tropicales o vaguadas deben validarse con NHC, NWS San Juan y manejo de emergencias.
