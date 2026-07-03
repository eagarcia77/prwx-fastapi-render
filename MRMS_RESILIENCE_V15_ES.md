# PR-WX v1.5 - MRMS-ready, Resiliencia y Salud del Sistema

## Arreglos y mejoras

- Panel de **salud del sistema** para saber si los archivos están listos, vacíos o degradados.
- Manifest de **MRMS QPE** para preparar integración real de radar por capas.
- Mejor manejo de archivos vacíos y fuentes externas que no respondan.
- Dashboard con pestaña adicional de **Sistema/MRMS**.
- Script nuevo `scripts/26_operational_update_v15.py`.

## Importante

La integración v1.5 deja el sistema listo para MRMS real, pero todavía mantiene visualización pseudo-radar como respaldo. La próxima versión puede convertir el servicio MRMS en raster/tiles reales dentro del mapa.
