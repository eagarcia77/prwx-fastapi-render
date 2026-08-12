# PR-WX v2.4.1 Desktop + Mobile Fixed

## Rutas principales

- Render Desktop: `https://prwx-fastapi-render.onrender.com/desktop/`
- Render Mobile: `https://prwx-fastapi-render.onrender.com/mobile/`
- Estado Desktop: `https://prwx-fastapi-render.onrender.com/desktop-health`
- Estado API: `https://prwx-fastapi-render.onrender.com/api/status`

## Corrección principal

Render ahora inicia con `api.desktop_app:app`. Este wrapper conserva todos los endpoints existentes de `api.app`, pero añade la versión Desktop, monta `/desktop/`, verifica `/desktop-health` y redirige `/` hacia `/desktop/`.

## Nota

El sistema es experimental. No predice terremotos ni sustituye fuentes oficiales de emergencia.
