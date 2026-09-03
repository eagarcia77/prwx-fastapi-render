# PR-WX v5.9.0 — AURORA RainCast PR Direct CDN First

## Propósito

Esta versión corrige el flujo de visualización de nubes cuando el proxy o el mapa WMS no muestran la imagen. La estrategia cambia a **CDN directo primero**: la página consulta el resolvedor backend para obtener las URLs reales del índice público NOAA/NESDIS/STAR y luego intenta cargar esas imágenes directamente en el navegador antes de usar los endpoints proxy de PR-WX.

## Cambios principales

- Nuevo `desktop/live-rain-v59.css`.
- Nuevo `desktop/live-rain-v59.js`.
- `desktop/live-rain.html` actualizado a v5.9.
- `api/live_rain_router.py` actualizado a v5.9.
- `api/desktop_app.py` actualizado a v5.9.
- `src/prwx/__init__.py` actualizado a v5.9.0.
- `desktop/service-worker.js` actualizado con cache v5.9.

## Estrategia de carga

La consola intenta cargar las imágenes satelitales en este orden:

1. URL directa del CDN NOAA/NESDIS/STAR encontrada por el backend.
2. Endpoint WFO San Juan de PR-WX.
3. Endpoint image `.jpg` de PR-WX.
4. Endpoint proxy de PR-WX.
5. Página oficial NOAA como referencia externa.

## Nota operacional

Este visor es experimental. La interpretación oficial de nubes, lluvia, tormentas, avisos y emergencias debe hacerse con NOAA, NWS, NHC y agencias oficiales de manejo de emergencias.