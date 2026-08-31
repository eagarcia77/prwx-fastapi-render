# PR-WX v3.8.0 — AURORA RainCast PR

## Propósito

Esta versión mejora el mapa de lluvias en vivo para que sea más útil en Puerto Rico. El enfoque principal es ver lluvia, nubes, avisos oficiales y una trayectoria aproximada por pueblo.

## Mejoras principales

- Radar NOAA nowCOAST sobre Puerto Rico.
- Capa de nubes GOES visible e infrarroja.
- Trayectorias aproximadas de lluvia por pueblo usando viento observado.
- Municipios monitoreados adicionales: Juana Díaz, Ponce, San Juan, San Germán, Mayagüez, Arecibo, Caguas, Fajardo, Humacao, Guayama, Aguadilla y Bayamón.
- Rain Impact Score experimental por municipio.
- Conteo separado de alertas activas y alertas de inundación.
- Selector de enfoque por pueblo.
- Modo emergencia visual.

## Página principal

- `/desktop/live-rain.html`

## Archivos de interfaz

- `desktop/live-rain-v38.js`
- `desktop/live-rain-v38.css`

## Nota operacional

La trayectoria por pueblo es un nowcast visual experimental basado en viento local, probabilidad de precipitación y lectura rápida municipal. No sustituye productos oficiales de NOAA/NWS, el Servicio Nacional de Meteorología ni manejo de emergencias.
