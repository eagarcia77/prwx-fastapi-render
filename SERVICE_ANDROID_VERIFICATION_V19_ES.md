# PR-WX v1.9 - Verificación de servicios y Android Earthquake Bridge

## Qué verifica

- NWS Alerts API.
- USGS Earthquake GeoJSON feeds.
- NOAA/NWS MRMS QPE.
- NHC Current Storms.
- Archivos locales generados.
- Android Sensor Bridge local para terremotos.

## Android Earthquake Bridge

PR-WX no puede conectarse directamente a la red privada de Android Earthquake Alerts de Google.  
Lo que sí verifica es el puente local diseñado para una futura app Android:

- acelerómetro,
- ubicación aproximada,
- sin identificadores personales,
- cluster de señales,
- recomendación de validación oficial,
- recordatorio de que esto no predice terremotos.

## Archivos generados

- `service_status_v19.csv`
- `android_earthquake_bridge_status_v19.json`
- `verification_summary_v19.json`
