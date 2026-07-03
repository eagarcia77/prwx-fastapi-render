# PR-WX Hybrid Model v1.0

**PR-WX Hybrid Model v1.0** es un prototipo experimental para Puerto Rico con temperatura, sensación térmica, lluvia, viento, riesgo operacional y alertas en un dashboard accesible.

## Pueblos prioritarios

La interfaz destaca primero:

- Juana Díaz
- Ponce
- San Juan
- San Germán

## Componentes principales

- Dashboard Streamlit accesible.
- Actualización visual cada minuto.
- Mapa animado de lluvia, viento y temperatura.
- Tabla de temperatura por municipio.
- Panel de terremotos, tsunami y Android Sensor Bridge experimental.
- API local FastAPI.
- Docker y Docker Compose.

## Ejecutar con Docker

```powershell
docker compose build --no-cache
docker compose run --rm prwx-update-once
docker compose up prwx-dashboard
```

Abrir:

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

Abrir:

```text
http://localhost:8000/docs
```

Endpoints nuevos:

- `/temperature`
- `/temperature/focus`
- `/weather-animation`
- `/safety-alerts`
- `/realtime-summary`

## Advertencia

Este sistema es experimental y educativo. No sustituye a NWS San Juan, NOAA, USGS, Red Sísmica de Puerto Rico ni agencias de manejo de emergencias.


## Novedades v2.1

- Vista **Emergency Display** en el dashboard.
- Enfoque tipo centro de mando con semáforo y acciones rápidas.
- Mayor claridad para temperatura, lluvia, viento y seguridad.
- Prioridad visual reforzada para Juana Díaz, Ponce, San Juan y San Germán.


## Novedades v2.1

- Sonido opcional para alertas críticas.
- Notificaciones locales del navegador mientras la página está abierta.
- Modo claro, oscuro y alto contraste.
- Modo pantalla gigante/kiosco.
- Panel temporal: ahora, próximas 6 horas y próximas 24 horas.


## Novedades v2.1

- Mapa animado de trayectoria de huracanes en el Atlántico.
- Mapa mundial de terremotos en tiempo real (o muestra offline).
- Información más completa en terremotos y tsunami.


## Novedades v2.1

- Radar por capas: 1h, 3h, 6h y 24h.
- Cono de incertidumbre para trayectorias de huracanes.
- Riesgo de huracán para Puerto Rico.
- Filtros mundiales de terremotos por magnitud, tsunami y cantidad.
- Alertas más fuertes para tsunami y terremotos.


## Novedades v2.1

- Panel de salud del sistema.
- Manifest MRMS QPE para integración real de radar.
- Mejor manejo de fuentes externas y archivos vacíos.
- Pestaña Sistema/MRMS en el dashboard.


## Novedades v2.1

- MRMS real en el mapa usando `exportImage` del ImageServer.
- Capas QPE 1h, 3h, 6h, 12h, 24h, 48h y 72h.
- Nueva pestaña MRMS Real.
- Endpoint `/radar/mrms-real`.


## Novedades v2.1

- Alertas activas por defecto.
- Sonido y notificaciones locales activos por defecto.
- Alertas persistentes hasta revisión.
- Reporte de endurecimiento y revisión del sistema.
- Dashboard con más fallbacks para evitar fallas por fuentes externas.


## Novedades v2.1

- Corrección MRMS con visor ArcGIS JS en navegador.
- Nuevas alternativas de URL `exportImage` y tabla de diagnóstico MRMS.
- Life Safety Board con acciones para inundación, calor, huracán, terremoto, tsunami, comunicaciones, energía y accesibilidad.
- Nueva pestaña MRMS Fix y Vida/Seguridad.


## Novedades v2.1

- Verificación de servicios externos y artefactos locales.
- Verificación específica del Android Sensor Bridge para terremotos.
- Nueva pestaña Servicios/Android.
- Nuevos endpoints de diagnóstico.


## Novedades v2.1

- Proyecto Android inicial en `android_sensor_app/`.
- App Kotlin para leer acelerómetro y enviar señales a `/seismic/android-trigger`.
- Consentimiento explícito, ubicación aproximada y sin identificadores personales.
- Estado de Android App Bridge.


## Novedades v2.1

- Preparado para Render + GitHub + FastAPI.
- `render.yaml`, `Procfile` y `start_render_api.sh`.
- Endpoints `/healthz`, `/readyz` y `/render/status`.
- Workflow de GitHub Actions para instalar, probar e importar la API.
