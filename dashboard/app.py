from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

from prwx.accessibility import focus_municipalities_table, focus_display_name
from prwx.temperature_v10 import add_temperature_columns, build_weather_animation_v10, build_temperature_table
from prwx.seismic import evaluate_android_trigger_cluster

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
META_PATH = PROCESSED / "latest_run.json"
PRED_PATHS = [
    PROCESSED / "live_predictions_v10.csv",
    PROCESSED / "live_predictions_v10.csv",
    PROCESSED / "live_predictions_v8.csv",
    PROCESSED / "live_predictions_v6.csv",
    PROCESSED / "live_predictions_v5.csv",
    PROCESSED / "live_predictions.csv",
]
ANIMATION_PATH = PROCESSED / "weather_animation_v10.csv"
SAFETY_PATH = PROCESSED / "safety_alerts_v9.csv"
SUMMARY_PATH = PROCESSED / "realtime_summary_v10.json"
FOCUS_PATH = PROCESSED / "focus_temperature_v10.csv"
TEMPERATURE_PATH = PROCESSED / "temperature_municipalities_v10.csv"
EARTHQUAKES_PATH = PROCESSED / "live_earthquakes_v7.csv"
EEW_PATH = PROCESSED / "seismic_eew_v7.csv"
ANDROID_PATH = PROCESSED / "android_triggers_sample_v7.csv"
HURRICANE_PATH = PROCESSED / "atlantic_hurricane_tracks_v13.csv"
HURRICANE_SUMMARY_PATH = PROCESSED / "atlantic_hurricane_summary_v13.json"
GLOBAL_EQ_PATH = PROCESSED / "global_earthquakes_v13.csv"
GLOBAL_TSUNAMI_PATH = PROCESSED / "global_tsunami_watch_v13.csv"
GLOBAL_SEISMIC_SUMMARY_PATH = PROCESSED / "global_seismic_summary_v13.json"
RADAR_LAYERS_PATH = PROCESSED / "radar_layers_v14.csv"
HURRICANE_CONE_PATH = PROCESSED / "atlantic_hurricane_cone_v14.csv"
HURRICANE_PR_RISK_PATH = PROCESSED / "hurricane_pr_risk_v14.csv"
V14_SUMMARY_PATH = PROCESSED / "v14_operational_summary.json"
SYSTEM_HEALTH_PATH = PROCESSED / "system_health_v15.json"
MRMS_MANIFEST_PATH = PROCESSED / "mrms_manifest_v15.csv"
MRMS_REAL_URLS_PATH = PROCESSED / "mrms_real_image_urls_v16.csv"
MRMS_REAL_SUMMARY_PATH = PROCESSED / "mrms_real_summary_v16.json"
ACTIVE_ALERTS_PATH = PROCESSED / "active_alerts_v17.csv"
NOTIFICATION_STATE_PATH = PROCESSED / "notification_state_v17.json"
HARDENING_REPORT_PATH = PROCESSED / "hardening_report_v17.json"
MRMS_FIXED_URLS_PATH = PROCESSED / "mrms_fixed_urls_v18.csv"
MRMS_FIXED_SUMMARY_PATH = PROCESSED / "mrms_fixed_summary_v18.json"
LIFE_SAFETY_ACTIONS_PATH = PROCESSED / "life_safety_actions_v18.csv"
MUNICIPAL_LIFE_SAFETY_PATH = PROCESSED / "municipal_life_safety_v18.csv"
LIFE_SAFETY_SUMMARY_PATH = PROCESSED / "life_safety_summary_v18.json"
SERVICE_STATUS_PATH = PROCESSED / "service_status_v19.csv"
ANDROID_STATUS_PATH = PROCESSED / "android_earthquake_bridge_status_v19.json"
VERIFICATION_SUMMARY_PATH = PROCESSED / "verification_summary_v19.json"
ANDROID_APP_STATUS_PATH = PROCESSED / "android_app_bridge_status_v20.json"

st.set_page_config(
    page_title="PR-WX v2.0 Service Android Verified",
    page_icon="🇵🇷",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
:root{
  --bg:#f8fafc; --text:#0f172a; --muted:#334155; --panel:#ffffff; --border:#94a3b8;
  --blue:#1d4ed8; --green:#166534; --amber:#92400e; --red:#991b1b; --purple:#6b21a8;
}
.stApp{background:var(--bg);color:var(--text)}
.block-container{max-width:1560px;padding-top:1rem;padding-bottom:2rem}
[data-testid="stSidebar"]{background:#e2e8f0;border-right:2px solid var(--border)}
[data-testid="stSidebar"] *{color:var(--text)}
:focus,button:focus,input:focus,textarea:focus,select:focus{outline:4px solid #f59e0b!important;outline-offset:3px!important}
.skip-link{position:absolute;left:-999px;top:auto;width:1px;height:1px;overflow:hidden}
.skip-link:focus{position:static;width:auto;height:auto;padding:.6rem;background:#fff7ed;border:3px solid #f59e0b;border-radius:8px;display:inline-block;margin-bottom:.5rem}
.hero{background:#ffffff;border:2px solid var(--border);border-radius:22px;padding:1.15rem 1.25rem;margin-bottom:1rem;box-shadow:0 12px 30px rgba(15,23,42,.07)}
.main-title{font-size:2.45rem;line-height:1.08;font-weight:950;margin:0;color:var(--text)}
.subtitle{font-size:1.08rem;color:var(--muted);max-width:1180px;margin:.55rem 0 0 0}
.badge{display:inline-block;border:2px solid var(--border);border-radius:999px;padding:.3rem .7rem;margin:.45rem .25rem 0 0;background:#fff;font-weight:800;color:var(--text)}
.card{background:#fff;border:2px solid var(--border);border-radius:18px;padding:1rem;min-height:126px;box-shadow:0 8px 22px rgba(15,23,42,.05)}
.card h3{margin:.1rem 0 .35rem 0;font-size:1rem;color:var(--muted)}
.big-number{font-size:2.15rem;font-weight:950;color:var(--text);line-height:1.05}
.note{font-size:.96rem;color:var(--muted);margin-top:.3rem}
.focus-card{background:#eff6ff;border:3px solid #1d4ed8;border-radius:18px;padding:1rem;height:100%}
.focus-card h3{font-size:1.25rem;margin:0 0 .4rem 0;color:#0f172a}
.alert-critical{background:#fef2f2;border-left:10px solid #991b1b;border-radius:14px;padding:1rem;margin:.65rem 0;color:#0f172a}
.alert-watch{background:#fffbeb;border-left:10px solid #92400e;border-radius:14px;padding:1rem;margin:.65rem 0;color:#0f172a}
.callout{background:#eff6ff;border-left:10px solid #1d4ed8;border-radius:14px;padding:1rem;margin:.65rem 0;color:#0f172a;font-size:1.04rem}
.ok{background:#ecfdf5;border-left:10px solid #166534;border-radius:14px;padding:1rem;margin:.65rem 0;color:#0f172a}
.small-table-note{font-size:.95rem;color:var(--muted)}
.stTabs [data-baseweb="tab-list"]{gap:.35rem;flex-wrap:wrap}
.stTabs [data-baseweb="tab"]{font-size:1rem;font-weight:850;background:#fff;border:1px solid var(--border);border-radius:10px 10px 0 0;padding:.65rem .85rem}
.stDataFrame,[data-testid="stTable"]{border:2px solid var(--border);border-radius:14px;overflow:hidden;background:#fff}
.emergency-band{background:#0f172a;color:#fff;border-radius:18px;padding:1rem 1.15rem;margin:0 0 1rem 0}.emergency-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}.em-box{background:#fff;border:2px solid var(--border);border-radius:18px;padding:1rem}.em-red{border-left:12px solid #991b1b}.em-amber{border-left:12px solid #92400e}.em-green{border-left:12px solid #166534}.em-blue{border-left:12px solid #1d4ed8}@media (max-width:1100px){.emergency-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}@media (prefers-reduced-motion: reduce){*{animation:none!important;transition:none!important;scroll-behavior:auto!important}}
</style>
""",
    unsafe_allow_html=True,
)


def safe_read_csv(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()
    except Exception as exc:
        st.warning(f"No se pudo leer {path.name}: {exc}")
        return pd.DataFrame()


def read_json(path: Path) -> dict:
    if not path.exists() or path.stat().st_size == 0:
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def age_minutes(value: str | None) -> float | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - dt).total_seconds() / 60
    except Exception:
        return None


def load_predictions() -> tuple[pd.DataFrame, str]:
    for path in PRED_PATHS:
        df = safe_read_csv(path)
        if not df.empty:
            return add_temperature_columns(df), path.name
    return pd.DataFrame(), "sin datos"


def friendly_level(value: str) -> str:
    text = str(value or "").lower()
    return {"bajo":"Bajo","vigilancia":"Vigilancia","moderado":"Moderado","alto":"Alto","crítico":"Crítico","critico":"Crítico"}.get(text, text.title() or "No disponible")


def simple_weather_table(df: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "municipality_display", "region", "temperature_f", "feels_like_f", "heat_risk_level", "corrected_precip_24h_in", "rain_rate_est_in_hr",
        "wind_speed_mph", "wind_direction_text", "operational_risk_score", "impact_level", "action_explained", "weather_plain_text",
    ]
    out = df[[c for c in columns if c in df.columns]].copy()
    out = out.rename(columns={
        "municipality_display":"Municipio",
        "region":"Región",
        "temperature_f":"Temperatura °F",
        "feels_like_f":"Sensación °F",
        "heat_risk_level":"Riesgo de calor",
        "corrected_precip_24h_in":"Lluvia 24h (pulgadas)",
        "rain_rate_est_in_hr":"Intensidad aprox. (in/h)",
        "wind_speed_mph":"Viento (mph)",
        "wind_direction_text":"Dirección",
        "operational_risk_score":"Riesgo 0-100",
        "impact_level":"Impacto",
        "action_explained":"Acción sugerida",
        "weather_plain_text":"Lectura clara",
    })
    for c in ["Temperatura °F", "Sensación °F", "Lluvia 24h (pulgadas)", "Intensidad aprox. (in/h)", "Viento (mph)"]:
        if c in out.columns:
            out[c] = pd.to_numeric(out[c], errors="coerce").round(2)
    if "Riesgo 0-100" in out.columns:
        out["Riesgo 0-100"] = pd.to_numeric(out["Riesgo 0-100"], errors="coerce").round(0).astype("Int64")
    if "Impacto" in out.columns:
        out["Impacto"] = out["Impacto"].map(friendly_level)
    return out



def period_action_table(df: pd.DataFrame) -> pd.DataFrame:
    """Create a simple now/6h/24h action table for emergency display."""
    if df is None or df.empty:
        return pd.DataFrame()
    out = df.copy()
    out["risk_now"] = pd.to_numeric(out.get("operational_risk_score", 0), errors="coerce").fillna(0)
    out["risk_6h"] = (out["risk_now"] * 0.88 + pd.to_numeric(out.get("wind_speed_mph", 0), errors="coerce").fillna(0) * 0.45 + pd.to_numeric(out.get("rain_rate_est_in_hr", 0), errors="coerce").fillna(0) * 12).clip(0, 100)
    out["risk_24h"] = (out["risk_now"] * 0.92 + pd.to_numeric(out.get("corrected_precip_24h_in", 0), errors="coerce").fillna(0) * 4 + pd.to_numeric(out.get("feels_like_f", 0), errors="coerce").fillna(0).sub(90).clip(lower=0) * 0.7).clip(0, 100)
    def label(v: float) -> str:
        if v >= 70:
            return "Alto: revisar acción inmediata"
        if v >= 45:
            return "Moderado: monitoreo intensivo"
        if v >= 25:
            return "Vigilancia: observar cambios"
        return "Bajo: monitoreo normal"
    out["Ahora"] = out["risk_now"].map(lambda x: label(float(x)))
    out["Próximas 6h"] = out["risk_6h"].map(lambda x: label(float(x)))
    out["Próximas 24h"] = out["risk_24h"].map(lambda x: label(float(x)))
    columns = ["municipality_display", "Ahora", "Próximas 6h", "Próximas 24h", "action_explained"]
    out = out[[c for c in columns if c in out.columns]].rename(columns={"municipality_display":"Municipio", "action_explained":"Acción sugerida"})
    return out


def make_animated_rain_wind_map(anim: pd.DataFrame, reduce_motion: bool) -> go.Figure:
    if reduce_motion:
        frame = anim[anim["forecast_minute"] == anim["forecast_minute"].min()].copy()
        fig = px.scatter_mapbox(
            frame,
            lat="lat", lon="lon", size="rain_frame_in_hr", color="wind_speed_mph",
            text="wind_arrow", hover_name="municipality_display",
            hover_data={
                "rain_frame_in_hr":":.3f", "rain_24h_in":":.2f", "wind_speed_mph":":.1f",
                "wind_direction_text":True, "temperature_frame_f":":.1f", "feels_like_f":":.1f", "operational_risk_score":":.0f", "lat":False, "lon":False,
            },
            color_continuous_scale="Cividis", zoom=8, center={"lat":18.21,"lon":-66.45}, height=640,
            labels={"rain_frame_in_hr":"Lluvia in/h", "wind_speed_mph":"Viento mph", "temperature_frame_f":"Temperatura °F", "feels_like_f":"Sensación °F"},
        )
    else:
        fig = px.scatter_mapbox(
            anim,
            lat="lat", lon="lon", size="rain_frame_in_hr", color="wind_speed_mph",
            text="wind_arrow", animation_frame="time_label", hover_name="municipality_display",
            hover_data={
                "rain_frame_in_hr":":.3f", "rain_24h_in":":.2f", "wind_speed_mph":":.1f",
                "wind_direction_text":True, "temperature_frame_f":":.1f", "feels_like_f":":.1f", "operational_risk_score":":.0f", "lat":False, "lon":False,
            },
            color_continuous_scale="Cividis", zoom=8, center={"lat":18.21,"lon":-66.45}, height=640,
            labels={"rain_frame_in_hr":"Lluvia in/h", "wind_speed_mph":"Viento mph", "temperature_frame_f":"Temperatura °F", "feels_like_f":"Sensación °F"},
        )
    fig.update_traces(textposition="top center", marker=dict(sizemin=8, opacity=.86))
    fig.update_layout(
        mapbox_style="carto-positron",
        margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor="#ffffff",
        font=dict(color="#0f172a", size=14),
        coloraxis_colorbar=dict(title="Viento mph"),
        legend=dict(orientation="h"),
    )
    if fig.layout.updatemenus:
        fig.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 850
        fig.layout.updatemenus[0].buttons[0].args[1]["transition"]["duration"] = 350
    return fig


def make_focus_bar(df: pd.DataFrame) -> go.Figure:
    focus = focus_municipalities_table(df)
    if focus.empty:
        return go.Figure()
    fig = px.bar(
        focus,
        x="municipality_display", y="operational_risk_score", text="operational_risk_score",
        hover_data={"corrected_precip_24h_in":":.2f", "temperature_f":":.1f", "feels_like_f":":.1f", "wind_speed_mph":":.1f", "wind_direction_text":True},
        labels={"municipality_display":"Municipio", "operational_risk_score":"Riesgo 0-100"},
        height=430,
    )
    fig.update_traces(texttemplate="%{text:.0f}", textposition="outside")
    fig.update_layout(paper_bgcolor="#fff", plot_bgcolor="#fff", font=dict(color="#0f172a", size=14), yaxis_range=[0, 100])
    return fig






def mrms_arcgis_component_html(layer_name: str) -> str:
    layer_map = {
        "QPE 1h": "rft_1hr", "QPE 3h": "rft_3hr", "QPE 6h": "rft_6hr",
        "QPE 12h": "rft_12hr", "QPE 24h": "rft_24hr", "QPE 48h": "rft_48hr", "QPE 72h": "rft_72hr",
    }
    fn = layer_map.get(layer_name, "rft_1hr")
    return f"""
<link rel="stylesheet" href="https://js.arcgis.com/4.30/esri/themes/light/main.css">
<script src="https://js.arcgis.com/4.30/"></script>
<div id="mrmsStatus" style="padding:8px;border:2px solid #1d4ed8;border-radius:8px;margin-bottom:8px;background:#eff6ff;color:#0f172a;font-family:Arial;font-weight:700">Cargando MRMS {layer_name}...</div>
<div id="mrmsView" style="height:650px;width:100%;border:2px solid #94a3b8;border-radius:12px;overflow:hidden"></div>
<script>
require(["esri/Map", "esri/views/MapView", "esri/layers/ImageryLayer", "esri/geometry/Extent"], function(Map, MapView, ImageryLayer, Extent) {{
 const serviceUrl = "https://mapservices.weather.noaa.gov/raster/rest/services/obs/mrms_qpe/ImageServer";
 const map = new Map({{ basemap: "gray-vector" }});
 const view = new MapView({{
   container: "mrmsView",
   map: map,
   extent: new Extent({{xmin:-68.25,ymin:17.55,xmax:-64.25,ymax:19.25,spatialReference:{{wkid:4326}}}})
 }});
 const layer = new ImageryLayer({{ url: serviceUrl, opacity: 0.72, renderingRule: {{ rasterFunction: "{fn}" }} }});
 layer.when(function() {{ document.getElementById("mrmsStatus").textContent = "MRMS {layer_name} cargado. Si no ve manchas de lluvia, puede que no haya precipitación o la capa esté transparente."; }})
 .catch(function(e) {{ document.getElementById("mrmsStatus").textContent = "MRMS no cargó en el navegador. Use radar de respaldo y fuentes oficiales."; console.error(e); }});
 map.add(layer);
}});
</script>
"""


def make_radar_layer_map(radar: pd.DataFrame, layer: str) -> go.Figure:
    if radar.empty:
        return go.Figure()
    plot = radar[radar["layer"].astype(str) == layer].copy() if "layer" in radar.columns else radar.copy()
    if plot.empty:
        plot = radar.copy()
    fig = px.scatter_mapbox(
        plot, lat="lat", lon="lon", size="rain_rate_in_hr", color="reflectivity_est_dbz",
        hover_name="municipality_display", text="municipality_display",
        hover_data={"rain_in":":.2f","rain_rate_in_hr":":.2f","reflectivity_est_dbz":":.1f","risk_score":":.0f","lat":False,"lon":False},
        color_continuous_scale="Turbo", zoom=8, center={"lat":18.21,"lon":-66.45}, height=640,
        labels={"rain_rate_in_hr":"Lluvia in/h", "reflectivity_est_dbz":"Reflectividad dBZ"}
    )
    fig.update_traces(textposition="top center", marker=dict(sizemin=10, opacity=.82))
    fig.update_layout(mapbox_style="carto-positron", margin=dict(l=0,r=0,t=10,b=0), paper_bgcolor="#ffffff", font=dict(color="#0f172a"))
    return fig


def make_hurricane_cone_map(tracks: pd.DataFrame, cone: pd.DataFrame, reduce_motion: bool) -> go.Figure:
    fig = make_hurricane_map(tracks, reduce_motion)
    if cone is not None and not cone.empty:
        fig.add_trace(go.Scattergeo(
            lon=cone["lon"], lat=cone["lat"], mode="markers", name="Cono de incertidumbre",
            marker=dict(size=5, opacity=0.28),
            text=cone.get("forecast_label", ""),
            hovertemplate="Cono %{text}<br>Lat %{lat:.2f}, Lon %{lon:.2f}<extra></extra>",
        ))
    return fig


def make_hurricane_map(tracks: pd.DataFrame, reduce_motion: bool) -> go.Figure:
    if tracks.empty:
        return go.Figure()
    hours = sorted(pd.to_numeric(tracks.get('forecast_hour', 0), errors='coerce').dropna().unique().tolist())
    storm_names = list(tracks['storm_name'].dropna().unique())
    fig = go.Figure()
    initial_hour = hours[0] if hours else 0
    for storm in storm_names:
        sub = tracks[(tracks['storm_name'] == storm) & (pd.to_numeric(tracks['forecast_hour'], errors='coerce') <= initial_hour)].copy()
        fig.add_trace(go.Scattergeo(
            lon=sub['lon'], lat=sub['lat'], mode='lines+markers+text', name=storm,
            text=[storm] + [''] * max(0, len(sub)-1), textposition='top center',
            hovertemplate='<b>%{text}</b><br>Lat %{lat:.2f}, Lon %{lon:.2f}<extra></extra>',
        ))
    if not reduce_motion and hours:
        frames = []
        for hr in hours:
            frame_traces = []
            for storm in storm_names:
                sub = tracks[(tracks['storm_name'] == storm) & (pd.to_numeric(tracks['forecast_hour'], errors='coerce') <= hr)].copy()
                frame_traces.append(go.Scattergeo(
                    lon=sub['lon'], lat=sub['lat'], mode='lines+markers+text', name=storm,
                    text=[storm] + [''] * max(0, len(sub)-1), textposition='top center'
                ))
            frames.append(go.Frame(data=frame_traces, name=f'+{int(hr)}h'))
        fig.frames = frames
        fig.update_layout(updatemenus=[dict(type='buttons', showactive=False, buttons=[dict(label='▶ Reproducir', method='animate', args=[None, {'frame': {'duration': 900, 'redraw': True}, 'transition': {'duration': 250}, 'fromcurrent': True}])])], sliders=[dict(active=0, steps=[dict(method='animate', label=f'+{int(hr)}h', args=[[f'+{int(hr)}h'], {'frame': {'duration': 0, 'redraw': True}, 'transition': {'duration': 0}}]) for hr in hours])])
    fig.update_layout(geo=dict(scope='world', projection_type='natural earth', showland=True, landcolor='#f8fafc', oceancolor='#dbeafe', showocean=True, lataxis_range=[0, 50], lonaxis_range=[-100, -10]), margin=dict(l=0,r=0,t=10,b=0), height=640, paper_bgcolor='#ffffff', font=dict(color='#0f172a'))
    return fig


def make_global_earthquake_map(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return go.Figure()
    plot = df.copy()
    plot['magnitude'] = pd.to_numeric(plot.get('magnitude', 0), errors='coerce').fillna(0)
    plot['tsunami_label'] = plot.get('tsunami', 0).map(lambda x: 'Tsunami' if int(float(x or 0)) > 0 else 'Sin tsunami')
    fig = px.scatter_geo(
        plot,
        lat='lat', lon='lon', size='magnitude', color='tsunami_label', hover_name='place',
        hover_data={'magnitude':':.1f', 'depth_km':':.1f', 'event_time_utc':True, 'lat':False, 'lon':False},
        projection='natural earth', height=650,
        labels={'magnitude':'Magnitud', 'depth_km':'Profundidad km', 'tsunami_label':'Bandera'}
    )
    fig.update_layout(margin=dict(l=0,r=0,t=10,b=0), paper_bgcolor='#ffffff', font=dict(color='#0f172a'))
    return fig

meta = read_json(META_PATH)
pred, source_name = load_predictions()
anim = safe_read_csv(ANIMATION_PATH)
safety = safe_read_csv(SAFETY_PATH)
summary = read_json(SUMMARY_PATH)
earthquakes = safe_read_csv(EARTHQUAKES_PATH)
eew = safe_read_csv(EEW_PATH)
android = safe_read_csv(ANDROID_PATH)
cluster = evaluate_android_trigger_cluster(android) if not android.empty else {"cluster_status":"sin señales", "trigger_count":0, "recommendation":"No hay señales Android agregadas."}
hurricane_tracks = safe_read_csv(HURRICANE_PATH)
hurricane_summary = read_json(HURRICANE_SUMMARY_PATH)
global_eq = safe_read_csv(GLOBAL_EQ_PATH)
global_tsunami = safe_read_csv(GLOBAL_TSUNAMI_PATH)
global_seismic_summary = read_json(GLOBAL_SEISMIC_SUMMARY_PATH)
radar_layers = safe_read_csv(RADAR_LAYERS_PATH)
hurricane_cone = safe_read_csv(HURRICANE_CONE_PATH)
hurricane_pr_risk = safe_read_csv(HURRICANE_PR_RISK_PATH)
v14_summary = read_json(V14_SUMMARY_PATH)
system_health = read_json(SYSTEM_HEALTH_PATH)
mrms_manifest = safe_read_csv(MRMS_MANIFEST_PATH)
mrms_real_urls = safe_read_csv(MRMS_REAL_URLS_PATH)
mrms_real_summary = read_json(MRMS_REAL_SUMMARY_PATH)
active_alerts = safe_read_csv(ACTIVE_ALERTS_PATH)
notification_state = read_json(NOTIFICATION_STATE_PATH)
hardening_report = read_json(HARDENING_REPORT_PATH)
mrms_fixed_urls = safe_read_csv(MRMS_FIXED_URLS_PATH)
mrms_fixed_summary = read_json(MRMS_FIXED_SUMMARY_PATH)
life_safety_actions = safe_read_csv(LIFE_SAFETY_ACTIONS_PATH)
municipal_life_safety = safe_read_csv(MUNICIPAL_LIFE_SAFETY_PATH)
life_safety_summary = read_json(LIFE_SAFETY_SUMMARY_PATH)
service_status = safe_read_csv(SERVICE_STATUS_PATH)
android_status = read_json(ANDROID_STATUS_PATH)
verification_summary = read_json(VERIFICATION_SUMMARY_PATH)
android_app_status = read_json(ANDROID_APP_STATUS_PATH)

st.sidebar.header("Control de actualización")
st.sidebar.write("El panel está configurado para refrescar la pantalla cada minuto y el contenedor actualizador puede correr cada 60 segundos.")
refresh_seconds = st.sidebar.selectbox("Refrescar pantalla cada", [60, 120, 300, 600, 0], index=0, format_func=lambda x: "No refrescar" if x == 0 else f"{int(x/60)} min")
if refresh_seconds:
    components.html(f"<script>setTimeout(function(){{window.parent.location.reload();}}, {refresh_seconds * 1000});</script>", height=0)
limit = st.sidebar.number_input("Límite de municipios para prueba rápida", min_value=0, max_value=78, value=0, help="0 procesa todos los municipios. Use 12 si desea una prueba rápida.")
if st.sidebar.button("Actualizar datos ahora", type="primary"):
    cmd = [sys.executable, "scripts/31_operational_update_v20.py"]
    if limit:
        cmd += ["--limit", str(limit)]
    with st.spinner("Actualizando clima, lluvia/viento animado, terremotos y tsunami..."):
        result = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=900)
    if result.returncode == 0:
        st.sidebar.success("Actualización v1.2 completada.")
        st.rerun()
    else:
        st.sidebar.error("No se pudo actualizar.")
        st.sidebar.code(result.stdout + "\n" + result.stderr)

st.sidebar.divider()
reduce_motion = st.sidebar.checkbox("Reducir animación", value=False, help="Muestra una imagen estática para apoyar accesibilidad y reducir movimiento.")
show_only_focus = st.sidebar.checkbox("Ver solo Juana Díaz, Ponce, San Juan y San Germán", value=False)
easy_mode = st.sidebar.checkbox("Modo lectura fácil", value=True)
show_raw = st.sidebar.checkbox("Mostrar datos técnicos", value=False)
kiosk_mode = st.sidebar.checkbox("Modo pantalla grande / kiosco", value=False)
play_sound_hint = st.sidebar.checkbox("Mostrar recordatorio de sonido de alerta", value=True)

visual_theme = st.sidebar.selectbox("Tema visual", ["Claro", "Oscuro emergencia", "Alto contraste"], index=0)
enable_sound = st.sidebar.checkbox("Activar sonido opcional de alerta", value=True)
enable_browser_notifications = st.sidebar.checkbox("Activar notificaciones locales del navegador", value=True)
alert_sound_threshold = st.sidebar.slider("Sonido si riesgo ≥", 40, 100, 70)
sticky_alerts_enabled = st.sidebar.checkbox("Mantener alertas visibles hasta revisar", value=True)
min_global_magnitude = st.sidebar.slider("Magnitud mínima mapa mundial", 0.0, 8.0, 3.0, 0.1)
show_tsunami_only = st.sidebar.checkbox("Mapa mundial: solo tsunami", value=False)
global_event_limit = st.sidebar.slider("Cantidad máxima eventos mundiales", 25, 500, 150, 25)
radar_layer_choice = st.sidebar.selectbox("Capa de radar respaldo", ["Radar 1h", "Radar 3h", "Radar 6h", "Radar 24h"], index=0)
mrms_real_layer_choice = st.sidebar.selectbox("Capa MRMS real", ["QPE 1h", "QPE 3h", "QPE 6h", "QPE 12h", "QPE 24h", "QPE 48h", "QPE 72h"], index=0)

age = age_minutes(meta.get("generated_at_utc"))
st.sidebar.caption(f"Fuente visible: {source_name}")
st.sidebar.caption(f"Versión: {meta.get('model_version', '2.0.0') if meta else '2.0.0'}")
if meta:
    st.sidebar.caption(f"Última corrida UTC: {meta.get('generated_at_utc', 'N/D')}")
if age is not None:
    st.sidebar.caption(f"Edad de datos: {age:.0f} min")


# Tema visual dinámico
if "visual_theme" in globals():
    if visual_theme == "Oscuro emergencia":
        st.markdown("""
<style>
.stApp{background:#020617!important;color:#f8fafc!important}
.hero,.card,.focus-card,.em-box,.stDataFrame,[data-testid="stTable"]{background:#0f172a!important;color:#f8fafc!important;border-color:#38bdf8!important}
.main-title,.subtitle,.note,.card h3,.focus-card h3{color:#f8fafc!important}
[data-testid="stSidebar"]{background:#111827!important}
[data-testid="stSidebar"] *{color:#f8fafc!important}
</style>
""", unsafe_allow_html=True)
    elif visual_theme == "Alto contraste":
        st.markdown("""
<style>
.stApp{background:#ffffff!important;color:#000000!important}
.hero,.card,.focus-card,.em-box{background:#ffffff!important;color:#000000!important;border:4px solid #000000!important}
.main-title,.subtitle,.note,.card h3,.focus-card h3{color:#000000!important}
.badge{border:3px solid #000000!important;color:#000000!important}
</style>
""", unsafe_allow_html=True)


st.markdown('<a class="skip-link" href="#contenido-principal">Saltar al contenido principal</a>', unsafe_allow_html=True)
st.markdown('<main id="contenido-principal" class="hero">', unsafe_allow_html=True)
st.markdown('<h1 class="main-title">PR-WX v2.0.1: Servicios verificados y Android Earthquake Bridge</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="subtitle">Centro accesible tipo centro de mando con actualización cada minuto, sonido opcional, notificaciones locales, temperatura por pueblo, mapa animado de lluvia/viento/temperatura, servicios verificados, Android Sensor Bridge para terremotos, MRMS corregido, alertas activas por defecto, notificaciones locales, Life Safety Board y radar de respaldo de huracanes del Atlántico y panel reforzado de terremotos/tsunami. Prioriza Juana Díaz, Ponce, San Juan y San Germán. Diseñado para pantalla grande, sala de operaciones o kiosco. Prototipo educativo; no sustituye NWS, NOAA, USGS, Red Sísmica ni manejo de emergencias.</p>',
    unsafe_allow_html=True,
)
st.markdown('<span class="badge">Alert Display</span><span class="badge">Sonido opcional</span><span class="badge">Notificaciones locales</span><span class="badge">Huracanes Atlántico</span><span class="badge">Cono de incertidumbre</span><span class="badge">Radar por capas</span><span class="badge">MRMS-ready</span><span class="badge">MRMS Real</span><span class="badge">Alertas activas</span><span class="badge">Notificaciones ON</span><span class="badge">MRMS Fix</span><span class="badge">Life Safety</span><span class="badge">Servicios verificados</span><span class="badge">Android Bridge</span><span class="badge">Android App</span><span class="badge">Salud del sistema</span><span class="badge">Terremotos mundiales</span><span class="badge">Actualización cada minuto</span><span class="badge">Temperatura por pueblo</span><span class="badge">Mapa lluvia/viento/temperatura</span><span class="badge">Alertas sísmicas y tsunami</span><span class="badge">WAVE-ready</span><span class="badge">Lectura fácil</span>', unsafe_allow_html=True)
st.markdown('</main>', unsafe_allow_html=True)

if pred.empty:
    st.markdown('<div class="alert-watch"><strong>No hay datos todavía.</strong> Ejecute la actualización v1.2 para crear el panel en tiempo real.</div>', unsafe_allow_html=True)
    st.code("python scripts\\20_operational_update_v9.py\nstreamlit run dashboard\\app.py", language="powershell")
    st.stop()

if show_only_focus:
    pred = focus_municipalities_table(pred)

with st.sidebar.expander("Filtros", expanded=not easy_mode):
    if "region" in pred.columns:
        regions = sorted(pred["region"].dropna().astype(str).unique())
        selected_regions = st.multiselect("Región", regions, default=regions)
        pred = pred[pred["region"].astype(str).isin(selected_regions)] if selected_regions else pred
    min_risk = st.slider("Riesgo mínimo", 0, 100, 0)
    pred = pred[pd.to_numeric(pred["operational_risk_score"], errors="coerce").fillna(0) >= min_risk]

if pred.empty:
    st.warning("No hay municipios para los filtros seleccionados.")
    st.stop()

if anim.empty:
    anim = build_weather_animation_v10(pred)
else:
    # keep animation aligned to currently filtered municipalities
    visible = set(pred["municipality"].astype(str)) if "municipality" in pred.columns else set()
    if visible and "municipality" in anim.columns:
        anim = anim[anim["municipality"].astype(str).isin(visible)]

focus_df = focus_municipalities_table(pred)
ranked = pred.sort_values(["is_focus_municipality", "operational_risk_score", "feels_like_f", "corrected_precip_24h_in"], ascending=[False, False, False, False])
max_risk = float(pd.to_numeric(pred["operational_risk_score"], errors="coerce").fillna(0).max())
max_precip = float(pd.to_numeric(pred["corrected_precip_24h_in"], errors="coerce").fillna(0).max())
max_wind = float(pd.to_numeric(pred["wind_speed_mph"], errors="coerce").fillna(0).max())
max_temp = float(pd.to_numeric(pred.get("temperature_f", pd.Series([0])), errors="coerce").fillna(0).max())
max_feels = float(pd.to_numeric(pred.get("feels_like_f", pd.Series([0])), errors="coerce").fillna(0).max())
alert_count = 0 if safety.empty else len(safety)

if age is not None and age > 5:
    st.markdown('<div class="alert-watch"><strong>Atención:</strong> los datos tienen más de 5 minutos. Use el botón de actualización o verifique que el actualizador Docker esté corriendo cada 60 segundos.</div>', unsafe_allow_html=True)

plain = summary.get("plain_language_summary") or "Vista operacional de lectura rápida. Verifique siempre fuentes oficiales antes de tomar decisiones."
st.markdown(f'<div class="callout"><strong>Lectura rápida:</strong><br>{plain}</div>', unsafe_allow_html=True)
if kiosk_mode:
    st.markdown('<div class="emergency-band"><strong>Modo pantalla grande:</strong> esta vista resalta la decisión inmediata y reduce elementos secundarios para lectura a distancia.</div>', unsafe_allow_html=True)
if play_sound_hint and not safety.empty:
    st.info('Sugerencia: en una próxima versión se puede añadir sonido opcional y notificaciones web push para alertas críticas.')

if sticky_alerts_enabled and not active_alerts.empty:
    top_active = active_alerts.iloc[0]
    st.markdown(f"<div class='alert-critical'><strong>Alertas activas v2.0:</strong> {len(active_alerts)} señal(es). Principal: {top_active.get('headline','revisar panel')}<br><strong>Acción:</strong> {top_active.get('recommended_action','Verificar fuentes oficiales.')}</div>", unsafe_allow_html=True)

if not safety.empty:
    top_alert = safety.iloc[0]
    css = "alert-critical" if str(top_alert.get("severity", "")).lower() in {"crítico", "critico", "alto", "severe", "critical"} else "alert-watch"
    st.markdown(f'<div class="{css}"><strong>Alerta principal:</strong> {top_alert.get("headline", "Señal relevante detectada")}<br><strong>Acción:</strong> {top_alert.get("recommended_action", "Verificar fuentes oficiales.")}</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="ok"><strong>Sin alertas activas en el prototipo.</strong> Continúe monitoreando fuentes oficiales.</div>', unsafe_allow_html=True)


# Sonido y notificaciones locales del navegador
critical_alert_active = (max_risk >= float(alert_sound_threshold)) or (not safety.empty and str(safety.iloc[0].get("severity", "")).lower() in {"crítico", "critico", "alto", "severe", "critical"})
alert_title = "PR-WX alerta operacional"
alert_message = f"Riesgo máximo {max_risk:.0f}/100. Revise el panel y fuentes oficiales."
if enable_sound and critical_alert_active:
    components.html("""
<div style="padding:10px;border:2px solid #991b1b;border-radius:10px;background:#fef2f2;color:#111827;font-family:Arial">
  <strong>Alerta sonora disponible.</strong>
  <button id="playAlert" style="margin-left:12px;padding:8px 12px;font-weight:bold">Reproducir alerta</button>
</div>
<script>
const button = document.getElementById('playAlert');
button.addEventListener('click', async () => {
  const ctx = new (window.AudioContext || window.webkitAudioContext)();
  for (let i=0; i<3; i++) {
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = 'sine';
    osc.frequency.value = 880;
    osc.connect(gain);
    gain.connect(ctx.destination);
    gain.gain.setValueAtTime(0.0001, ctx.currentTime + i*0.35);
    gain.gain.exponentialRampToValueAtTime(0.25, ctx.currentTime + i*0.35 + 0.02);
    gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + i*0.35 + 0.22);
    osc.start(ctx.currentTime + i*0.35);
    osc.stop(ctx.currentTime + i*0.35 + 0.24);
  }
});
</script>
""", height=74)
if enable_browser_notifications and critical_alert_active:
    safe_title = json.dumps(alert_title)
    safe_msg = json.dumps(alert_message)
    components.html(f"""
<div style="padding:10px;border:2px solid #92400e;border-radius:10px;background:#fffbeb;color:#111827;font-family:Arial">
  <strong>Notificación local:</strong>
  <button id="notifyBtn" style="margin-left:12px;padding:8px 12px;font-weight:bold">Activar / enviar notificación</button>
</div>
<script>
document.getElementById('notifyBtn').addEventListener('click', async () => {{
  if (!('Notification' in window)) {{
    alert('Este navegador no permite notificaciones.');
    return;
  }}
  let perm = Notification.permission;
  if (perm !== 'granted') {{
    perm = await Notification.requestPermission();
  }}
  if (perm === 'granted') {{
    new Notification({safe_title}, {{ body: {safe_msg}, requireInteraction: true }});
  }} else {{
    alert('Permiso de notificaciones no concedido.');
  }}
}});
</script>
""", height=74)


c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
c1.markdown(f'<div class="card"><h3>Municipios visibles</h3><div class="big-number">{len(pred)}</div><div class="note">incluye filtros actuales</div></div>', unsafe_allow_html=True)
c2.markdown(f'<div class="card"><h3>Lluvia máxima 24h</h3><div class="big-number">{max_precip:.2f} in</div><div class="note">estimado corregido</div></div>', unsafe_allow_html=True)
c3.markdown(f'<div class="card"><h3>Temperatura máxima</h3><div class="big-number">{max_temp:.1f} °F</div><div class="note">por municipio</div></div>', unsafe_allow_html=True)
c4.markdown(f'<div class="card"><h3>Sensación máxima</h3><div class="big-number">{max_feels:.1f} °F</div><div class="note">calor aparente</div></div>', unsafe_allow_html=True)
c5.markdown(f'<div class="card"><h3>Viento máximo</h3><div class="big-number">{max_wind:.1f}</div><div class="note">mph estimado/observado</div></div>', unsafe_allow_html=True)
c6.markdown(f'<div class="card"><h3>Riesgo máximo</h3><div class="big-number">{max_risk:.0f}/100</div><div class="note">índice operacional</div></div>', unsafe_allow_html=True)
c7.markdown(f'<div class="card"><h3>Alertas/señales</h3><div class="big-number">{alert_count}</div><div class="note">clima, sismo o tsunami</div></div>', unsafe_allow_html=True)

st.subheader("Pueblos prioritarios")
if focus_df.empty:
    st.info("No hay datos de Juana Díaz, Ponce, San Juan o San Germán en los filtros actuales.")
else:
    cols = st.columns(4)
    for i, (_, row) in enumerate(focus_df.iterrows()):
        cols[i % 4].markdown(
            f"""
<div class="focus-card">
<h3>{focus_display_name(row.get('municipality_display') or row.get('municipality'))}</h3>
<p><strong>Temperatura:</strong> {float(row.get('temperature_f', 0)):.1f} °F</p>
<p><strong>Sensación:</strong> {float(row.get('feels_like_f', 0)):.1f} °F</p>
<p><strong>Lluvia:</strong> {float(row.get('corrected_precip_24h_in', 0)):.2f} pulgadas / 24h</p>
<p><strong>Viento:</strong> {float(row.get('wind_speed_mph', 0)):.1f} mph desde {row.get('wind_direction_text', 'N/D')}</p>
<p><strong>Riesgo:</strong> {float(row.get('operational_risk_score', 0)):.0f}/100</p>
<p><strong>Acción:</strong> {row.get('action_explained', 'Monitoreo')}</p>
</div>
""",
            unsafe_allow_html=True,
        )

tabs = st.tabs(["Alertas activas", "Alert Display", "Vista rápida", "Temperatura", "Mapa animado", "MRMS Fix", "MRMS Real", "Radar respaldo", "Huracanes Atlántico", "Cono huracanes", "Pueblos prioritarios", "Terremotos y tsunami", "Terremotos mundo", "Sistema/MRMS", "Panel horario", "Mejoras futuras", "Datos accesibles/WAVE", "Vida/Seguridad", "Servicios/Android", "Android App"])



with tabs[0]:
    st.header("Alertas activas y notificaciones")
    st.write("Las alertas, sonido y notificaciones locales están configuradas como activas por defecto. El navegador pedirá permiso para mostrar notificaciones.")
    if notification_state:
        n1, n2, n3, n4 = st.columns(4)
        n1.metric("Alertas", notification_state.get("alert_count", 0))
        n2.metric("Críticas/altas", notification_state.get("critical_count", 0))
        n3.metric("Sonido", "Activo" if notification_state.get("sound_default_active", True) else "Inactivo")
        n4.metric("Notificaciones", "Activas")
        st.markdown(f"<div class='alert-watch'><strong>{notification_state.get('notification_title','PR-WX')}</strong><br>{notification_state.get('notification_body','Revise el panel.')}</div>", unsafe_allow_html=True)
    else:
        st.info("No hay estado de notificaciones v2.0 todavía. Ejecute la actualización.")
    if not active_alerts.empty:
        st.dataframe(active_alerts[[c for c in ["alert_type","severity","source","headline","area","recommended_action","sticky_until_cleared","screen_reader_label"] if c in active_alerts.columns]].rename(columns={"alert_type":"Tipo","severity":"Severidad","source":"Fuente","headline":"Mensaje","area":"Área","recommended_action":"Acción","sticky_until_cleared":"Persistente","screen_reader_label":"Lectura clara"}), use_container_width=True, hide_index=True)
        st.download_button("Descargar alertas activas CSV", active_alerts.to_csv(index=False).encode("utf-8"), "prwx_v17_alertas_activas.csv", "text/csv")
    else:
        st.info("No hay alertas activas consolidadas todavía.")
    if hardening_report:
        st.subheader("Verificación de endurecimiento")
        st.dataframe(pd.DataFrame(hardening_report.get("checks", [])), use_container_width=True, hide_index=True)

with tabs[1]:
    st.header("Alert Display")
    st.write("Pantalla simplificada para lectura rápida en un centro de mando, laboratorio, salón o pantalla proyectada. Incluye sonido opcional y notificaciones locales cuando el usuario las active.")
    top5 = ranked.head(5).copy()
    semaforo = []
    for _, row in top5.iterrows():
        risk = float(row.get("operational_risk_score", 0) or 0)
        cls = "em-green"
        estado = "Bajo"
        if risk >= 70:
            cls = "em-red"; estado = "Alto"
        elif risk >= 45:
            cls = "em-amber"; estado = "Moderado"
        elif risk >= 25:
            cls = "em-blue"; estado = "Vigilancia"
        semaforo.append(f"<div class='em-box {cls}'><h3>{focus_display_name(row.get('municipality_display') or row.get('municipality'))}</h3><p><strong>Estado:</strong> {estado}</p><p><strong>Temp:</strong> {float(row.get('temperature_f',0)):.1f} °F | <strong>Sensación:</strong> {float(row.get('feels_like_f',0)):.1f} °F</p><p><strong>Lluvia:</strong> {float(row.get('corrected_precip_24h_in',0)):.2f} in/24h</p><p><strong>Viento:</strong> {float(row.get('wind_speed_mph',0)):.1f} mph</p><p><strong>Acción:</strong> {row.get('action_explained', 'Monitoreo')}</p></div>")
    st.markdown("<div class='emergency-grid'>" + "".join(semaforo) + "</div>", unsafe_allow_html=True)
    st.subheader("Qué hacer ahora")
    quick_actions = top5[[c for c in ["municipality_display", "impact_level", "action_explained", "weather_plain_text"] if c in top5.columns]].copy()
    quick_actions = quick_actions.rename(columns={"municipality_display":"Municipio","impact_level":"Impacto","action_explained":"Acción sugerida","weather_plain_text":"Lectura clara"})
    st.dataframe(quick_actions, use_container_width=True, hide_index=True)

with tabs[2]:
    st.header("Vista rápida")
    st.write("Esta tabla es la lectura principal. El mapa es apoyo visual; no es la única forma de entender los datos.")
    st.dataframe(simple_weather_table(ranked.head(20)), use_container_width=True, hide_index=True)
    st.download_button("Descargar vista rápida CSV", simple_weather_table(ranked).to_csv(index=False).encode("utf-8"), "prwx_v12_vista_rapida.csv", "text/csv")

with tabs[3]:
    st.header("Temperatura y sensación térmica por pueblo")
    st.write("Esta vista muestra la temperatura real o estimada, la sensación térmica y el nivel de riesgo por calor. Los pueblos prioritarios aparecen primero.")
    temp_table = build_temperature_table(pred)
    st.dataframe(temp_table.rename(columns={
        "municipality_display":"Municipio", "region":"Región", "temperature_f":"Temperatura °F", "feels_like_f":"Sensación °F", "relative_humidity":"Humedad %", "heat_risk_level":"Riesgo de calor", "heat_action":"Acción sugerida", "temperature_plain_text":"Lectura clara"
    })[[c for c in ["Municipio", "Región", "Temperatura °F", "Sensación °F", "Humedad %", "Riesgo de calor", "Acción sugerida", "Lectura clara"] if c in temp_table.rename(columns={"municipality_display":"Municipio", "region":"Región", "temperature_f":"Temperatura °F", "feels_like_f":"Sensación °F", "relative_humidity":"Humedad %", "heat_risk_level":"Riesgo de calor", "heat_action":"Acción sugerida", "temperature_plain_text":"Lectura clara"}).columns]], use_container_width=True, hide_index=True)
    st.download_button("Descargar temperatura CSV", temp_table.to_csv(index=False).encode("utf-8"), "prwx_v12_temperatura.csv", "text/csv")

with tabs[4]:
    st.header("Mapa animado de lluvia, viento y temperatura")
    st.write("El tamaño muestra intensidad aproximada de lluvia, el color muestra velocidad del viento y la flecha indica dirección. Active 'Reducir animación' para una alternativa estática.")
    if anim.empty:
        st.info("No hay datos de animación todavía. Ejecute la actualización v1.2.")
    else:
        st.plotly_chart(make_animated_rain_wind_map(anim, reduce_motion), use_container_width=True)
        st.caption("La animación es una visualización de apoyo generada a partir de la predicción disponible; no sustituye radar oficial ni avisos oficiales.")
        st.subheader("Alternativa textual del mapa")
        current = anim[anim["forecast_minute"] == anim["forecast_minute"].min()].copy()
        st.dataframe(current[[c for c in ["municipality_display", "rain_frame_in_hr", "wind_speed_mph", "wind_direction_text", "temperature_frame_f", "feels_like_f", "operational_risk_score", "screen_reader_label"] if c in current.columns]].rename(columns={
            "municipality_display":"Municipio", "rain_frame_in_hr":"Lluvia in/h", "wind_speed_mph":"Viento mph", "temperature_frame_f":"Temperatura °F", "feels_like_f":"Sensación °F", "wind_direction_text":"Dirección", "temperature_frame_f":"Temperatura °F", "feels_like_f":"Sensación °F", "operational_risk_score":"Riesgo", "screen_reader_label":"Lectura clara"
        }).head(25), use_container_width=True, hide_index=True)





with tabs[5]:
    st.header("MRMS Fix: visor ArcGIS en navegador")
    st.write("Esta vista corrige el problema de MRMS cargando el ImageServer directamente en el navegador con ArcGIS JS. Si no carga, use el radar de respaldo y los enlaces diagnósticos.")
    components.html(mrms_arcgis_component_html(mrms_real_layer_choice), height=735)
    if mrms_fixed_summary:
        st.subheader("Diagnóstico MRMS")
        st.json(mrms_fixed_summary.get("service_test", {}))
        st.write("Posibles causas si no se ve lluvia:", mrms_fixed_summary.get("why_previous_may_fail", []))
    if not mrms_fixed_urls.empty:
        st.subheader("URLs alternas MRMS")
        st.dataframe(mrms_fixed_urls.rename(columns={"layer":"Capa","raster_function":"Función","arcgis_export_image_url":"Imagen exportImage","arcgis_export_json_url":"JSON exportImage","screen_reader_label":"Lectura clara"}), use_container_width=True, hide_index=True)
        st.download_button("Descargar diagnóstico MRMS v2.0", mrms_fixed_urls.to_csv(index=False).encode("utf-8"), "prwx_v18_mrms_fix_urls.csv", "text/csv")

with tabs[6]:
    st.header("MRMS real: radar QPE para Puerto Rico")
    st.write("Esta vista usa enlaces reales `exportImage` del servicio NOAA/NWS MRMS QPE ImageServer. Si la red no carga la imagen, use el radar de respaldo.")
    if mrms_real_urls.empty:
        st.info("No hay URLs MRMS reales todavía. Ejecute la actualización v2.0.1.")
    else:
        selected = mrms_real_urls[mrms_real_urls["layer"].astype(str) == mrms_real_layer_choice]
        if selected.empty:
            selected = mrms_real_urls.head(1)
        image_url = str(selected.iloc[0].get("image_url", ""))
        st.image(image_url, caption=f"MRMS real {mrms_real_layer_choice} - Puerto Rico", use_container_width=True)
        st.caption("Fuente: NOAA/NWS MRMS QPE ImageServer. Esta imagen depende de conexión externa.")
        if mrms_real_summary:
            st.json(mrms_real_summary.get("service_status", {}))
        st.subheader("Tabla accesible de capas MRMS")
        st.dataframe(mrms_real_urls.rename(columns={"layer":"Capa","raster_function":"Función raster","image_url":"URL imagen","source":"Fuente","screen_reader_label":"Lectura clara"}), use_container_width=True, hide_index=True)
        st.download_button("Descargar URLs MRMS reales CSV", mrms_real_urls.to_csv(index=False).encode("utf-8"), "prwx_v16_mrms_real_urls.csv", "text/csv")

with tabs[7]:
    st.header("Radar de respaldo: 1h, 3h, 6h y 24h")
    st.write("Visualización tipo radar basada en estimados municipales. La próxima etapa debe integrar raster MRMS real.")
    if radar_layers.empty:
        st.info("No hay capas de radar v2.0 disponibles. Ejecute la actualización v2.0.1.")
    else:
        st.plotly_chart(make_radar_layer_map(radar_layers, radar_layer_choice), use_container_width=True)
        st.subheader("Alternativa textual de radar")
        rt = radar_layers[radar_layers["layer"].astype(str) == radar_layer_choice].copy()
        st.dataframe(rt[[c for c in ["municipality_display","layer","rain_in","rain_rate_in_hr","reflectivity_est_dbz","risk_score","screen_reader_label"] if c in rt.columns]].rename(columns={"municipality_display":"Municipio","layer":"Capa","rain_in":"Lluvia in","rain_rate_in_hr":"Intensidad in/h","reflectivity_est_dbz":"dBZ estimado","risk_score":"Riesgo","screen_reader_label":"Lectura clara"}).head(50), use_container_width=True, hide_index=True)
        st.download_button("Descargar radar por capas CSV", radar_layers.to_csv(index=False).encode("utf-8"), "prwx_v14_radar_capas.csv", "text/csv")

with tabs[8]:
    st.header("Mapa animado de huracanes en el Atlántico")
    st.write("Esta vista muestra trayectorias animadas de sistemas tropicales del Atlántico como apoyo visual. Valide siempre con el National Hurricane Center.")
    if hurricane_tracks.empty:
        st.info("No hay datos de huracanes disponibles todavía. Ejecute la actualización v2.0.1.")
    else:
        st.plotly_chart(make_hurricane_map(hurricane_tracks, reduce_motion), use_container_width=True)
        if hurricane_summary:
            st.markdown(f"<div class='callout'><strong>Resumen de huracanes:</strong><br>{hurricane_summary.get('headline','Resumen no disponible.')}</div>", unsafe_allow_html=True)
        latest_h = hurricane_tracks.sort_values(['storm_name','forecast_hour']).groupby('storm_name', as_index=False).first()
        st.dataframe(latest_h[[c for c in ['storm_name','storm_type','status','max_wind_mph','lat','lon','screen_reader_label'] if c in latest_h.columns]].rename(columns={'storm_name':'Sistema','storm_type':'Tipo','status':'Estado','max_wind_mph':'Viento mph','lat':'Latitud','lon':'Longitud','screen_reader_label':'Lectura clara'}), use_container_width=True, hide_index=True)
        st.download_button("Descargar trayectorias de huracanes CSV", hurricane_tracks.to_csv(index=False).encode('utf-8'), "prwx_v13_huracanes_atlantico.csv", "text/csv")


with tabs[9]:
    st.header("Cono de incertidumbre de huracanes")
    st.write("Visualización educativa del cono de incertidumbre. Debe validarse siempre con el National Hurricane Center.")
    if hurricane_tracks.empty:
        st.info("No hay trayectorias para generar cono.")
    else:
        st.plotly_chart(make_hurricane_cone_map(hurricane_tracks, hurricane_cone, reduce_motion), use_container_width=True)
        if not hurricane_pr_risk.empty:
            st.subheader("Riesgo de huracán para Puerto Rico")
            st.dataframe(hurricane_pr_risk[[c for c in ["storm_name","forecast_label","distance_to_pr_km","max_wind_mph","pr_watch_level","screen_reader_label"] if c in hurricane_pr_risk.columns]].rename(columns={"storm_name":"Sistema","forecast_label":"Tiempo","distance_to_pr_km":"Distancia a PR km","max_wind_mph":"Viento mph","pr_watch_level":"Nivel PR","screen_reader_label":"Lectura clara"}).head(100), use_container_width=True, hide_index=True)
        if not hurricane_cone.empty:
            st.download_button("Descargar cono huracanes CSV", hurricane_cone.to_csv(index=False).encode("utf-8"), "prwx_v14_cono_huracanes.csv", "text/csv")

with tabs[10]:
    st.header("Seguimiento especial")
    st.write("Comparación directa de Juana Díaz, Ponce, San Juan y San Germán.")
    if not focus_df.empty:
        st.plotly_chart(make_focus_bar(pred), use_container_width=True)
        st.dataframe(simple_weather_table(focus_df), use_container_width=True, hide_index=True)
        st.download_button("Descargar pueblos prioritarios CSV", focus_df.to_csv(index=False).encode("utf-8"), "prwx_v12_pueblos_prioritarios.csv", "text/csv")
    else:
        st.info("No hay datos para los pueblos prioritarios con los filtros actuales.")

with tabs[11]:
    st.header("Terremotos, tsunami y Android Sensor Bridge")
    st.markdown('<div class="alert-watch"><strong>Nota clara:</strong> este sistema no predice terremotos. Solo puede apoyar una alerta temprana después de que un evento comienza y debe validarse contra fuentes oficiales.</div>', unsafe_allow_html=True)
    a1, a2, a3, a4 = st.columns(4)
    a1.metric("Alertas/señales", alert_count)
    a2.metric("Eventos sísmicos", len(earthquakes))
    a3.metric("Señales Android", cluster.get("trigger_count", 0))
    a4.metric("Cluster Android", cluster.get("cluster_status", "sin señales"))
    st.write(cluster.get("recommendation", ""))
    if not safety.empty:
        st.subheader("Panel de seguridad")
        st.dataframe(safety[[c for c in ["hazard_type", "severity", "source", "headline", "municipality", "recommended_action", "is_official", "confidence_note"] if c in safety.columns]].rename(columns={
            "hazard_type":"Riesgo", "severity":"Severidad", "source":"Fuente", "headline":"Mensaje", "municipality":"Área", "recommended_action":"Acción", "is_official":"Oficial", "confidence_note":"Nota"
        }), use_container_width=True, hide_index=True)
    else:
        st.info("No hay alertas o señales relevantes generadas en este momento.")
    if not eew.empty and show_raw:
        st.subheader("Matriz de alerta temprana sísmica experimental")
        st.dataframe(eew.head(100), use_container_width=True, hide_index=True)
    st.subheader("Resumen ampliado")
    st.write(f"Eventos sísmicos regionales visibles: {len(earthquakes)}. Candidatos con bandera de tsunami a nivel mundial: {len(global_tsunami)}.")
    if not earthquakes.empty:
        st.dataframe(earthquakes[[c for c in ["event_time_utc","place","magnitude","depth_km","tsunami","source"] if c in earthquakes.columns]].rename(columns={"event_time_utc":"Hora UTC","place":"Lugar","magnitude":"Magnitud","depth_km":"Profundidad km","tsunami":"Tsunami","source":"Fuente"}), use_container_width=True, hide_index=True)



with tabs[12]:
    st.header("Mapa mundial de terremotos o movimientos de tierra")
    st.write("Mapa mundial con los eventos sísmicos más recientes del feed disponible. Los eventos con bandera de tsunami aparecen diferenciados.")
    if global_eq.empty:
        st.info("No hay datos globales disponibles todavía. Ejecute la actualización v2.0.1.")
    else:
        filtered_global = global_eq.copy()
        filtered_global["magnitude"] = pd.to_numeric(filtered_global.get("magnitude", 0), errors="coerce").fillna(0)
        filtered_global = filtered_global[filtered_global["magnitude"] >= float(min_global_magnitude)]
        if show_tsunami_only:
            filtered_global = filtered_global[pd.to_numeric(filtered_global.get("tsunami", 0), errors="coerce").fillna(0) > 0]
        filtered_global = filtered_global.head(int(global_event_limit))
        st.plotly_chart(make_global_earthquake_map(filtered_global), use_container_width=True)
        if global_seismic_summary:
            st.markdown(f"<div class='callout'><strong>Resumen sísmico mundial:</strong><br>{global_seismic_summary.get('headline','Resumen no disponible.')}</div>", unsafe_allow_html=True)
        g1, g2, g3 = st.columns(3)
        g1.metric("Eventos visibles", len(filtered_global))
        g2.metric("Bandera de tsunami", len(global_tsunami))
        maxmag = float(pd.to_numeric(filtered_global.get('magnitude', 0), errors='coerce').fillna(0).max()) if not filtered_global.empty else 0.0
        g3.metric("Magnitud máxima", f"{maxmag:.1f}")
        st.subheader("Tabla mundial de eventos")
        st.dataframe(filtered_global[[c for c in ['event_time_utc','place','magnitude','depth_km','tsunami','felt_reports','screen_reader_label'] if c in filtered_global.columns]].rename(columns={'event_time_utc':'Hora UTC','place':'Lugar','magnitude':'Magnitud','depth_km':'Profundidad km','tsunami':'Tsunami','felt_reports':'Reportes','screen_reader_label':'Lectura clara'}).head(200), use_container_width=True, hide_index=True)
        if not global_tsunami.empty:
            st.subheader("Eventos con bandera de tsunami")
            st.dataframe(global_tsunami[[c for c in ['event_time_utc','place','magnitude','depth_km','source'] if c in global_tsunami.columns]].rename(columns={'event_time_utc':'Hora UTC','place':'Lugar','magnitude':'Magnitud','depth_km':'Profundidad km','source':'Fuente'}), use_container_width=True, hide_index=True)
        st.download_button("Descargar terremotos mundiales CSV", filtered_global.to_csv(index=False).encode('utf-8'), "prwx_v14_terremotos_mundo.csv", "text/csv")


with tabs[13]:
    st.header("Sistema/MRMS: salud operacional y radar real")
    st.write("Esta vista ayuda a confirmar si el sistema está saludable y preparado para integrar MRMS QPE real.")
    if system_health:
        h1, h2, h3 = st.columns(3)
        h1.metric("Estado", system_health.get("overall_status", "N/D"))
        h2.metric("Archivos listos", system_health.get("files_ready", 0))
        h3.metric("Archivos revisados", system_health.get("files_checked", 0))
        st.subheader("Salud de archivos")
        st.dataframe(pd.DataFrame(system_health.get("file_status", [])), use_container_width=True, hide_index=True)
        st.subheader("Estado MRMS QPE")
        st.json(system_health.get("mrms_qpe_service", {}))
    else:
        st.info("Todavía no hay reporte de salud v2.0. Ejecute la actualización v2.0.1.")
    st.subheader("Manifest MRMS QPE")
    if not mrms_manifest.empty:
        st.dataframe(mrms_manifest.rename(columns={"layer":"Capa","service_url":"Servicio","description":"Descripción","implementation_status":"Estado","screen_reader_label":"Lectura clara"}), use_container_width=True, hide_index=True)
        st.download_button("Descargar manifest MRMS CSV", mrms_manifest.to_csv(index=False).encode("utf-8"), "prwx_v15_mrms_manifest.csv", "text/csv")
    else:
        st.info("No hay manifest MRMS disponible.")

with tabs[14]:
    st.header("Panel horario: ahora, próximas 6 horas y próximas 24 horas")
    st.write("Este panel convierte los datos en acciones por periodo para que la lectura sea más fácil.")
    period_table = period_action_table(ranked.head(30))
    st.dataframe(period_table, use_container_width=True, hide_index=True)
    st.download_button("Descargar panel horario CSV", period_table.to_csv(index=False).encode("utf-8"), "prwx_v12_panel_horario.csv", "text/csv")

with tabs[15]:
    st.header("Mejoras futuras para hacerlo más avanzado")
    st.write("Estas mejoras se pueden añadir en la próxima versión para que el sistema sea más útil, claro e innovador.")
    improvements = summary.get("recommendations_to_improve", []) if summary else []
    if not improvements:
        improvements = ["Radar real por capas MRMS", "Notificaciones web push", "Modo kiosco para pantalla grande", "Sensores IoT locales", "App Android propia para acelerómetro", "Integración directa con Red Sísmica y NOAA Tsunami", "Trayectoria oficial de ciclones desde NHC", "Capa mundial sísmica con filtros por magnitud y hora"]
    for item in improvements:
        st.write(f"✓ {item}")

with tabs[16]:
    st.header("Datos accesibles y validación WAVE")
    st.write("La página usa texto visible, alto contraste, controles etiquetados, tablas descargables y alternativa textual para el mapa animado.")
    notes = summary.get("wave_accessibility_notes", []) if summary else []
    for note in notes:
        st.write(f"✓ {note}")
    st.subheader("Tabla completa")
    st.dataframe(simple_weather_table(pred.sort_values("operational_risk_score", ascending=False)), use_container_width=True, hide_index=True)
    b1, b2, b3 = st.columns(3)
    b1.download_button("Predicciones v1.2 CSV", pred.to_csv(index=False).encode("utf-8"), "live_predictions_v12_view.csv", "text/csv")
    if not anim.empty:
        b2.download_button("Animación lluvia/viento CSV", anim.to_csv(index=False).encode("utf-8"), "weather_animation_v10.csv", "text/csv")
    if not safety.empty:
        b3.download_button("Alertas seguridad CSV", safety.to_csv(index=False).encode("utf-8"), "safety_alerts_v9.csv", "text/csv")
    if show_raw:
        st.subheader("Metadata")
        st.json(meta)


with tabs[17]:
    st.header("Vida/Seguridad: acciones que pueden salvar vidas")
    st.write("Convierte la información del tablero en acciones claras para reducir riesgo. Valide siempre con fuentes oficiales y manejo de emergencias.")
    if life_safety_summary:
        st.markdown(f"<div class='callout'><strong>Life Safety Board:</strong><br>{life_safety_summary.get('headline','Resumen no disponible')}</div>", unsafe_allow_html=True)
    if not municipal_life_safety.empty:
        st.subheader("Pueblos prioritarios")
        st.dataframe(municipal_life_safety.rename(columns={"municipality":"Municipio","status":"Estado","operational_risk_score":"Riesgo","feels_like_f":"Sensación °F","rain_24h_in":"Lluvia 24h","active_alerts_for_area":"Alertas","priority_action":"Acción prioritaria","screen_reader_label":"Lectura clara"}), use_container_width=True, hide_index=True)
    if not life_safety_actions.empty:
        st.subheader("Acciones por riesgo")
        st.dataframe(life_safety_actions.rename(columns={"hazard":"Riesgo","priority":"Prioridad","recommended_action":"Acción recomendada","validation_source":"Fuente de validación","life_safety_reason":"Por qué ayuda","screen_reader_label":"Lectura clara"}), use_container_width=True, hide_index=True)
        st.download_button("Descargar Life Safety CSV", life_safety_actions.to_csv(index=False).encode("utf-8"), "prwx_v19_life_safety.csv", "text/csv")
    if life_safety_summary:
        st.subheader("Próximas integraciones que pueden salvar vidas")
        for item in life_safety_summary.get("recommended_next_integrations", []):
            st.write(f"✓ {item}")

with tabs[18]:
    st.header("Servicios/Android: verificación operacional")
    st.write("Verifica servicios externos, archivos locales y el Android Sensor Bridge usado para alertas tempranas sísmicas experimentales.")
    if verification_summary:
        v1, v2, v3, v4 = st.columns(4)
        v1.metric("Estado", verification_summary.get("overall_status", "N/D"))
        v2.metric("Servicios externos OK", verification_summary.get("external_services_ok", 0))
        v3.metric("Artefactos locales OK", verification_summary.get("local_artifacts_ok", 0))
        v4.metric("Android Bridge", verification_summary.get("android_bridge_status", "N/D"))
        st.info(verification_summary.get("must_not_overclaim", "Android de Google no es API pública integrada."))
    if not service_status.empty:
        st.subheader("Estado de servicios y artefactos")
        st.dataframe(service_status.rename(columns={"service":"Servicio","url":"URL","ok":"OK","status_code":"Código","content_type":"Tipo","message":"Mensaje","file":"Archivo","size_bytes":"Tamaño"}), use_container_width=True, hide_index=True)
        st.download_button("Descargar verificación servicios CSV", service_status.to_csv(index=False).encode("utf-8"), "prwx_v19_service_status.csv", "text/csv")
    if android_status:
        st.subheader("Android Earthquake Bridge")
        st.json(android_status)
        st.warning("Esto verifica el puente local PR-WX. No accede directamente a la red privada de Google Android Earthquake Alerts.")
    else:
        st.info("No hay verificación Android v2.0 todavía. Ejecute la actualización.")


with tabs[19]:
    st.header("Android App: Sensor Bridge real")
    st.write("Estado del proyecto Android incluido para enviar señales experimentales del acelerómetro al dashboard.")
    if android_app_status:
        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Estado", android_app_status.get("overall_status", "N/D"))
        s2.metric("Privacidad", "OK" if android_app_status.get("privacy_ok") else "Revisar")
        s3.metric("Endpoint", "OK" if android_app_status.get("endpoint_ok") else "Revisar")
        s4.metric("Acelerómetro", "OK" if android_app_status.get("accelerometer_ok") else "Revisar")
        st.json(android_app_status)
    else:
        st.info("Ejecute la actualización v2.0 para generar android_app_bridge_status_v20.json.")
    st.subheader("Cómo probar")
    st.code("docker compose up prwx-api\n# Abrir android_sensor_app en Android Studio\n# Emulador: usar http://10.0.2.2:8000\n# Teléfono real: usar http://IP-DE-TU-PC:8000", language="powershell")
    st.warning("La app no predice terremotos y no debe emitir alertas públicas. Solo envía señales experimentales que deben validarse contra fuentes oficiales.")

