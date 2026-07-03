# CHANGELOG

## v2.1.0 - Render + GitHub + FastAPI

- Añadido `render.yaml` para deploy en Render.
- Añadido `start_render_api.sh` y `Procfile`.
- Añadido bootstrap para Render: `scripts/render_bootstrap_v21.py`.
- Añadidos endpoints `/healthz`, `/readyz` y `/render/status`.
- Añadido workflow `.github/workflows/ci-render-fastapi.yml`.

# CHANGELOG

## v2.0.0 - Android Sensor Bridge App Starter

- Añadido proyecto Android Kotlin `android_sensor_app/`.
- Añadida lectura de acelerómetro y POST a `/seismic/android-trigger`.
- Añadido estado `android_app_bridge_status_v20.json`.
- Nuevo script `scripts/31_operational_update_v20.py`.

# CHANGELOG

## v1.9.1 - Dashboard filtered_global Fix

- Corregido `NameError: filtered_global is not defined` en el mapa mundial de terremotos.
- Restaurados filtros por magnitud, tsunami y cantidad de eventos visibles.
- Añadido manejo cuando los filtros no devuelven eventos.

# CHANGELOG

## v1.9.0 - Service Verification + Android Earthquake Bridge

- Añadida verificación de NWS, USGS, MRMS y NHC.
- Añadida verificación del Android Sensor Bridge local.
- Añadida pestaña Servicios/Android.
- Nuevo script `scripts/30_operational_update_v19.py`.

# CHANGELOG

## v1.8.0 - MRMS Fix + Life Safety Board

- Corregido MRMS mediante ArcGIS JS en navegador.
- Añadidos diagnósticos y URLs alternas MRMS.
- Añadido Life Safety Board.
- Nuevo script `scripts/29_operational_update_v18.py`.

# CHANGELOG

## v1.7.0 - Active Alerts Hardened

- Alertas y notificaciones activas por defecto.
- Sonido opcional activo por defecto.
- Consolidador de alertas `active_alerts_v17.csv`.
- Estado de notificaciones `notification_state_v17.json`.
- Reporte de endurecimiento `hardening_report_v17.json`.
- Nuevo script `scripts/28_operational_update_v17.py`.

# CHANGELOG

## v1.6.0 - Real MRMS Radar Display

- Añadidas URLs reales `exportImage` para MRMS QPE.
- Añadida pestaña MRMS Real en el dashboard.
- Añadido endpoint `/radar/mrms-real`.
- Nuevo script `scripts/27_operational_update_v16.py`.

# CHANGELOG

## v1.5.0 - MRMS-ready Resilience

- Añadido panel de salud del sistema.
- Añadido manifest MRMS QPE.
- Añadida resiliencia para archivos vacíos/fuentes externas.
- Nuevo script `scripts/26_operational_update_v15.py`.

# CHANGELOG

## v1.4.0 - Radar + Hurricane Cone + Enhanced Alerts

- Añadidas capas pseudo-radar 1h, 3h, 6h y 24h.
- Añadido cono de incertidumbre de huracanes.
- Añadido riesgo de huracán para Puerto Rico.
- Añadidos filtros mundiales de sismos.
- Añadidas alertas reforzadas para tsunami y terremoto.
- Nuevo script `scripts/25_operational_update_v14.py`.

# CHANGELOG

## v1.3.0 - Atlantic Hurricanes + Global Seismic

- Añadido mapa animado de huracanes en el Atlántico.
- Añadido mapa mundial de terremotos y tabla de tsunami.
- Añadida ampliación de información sísmica y de tsunami.
- Nuevo script `scripts/24_operational_update_v13.py`.

# CHANGELOG

## v1.2.0 - Alert Display

- Añadido sonido opcional para alertas críticas.
- Añadidas notificaciones locales del navegador.
- Añadidos modos claro, oscuro y alto contraste.
- Añadido modo pantalla gigante/kiosco.
- Añadido panel temporal ahora/6h/24h.
- Añadido wrapper operacional `scripts/23_operational_update_v12.py`.

# CHANGELOG

## v1.1.0 - Emergency Display

- Añadida vista tipo centro de mando.
- Nueva pestaña de Emergency Display en el dashboard.
- Wrapper operacional `scripts/22_operational_update_v11.py`.
- Archivo de documentación `EMERGENCY_DISPLAY_V11_ES.md`.
- Mantiene la base operacional y la accesibilidad WAVE de v1.0.

# Changelog

## v1.0.0 - Temperature Realtime Accessible Command Center

- Añade temperatura por pueblo.
- Añade sensación térmica por pueblo.
- Añade tabla `temperature_municipalities_v10.csv`.
- Añade tabla `focus_temperature_v10.csv` para Juana Díaz, Ponce, San Juan y San Germán.
- Añade `weather_animation_v10.csv` con lluvia, viento y temperatura.
- Añade `realtime_summary_v10.json` con recomendaciones futuras.
- Añade endpoints `/temperature` y `/temperature/focus`.
- Actualiza Docker para ejecutar `scripts/21_operational_update_v10.py`.
- Mejora lectura WAVE: más texto visible, tablas claras y explicación de calor.

## v0.9.0

- Actualización cada minuto.
- Mapa animado lluvia/viento.
- Alertas de seguridad climática, terremoto y tsunami.
