# PR-WX v2.2.1 - Render + GitHub + Python FastAPI

## Objetivo

Esta versión prepara PR-WX para publicarse como API FastAPI en Render desde GitHub.

## Archivos añadidos

- `render.yaml`
- `Procfile`
- `runtime.txt`
- `start_render_api.sh`
- `scripts/render_bootstrap_v21.py`
- `.github/workflows/ci-render-fastapi.yml`
- `Dockerfile.render`

## Endpoints principales

- `/healthz`
- `/readyz`
- `/render/status`
- `/docs`
- `/seismic/android-trigger`
- `/services/android-earthquake`
- `/services/android-app-status`

## Deploy en Render

1. Suba este proyecto a GitHub.
2. En Render, cree un nuevo Web Service desde el repositorio.
3. Use la configuración de `render.yaml` o estos comandos:

Build Command:

```bash
pip install --upgrade pip && pip install -r requirements.txt && pip install -e .
```

Start Command:

```bash
bash start_render_api.sh
```

Health Check Path:

```text
/healthz
```

## Android/iPhone o cliente móvil

Cuando Render publique la API, use la URL pública en la app:

```text
https://NOMBRE-DE-TU-SERVICIO.onrender.com
```

El endpoint para señales Android es:

```text
/seismic/android-trigger
```

## Nota

Render usa almacenamiento efímero en servicios web. Esta versión incluye `render_bootstrap_v21.py` para crear archivos mínimos si el servicio inicia sin datos procesados.


## Novedades v2.2.1

- Página web móvil en `/mobile/`.
- Endpoint `/seismic/web-trigger`.
- Cluster combinado `/seismic/mobile-cluster`.
- PWA básica con manifest y service worker.
- Funciona desde Render usando HTTPS.


## Corrección v2.2.1

- Ahora existe una carpeta real llamada `mobile/` en la raíz del proyecto.
- La ruta pública sigue siendo `/mobile/`.
- Se mantiene `web_mobile_bridge/` como respaldo heredado.
