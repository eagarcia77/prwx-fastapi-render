# PR-WX v2.8.0 — Mapas interactivos con IA por municipio

Esta versión añade un componente de análisis geoespacial experimental para Puerto Rico. El objetivo es presentar un mapa interactivo por pueblo que ayude a interpretar el informe del tiempo con más claridad.

## Funcionalidad nueva

- Mapa interactivo de los 78 municipios de Puerto Rico.
- Marcadores por municipio usando centroides aproximados.
- Puntuación IA de riesgo meteorológico de 0 a 100.
- Clasificación bajo, moderado o alto.
- Análisis narrativo por municipio.
- Recomendación automática por pueblo.
- Integración con los productos ya existentes de temperatura, lluvia, viento, alertas y modelo PR-CARIBE WX.
- Endpoints GeoJSON para futura integración con Leaflet, ArcGIS, Mapbox o QGIS.

## Endpoints

```text
/ai/maps/status
/ai/maps/layers
/ai/maps/summary
/ai/maps/pr-municipalities
/ai/maps/pr-municipalities.geojson
/ai/maps/municipality/{municipality}
```

## Cómo se calcula el análisis IA

El motor analiza los datos operacionales disponibles y genera un índice integrado. La puntuación considera:

1. Temperatura y sensación térmica.
2. Lluvia estimada o corregida a 24 horas.
3. Probabilidad de precipitación, cuando está disponible.
4. Viento y ráfagas.
5. Alertas activas o asociadas.
6. Disponibilidad de datos por municipio.
7. Confianza del análisis según cantidad de variables disponibles.

## Uso en Desktop

El dashboard Desktop añade la sección:

```text
Mapa interactivo con IA por pueblo
```

Desde esa sección se puede:

- Actualizar el mapa.
- Seleccionar un municipio.
- Ver el análisis IA del pueblo.
- Revisar el nivel de riesgo y la recomendación.

## Limitación importante

Los puntos del mapa son centroides aproximados para visualización. No son una capa GIS oficial de límites municipales. Para cartografía oficial se recomienda integrar en una versión futura un shapefile o GeoJSON oficial de municipios de Puerto Rico.

## Uso operacional

Este componente no reemplaza fuentes oficiales. El análisis debe validarse con NOAA/NWS San Juan, NHC y manejo de emergencias antes de tomar decisiones públicas.
