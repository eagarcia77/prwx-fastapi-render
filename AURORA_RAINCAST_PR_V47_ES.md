# PR-WX v4.7.0 — AURORA RainCast PR Cloud Motion Tracker

## Propósito

Esta versión responde al problema de visibilidad de nubes en el mapa. El objetivo principal es que el usuario pueda ver con más claridad por dónde pasan las nubes sobre Puerto Rico, no solamente el radar de lluvia.

## Cambios principales

- Mapa principal reconstruido con prioridad visual a nubes GOES.
- GOES infrarrojo activado por defecto con opacidad alta.
- GOES visible añadido como apoyo.
- Radar NOAA nowCOAST colocado encima de las nubes.
- Controles rápidos para Todo, IR fuerte, Visible + IR y Radar + IR.
- Imágenes WMS directas de respaldo para confirmar que el servicio entrega nubosidad.
- Botones por municipio para Juana Díaz, Ponce, San Juan, San Germán, Mayagüez, Fajardo, Vieques y Culebra.
- Modo kiosco para pantalla grande.

## Página principal

- `/desktop/live-rain.html`

## Capas usadas

- `RAS_GOES_I4` — nubes infrarrojas GOES.
- `RAS_GOES` — nubes visibles GOES.
- `RAS_RIDGE_NEXRAD` — radar de lluvia.

## Uso recomendado

1. Abrir `/desktop/live-rain.html`.
2. Presionar Ctrl + F5.
3. Usar el botón `IR fuerte` si las nubes se ven débiles.
4. Subir la opacidad de nubes IR a 100%.
5. Validar la lectura con NOAA, NWS San Juan, NHC y manejo de emergencias.

## Advertencia

PR-WX es experimental. No emite avisos oficiales y no debe sustituir productos oficiales de emergencia.