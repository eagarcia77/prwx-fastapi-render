# PR-WX v4.0.0 — AURORA RainCast PR 4D

Esta versión añade una capa visual y analítica adicional sobre el mapa de lluvia en vivo.

## Nombre del modelo

**AURORA RainCast PR 4D**

## Objetivo

Fortalecer el mapa de lluvias de Puerto Rico con una lectura más moderna, visual y operativa para identificar lluvia actual, nubes de lluvia, zonas con mayor probabilidad de precipitación en las próximas horas y calidad básica de los servicios de datos.

## Mejoras principales

- Capa visual 4D de nubes animadas sobre el mapa.
- Panel **AURORA 4D Intelligence**.
- Ranking municipal de lluvia a corto plazo.
- Narrativa automática del modelo.
- Panel de calidad de datos.
- Integración no destructiva sobre `live-rain-v39.js`.
- Cache nuevo para evitar archivos viejos del navegador.

## Archivos añadidos

- `desktop/live-rain-v40.css`
- `desktop/live-rain-v40.js`

## Archivos actualizados

- `desktop/live-rain.html`
- `desktop/service-worker.js`
- `src/prwx/__init__.py`

## Nota importante

La visualización 4D y el análisis municipal son experimentales. No sustituyen los avisos oficiales de NOAA, NWS, NHC ni las instrucciones de manejo de emergencias.