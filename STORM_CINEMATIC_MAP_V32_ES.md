# PR-WX v3.2.0 — Mapa IA cinemático de trayectoria hacia Puerto Rico

## Propósito

Esta versión mejora el mapa IA de trayectoria tropical para que se vea más moderno e innovador. La visualización añade un modo de centro de operaciones con trayectoria animada, dibujo de tormenta, controles de reproducción y estimación experimental de impacto por pueblos prioritarios.

## Mejoras principales

- Ícono animado de tormenta/huracán sobre el mapa.
- Modo visual cinemático con fondo satelital por defecto.
- Trayectoria con línea brillante y puntos de pronóstico.
- Control de reproducción, pausa, reinicio y línea de tiempo.
- Tarjeta lateral con probabilidad IA, puntuación de riesgo, distancia a PR, viento máximo y confianza.
- Estimación experimental de impacto para San Juan, Ponce, Juana Díaz, San Germán, Fajardo y Mayagüez.
- Nuevo archivo de estilos `desktop/storm-cinematic.css`.
- Actualización del service worker para evitar que el navegador retenga la versión anterior.

## Archivos modificados

```text
desktop/index.html
desktop/storm-map.js
desktop/storm-cinematic.css
desktop/service-worker.js
desktop/api-config.js
src/prwx/__init__.py
```

## Enlaces de prueba

```text
https://prwx-fastapi-render.onrender.com/desktop/
https://prwx-fastapi-render.onrender.com/ai/storm-tracks/map.geojson
https://prwx-fastapi-render.onrender.com/ai/storm-tracks/analysis
https://prwx-fastapi-render.onrender.com/desktop-health
```

## Uso responsable

La visualización es experimental. No emite avisos oficiales y no sustituye los productos del National Hurricane Center, NWS San Juan ni manejo de emergencias.
