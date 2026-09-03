# PR-WX v5.7.0 — AURORA RainCast PR Page Resolver

## Propósito
Esta versión refuerza el visor de nubes de Puerto Rico cuando la imagen no aparece, el iframe externo se bloquea o el WMS no muestra nubosidad.

## Cambio principal
El backend ahora usa un resolvedor basado en la página oficial de NOAA/NESDIS/STAR para el sector Puerto Rico. En lugar de depender solamente del índice del CDN, consulta la página oficial del producto, extrae candidatos de imagen y los sirve desde endpoints propios de PR-WX.

## Endpoints principales
- `/rain/live/satellite/latest`
- `/rain/live/satellite/self-test`
- `/rain/live/satellite/proxy/band13`
- `/rain/live/satellite/image/band13.jpg`
- `/rain/live/satellite/debug/band13.html`

## Productos
- Banda 13 IR
- GeoColor
- Banda 14 IR
- Banda 2 Visible

## Nota operacional
La vista es experimental y debe utilizarse como apoyo visual. Las decisiones críticas deben validarse con NOAA, NWS San Juan, NHC y manejo de emergencias.