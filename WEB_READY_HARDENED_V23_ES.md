# PR-WX v2.3 - Web Ready Hardened

## Qué mejora esta versión

Esta versión endurece el funcionamiento web para Android, iPhone, Render y GitHub Pages.

## Correcciones principales

- Carpeta física `mobile/` confirmada.
- Página raíz `index.html` para GitHub Pages que redirige a `mobile/`.
- Archivo `.nojekyll` para que GitHub Pages sirva los archivos sin interferencias.
- `api-config.js` para que GitHub Pages use automáticamente la API de Render.
- CORS configurado para permitir llamadas desde `https://eagarcia77.github.io` hacia Render.
- Endpoint `/web-bridge/status` más completo.
- Endpoint `/mobile/config.json` para verificar la configuración móvil.
- Workflows que escribían datos operacionales se movieron a `.github/workflows_disabled/` para evitar conflictos y sobrescrituras automáticas.
- `.gitattributes` para reducir advertencias LF/CRLF en Windows.
- `.gitignore` mejorado para datos generados.

## URLs esperadas

Render:

```text
https://prwx-fastapi-render.onrender.com/mobile/
https://prwx-fastapi-render.onrender.com/web-bridge/status
https://prwx-fastapi-render.onrender.com/mobile/config.json
```

GitHub Pages:

```text
https://eagarcia77.github.io/prwx-fastapi-render/
```

## Verificación local

```powershell
python scriptsender_bootstrap_v21.py
python scriptserify_web_mobile_v23.py
python -m pytest -q
```

## Importante

Este sistema es experimental. No predice terremotos ni reemplaza fuentes oficiales.
