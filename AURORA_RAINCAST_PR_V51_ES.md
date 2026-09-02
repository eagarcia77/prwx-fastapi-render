# PR-WX v5.1.0 — AURORA RainCast PR Satellite Fallback

## Propósito
Esta versión corrige el problema reportado de que las nubes no se ven en el mapa. La solución deja de depender exclusivamente de las capas WMS de nowCOAST y añade imágenes satelitales directas de NOAA/NESDIS/STAR para el sector de Puerto Rico.

## Cambio principal
La vista `desktop/live-rain.html` ahora presenta primero un panel de **Imagen satelital directa NOAA STAR**, con productos GOES-19 para Puerto Rico:

- GOES-19 GeoColor
- GOES-19 Banda 13 IR limpia
- GOES-19 Banda 14 IR larga
- GOES-19 Banda 2 visible

## Por qué esta versión es necesaria
Las capas WMS pueden cargar pero verse transparentes, débiles o prácticamente vacías dependiendo del servicio, del producto, del navegador, del cache o de la hora. Las imágenes directas de STAR permiten ver la nubosidad real como imagen satelital completa del sector de Puerto Rico.

## Componentes añadidos
- `desktop/live-rain-v51.css`
- `desktop/live-rain-v51.js`
- actualización de `desktop/live-rain.html`
- actualización de `desktop/service-worker.js`
- versión interna `5.1.0`

## Modo recomendado
Usar primero **Banda 13 IR**. Si la imagen se ve débil, probar **GeoColor** o **Banda 14 IR**. Para lluvia asociada, revisar la capa de radar en el mapa inferior.

## Advertencia
Esta vista es experimental y educativa. Para decisiones críticas debe validarse con NOAA, NWS San Juan, NHC y agencias de manejo de emergencias.