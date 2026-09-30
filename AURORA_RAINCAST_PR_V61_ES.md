# PR-WX v6.1.0 — AURORA RainCast PR Immersive VR Cloud Lab

## Propósito

Esta versión añade una experiencia inmersiva tipo WebXR para visualizar nubes reales sobre Puerto Rico usando los endpoints satelitales ya incorporados en PR-WX.

## Cambios principales

- Nueva escena inmersiva con A-Frame/WebXR.
- Panel 3D para imagen fija satelital.
- Panel 3D para loop animado de nubes.
- Compatibilidad visual con navegador de escritorio, móvil y Meta Quest cuando el navegador soporte VR.
- Botón para enfocar la escena VR.
- Mantiene vista fija, loop, fuentes de diagnóstico y comparación WMS.
- Mantiene productos: Banda 13 IR, GeoColor, Banda 14 IR y Banda 2 Visible.

## Archivos añadidos

- `desktop/live-rain-v61.css`
- `desktop/live-rain-v61.js`
- `AURORA_RAINCAST_PR_V61_ES.md`

## Archivos actualizados

- `desktop/live-rain.html`
- `desktop/service-worker.js`
- `src/prwx/__init__.py`

## Uso recomendado

1. Abrir `/desktop/live-rain.html`.
2. Presionar `Limpiar cache visual`.
3. Usar `Banda 13 IR`.
4. Presionar `Enfocar escena VR`.
5. En un navegador compatible, usar el botón VR de la escena.

## Nota operacional

Esta vista es experimental y educativa. No sustituye avisos, pronósticos ni instrucciones oficiales de NOAA, NWS, NHC ni manejo de emergencias.
