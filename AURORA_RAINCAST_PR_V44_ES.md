# PR-WX v4.4.0 — AURORA RainCast PR Cloud Visibility Fix

## Propósito
Esta versión atiende el problema reportado: **las nubes no se veían claramente en el mapa**.

## Cambios principales
- Añade un mapa dedicado: **Mapa real de nubes sobre Puerto Rico**.
- Fuerza la capa GOES infrarroja `RAS_GOES_I4` por defecto.
- Mantiene la capa visible `RAS_GOES` como apoyo.
- Mantiene radar de lluvia `RAS_RIDGE_NEXRAD` encima de la nubosidad.
- Añade controles de opacidad independientes para nubes infrarrojas, nubes visibles y radar.
- Añade modos rápidos: Todo, Solo IR, Visible y Radar.
- Añade botones de enfoque para Juana Díaz, Ponce, San Juan, San Germán, Fajardo y Mayagüez.
- Fuerza refresco de capas cada dos minutos para reducir problemas de caché.

## Nota operacional
La capa infrarroja es la prioridad porque puede mostrar nubosidad aunque la capa visible esté débil o sea de noche. La lectura continúa siendo experimental y debe validarse con NOAA/NWS/NHC y manejo de emergencias para decisiones críticas.
