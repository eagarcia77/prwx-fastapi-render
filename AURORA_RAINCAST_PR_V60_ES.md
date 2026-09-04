# PR-WX v6.0.0 — AURORA RainCast PR Animated Cloud Loop

## Propósito

Esta versión añade una vista principal con loop animado de nubes para Puerto Rico. La corrección responde al problema recurrente de que las nubes no se observaban de forma clara en el mapa WMS o en las vistas estáticas.

## Cambios principales

- Nueva página `desktop/live-rain.html` con dos vistas principales:
  - imagen fija satelital;
  - loop GIF animado de NOAA/NESDIS/STAR.
- Nuevo archivo `desktop/live-rain-v60.js`.
- Nuevo archivo `desktop/live-rain-v60.css`.
- Nuevo endpoint backend:
  - `/rain/live/satellite/loop/{product}.gif`
- El endpoint `/rain/live/satellite/latest` ahora devuelve también candidatos `loops`.
- El self-test indica si el producto tiene imagen fija y loop animado.
- El debug HTML muestra imagen fija, loop y candidatos detectados.

## Productos

- `band13`: Banda 13 IR, recomendada para nubes de día y de noche.
- `geocolor`: GeoColor.
- `band14`: Banda 14 IR alternativa.
- `visible`: Banda 2 visible.

## Prueba recomendada

1. Abrir `/rain/live/satellite/loop/band13.gif`.
2. Abrir `/rain/live/satellite/image/band13.jpg`.
3. Abrir `/rain/live/satellite/debug/band13.html`.
4. Abrir `/desktop/live-rain.html`.
5. Presionar **Limpiar cache visual**.
6. Presionar **Actualizar imagen**.

## Nota operacional

PR-WX es un tablero experimental. La interpretación oficial de condiciones meteorológicas debe provenir de NOAA, NWS, NHC y agencias de manejo de emergencias.