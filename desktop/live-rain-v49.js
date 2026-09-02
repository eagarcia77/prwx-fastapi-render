(() => {
  const VERSION = '4.9.0';
  const NOWCOAST_WMS = 'https://nowcoast.noaa.gov/wms/com.esri.wms.Esrimap/obs';
  const PR_BOUNDS = [[17.72,-67.60],[18.82,-64.92]];
  const PR_BBOX = '-67.60,17.72,-64.92,18.82';
  const TOWNS = {
    juana_diaz:[18.0533,-66.5060,'Juana Díaz'], ponce:[18.0111,-66.6141,'Ponce'], san_juan:[18.4655,-66.1057,'San Juan'], san_german:[18.0816,-67.0449,'San Germán'], mayaguez:[18.2011,-67.1396,'Mayagüez'], fajardo:[18.3258,-65.6524,'Fajardo'], vieques:[18.1263,-65.4401,'Vieques'], culebra:[18.3030,-65.3009,'Culebra'], arecibo:[18.4724,-66.7157,'Arecibo'], humacao:[18.1497,-65.8274,'Humacao'], guayama:[17.9841,-66.1138,'Guayama'], aguadilla:[18.4274,-67.1541,'Aguadilla']
  };
  const $ = id => document.getElementById(id);
  const fmt = (d=new Date()) => d.toLocaleString('es-PR',{dateStyle:'short',timeStyle:'medium'});
  function setText(id, text){ const el=$(id); if(el) el.textContent = text; }
  function wmsUrl(layer, width='1200', height='720'){
    const p = new URLSearchParams({SERVICE:'WMS',VERSION:'1.1.1',REQUEST:'GetMap',FORMAT:'image/png',TRANSPARENT:'true',SRS:'EPSG:4326',LAYERS:layer,STYLES:'',BBOX:PR_BBOX,WIDTH:width,HEIGHT:height,_t:String(Date.now())});
    return `${NOWCOAST_WMS}?${p.toString()}`;
  }
  function addLayer(map, layer, opacity, zIndex, attr){
    return L.tileLayer.wms(NOWCOAST_WMS,{layers:layer,format:'image/png',transparent:true,version:'1.1.1',opacity,zIndex,attribution:attr}).addTo(map);
  }
  function pct(v){ return `${Math.round(Number(v)*100)}%`; }
  function scoreFromHour(){
    const h = Number(new Date().toLocaleString('en-US',{timeZone:'America/Puerto_Rico',hour:'2-digit',hour12:false}));
    return h>=6 && h<18 ? 68 : 78;
  }
  async function loadImg(id, layer){
    const img=$(id); if(!img) return false;
    return new Promise(resolve=>{
      const src = wmsUrl(layer);
      img.onload=()=>resolve(true);
      img.onerror=()=>resolve(false);
      img.src=src;
    });
  }
  async function checkLayer(layer){
    try{
      const url = wmsUrl(layer,'420','260');
      const controller = new AbortController();
      const timer = setTimeout(()=>controller.abort(), 8500);
      const r = await fetch(url,{signal:controller.signal,cache:'no-store'});
      clearTimeout(timer);
      return {layer, ok:r.ok, status:r.status, type:r.headers.get('content-type')||'desconocido'};
    }catch(e){ return {layer, ok:false, status:'error', type:String(e.message||e)}; }
  }
  function renderDiagnostics(results){
    const ok = results.filter(r=>r.ok).length;
    setText('diagLayer', `${ok}/3 capas responden`);
    setText('diagSource','NOAA nowCOAST WMS');
    setText('diagVersion', VERSION);
    setText('diagRefresh','120 segundos');
    const box=$('diagnosticList');
    if(box){
      box.innerHTML = results.map(r=>`<div class="diagItem"><span>${r.layer}</span><strong>${r.ok?'OK':'Revisar'} · ${r.status}</strong></div>`).join('');
    }
    const base = scoreFromHour();
    const score = Math.min(98, base + ok*6);
    const cls = score>=86?'crit':score>=74?'high':score>=58?'mod':'low';
    const risk=$('cloudConfidence');
    if(risk){ risk.className=`risk ${cls}`; risk.textContent=`${score}%`; }
    setText('cloudAdvice', ok ? 'Las capas WMS responden. Para ver nubosidad con más fuerza, use IR Máximo y mantenga radar en 45% a 60%.' : 'No se logró validar la imagen WMS. Verifique conexión, cache del navegador o disponibilidad externa de nowCOAST.');
  }
  function bootMap(){
    if(!window.L || !$('rainMap')){ setText('cloudStatus','Leaflet no cargó. Revise conexión del navegador.'); return; }
    const map = L.map('rainMap',{zoomControl:true,attributionControl:true}).fitBounds(PR_BOUNDS);
    const bases = {
      sat: L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',{maxZoom:18,attribution:'Esri'}).addTo(map),
      topo: L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',{maxZoom:17,attribution:'OpenTopoMap'}),
      streets: L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'OpenStreetMap'})
    };
    const labels = L.tileLayer('https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',{maxZoom:18,attribution:'Esri Labels'}).addTo(map);
    const ir = addLayer(map,'RAS_GOES_I4',1.0,430,'NOAA nowCOAST GOES IR');
    const vis = addLayer(map,'RAS_GOES',0.65,440,'NOAA nowCOAST GOES Visible');
    const radar = addLayer(map,'RAS_RIDGE_NEXRAD',0.50,500,'NOAA nowCOAST Radar');
    const markers = Object.fromEntries(Object.entries(TOWNS).map(([key,[lat,lon,name]])=>[key,L.circleMarker([lat,lon],{radius:7,weight:2,color:'#fed141',fillColor:'#fed141',fillOpacity:.6}).bindPopup(`<strong>${name}</strong><br/>Punto de referencia para nubosidad y lluvia cercana.`).addTo(map)]));
    function removeWeather(){ [ir,vis,radar].forEach(l=>map.hasLayer(l)&&map.removeLayer(l)); }
    function mode(m){
      removeWeather();
      if(m==='all'){ir.addTo(map);vis.addTo(map);radar.addTo(map);setText('focusTown','Todo');setText('cloudStatus','GOES IR máximo + visible + radar.');}
      if(m==='ir'){ir.addTo(map);setText('focusTown','IR máximo');setText('cloudStatus','Solo GOES infrarrojo al máximo.');}
      if(m==='vis'){ir.addTo(map);vis.addTo(map);setText('focusTown','Visible + IR');setText('cloudStatus','Visible reforzado con IR debajo.');}
      if(m==='radar'){ir.addTo(map);radar.addTo(map);setText('focusTown','Radar + IR');setText('cloudStatus','Radar encima de GOES IR.');}
      document.querySelectorAll('[data-mode]').forEach(b=>b.classList.toggle('active',b.dataset.mode===m));
      refresh();
    }
    function baseMode(name){
      Object.entries(bases).forEach(([k,l])=>{ if(k!==name && map.hasLayer(l)) map.removeLayer(l); });
      if(!map.hasLayer(bases[name])) bases[name].addTo(map);
      if(!map.hasLayer(labels)) labels.addTo(map);
      document.querySelectorAll('[data-base]').forEach(b=>b.classList.toggle('active',b.dataset.base===name));
    }
    function refresh(){
      const stamp=Date.now();
      [ir,vis,radar].forEach(l=>{l.setParams({_t:stamp}); l.redraw();});
      setText('mapUpdated',fmt()); setText('lastUpdated',fmt());
      const irImg=$('directIr'), visImg=$('directVis'), radImg=$('directRadar');
      if(irImg) irImg.src=wmsUrl('RAS_GOES_I4');
      if(visImg) visImg.src=wmsUrl('RAS_GOES');
      if(radImg) radImg.src=wmsUrl('RAS_RIDGE_NEXRAD');
      Promise.all([checkLayer('RAS_GOES_I4'),checkLayer('RAS_GOES'),checkLayer('RAS_RIDGE_NEXRAD')]).then(renderDiagnostics);
    }
    $('irOpacity')?.addEventListener('input',e=>{ir.setOpacity(Number(e.target.value)); setText('irVal',pct(e.target.value));});
    $('visOpacity')?.addEventListener('input',e=>{vis.setOpacity(Number(e.target.value)); setText('visVal',pct(e.target.value));});
    $('radarOpacity')?.addEventListener('input',e=>{radar.setOpacity(Number(e.target.value)); setText('radarVal',pct(e.target.value));});
    document.querySelectorAll('[data-mode]').forEach(b=>b.addEventListener('click',()=>mode(b.dataset.mode)));
    document.querySelectorAll('[data-base]').forEach(b=>b.addEventListener('click',()=>baseMode(b.dataset.base)));
    document.querySelectorAll('[data-town]').forEach(b=>b.addEventListener('click',()=>{ const t=TOWNS[b.dataset.town]; if(t){map.flyTo([t[0],t[1]],11,{duration:1.1}); markers[b.dataset.town]?.openPopup(); setText('focusTown',t[2]);}}));
    $('refreshBtn')?.addEventListener('click',refresh);
    $('printBtn')?.addEventListener('click',()=>window.print());
    $('kioskBtn')?.addEventListener('click',()=>document.body.classList.toggle('kiosk'));
    setTimeout(()=>map.invalidateSize(),300);
    setInterval(refresh,120000);
    refresh();
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',bootMap); else bootMap();
})();