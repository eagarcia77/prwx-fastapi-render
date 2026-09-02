# PR-WX v4.9.0 — AURORA RainCast PR Cloud Analysis Lab

## Propósito

Esta versión refuerza la lectura de nubosidad sobre Puerto Rico. El objetivo es que el usuario pueda confirmar si las nubes están pasando por el área de PR mediante tres mecanismos simultáneos: mapa Leaflet con WMS, imágenes WMS directas y diagnóstico de respuesta de capas.

## Capas usadas

- `RAS_GOES_I4`: nubosidad infrarroja GOES.
- `RAS_GOES`: nubosidad visible GOES.
- `RAS_RIDGE_NEXRAD`: mosaico de radar meteorológico.

## Mejoras principales

- GOES IR inicia a 100% de opacidad.
- GOES visible inicia a 65% como apoyo.
- Radar inicia a 50% para no tapar completamente la nubosidad.
- Validación directa de imágenes WMS para IR, visible y radar.
- Diagnóstico de capas: indica si las tres capas responden.
- Indicador de confianza visual.
- Controles de mapa base: satélite, topográfico y calles.
- Enfoque municipal ampliado.
- Botones de modo: Todo, IR Máximo, Visible + IR y Radar + IR.

## Uso recomendado

1. Abrir `/desktop/live-rain.html`.
2. Presionar `Ctrl + F5`.
3. Seleccionar `IR Máximo`.
4. Confirmar la imagen en `Validación directa WMS`.
5. Usar los pueblos para centrar el mapa.

## Advertencia

Esta lectura es experimental y educativa. No sustituye a NOAA, NWS San Juan, NHC ni agencias de manejo de emergencias. Las capas externas pueden tardar, verse débiles o fallar temporalmente.