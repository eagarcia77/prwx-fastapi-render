# PR-WX Hybrid Model v0.5 — Mejoras avanzadas

La versión v0.5 convierte el prototipo en un sistema operacional experimental. El cambio principal es que ya no depende únicamente del pronóstico base de NWS; ahora puede incorporar observaciones recientes de MRMS, datos hidrológicos de USGS y alertas activas de NWS.

## Arquitectura nueva

1. **NWS live**: pronóstico base por municipio.
2. **MRMS QPE**: lluvia observada estimada por radar.
3. **USGS NWIS**: señales de ríos y niveles de agua.
4. **NWS Alerts**: avisos activos para Puerto Rico.
5. **Modelo avanzado**: ensamble de Ridge, Huber, Random Forest, Extra Trees y Gradient Boosting.
6. **Riesgo operacional**: índice 0-100 calibrable para impacto local.
7. **Dashboard**: mapa, tabla, fuentes, calidad y documentación.
8. **API local**: endpoints para consultar predicciones.

## Por qué es más avanzado

El modelo ahora combina predicción, observación, incertidumbre y riesgo. Esto se acerca más a un sistema meteorológico operacional moderno, donde no solo se pregunta “cuánta lluvia caerá”, sino “qué nivel de impacto puede provocar en un municipio específico”.

## Próximo paso v0.6

La versión v0.6 debe enfocarse en entrenamiento histórico real: descargar datos pasados, construir una base de verificación y calibrar el modelo con eventos como María, Fiona, ondas tropicales, vaguadas, polvo del Sahara y episodios de calor extremo.
