# PR-WX v5.2.0 — AURORA RainCast PR Official Satellite Viewer

## Propósito

Esta versión atiende directamente el problema reportado: las nubes no se ven en el mapa. La vista principal deja de depender del renderizado de capas WMS y coloca primero una imagen satelital directa NOAA/NESDIS/STAR del sector Puerto Rico.

## Cambios principales

- Vista principal con imagen directa STAR del sector Puerto Rico.
- Botón de producto para Banda 13 IR, GeoColor, Banda 14 IR y Banda 2 visible.
- Enlace visible a la página oficial NOAA STAR.
- Iframe oficial NOAA integrado como respaldo cuando las imágenes directas o WMS no renderizan.
- Mapa nowCOAST se mantiene como comparación secundaria.
- Botón para limpiar cache visual y service worker.
- Versión reducida y más directa para evitar confusión de múltiples mapas.

## Uso recomendado

1. Abrir `/desktop/live-rain.html`.
2. Presionar `Ctrl + F5`.
3. Usar primero `Banda 13 IR`.
4. Si la imagen directa no se ve, usar `Vista oficial NOAA` o el panel oficial integrado.
5. Usar nowCOAST solamente como comparación de radar y WMS.

## Advertencia

Sistema experimental y educativo. Validar siempre con NOAA, NWS San Juan, NHC y manejo de emergencias antes de decisiones críticas.