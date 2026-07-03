# PR-WX v2.2.1 - Web Mobile Sensor Bridge

## Objetivo

Esta versión permite usar PR-WX desde una página web móvil sin instalar app nativa.

## Página principal

Una vez desplegado en Render, abra:

```text
https://TU-SERVICIO.onrender.com/mobile/
```

También puede usar:

```text
https://TU-SERVICIO.onrender.com/mobile-app
```

## Qué hace

- Solicita consentimiento.
- Usa ubicación aproximada.
- Pide permiso de movimiento cuando el navegador lo requiere.
- Lee `devicemotion` desde el navegador.
- Envía señales experimentales a `/seismic/web-trigger`.
- Mantiene un cluster conjunto en `/seismic/mobile-cluster`.
- Funciona como PWA básica con manifest y service worker.

## Limitaciones

- Requiere HTTPS para sensores, geolocalización y notificaciones en la mayoría de navegadores modernos.
- En iPhone/iOS debe tocar el botón “Permitir sensores” porque iOS requiere permiso por interacción del usuario.
- No predice terremotos.
- No emite alertas públicas automáticamente.
- Toda señal debe validarse contra USGS, Red Sísmica, NOAA/NWS o manejo de emergencias.


## Corrección v2.2.1

- Ahora existe una carpeta real llamada `mobile/` en la raíz del proyecto.
- La ruta pública sigue siendo `/mobile/`.
- Se mantiene `web_mobile_bridge/` como respaldo heredado.
