(() => {
  const TOWNS = [
    { key:'juana_diaz', name:'Juana Díaz', lat:18.0533, lon:-66.5060, priority:true },
    { key:'ponce', name:'Ponce', lat:18.0111, lon:-66.6141, priority:true },
    { key:'san_juan', name:'San Juan', lat:18.4655, lon:-66.1057, priority:true },
    { key:'san_german', name:'San Germán', lat:18.0816, lon:-67.0449, priority:true },
    { key:'mayaguez', name:'Mayagüez', lat:18.2011, lon:-67.1396 },
    { key:'arecibo', name:'Arecibo', lat:18.4724, lon:-66.7157 },
    { key:'caguas', name:'Caguas', lat:18.2341, lon:-66.0485 },
    { key:'fajardo', name:'Fajardo', lat:18.3258, lon:-65.6524 },
    { key:'humacao', name:'Humacao', lat:18.1497, lon:-65.8274 },
    { key:'guayama', name:'Guayama', lat:17.9841, lon:-66.1138 },
    { key:'aguadilla', name:'Aguadilla', lat:18.4274, lon:-67.1541 },
    { key:'bayamon', name:'Bayamón', lat:18.3986, lon:-66.1557 }
  ];
  const FEATURED = ['juana_diaz','ponce','san_juan','san_german'];
  const PR_BOUNDS = [[17.75,-67.45],[18.6,-65.2]];
  const ALERTS_URL = 'https://api.weather.gov/alerts/active?area=PR';
  const WMS = 'https://nowcoast.noaa.gov/wms/com.esri.wms.Esrimap/obs';
  const RADAR = 'RAS_RIDGE_NEXRAD';
  const GOES_VISIBLE = 'RAS_GOES';
  const GOES_IR = 'RAS_GOES_I4';
  const state = { map:null, layers:{}, vectorLayers:[], results:[] };
  const $ = (id) => document.getElementById(id);
  const safe = (v) => (v ?? '').toString();
  const fmt = (d=new Date()) => d.toLocaleString('es-PR', { dateStyle:'short', timeStyle:'short' });
  const mps2mph = (m) => m == null ? null : m * 2.236936;
  function degToCompass(num){
    if(num == null || Number.isNaN(Number(num))) return 'Variable';
    const dirs = ['N','NNE','NE','ENE','E','ESE','SE','SSE','S','SSW','SW','WSW','W','WNW','NW','NNW'];
    return dirs[Math.round(num/22.5)%16];
  }
  function bearingEmoji(num){
    if(num == null || Number.isNaN(Number(num))) return '•';
    const e = ['↑','↗','→','↘','↓','↙','←','↖'];
    return e[Math.round(num/45)%8];
  }
  function rankSeverity(s){ return ({Extreme:4,Severe:3,Moderate:2,Minor:1,Unknown:0}[s] ?? 0); }
  function riskLabel(v){ return v>=75?'Muy alto':v>=55?'Alto':v>=35?'Moderado':'Bajo'; }
  function riskClass(v){ return v>=65?'hot':''; }
  function setText(id, value){ const el=$(id); if(el) el.textContent=value; }
  async function json(url){
    const res = await fetch(url, { headers:{Accept:'application/geo+json, application/ld+json, application/json'} });
    if(!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  }
  function destination(lat, lon, bearing, km){
    const R=6371, br=bearing*Math.PI/180, lat1=lat*Math.PI/180, lon1=lon*Math.PI/180, d=km/R;
    const lat2=Math.asin(Math.sin(lat1)*Math.cos(d)+Math.cos(lat1)*Math.sin(d)*Math.cos(br));
    const lon2=lon1+Math.atan2(Math.sin(br)*Math.sin(d)*Math.cos(lat1),Math.cos(d)-Math.sin(lat1)*Math.sin(lat2));
    return [lat2*180/Math.PI, lon2*180/Math.PI];
  }
  async function townForecast(town){
    const pt = await json(`https://api.weather.gov/points/${town.lat},${town.lon}`);
    const hourlyUrl = pt?.properties?.forecastHourly;
    const stationsUrl = pt?.properties?.observationStations;
    let hourly=[]; let obs=null;
    if(hourlyUrl){ const h=await json(hourlyUrl); hourly=h?.properties?.periods?.slice(0,6)||[]; }
    if(stationsUrl){
      try{
        const st = await json(stationsUrl);
        const id = st?.features?.[0]?.properties?.stationIdentifier;
        if(id){ const o=await json(`https://api.weather.gov/stations/${id}/observations/latest`); obs=o?.properties||null; }
      }catch(e){ obs=null; }
    }
    return {town, hourly, obs};
  }
  function summary(item){
    const first=item.hourly?.[0]||{}, second=item.hourly?.[1]||{}, third=item.hourly?.[2]||{};
    const p0=first.probabilityOfPrecipitation?.value??0, p1=second.probabilityOfPrecipitation?.value??p0, p2=third.probabilityOfPrecipitation?.value??p1;
    const temp=first.temperature!=null?`${first.temperature}°${first.temperatureUnit||'F'}`:'—';
    const text=item.obs?.textDescription||first.shortForecast||'Sin dato';
    const windDeg=item.obs?.windDirection?.value;
    const windMph=mps2mph(item.obs?.windSpeed?.value);
    const wind=windMph!=null?`${Math.round(windMph)} mph ${degToCompass(windDeg)}`:(first.windSpeed||'—');
    let trend='estable'; if(p1>p0+10) trend='en aumento'; else if(p1<p0-10) trend='disminuyendo';
    const score=Math.min(100, Math.round((p1*0.62)+(p2*0.23)+(windMph||8)*0.5));
    return {p0,p1,p2,temp,text,wind,windDeg,trend,score};
  }
  function townCard(item){
    const s=summary(item);
    return `<article class="townCard"><h4>${item.town.name} ${item.town.priority?'<span class="badge">Prioritario</span>':''}</h4><div class="townMeta"><div><strong>Temp.:</strong> ${s.temp}</div><div><strong>Lluvia ahora:</strong> ${s.p0}%</div><div><strong>Próx. hora:</strong> ${s.p1}%</div><div><strong>3 horas:</strong> ${s.p2}%</div><div><strong>Viento:</strong> ${safe(s.wind)}</div><div><strong>Riesgo:</strong> ${riskLabel(s.score)}</div><div><strong>Condición:</strong> ${safe(s.text)}</div><div><strong>Tendencia:</strong> ${s.trend}</div></div></article>`;
  }
  function analysisItem(item){
    const s=summary(item);
    return `<li><strong>${item.town.name}:</strong> riesgo <strong>${riskLabel(s.score)}</strong>, lluvia próxima hora <strong>${s.p1}%</strong>, movimiento probable <strong>${degToCompass(s.windDeg)}</strong> ${bearingEmoji(s.windDeg)}, tendencia <strong>${s.trend}</strong>.</li>`;
  }
  function initMap(){
    if(!window.L || !$('rainMap')) return;
    const map=L.map('rainMap',{zoomControl:true,attributionControl:true}).fitBounds(PR_BOUNDS);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:18,attribution:'&copy; OpenStreetMap contributors'}).addTo(map);
    const radar=L.tileLayer.wms(WMS,{layers:RADAR,format:'image/png',transparent:true,opacity:.78,attribution:'NOAA nowCOAST'}).addTo(map);
    const cloudsVisible=L.tileLayer.wms(WMS,{layers:GOES_VISIBLE,format:'image/png',transparent:true,opacity:.35,attribution:'NOAA GOES'}).addTo(map);
    const cloudsIR=L.tileLayer.wms(WMS,{layers:GOES_IR,format:'image/png',transparent:true,opacity:.42,attribution:'NOAA GOES'});
    const towns=L.layerGroup().addTo(map);
    TOWNS.forEach(t=>{
      L.marker([t.lat,t.lon],{icon:L.divIcon({className:'leaflet-town',html:`<div class="townDot" id="dot-${t.key}"></div>`,iconSize:[24,24],iconAnchor:[12,12]})}).bindPopup(`<strong>${t.name}</strong><br>Pueblo monitoreado`).addTo(towns);
    });
    state.map=map; state.layers={radar,cloudsVisible,cloudsIR,towns};
    function view(k){
      if(k==='rain'){radar.addTo(map);cloudsVisible.remove();cloudsIR.remove();}
      else if(k==='visible'){radar.addTo(map);cloudsVisible.addTo(map);cloudsIR.remove();}
      else if(k==='ir'){radar.addTo(map);cloudsIR.addTo(map);cloudsVisible.remove();}
      else{radar.addTo(map);cloudsVisible.addTo(map);cloudsIR.addTo(map);}
      document.querySelectorAll('[data-layer]').forEach(b=>b.classList.toggle('active',b.dataset.layer===k));
    }
    document.querySelectorAll('[data-layer]').forEach(btn=>btn.addEventListener('click',()=>view(btn.dataset.layer)));
    $('townFocus')?.addEventListener('change',e=>{ const t=TOWNS.find(x=>x.key===e.target.value); t?map.setView([t.lat,t.lon],10):map.fitBounds(PR_BOUNDS); });
    $('resetView')?.addEventListener('click',()=>map.fitBounds(PR_BOUNDS));
    $('emergencyMode')?.addEventListener('click',()=>document.body.classList.toggle('emergency'));
    $('refreshBtn')?.addEventListener('click',refreshAll);
    function refreshLayers(){radar.setParams({_t:Date.now()});cloudsVisible.setParams({_t:Date.now()});cloudsIR.setParams({_t:Date.now()});setText('mapUpdated',fmt());}
    setInterval(refreshLayers,60000); refreshLayers(); view('all');
  }
  function drawVectors(results){
    if(!state.map) return;
    state.vectorLayers.forEach(l=>state.map.removeLayer(l)); state.vectorLayers=[];
    results.forEach(item=>{
      const s=summary(item); const b=s.windDeg??90; const end=destination(item.town.lat,item.town.lon,b,11+Math.min(10,s.p1/8));
      const color=s.score>=65?'#ef4444':s.score>=45?'#f59e0b':'#0ea5e9';
      const line=L.polyline([[item.town.lat,item.town.lon],end],{color,weight:Math.max(2,Math.min(8,Math.round(s.score/16))),opacity:.82,dashArray:'8 6'}).addTo(state.map);
      const arrow=L.marker(end,{icon:L.divIcon({className:'leaflet-town',html:`<div class="windArrow" style="transform:rotate(${b}deg)">➤</div>`,iconSize:[28,28],iconAnchor:[14,14]})}).bindTooltip(`${item.town.name}: trayectoria ${degToCompass(b)} · riesgo ${riskLabel(s.score)}`).addTo(state.map);
      state.vectorLayers.push(line,arrow);
      const dot=document.getElementById(`dot-${item.town.key}`); if(dot) dot.classList.toggle('hot',s.score>=65);
    });
  }
  async function renderAlerts(){
    const box=$('alerts'); if(box) box.innerHTML='<p class="muted">Cargando alertas oficiales…</p>';
    try{
      const data=await json(ALERTS_URL);
      const alerts=(data.features||[]).map(f=>f.properties).sort((a,b)=>rankSeverity(b.severity)-rankSeverity(a.severity));
      const flood=alerts.filter(a=>/flood|inund/i.test(`${a.event} ${a.headline||''}`));
      setText('alertCount',String(alerts.length)); setText('floodCount',String(flood.length));
      if(!alerts.length){ if(box) box.innerHTML='<div class="notice">No hay alertas activas del NWS para Puerto Rico.</div>'; return; }
      if(box) box.innerHTML=alerts.slice(0,10).map(a=>`<article class="alertCard ${/flood|inund/i.test(`${a.event} ${a.headline||''}`)?'flood':''}"><h4>${safe(a.event)} · ${safe(a.severity||'Sin severidad')}</h4><p><strong>Área:</strong> ${safe(a.areaDesc||'No especificada')}</p><p><strong>Expira:</strong> ${a.expires?new Date(a.expires).toLocaleString('es-PR'):'—'}</p>${a.headline?`<p>${safe(a.headline)}</p>`:''}</article>`).join('');
    }catch(e){ if(box) box.innerHTML=`<div class="notice">No se pudieron cargar alertas. ${safe(e.message)}</div>`; setText('alertCount','—'); setText('floodCount','—'); }
  }
  async function renderTowns(){
    const box=$('towns'); if(box) box.innerHTML='<p class="muted">Cargando municipios…</p>';
    try{
      const results=await Promise.all(TOWNS.map(townForecast)); state.results=results;
      const featured=results.filter(r=>FEATURED.includes(r.town.key));
      if(box) box.innerHTML=results.map(townCard).join('');
      const analysis=$('analysis'); if(analysis) analysis.innerHTML=`<ul class="analysisList">${featured.map(analysisItem).join('')}</ul>`;
      const avg=Math.round(featured.reduce((n,r)=>n+summary(r).p1,0)/featured.length);
      const focus=[...featured].sort((a,b)=>summary(b).score-summary(a).score)[0];
      const fs=focus?summary(focus):null;
      setText('avgRain',`${avg}%`); setText('focusTown',focus?.town?.name||'—'); setText('riskScore',fs?`${fs.score}/100`:'—'); setText('townsUpdated',fmt());
      ['juana_diaz','ponce','san_juan','san_german'].forEach(k=>{ const r=results.find(x=>x.town.key===k); setText(`temp-${k}`,r?summary(r).temp:'—'); });
      const focusBox=$('focusBox'); if(focusBox && focus && fs){focusBox.innerHTML=`<div class="focusCard"><h3>Pueblo de vigilancia</h3><p><strong>${focus.town.name}</strong> presenta la señal de mayor impacto de corto plazo.</p><p><strong>Lluvia próxima hora:</strong> ${fs.p1}%</p><p><strong>Riesgo:</strong> ${riskLabel(fs.score)}</p><p><strong>Trayectoria:</strong> ${degToCompass(fs.windDeg)} ${bearingEmoji(fs.windDeg)}</p></div>`;}
      const advice=$('advice'); if(advice){advice.innerHTML=`<div class="notice"><strong>Recomendación:</strong> ${avg>=70?'Vigilancia alta por posible lluvia fuerte e inundación urbana localizada.':avg>=45?'Monitoreo preventivo por lluvia moderada a fuerte en sectores aislados.':'Vigilancia normal con seguimiento de radar.'}</div>`;}
      drawVectors(featured);
    }catch(e){ if(box) box.innerHTML=`<div class="notice">No se pudieron cargar los municipios. ${safe(e.message)}</div>`; }
  }
  async function refreshAll(){ setText('lastUpdated',fmt()); await Promise.all([renderAlerts(),renderTowns()]); }
  function boot(){
    initMap();
    document.querySelectorAll('[data-now]').forEach(el=>el.textContent=fmt());
    refreshAll(); setInterval(refreshAll,60000);
  }
  window.addEventListener('DOMContentLoaded',boot);
})();
