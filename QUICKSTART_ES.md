# Guía rápida - PR-WX v2.2.1

## 1. Abrir la carpeta

Descomprima el ZIP y abra PowerShell dentro de la carpeta.

## 2. Construir Docker

```powershell
docker compose build --no-cache
```

## 3. Generar datos

```powershell
docker compose run --rm prwx-update-once
```

## 4. Abrir dashboard

```powershell
docker compose up prwx-dashboard
```

Luego abra:

```text
http://localhost:8501
```

## 5. Activar actualización cada minuto

En otra ventana de PowerShell:

```powershell
docker compose --profile updater up -d prwx-updater
```

## 6. Ver logs

```powershell
docker compose logs -f prwx-updater
```

## 7. Detener

```powershell
docker compose down
```

## Archivos importantes

- `dashboard/app.py`
- `scripts/21_operational_update_v10.py`
- `src/prwx/temperature_v10.py`
- `src/prwx/operational_v10.py`
- `REALTIME_V10_ES.md`


## Ejecución recomendada v2.2.1

```powershell
docker compose build --no-cache
docker compose run --rm prwx-update-once
docker compose up prwx-dashboard
```

Luego abra `http://localhost:8501`.


## Novedades v2.2.1

- Sonido opcional para alertas críticas.
- Notificaciones locales del navegador mientras la página está abierta.
- Modo claro, oscuro y alto contraste.
- Modo pantalla gigante/kiosco.
- Panel temporal: ahora, próximas 6 horas y próximas 24 horas.


## Novedades v2.2.1

- Mapa animado de trayectoria de huracanes en el Atlántico.
- Mapa mundial de terremotos en tiempo real (o muestra offline).
- Información más completa en terremotos y tsunami.


## Novedades v2.2.1

- Radar por capas: 1h, 3h, 6h y 24h.
- Cono de incertidumbre para trayectorias de huracanes.
- Riesgo de huracán para Puerto Rico.
- Filtros mundiales de terremotos por magnitud, tsunami y cantidad.
- Alertas más fuertes para tsunami y terremotos.


## Novedades v2.2.1

- Panel de salud del sistema.
- Manifest MRMS QPE para integración real de radar.
- Mejor manejo de fuentes externas y archivos vacíos.
- Pestaña Sistema/MRMS en el dashboard.


## Novedades v2.2.1

- MRMS real en el mapa usando `exportImage` del ImageServer.
- Capas QPE 1h, 3h, 6h, 12h, 24h, 48h y 72h.
- Nueva pestaña MRMS Real.
- Endpoint `/radar/mrms-real`.


## Novedades v2.2.1

- Alertas activas por defecto.
- Sonido y notificaciones locales activos por defecto.
- Alertas persistentes hasta revisión.
- Reporte de endurecimiento y revisión del sistema.
- Dashboard con más fallbacks para evitar fallas por fuentes externas.


## Novedades v2.2.1

- Corrección MRMS con visor ArcGIS JS en navegador.
- Nuevas alternativas de URL `exportImage` y tabla de diagnóstico MRMS.
- Life Safety Board con acciones para inundación, calor, huracán, terremoto, tsunami, comunicaciones, energía y accesibilidad.
- Nueva pestaña MRMS Fix y Vida/Seguridad.


## Novedades v2.2.1

- Verificación de servicios externos y artefactos locales.
- Verificación específica del Android Sensor Bridge para terremotos.
- Nueva pestaña Servicios/Android.
- Nuevos endpoints de diagnóstico.


## Novedades v2.2.1

- Proyecto Android inicial en `android_sensor_app/`.
- App Kotlin para leer acelerómetro y enviar señales a `/seismic/android-trigger`.
- Consentimiento explícito, ubicación aproximada y sin identificadores personales.
- Estado de Android App Bridge.


## Novedades v2.2.1

- Preparado para Render + GitHub + FastAPI.
- `render.yaml`, `Procfile` y `start_render_api.sh`.
- Endpoints `/healthz`, `/readyz` y `/render/status`.
- Workflow de GitHub Actions para instalar, probar e importar la API.


## Novedades v2.2.1

- Página web móvil en `/mobile/`.
- Endpoint `/seismic/web-trigger`.
- Cluster combinado `/seismic/mobile-cluster`.
- PWA básica con manifest y service worker.
- Funciona desde Render usando HTTPS.


## Corrección v2.2.1

- Ahora existe una carpeta real llamada `mobile/` en la raíz del proyecto.
- La ruta pública sigue siendo `/mobile/`.
- Se mantiene `web_mobile_bridge/` como respaldo heredado.
