# PR-WX v2.6.0 — Informe meteorológico Caribe-Atlántico

Esta actualización formaliza el informe meteorológico institucional y la ruta de entrenamiento para un modelo híbrido Caribe-Atlántico. El trabajo anterior de PR-CARIBE WX se conserva y ahora se amplía con una capa de análisis, matriz de fuentes, plan de entrenamiento y endpoints dedicados.

## Nuevos endpoints

- `/weather/report/caribbean-atlantic`
- `/weather/report/caribbean-atlantic.md`
- `/caribbean/model/training-plan`
- `/caribbean/model/feature-matrix`

## Qué analiza el informe

- Estado del modelo PR-CARIBE WX Hybrid.
- Si el modelo tiene datos suficientes para investigación, candidato operacional o producción.
- Fuentes necesarias para Caribe y Atlántico: GFS, GEFS, HAFS, NHC, ERA5, OISST, MRMS, radar, satélite, NWS San Juan y observaciones históricas.
- Variables objetivo: temperatura, lluvia 1h/6h/24h, viento, ráfagas, humedad, presión y riesgo tropical.
- Criterios mínimos antes de uso operacional.
- Limitaciones institucionales y necesidad de validación oficial.

## Comando para generar artefactos del informe

```bash
python scripts/34_generate_caribbean_atlantic_report_v26.py
```

## Advertencia

PR-WX es experimental. No sustituye a NOAA, NWS, NHC, Red Sísmica ni manejo de emergencias.
