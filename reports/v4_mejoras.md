# Mejoras versión v0.4

La versión v0.4 convierte el prototipo en un sistema actualizable.

## Cambios principales

- Se añadió `src/prwx/pipeline.py` para centralizar la actualización live.
- Se creó `scripts/07_update_live_pipeline.py` como punto de entrada principal.
- Se añadió `scripts/08_validate_outputs.py` para verificar integridad de archivos generados.
- Se agregó GitHub Actions para actualizar datos cada 3 horas.
- Se agregó `run_auto_update_windows.bat` para actualización local cada 30 minutos.
- El dashboard ahora permite actualizar NWS manualmente, mostrar edad de datos y auto-refrescar pantalla.
- Se guarda historial compacto de predicciones.

## Limitaciones

- La corrección de sesgo todavía usa modelo demo.
- La precipitación base live depende de lo que entregue NWS; cuando no hay QPF, se usa proxy basado en PoP.
- Todavía falta validación contra lluvia observada de MRMS, estaciones NOAA y USGS.

## Próximo paso v0.5

Integrar MRMS QPE y crear una tabla de evaluación forecast vs observación para medir precisión real por municipio.
