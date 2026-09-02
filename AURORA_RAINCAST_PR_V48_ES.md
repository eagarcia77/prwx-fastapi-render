# PR-WX v4.8.0 — AURORA RainCast PR Cloud Verification Pro

## Propósito

Esta versión consolida la corrección de visibilidad de nubes en `desktop/live-rain.html`. La página se enfoca en mostrar la nubosidad que pasa sobre Puerto Rico con tres mecanismos de validación visual.

## Mejoras principales

- GOES infrarrojo (`RAS_GOES_I4`) activo con opacidad alta por defecto.
- GOES visible (`RAS_GOES`) como capa de apoyo.
- Radar de lluvia (`RAS_RIDGE_NEXRAD`) encima de las nubes.
- Validación directa por imágenes WMS independientes.
- Selector de mapa base: satélite, topográfico y calles.
- Enfoque rápido por municipios prioritarios.
- Botón de actualización manual.
- Modo kiosco para pantalla grande.
- Panel diagnóstico de versión, fuente, capa y frecuencia de actualización.

## Cómo probar

Abrir:

```text
https://prwx-fastapi-render.onrender.com/desktop/live-rain.html
```

Luego presionar `Ctrl + F5`.

Primero utilizar el modo `IR fuerte` y subir la opacidad de `Nubes IR` a 100%.

## Interpretación

La capa infrarroja debe ser la primera opción cuando la nubosidad no se distingue bien. La capa visible puede verse débil de noche o bajo ciertas condiciones de iluminación. Por eso esta versión no depende solo de la capa visible.

## Nota operacional

Este proyecto es experimental. Para decisiones críticas debe validarse con NOAA, NWS San Juan, NHC y manejo de emergencias.