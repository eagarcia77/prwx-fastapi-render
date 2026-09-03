# PR-WX v5.5.0 — AURORA RainCast PR Satellite Proxy Diagnostic Console

## Propósito
Esta versión fortalece la vista de nubes cuando el iframe oficial aparece gris o cuando el navegador bloquea imágenes externas. La imagen satelital principal se carga desde un endpoint del mismo dominio de PR-WX.

## Cambios principales
- Vista principal por proxy: `/rain/live/satellite/proxy/band13`.
- Self-test técnico: `/rain/live/satellite/self-test`.
- Indicadores por producto: Banda 13 IR, GeoColor, Banda 14 IR y Banda 2 visible.
- Enlaces de prueba directa para abrir cada imagen proxy en una pestaña.
- Fallback SVG diagnóstico para evitar paneles grises o imagen rota.
- Cache visual v5.5 y versión interna 5.5.0.

## Uso recomendado
1. Abrir `/desktop/live-rain.html`.
2. Presionar `Limpiar cache visual`.
3. Usar `Banda 13 IR`.
4. Presionar `Probar proxy`.
5. Abrir `/rain/live/satellite/proxy/band13` si la imagen principal no se ve.

## Nota operacional
El visor es experimental. Las decisiones oficiales deben validarse con NOAA, NWS San Juan, NHC y manejo de emergencias.