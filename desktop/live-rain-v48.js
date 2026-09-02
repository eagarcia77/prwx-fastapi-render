(() => {
  const VERSION = '4.8.0';
  const NOWCOAST_WMS = 'https://nowcoast.noaa.gov/wms/com.esri.wms.Esrimap/obs';
  const PR_BOUNDS = [[17.74,-67.52],[18.76,-65.00]];
  const PR_BBOX = '-67.52,17.74,-65.00,18.76';
  const TOWNS = {
    juana_diaz:[18.0533,-66.5060,'Juana Díaz'], ponce:[18.0111,-66.6141,'Ponce'], san_juan:[18.4655,-66.1057,'San Juan'], san_german:[18.0816,-67.0449,'San Germán'], mayaguez:[18.2011,-67.1396,'Mayagüez'], fajardo:[18.3258,-65.6524,'Fajardo'], vieques:[18.1263,-65.4401,'Vieques'], culebra:[18.3030,-65.3009,'Culebra'], arecibo:[18.4724,-66.7157,'Arecibo'], humacao:[18.1497,-65.8274,'Humacao']
  };
  const $ = id => document.getElementById(id);
  const fmt = (d=new Date()) => d.toLocaleString('es-PR',{dateStyle:'short',timeStyle:'medium'});
  function setText(id, text){ const el=$(id); if(el) el.textContent = text; }
  function wmsUrl(layer, width='1200', height='720'){
    const p = new URLSearchParams({SERVICE:'WMS',VERSION:'1.1.1',REQUEST:'GetMap',FORMAT:'image/png',TRANSPARENT:'true',SRS:'EPSG:4326',LAYERS:layer,STYLES:'',BBOX:PR_BBOX,WIDTH:width,HEIGHT:height,_t:String(Date.now())});
    return `${NOWCOAST_WMS}?${p.toString()}`;
  }
  function pct(v){ return `${Math.round(Number(v)*100)}%`; }
  async function testImage(id, layer){
    const img=$(id); if(!img) return false;
    return new Promise(resolve=>{
      img.onload=()=>resolve(true); img.onerror=()=>resolve(false); img.src=wmsUrl(layer);
    });
  }
  function boot(){
    if(!window.L){ setText('cloudStatus','Leaflet no cargó. Revise conexión al CDN.'); return; }
    const map = L.map('rainMap',{zoomControl:true,attributionControl:true,preferCanvas:true}).fitBounds(PR_BOUNDS);
    const sat = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',{maxZoom:18,attribution:'Esri World Imagery'}).addTo(map);
    const labels = L.tileLayer('https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',{maxZoom:18,attribution:'Esri Labels'}).addTo(map);
    const topo = L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',{maxZoom:16,attribution:'OpenTopoMap'});
    const streets = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'OpenStreetMap'});
    const ir = L.tileLayer.wms(NOWCOAST_WMS,{layers:'RAS_GOES_I4',format:'image/png',transparent:true,version:'1.1.1',opacity:.98,zIndex:420,attribution:'NOAA nowCOAST GOES IR'}).addTo(map);
    const vis = L.tileLayer.wms(NOWCOAST_WMS,{layers:'RAS_GOES',format:'image/png',transparent:true,version:'1.1.1',opacity:.62,zIndex:430,attribution:'NOAA nowCOAST GOES Visible'}).addTo(map);
    const radar = L.tileLayer.wms(NOWCOAST_WMS,{layers:'RAS_RIDGE_NEXRAD',format:'image/png',transparent:true,version:'1.1.1',opacity:.58,zIndex:520,attribution:'NOAA nowCOAST Radar'}).addTo(map);
    const base = {sat,labels,topo,streets};
    const layers = {ir,vis,radar};
    const markers = L.layerGroup().addTo(map);
    Object.entries(TOWNS).forEach(([key,[lat,lon,name]])=>{
      L.circleMarker([lat,lon],{radius:7,weight:2,color:'#fed141',fillColor:'#007b5f',fillOpacity:.95}).bindPopup(`<strong>${name}</strong><br>Referencia municipal para nubosidad y lluvia cercana.`).addTo(markers);
    });
    function refresh(){
      const stamp = Date.now();
      Object.values(layers).forEach(layer=>{ layer.setParams({_t:stamp}); layer.redraw(); });
      testImage('directIr','RAS_GOES_I4').then(ok=>setText('irStatus', ok?'IR directo: recibido':'IR directo: no recibido'));
      testImage('directVis','RAS_GOES').then(ok=>setText('visStatus', ok?'Visible directo: recibido':'Visible directo: no recibido'));
      testImage('directRadar','RAS_RIDGE_NEXRAD').then(ok=>setText('radarStatus', ok?'Radar directo: recibido':'Radar directo: no recibido'));
      setText('lastUpdated', fmt()); setText('mapUpdated', fmt());
      setText('cloudStatus','GOES IR fuerte activo. Validación directa actualizada. Si el mapa se ve débil, revise las imágenes directas debajo.');
    }
    function mode(name){
      Object.values(layers).forEach(layer=>{ if(map.hasLayer(layer)) map.removeLayer(layer); });
      if(name==='all'){ ir.addTo(map); vis.addTo(map); radar.addTo(map); setText('focusTown','Todo'); }
      if(name==='ir'){ ir.addTo(map); setText('focusTown','IR fuerte'); }
      if(name==='vis'){ ir.addTo(map); vis.addTo(map); setText('focusTown','Visible + IR'); }
      if(name==='radar'){ ir.addTo(map); radar.addTo(map); setText('focusTown','Radar + IR'); }
      document.querySelectorAll('[data-mode]').forEach(b=>b.classList.toggle('active',b.dataset.mode===name));
      refresh();
    }
    function baseMode(name){
      Object.values(base).forEach(layer=>{ if(layer!==labels && map.hasLayer(layer)) map.removeLayer(layer); });
      if(name==='sat'){ sat.addTo(map); labels.addTo(map); }
      if(name==='topo'){ topo.addTo(map); labels.addTo(map); }
      if(name==='streets'){ streets.addTo(map); labels.addTo(map); }
      document.querySelectorAll('[data-base]').forEach(b=>b.classList.toggle('active',b.dataset.base===name));
    }
    $('irOpacity')?.addEventListener('input',e=>{ ir.setOpacity(Number(e.target.value)); setText('irVal',pct(e.target.value)); });
    $('visOpacity')?.addEventListener('input',e=>{ vis.setOpacity(Number(e.target.value)); setText('visVal',pct(e.target.value)); });
    $('radarOpacity')?.addEventListener('input',e=>{ radar.setOpacity(Number(e.target.value)); setText('radarVal',pct(e.target.value)); });
    document.querySelectorAll('[data-mode]').forEach(btn=>btn.addEventListener('click',()=>mode(btn.dataset.mode)));
    document.querySelectorAll('[data-base]').forEach(btn=>btn.addEventListener('click',()=>baseMode(btn.dataset.base)));
    document.querySelectorAll('[data-town]').forEach(btn=>btn.addEventListener('click',()=>{const t=TOWNS[btn.dataset.town]; if(t){ map.flyTo([t[0],t[1]],10,{duration:1.1}); setText('focusTown',t[2]); }}));
    $('refreshBtn')?.addEventListener('click',refresh);
    $('kioskBtn')?.addEventListener('click',()=>document.body.classList.toggle('kiosk'));
    $('printBtn')?.addEventListener('click',()=>window.print());
    setText('cloudAdvice','Operación recomendada: usar IR fuerte, comparar con la imagen directa GOES IR y validar alertas oficiales antes de tomar decisiones.');
    setText('diagVersion', VERSION);
    setText('diagSource','NOAA nowCOAST WMS');
    setText('diagLayer','RAS_GOES_I4');
    setText('diagRefresh','120 s');
    setTimeout(()=>map.invalidateSize(),350);
    refresh(); setInterval(refresh,120000);
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',boot); else boot();
})();