# Android Sensor Bridge v0.7, diseño experimental

Este módulo NO accede al sistema interno de Google Android Earthquake Alerts. Ese sistema pertenece a Google/Android y no se incluye como API pública directa dentro de este prototipo.

La idea de PR-WX v0.7 es preparar una ruta propia, ética y privada, para un piloto con teléfonos Android voluntarios:

1. Una app Android propia lee el acelerómetro cuando el teléfono está quieto.
2. Si detecta una señal compatible con onda P, envía un trigger anónimo al endpoint `/seismic/android-trigger`.
3. El servidor agrupa múltiples triggers cercanos en tiempo y espacio.
4. El sistema marca “posible señal colectiva”, pero no emite alertas públicas sin validación oficial.

Datos permitidos para el piloto:

- hora UTC aproximada;
- latitud/longitud aproximada o celda geográfica;
- aceleración estimada;
- confianza del algoritmo local.

Datos que NO se deben recopilar:

- nombre;
- número de teléfono;
- dirección exacta;
- historial individual de ubicación;
- identificador persistente del equipo.

Ejemplo de payload:

```json
{
  "coarse_lat": 18.02,
  "coarse_lon": -66.90,
  "pga_g": 0.021,
  "confidence": 0.72,
  "source": "android_sensor_bridge"
}
```

Endpoint local:

```text
POST http://localhost:8000/seismic/android-trigger
```

Este módulo es educativo y de investigación. Para un despliegue real se requiere validación con sismólogos, manejo de emergencias, Red Sísmica de Puerto Rico, control de falsas alarmas y protocolos legales de privacidad.
