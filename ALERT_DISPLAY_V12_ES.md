# PR-WX v1.2 Alert Display

Esta versión añade una capa de comunicación de emergencia para que el panel sea más útil en pantalla grande,
laboratorio, oficina, centro de mando o sala de monitoreo.

## Funciones nuevas

- **Sonido opcional de alerta** para riesgo alto, terremoto, tsunami o señales críticas.
- **Notificaciones locales del navegador** mientras la página esté abierta.
- **Modo pantalla gigante / kiosco** para proyección.
- **Modo claro, oscuro y alto contraste**.
- **Panel por periodo**: ahora, próximas 6 horas y próximas 24 horas.
- **Vista de acción inmediata**: qué municipio revisar primero y qué acción tomar.
- **Accesibilidad WAVE**: texto visible, tablas equivalentes, alto contraste y modo de movimiento reducido.

## Importante

Las notificaciones locales del navegador requieren permiso del usuario y funcionan mientras la página está abierta.
Para notificaciones web push reales en segundo plano se necesitaría un service worker, servidor de push y configuración de dominio HTTPS.

## Uso recomendado

1. Ejecutar el dashboard.
2. Activar `Modo pantalla grande / kiosco`.
3. Activar `Sonido opcional`.
4. Activar `Notificaciones locales`.
5. Dejar el actualizador Docker corriendo cada minuto.
