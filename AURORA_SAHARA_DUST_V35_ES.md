# PR-WX v3.5.0 — AURORA Sahara-Caribe

## Nombre del submodelo

**AURORA Sahara-Caribe** (`AURORA-SAHARA`) es el submodelo experimental de AURORA Caribe-Atlántico para analizar polvo del Sahara, aerosoles, bruma, AOD, PM2.5 estimado, visibilidad y riesgo respiratorio regional.

## Alcance

El modelo cubre Puerto Rico, el Caribe oriental y corredores de polvo desde África occidental hacia el Atlántico tropical. El objetivo es añadir una capa preventiva al dashboard para apoyar decisiones académicas, institucionales y operacionales cuando el polvo del Sahara pueda afectar visibilidad, salud respiratoria o actividades al aire libre.

## Fuentes contempladas

- NASA Worldview / MERRA-2 para AOD y polvo.
- NOAA/NESDIS GOES-East para validación visual satelital.
- Copernicus Atmosphere Monitoring Service para aerosol/dust forecast.
- EPA AirNow o datos locales de PM2.5 cuando estén disponibles.
- NWS San Juan para contexto operacional y mensajes oficiales.

## Endpoints añadidos

```text
/aurora-caribe/dust/model
/aurora-caribe/dust/status
/aurora-caribe/dust/sources
/aurora-caribe/dust/analysis
/aurora-caribe/dust/map
/aurora-caribe/dust/map.geojson
/aurora-caribe/dust/training/plan
/aurora-caribe/dust/training/plan.md
/aurora-caribe/dust/training/status
/aurora-caribe/dust/health-guidance
```

## Entrenamiento continuo

Se añadió el workflow:

```text
.github/workflows/aurora-sahara-dust-continuous-training-v35.yml
```

Corre cada 6 horas y genera el artifact:

```text
aurora-sahara-dust-training-v35
```

## Advertencia

Este sistema es experimental. No sustituye avisos oficiales de NWS San Juan, NOAA, NASA, AirNow, agencias de salud pública ni manejo de emergencias.
