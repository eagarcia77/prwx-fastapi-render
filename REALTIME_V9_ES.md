# PR-WX v0.9: actualización cada minuto, mapa animado y seguridad sísmica/tsunami

## Objetivo

Convertir el prototipo en un centro de comando más claro y moderno que pueda actualizarse constantemente desde Docker y mostrar la situación meteorológica de Puerto Rico con una lectura fácil.

## Componentes nuevos

1. **Actualizador cada minuto**  
   El servicio `prwx-updater` corre `scripts/20_operational_update_v9.py` cada 60 segundos.

2. **Mapa animado lluvia/viento**  
   El archivo `weather_animation_v9.csv` crea fotogramas de +0 a +60 minutos. El tamaño representa intensidad aproximada de lluvia, el color representa viento y la flecha indica dirección.

3. **Panel de alertas**  
   El archivo `safety_alerts_v9.csv` consolida señales de clima, terremotos, Android Sensor Bridge experimental y posibles avisos de tsunami detectados desde alertas oficiales NWS/NOAA.

4. **Pueblos prioritarios**  
   Juana Díaz, Ponce, San Juan y San Germán se muestran primero en tarjetas, tablas y comparaciones.

5. **Accesibilidad WAVE-ready**  
   El mapa no es la única fuente de información. Cada visual tiene una tabla equivalente en lenguaje claro.

## Ejecutar

```powershell
docker compose build --no-cache
docker compose run --rm prwx-update-once
docker compose up prwx-dashboard
```

## Modo automático cada minuto

```powershell
docker compose --profile updater up -d prwx-updater
```

## Archivos principales

- `src/prwx/realtime_v9.py`
- `src/prwx/operational_v9.py`
- `scripts/20_operational_update_v9.py`
- `dashboard/app.py`
- `data/processed/live_predictions_v9.csv`
- `data/processed/weather_animation_v9.csv`
- `data/processed/safety_alerts_v9.csv`
- `data/processed/realtime_summary_v9.json`

## Limitación importante

Los terremotos no se predicen. El sistema solo puede modelar una alerta temprana después de que el evento comienza, usando señales oficiales o agregadas. Para tsunami, se deben seguir solamente fuentes oficiales.
