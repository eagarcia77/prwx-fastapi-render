# PR-WX v5.6.0 — AURORA RainCast PR No-Blank Satellite Image Console

Esta versión refuerza la vista de nubes sobre Puerto Rico para evitar paneles grises, iframes bloqueados o imágenes rotas.

## Cambios principales

- La imagen principal ahora usa un `src` directo desde HTML: `/rain/live/satellite/image/band13.jpg`.
- Se mantiene el proxy alterno: `/rain/live/satellite/proxy/band13`.
- Se añade ruta con extensión `.jpg` para mejorar compatibilidad del navegador.
- El backend devuelve una imagen SVG de diagnóstico si NOAA STAR no responde, evitando un recuadro vacío.
- Se mantiene el self-test JSON en `/rain/live/satellite/self-test`.
- Se actualizan `desktop/live-rain.html`, `live-rain-v56.css`, `live-rain-v56.js`, `service-worker.js`, `api/live_rain_router.py`, `api/desktop_app.py` y la versión interna.

## Prueba crítica

Abrir:

```text
https://prwx-fastapi-render.onrender.com/rain/live/satellite/image/band13.jpg
```

Si la fuente oficial responde, debe mostrarse una imagen satelital real del sector Puerto Rico. Si no responde, debe mostrarse una tarjeta de diagnóstico generada por PR-WX en vez de una pantalla gris.

## Nota

Este sistema es experimental y no sustituye fuentes oficiales. Las decisiones críticas deben validarse con NOAA, NWS San Juan, NHC y manejo de emergencias.