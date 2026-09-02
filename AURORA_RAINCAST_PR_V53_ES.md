# PR-WX v5.3.0 — AURORA RainCast PR Backend Latest Satellite Resolver

## Propósito
Esta versión corrige el problema persistente de nubes invisibles usando un resolvedor backend. En vez de depender solamente de URLs estáticas o de capas WMS que pueden renderizarse transparentes, el backend consulta el índice público de NOAA/NESDIS/STAR y devuelve la imagen más reciente disponible para el sector Puerto Rico.

## Cambios principales
- Nuevo endpoint: `/rain/live/satellite/latest`.
- El endpoint busca imágenes recientes de GOES-19 para Puerto Rico.
- Productos incluidos: Banda 13 IR, GeoColor, Banda 14 IR y Banda 2 visible.
- La página `desktop/live-rain.html` carga la versión v5.3.
- El mapa nowCOAST queda como comparación secundaria.
- Se mantiene el botón para limpiar cache visual.

## Importante
La vista principal ahora es NOAA STAR latest resuelto por backend. Si la imagen principal carga, deben verse nubes reales sobre Puerto Rico. Si no carga, usar el botón Vista oficial NOAA.

## Uso
Abrir:

```text
https://prwx-fastapi-render.onrender.com/desktop/live-rain.html
```

Luego usar:

```text
Limpiar cache visual
```

Producto recomendado:

```text
Banda 13 IR
```

## Nota operacional
Uso experimental. Validar cualquier decisión crítica con NOAA, NWS San Juan, NHC, Red Sísmica y manejo de emergencias.