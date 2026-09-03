# PR-WX v5.8.0 — AURORA RainCast PR WFO Satellite Fallback

Esta versión refuerza el visor de nubes sobre Puerto Rico cuando el mapa WMS, el iframe o las rutas directas del CDN no muestran imagen.

## Cambio principal

Se añadió un fallback usando la página oficial de GOES para el WFO de San Juan (`wfo=sju`) como una fuente adicional para localizar imágenes satelitales del sector Puerto Rico.

## Nuevas rutas principales

- `/rain/live/satellite/image/band13.jpg`
- `/rain/live/satellite/wfo/band13.jpg`
- `/rain/live/satellite/proxy/band13`
- `/rain/live/satellite/debug/band13.html`
- `/rain/live/satellite/self-test`

## Validación visual

La página muestra cuatro fuentes simultáneas:

1. Image endpoint
2. WFO SJU fallback
3. Proxy alterno
4. Segunda llamada anti-cache

## Nota operacional

Este visor es experimental. La interpretación oficial debe venir de NOAA, NWS San Juan, NHC y agencias de manejo de emergencias.