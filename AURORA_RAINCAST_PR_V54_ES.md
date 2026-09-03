# PR-WX v5.4.0 — AURORA RainCast PR Backend Image Proxy

Esta versión corrige el problema observado donde el respaldo oficial integrado aparecía en gris con un ícono de error. Ese fallo ocurre porque la página oficial puede bloquearse dentro de un iframe por políticas del navegador o del servidor externo.

## Cambio principal

La vista principal ya no depende de un iframe. PR-WX ahora usa un endpoint backend propio que descarga la imagen más reciente de NOAA/NESDIS/STAR y la sirve desde el mismo dominio de PR-WX.

## Endpoint nuevo

- `/rain/live/satellite/proxy/{product}`

Productos:

- `band13` — Banda 13 IR, recomendado para ver nubes de día y noche.
- `geocolor` — GeoColor.
- `band14` — Banda 14 IR.
- `visible` — Banda 2 visible.

## Endpoints relacionados

- `/rain/live/satellite/latest`
- `/desktop/live-rain.html`

## Uso recomendado

1. Abrir `/desktop/live-rain.html`.
2. Presionar **Limpiar cache visual**.
3. Usar **Banda 13 IR**.
4. Comparar con GeoColor o Banda 14 IR.

## Nota operacional

Este visor es experimental. La interpretación oficial debe venir de NOAA, NWS San Juan, NHC y las agencias de manejo de emergencias.