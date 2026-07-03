# PR-WX v1.7 - Alertas activas, notificaciones y dashboard endurecido

## Qué corrige y añade

- Las alertas quedan activas por defecto.
- Las notificaciones del navegador quedan activadas en el panel; el usuario solo debe conceder permiso del navegador.
- El sonido opcional queda activo por defecto.
- Se añade tabla consolidada `active_alerts_v17.csv`.
- Se añade estado de notificaciones `notification_state_v17.json`.
- Se añade reporte de endurecimiento `hardening_report_v17.json`.
- El dashboard mantiene fallbacks para no romperse si una fuente externa no responde.

## Importante

Las notificaciones de navegador requieren que la página esté abierta y que el usuario acepte el permiso del navegador. Para notificaciones push reales en segundo plano se necesita HTTPS, service worker y servidor push.
