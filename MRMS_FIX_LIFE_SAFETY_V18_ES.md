# PR-WX v1.8 - MRMS corregido + Life Safety Board

## Arreglo MRMS

El MRMS anterior podía fallar porque Streamlit/Docker intentaba descargar la imagen del ImageServer desde el servidor local.  
La v1.8 añade un visor ArcGIS JS embebido para que el navegador cargue directamente el ImageServer de NOAA/NWS.

Incluye:
- Visor ArcGIS JS en navegador.
- URLs `exportImage` como alternativa.
- Tabla accesible de capas.
- Radar de respaldo si MRMS no carga.

## Life Safety Board

Añade acciones que pueden ayudar a salvar vidas:
- Inundaciones.
- Calor extremo.
- Huracanes.
- Terremotos.
- Tsunami.
- Comunicaciones redundantes.
- Energía de respaldo.
- Accesibilidad de alertas.

## Importante

Este sistema no sustituye NWS, NOAA, USGS, Red Sísmica, FEMA ni manejo de emergencias. Sirve como tablero de apoyo operacional y educativo.
