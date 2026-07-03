# Automatización del modelo meteorológico PR-WX v0.4

## Objetivo

Mantener el dashboard actualizado de forma recurrente sin tener que correr todos los comandos manualmente.

## Opción A: computadora local Windows

Usa:

```powershell
.\run_auto_update_windows.bat
```

Este archivo ejecuta el pipeline completo cada 30 minutos:

```powershell
python scripts\07_update_live_pipeline.py --all --append-history
```

Para cambiar el intervalo, edita el archivo y cambia:

```bat
set INTERVAL_SECONDS=1800
```

Ejemplos:

```text
900  = cada 15 minutos
1800 = cada 30 minutos
3600 = cada 1 hora
```

## Opción B: GitHub Actions

El archivo `.github/workflows/update-live-data.yml` actualiza el CSV automáticamente cada 3 horas y hace commit de los resultados al repositorio.

Para activarlo:

1. Publica el proyecto en GitHub.
2. Entra al repositorio.
3. Abre la pestaña **Actions**.
4. Selecciona **Update PR-WX live data**.
5. Presiona **Run workflow** para probarlo manualmente.

Luego correrá solo según el cron configurado.

## Opción C: Streamlit Community Cloud

1. Publica el repositorio en GitHub.
2. Entra a Streamlit Community Cloud.
3. Conecta el repositorio.
4. Usa como archivo principal:

```text
dashboard/app.py
```

El app mostrará los datos que GitHub Actions va actualizando en `data/processed/live_predictions.csv`.

## Recomendación

Para una versión pública estable, usa esta combinación:

```text
GitHub Actions actualiza datos cada 3 horas.
Streamlit Community Cloud muestra el dashboard.
La computadora local se usa solo para desarrollo.
```
