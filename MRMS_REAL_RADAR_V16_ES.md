# PR-WX v1.6 - MRMS real en el mapa

## Qué añade

- URLs reales `exportImage` del servicio NOAA/NWS MRMS QPE ImageServer.
- Capas QPE 1h, 3h, 6h, 12h, 24h, 48h y 72h.
- Nueva pestaña **MRMS Real** en el dashboard.
- Tabla accesible con enlaces de imagen por capa.
- Endpoint API `/radar/mrms-real`.

## Nota importante

Esta versión ya prepara imagen real desde MRMS QPE. Si el navegador o la red no puede cargar el servicio externo, el dashboard mantiene el pseudo-radar como respaldo.
