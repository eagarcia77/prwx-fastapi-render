# PR-WX v2.0 - Android Sensor Bridge App Starter

## Qué incluye

Esta versión añade un proyecto Android inicial en la carpeta:

`android_sensor_app/`

La app permite:

- consentimiento explícito del usuario,
- lectura del acelerómetro,
- ubicación aproximada/manual,
- envío de señales al endpoint `/seismic/android-trigger`,
- prueba segura con señal baja,
- sin nombre, teléfono, IMEI ni device ID,
- configuración del servidor PR-WX API.

## Cómo abrirlo

1. Instale Android Studio.
2. Abra la carpeta `android_sensor_app`.
3. Sincronice Gradle.
4. Ejecute en emulador o teléfono Android.

## URL del servidor

En emulador Android use:

`http://10.0.2.2:8000`

En teléfono real use la IP LAN de la computadora donde corre la API, por ejemplo:

`http://192.168.1.25:8000`

## Seguridad

La app no predice terremotos ni emite alertas públicas. Solo envía señales experimentales al dashboard para validación contra USGS, Red Sísmica y fuentes oficiales.
