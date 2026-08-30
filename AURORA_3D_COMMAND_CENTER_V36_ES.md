# PR-WX v3.6.0 — AURORA 3D Command Center

Esta versión añade una experiencia 3D moderna para visualizar el Caribe, el Atlántico tropical y Puerto Rico de una forma distinta a los mapas meteorológicos tradicionales.

## Nombre del componente

**AURORA Caribe 3D Command Center**  
Código interno: **AURORA-3D**

## Qué integra

- Escena 3D holográfica del Caribe y Atlántico tropical.
- Flujos volumétricos de polvo del Sahara.
- Trayectorias tropicales experimentales.
- Torres municipales por riesgo IA.
- Domo de riesgo sobre Puerto Rico.
- Rejilla atmosférica visual.
- Panel de control con métricas.
- Fallback accesible en CSS si Three.js/WebGL no carga.

## Endpoints

```text
/aurora-caribe/3d/model
/aurora-caribe/3d/status
/aurora-caribe/3d/layers
/aurora-caribe/3d/scene
/aurora-caribe/3d/report
```

## Archivos principales

```text
src/prwx/aurora_3d_scene_v36.py
api/aurora_3d_router.py
desktop/aurora-3d-command-center.js
desktop/aurora-3d.css
scripts/43_aurora_3d_scene_v36.py
tests/test_aurora_3d_v36.py
```

## Comando para generar artefactos locales

```bash
python scripts/43_aurora_3d_scene_v36.py --pretty
```

## Nota operacional

Este componente es una visualización IA experimental. No emite avisos oficiales. Las decisiones sobre tormentas, polvo del Sahara, salud respiratoria o emergencias deben validarse con NHC, NWS San Juan, agencias de salud y manejo de emergencias.
