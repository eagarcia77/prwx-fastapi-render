# PR-WX v5.0.0 — AURORA RainCast PR Cloud Operational Console

## Propósito
Esta versión consolida la vista de nubes reales sobre Puerto Rico en una consola operacional más directa. La prioridad es que el usuario pueda confirmar visualmente la nubosidad que pasa por PR usando GOES infrarrojo, GOES visible y radar NOAA nowCOAST.

## Cambios principales
- Nueva página limpia enfocada en nubes, radar y validación WMS.
- GOES IR inicia al 100% para mejorar visibilidad.
- GOES visible inicia como apoyo al 70%.
- Radar inicia al 42% para no cubrir la nubosidad.
- Imágenes directas WMS para validar IR, visible y radar.
- Diagnóstico de confianza visual.
- Enfoque por municipios prioritarios.
- Botones de mapa base: satélite, topográfico y calles.
- Modo kiosco, impresión y actualización manual.

## Capas usadas
- RAS_GOES_I4: nubes infrarrojas GOES.
- RAS_GOES: nubes visibles GOES.
- RAS_RIDGE_NEXRAD: radar de lluvia.

## Uso recomendado
1. Abrir `/desktop/live-rain.html`.
2. Usar el modo `Todo` o `IR Máximo`.
3. Revisar `Validación directa WMS`.
4. Si IR carga y el mapa se ve débil, subir contraste/opacidad y usar mapa base satelital.

## Advertencia
Este sistema es experimental. No sustituye a NOAA, NWS San Juan, NHC, USGS, Red Sísmica de Puerto Rico ni agencias de manejo de emergencias.