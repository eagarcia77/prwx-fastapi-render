# Plan de implementación

## Fase 1: Prototipo mínimo viable

Duración sugerida: 2 a 4 semanas.

Objetivo: demostrar que una corrección local mejora el pronóstico base de lluvia de 24 horas.

Tareas:

1. Seleccionar 10 a 20 puntos representativos de PR.
2. Descargar observaciones históricas de estaciones y/o MRMS QPE.
3. Descargar pronósticos base o usar archivo histórico de pronóstico si está disponible.
4. Crear tabla de entrenamiento.
5. Entrenar modelo de sesgo.
6. Comparar base vs corregido.
7. Crear dashboard simple.

## Fase 2: Modelo por municipio

Duración sugerida: 1 a 2 meses.

Objetivo: producir predicción por municipio.

Tareas:

1. Añadir todos los municipios.
2. Añadir elevación y distancia a la costa.
3. Usar MRMS QPE para lluvia observada.
4. Añadir USGS para variables hidrológicas.
5. Entrenar por estación/municipio/región.
6. Calibrar umbrales de lluvia fuerte por región.

## Fase 3: Nowcasting de 0 a 6 horas

Duración sugerida: 2 a 4 meses.

Objetivo: mejorar lluvia de corto plazo usando radar/MRMS.

Tareas:

1. Descargar secuencias de MRMS.
2. Calcular movimiento de lluvia.
3. Probar persistencia, optical flow y modelos ML.
4. Validar contra acumulados de lluvia.

## Fase 4: Sistema operacional

Duración sugerida: 3 a 6 meses.

Objetivo: correr automáticamente cada hora.

Componentes:

- Ingesta automática de datos.
- Base de datos temporal.
- Modelo entrenado versionado.
- Dashboard web.
- Alertas experimentales.
- Reporte de precisión por región.

## Advertencia

El sistema debe presentarse como apoyo analítico. Las decisiones oficiales deben tomar como base los avisos del National Weather Service, NOAA, USGS y las autoridades de emergencia.
