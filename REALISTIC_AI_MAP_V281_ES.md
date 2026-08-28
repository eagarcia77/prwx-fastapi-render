# PR-WX v2.8.1 — Mapa real interactivo con IA por municipio

## Objetivo

Esta versión mejora el mapa IA de Puerto Rico para que se vea más real y útil desde la versión Desktop. El mapa anterior mostraba una visualización experimental por puntos; ahora se integra una base cartográfica real con capas de calles, satélite y topografía.

## Cambios principales

- Se añade `desktop/real-map.js`.
- Se integra Leaflet en `desktop/index.html`.
- Se actualiza `desktop/styles.css` con un contenedor de mapa más grande y moderno.
- Se actualiza el service worker para limpiar el cache anterior.
- Se mantiene el endpoint `GET /ai/maps/pr-municipalities.geojson`.
- Se mantiene el análisis IA por municipio desde `GET /ai/maps/municipality/{municipality}`.

## Capas del mapa

El usuario puede alternar entre:

1. Calles.
2. Satélite.
3. Topográfico.

## Análisis por municipio

Cada marcador municipal muestra:

- Nombre del municipio.
- Riesgo IA de 0 a 100.
- Nivel de riesgo: bajo, moderado o alto.
- Temperatura.
- Sensación térmica.
- Lluvia estimada en 24 horas.
- Viento.
- Alertas asociadas.
- Resumen IA.
- Recomendación práctica.

## Limitación importante

Los marcadores usan centroides aproximados por municipio. Esta versión mejora la apariencia real del mapa usando una base cartográfica, pero todavía no sustituye un GeoJSON oficial de polígonos municipales. La próxima mejora recomendada es incorporar polígonos oficiales de los 78 municipios para colorear el territorio completo.

## Endpoints relacionados

```text
/ai/maps/status
/ai/maps/layers
/ai/maps/summary
/ai/maps/pr-municipalities
/ai/maps/pr-municipalities.geojson
/ai/maps/municipality/{municipality}
```

## Uso

Abrir:

```text
https://prwx-fastapi-render.onrender.com/desktop/
```

Luego ir a la sección:

```text
Mapa real interactivo con IA por pueblo
```

## Advertencia operacional

PR-WX es experimental. No reemplaza avisos oficiales de NOAA, NWS San Juan, NHC ni manejo de emergencias.
