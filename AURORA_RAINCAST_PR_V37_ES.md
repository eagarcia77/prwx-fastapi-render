# PR-WX v3.7.0 — AURORA RainCast PR

## Propósito

AURORA RainCast PR añade un componente especializado para lluvia en vivo, radar, lluvia observada, pronóstico cuantitativo de precipitación y alertas de inundación/lluvia para Puerto Rico.

## Nombre del modelo

- **Nombre:** AURORA RainCast PR
- **Código:** AURORA-RAIN
- **Versión:** 3.7.0
- **Uso:** apoyo operacional experimental para monitoreo de lluvia e inundación.

## Nuevos endpoints

```text
/rain/live/model
/rain/live/status
/rain/live/sources
/rain/live/layers
/rain/live/alerts
/rain/live/summary
/rain/live/municipal-risk
```

## Nueva página Desktop

```text
/desktop/live-rain.html
```

La página incluye:

- Radar en vivo.
- Lluvia observada 1h.
- Lluvia observada 3h.
- Lluvia observada 24h.
- QPF forecast.
- Alertas filtradas de lluvia e inundación.
- Panel municipal para Juana Díaz, Ponce, San Juan, San Germán, Mayagüez, Fajardo, Arecibo y Caguas.

## Fuentes conectadas

- NWS Active Alerts para Puerto Rico.
- NOAA/NWS MRMS Radar Base Reflectivity.
- NOAA/NWS Radar Base Reflectivity Time Image Service.
- NOAA/NWS MRMS QPE.
- NOAA/WPC Quantitative Precipitation Forecast.

## Política de actualización

- Alertas: 60 segundos.
- Radar: 5 minutos recomendado por servicio.
- QPE/QPF: según actualización de cada producto oficial.

## Advertencia

El sistema es experimental. No emite avisos oficiales ni sustituye NWS San Juan, NOAA, NHC, agencias de salud, municipios ni manejo de emergencias.
