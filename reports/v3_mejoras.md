# PR-WX v0.3 - Mejoras implementadas

## Objetivo de la versión

Esta versión convierte el prototipo inicial en una base más cercana a un sistema operativo para Puerto Rico. La meta no es producir un pronóstico oficial, sino preparar la infraestructura para comparar pronósticos base contra observaciones reales y aplicar corrección local por municipio.

## Cambios principales

1. Se añadió un archivo con los 78 municipios de Puerto Rico.
2. Se añadió un conector experimental a NWS API para pronóstico horario por punto geográfico.
3. Se añadió un flujo live:
   - descargar pronóstico NWS;
   - convertirlo a variables de entrada;
   - aplicar corrección de sesgo;
   - clasificar riesgo de lluvia.
4. Se actualizó el dashboard para escoger entre demo y datos NWS live.
5. Se añadió botón para descargar predicciones en CSV.
6. Se añadieron pruebas unitarias nuevas.

## Limitaciones conocidas

- Los centroides municipales son aproximados y deben sustituirse por datos GIS oficiales si se usa el sistema para investigación formal.
- NWS hourly puede proveer probabilidad de precipitación sin cantidad de precipitación acumulada. En esos casos el script usa un proxy marcado como `pop_proxy_no_qpf`.
- El modelo todavía entrena con datos de ejemplo; necesita histórico real de MRMS, NOAA/NCEI, USGS y pronósticos base.
- El riesgo de inundación es una clasificación inicial basada en lluvia; no incorpora todavía saturación de suelo, ríos, cuencas ni escorrentía.

## Recomendación para v0.4

La próxima versión debe enfocarse en datos reales de entrenamiento:

- MRMS QPE como lluvia observada.
- NBM/QPF o WRF como pronóstico base.
- USGS NWIS para ríos y respuesta hidrológica.
- Validación por región climática.
- Reporte automático de errores por municipio.
