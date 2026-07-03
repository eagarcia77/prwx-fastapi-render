# PR-WX v1.0 Temperature Realtime Accessible Command Center

Esta versión corrige el problema principal reportado: la temperatura no se veía claramente. Ahora el panel muestra temperatura por pueblo, sensación térmica, humedad, lluvia, viento, riesgo operacional y alertas.

## Mejoras principales

- Temperatura visible por municipio.
- Sensación térmica visible por municipio.
- Tabla dedicada de temperatura y calor.
- Tarjetas prioritarias para Juana Díaz, Ponce, San Juan y San Germán.
- Mapa animado con lluvia, viento y temperatura en el texto alternativo.
- Resumen en lenguaje claro.
- Recomendaciones de mejora dentro del dashboard.
- Endpoints nuevos en API:
  - `/temperature`
  - `/temperature/focus`

## Cómo correr con Docker

```powershell
docker compose build --no-cache
docker compose run --rm prwx-update-once
docker compose up prwx-dashboard
```

Abrir:

```text
http://localhost:8501
```

## Actualización cada minuto

```powershell
docker compose --profile updater up -d prwx-updater
```

Ver logs:

```powershell
docker compose logs -f prwx-updater
```

## Nota operacional

El panel se actualiza visualmente cada minuto. Para proteger estabilidad y evitar abuso de APIs públicas, una implementación de producción debe separar actualización visual de actualización profunda de fuentes externas. Recomendación:

- Juana Díaz, Ponce, San Juan y San Germán: actualización frecuente.
- 78 municipios completos: actualización programada menos frecuente o por lotes.
- Alertas oficiales: revisar cada minuto si la API lo permite.
- Radar/MRMS y estaciones: usar caché y validación.

## Próximas mejoras sugeridas

1. Radar real por capas MRMS 1h, 3h y 24h.
2. Notificaciones web push para alertas.
3. Sonido opcional accesible para alertas críticas.
4. Modo kiosco para pantallas grandes.
5. Mini app Android propia para sensores anónimos.
6. Integración visible con Red Sísmica de Puerto Rico y NOAA Tsunami.
7. Panel por hora: mañana, tarde, noche.
8. Sensores IoT locales de lluvia, temperatura y presión.
