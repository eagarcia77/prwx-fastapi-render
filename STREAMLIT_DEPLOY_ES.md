# Publicar PR-WX v0.4 en Streamlit Community Cloud

## Preparación

Verifica que el proyecto esté en GitHub y que el workflow de actualización ya haya generado:

```text
data/processed/live_predictions.csv
data/processed/latest_run.json
```

## Configuración en Streamlit

En Streamlit Community Cloud crea una nueva app y selecciona:

```text
Repository: pr-weather-hybrid-model
Branch: main
Main file path: dashboard/app.py
```

## Cómo se actualiza

Streamlit leerá los CSV que están en el repositorio. GitHub Actions actualiza esos CSV y hace commit cada 3 horas. Cuando Streamlit detecte cambios o reinicie el app, leerá los datos más recientes.

## Nota importante

El botón **Actualizar datos NWS ahora** funciona mejor cuando corres el dashboard localmente. En la nube puede actualizar la sesión temporal, pero no necesariamente guarda el resultado de forma permanente en GitHub. Para actualización permanente, usa GitHub Actions.
