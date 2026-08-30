# PR-WX v3.4.0 — AURORA Caribe-Atlántico

## Nombre del modelo

El nuevo modelo experimental se llama **AURORA Caribe-Atlántico**.

Código interno:

```text
AURORA-CARIBE
```

Nombre completo:

```text
AURORA Caribe-Atlántico AI Forecast Model
```

AURORA significa:

```text
Análisis Unificado de Riesgo Operacional, Radar y Atmósfera para el Caribe y Atlántico
```

## Objetivo

AURORA-CARIBE integra mapas IA, predicción municipal, trayectoria tropical, alertas y preparación de datos históricos para apoyar el análisis meteorológico experimental de Puerto Rico, el Caribe y el Atlántico tropical.

## Entrenamiento continuo

Se añadió un workflow de GitHub Actions:

```text
.github/workflows/aurora-caribe-continuous-training-v34.yml
```

El workflow corre automáticamente:

```text
cada 6 horas
```

También puede ejecutarse manualmente desde GitHub Actions.

## Endpoints nuevos

```text
/aurora-caribe/model
/aurora-caribe/status
/aurora-caribe/readiness
/aurora-caribe/training/status
/aurora-caribe/training/plan
/aurora-caribe/maps/layers
/aurora-caribe/predictions/summary
/aurora-caribe/report
/aurora-caribe/training/run
```

## Dashboard

El Desktop ahora incluye una sección nueva:

```text
Modelo AURORA Caribe-Atlántico
```

Esta sección muestra:

- nombre oficial del modelo,
- confianza predictiva experimental,
- preparación de datos,
- disponibilidad de fuentes,
- capas predictivas conectadas,
- enlace al entrenamiento continuo.

## Seguridad operacional

AURORA-CARIBE no emite avisos oficiales. Los avisos oficiales deben venir de NHC, NWS San Juan y manejo de emergencias. El modelo se usa como apoyo analítico y educativo experimental.
