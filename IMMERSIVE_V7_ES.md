# PR-WX v0.7 Clear Immersive

La v0.7 rediseña la experiencia para que la información sea más fácil de leer y más útil operacionalmente.

## Filosofía visual

La v0.6 era inmersiva, pero podía sentirse cargada. La v0.7 mantiene lo innovador, pero organiza la información en capas:

1. Resumen ejecutivo.
2. Prioridad de acción por municipio.
3. Mapa claro de lluvia/riesgo.
4. Gemelo 3D simplificado.
5. Módulo sísmico + Android Sensor Bridge.
6. Datos descargables.

## Android Sensor Bridge

No se conecta al sistema propietario de Google. En su lugar, prepara la arquitectura para una app Android propia que use el acelerómetro del equipo con consentimiento del usuario.

La app futura enviaría señales agregadas al endpoint:

```text
POST /seismic/android-trigger
```

El servidor evalúa múltiples señales y produce un estado de cluster, pero no emite alerta pública automática.

## Límite científico importante

Los terremotos no se predicen de forma confiable antes de que comiencen. La alerta temprana detecta ondas P después del inicio del evento y puede ofrecer segundos de ventaja antes de la llegada de sacudida más fuerte en algunas zonas.
