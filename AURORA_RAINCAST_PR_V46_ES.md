# PR-WX v4.6.0 — AURORA RainCast PR Cloud Reveal

## Propósito

Esta versión refuerza la visualización de nubes sobre Puerto Rico cuando la capa visible o infrarroja se ve demasiado clara en el mapa principal.

## Mejora principal

- Nuevo panel **Mapa nubes REVEAL sobre Puerto Rico**.
- Usa GOES infrarrojo `RAS_GOES_I4` con contraste reforzado.
- Mantiene GOES visible `RAS_GOES` como capa secundaria.
- Mantiene radar `RAS_RIDGE_NEXRAD` encima para comparar nubes y lluvia.
- Añade imagen WMS directa de respaldo para validar si el servicio está entregando la nube aunque Leaflet la muestre débil.
- Añade botones: IR Reveal, Todo, Visible y Radar.
- Añade enfoque rápido por Juana Díaz, Ponce, San Juan, San Germán, Vieques y Culebra.

## Validación

El panel es experimental. Las decisiones críticas deben validarse con NOAA, NWS San Juan, NHC y manejo de emergencias.
