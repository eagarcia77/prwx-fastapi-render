# PR-WX Hybrid Model / PR-CARIBE WX v2

**PR-WX** es una plataforma meteorológica experimental para Puerto Rico con temperatura, sensación térmica, lluvia, viento, riesgo operacional, radar, ciclones y alertas. La nueva línea **PR-CARIBE WX Hybrid v2.0** añade una arquitectura entrenable específica para Puerto Rico y el Caribe sin asumir que los modelos de Estados Unidos continental tienen cobertura válida para la región.

## Pueblos prioritarios

La interfaz destaca primero:

- Juana Díaz
- Ponce
- San Juan
- San Germán

## Componentes principales

- Desktop web accesible.
- Mobile/PWA.
- Dashboard Streamlit.
- API FastAPI.
- Mapa de lluvia, viento y temperatura.
- Temperatura y riesgo por municipio.
- Radar/MRMS y productos tropicales.
- Panel de terremotos, tsunami y Android Sensor Bridge experimental.
- PR-CARIBE WX Hybrid v2.0: ensemble entrenable para temperatura, lluvia, viento, ráfagas, humedad y presión.

## PR-CARIBE WX Hybrid v2.0

El nuevo modelo utiliza solamente fuentes cuyo dominio documentado cubre Puerto Rico o el Caribe. El registro inicial contempla NWS San Juan, NAM Puerto Rico Nest, GFS, GEFS, MRMS Caribbean, TJUA/NEXRAD, GOES-East/GOES-19, NHC, HAFS, GFS-Wave/WAVEWATCH III, NDBC y NCEI Integrated Surface Database.

El modelo v2.0 está creado y el pipeline de entrenamiento está disponible, pero **no se marca como entrenado ni validado para producción hasta disponer de un dataset histórico real y completar backtesting independiente**. El pequeño `data/sample/training_sample.csv` heredado sigue siendo solamente un dataset de demostración y no se usa para declarar el nuevo modelo operacional.

Documentación completa:

```text
docs/PR_CARIBE_WX_V2.md
```

Entrenamiento con el dataset histórico canónico:

```bash
python scripts/22_train_pr_caribbean_v20.py
```

Estado y preparación:

```text
GET /caribbean/model/status
GET /caribbean/model/readiness
GET /caribbean/model/sources
```

Informe meteorológico municipal:

```text
GET /weather/report/{municipality}
```

Ejemplo:

```text
GET /weather/report/San Juan
```

## Desktop en Render

Rutas principales:

```text
/desktop/
/mobile/
/desktop-health
/api/status
/docs
```

La interfaz Desktop v2.5 incluye un generador de informe del tiempo por municipio y muestra separadamente el estado del modelo PR-CARIBE WX para evitar presentar como validado un modelo que todavía está en fase de entrenamiento.

## Ejecutar con Docker

```powershell
docker compose build --no-cache
docker compose run --rm prwx-update-once
docker compose up prwx-dashboard
```

Dashboard local:

```text
http://localhost:8501
```

## Actualización automática cada minuto

```powershell
docker compose --profile updater up -d prwx-updater
```

## API local

```powershell
docker compose up prwx-api
```

Documentación:

```text
http://localhost:8000/docs
```

Endpoints operacionales existentes incluyen:

- `/predictions`
- `/temperature`
- `/temperature/focus`
- `/weather-animation`
- `/safety-alerts`
- `/realtime-summary`
- `/radar/mrms-real`
- `/hurricanes/cone`
- `/hurricanes/pr-risk`
- endpoints sísmicos y de diagnóstico.

## Evolución existente

PR-WX ya incluye:

- Emergency Display tipo centro de mando.
- Sonido y notificaciones locales para alertas críticas.
- Modos claro, oscuro, alto contraste y kiosco.
- Panel temporal de ahora, 6 horas y 24 horas.
- Trayectorias y cono de incertidumbre para ciclones tropicales.
- Capas MRMS/QPE.
- Mapa mundial de terremotos y panel de tsunami.
- Life Safety Board.
- Android Sensor Bridge y Web Sensor Bridge experimentales con ubicación aproximada.
- Render + GitHub + FastAPI.
- Desktop y Mobile servidos desde el mismo backend.

## Advertencia

Este sistema es experimental y educativo. No sustituye las advertencias, vigilancias, pronósticos ni instrucciones oficiales de NOAA/NWS San Juan, National Hurricane Center, USGS, Red Sísmica de Puerto Rico o las agencias de manejo de emergencias. PR-CARIBE WX nunca debe cancelar ni reducir automáticamente la severidad de una alerta oficial.
