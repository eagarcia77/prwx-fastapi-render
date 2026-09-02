(() => {
  const VERSION = '5.0.0';
  const NOWCOAST_WMS = 'https://nowcoast.noaa.gov/wms/com.esri.wms.Esrimap/obs';
  const PR_BOUNDS = [[17.70,-67.70],[18.88,-64.82]];
  const PR_BBOX = '-67.70,17.70,-64.82,18.88';
  const TOWNS = {
    juana_diaz:[18.0533,-66.5060,'Juana Díaz'], ponce:[18.0111,-66.6141,'Ponce'], san_juan:[18.4655,-66.1057,'San Juan'], san_german:[18.0816,-67.0449,'San Germán'], mayaguez:[18.2011,-67.1396,'Mayagüez'], fajardo:[18.3258,-65.6524,'Fajardo'], vieques:[18.1263,-65.4401,'Vieques'], culebra:[18.3030,-65.3009,'Culebra'], arecibo:[18.4724,-66.7157,'Arecibo'], humacao:[18.1497,-65.8274,'Humacao'], guayama:[17.9841,-66.1138,'Guayama'], aguadilla:[18.4274,-67.1541,'Aguadilla'], salinas:[17.9775,-66.2970,'Salinas'], yabucoa:[18.0505,-65.8793,'Yabucoa']
  };
  const $ = id => document.getElementById(id);
  const fmt = (d=new Date()) => d.toLocaleString('es-PR',{dateStyle:'short',timeStyle:'medium'});
  function setText(id, text){ const el=$(id); if(el) el.textContent = text; }
  function wmsUrl(layer, width='1280', height='760'){
    const p = new URLSearchParams({SERVICE:'WMS',VERSION:'1.1.1',REQUEST:'GetMap',FORMAT:'image/png',TRANSPARENT:'true',SRS:'EPSG:4326',LAYERS:layer,STYLES:'',BBOX:PR_BBOX,WIDTH:width,HEIGHT:height,_t:String(Date.now())});
    return `${NOWCOAST_WMS}?${p.toString()}`;
  }
  function pct(v){return `${Math.round(Number(v)*100)}%`;}
  function layer(map, name, opacity, z){return L.tileLayer.wms(NOWCOAST_WMS,{layers:name,format:'image/png',transparent:true,version:'1.1.1',opacity,zIndex:z,attribution:'NOAA nowCOAST'});}
  async function probe(id, layerName){
    const img=$(id); if(!img) return false;
    return new Promise(resolve=>{ img.onload=()=>resolve(true); img.onerror=()=>resolve(false); img.src=wmsUrl(layerName); });
  }
  function advice(okIr, okVis, okRadar){
    if(okIr && okRadar) return 'GOES IR y radar responden. Use Todo o Radar + IR para interpretar nubes con lluvia asociada.';
    if(okIr) return 'GOES IR responde. Hay nubosidad visible en la capa infrarroja, pero radar puede no mostrar lluvia en ese momento.';
    if(okVis || okRadar) return 'Alguna capa responde, pero GOES IR no cargó. Actualice o verifique disponibilidad del servicio externo.';
    return 'No llegaron imágenes WMS directas. Puede ser limitación temporal del servicio o caché del navegador.';
  }
  function boot(){
    if(!window.L) { setText('cloudStatus','Leaflet no cargó. Verifique conexión al CDN.'); return; }
    const map = L.map('rainMap',{zoomControl:true,attributionControl:true}).fitBounds(PR_BOUNDS);
    const bases={
      sat:L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',{maxZoom:18,attribution:'Esri'}),
      topo:L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',{maxZoom:17,attribution:'OpenTopoMap'}),
      streets:L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'OpenStreetMap'})
    };
    bases.sat.addTo(map);
    const labels=L.tileLayer('https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',{maxZoom:18,attribution:'Esri Labels'}).addTo(map);
    const ir=layer(map,'RAS_GOES_I4',1,420).addTo(map);
    const vis=layer(map,'RAS_GOES',.70,430).addTo(map);
    const radar=layer(map,'RAS_RIDGE_NEXRAD',.42,510).addTo(map);
    Object.values(TOWNS).forEach(([lat,lon,name])=>L.circleMarker([lat,lon],{radius:6,weight:2,fillOpacity:.85,color:'#fed141',fillColor:'#007b5f'}).bindPopup(`<strong>${name}</strong><br>Referencia municipal para ver nubes cercanas.`).addTo(map));
    const active={base:'sat',mode:'all'};
    function setBase(key){Object.values(bases).forEach(b=>map.removeLayer(b)); bases[key].addTo(map); labels.addTo(map); active.base=key; document.querySelectorAll('[data-base]').forEach(b=>b.classList.toggle('active',b.dataset.base===key));}
    function show(mode){[ir,vis,radar].forEach(l=>map.hasLayer(l)&&map.removeLayer(l)); if(mode==='all'){ir.addTo(map);vis.addTo(map);radar.addTo(map);} if(mode==='ir'){ir.addTo(map);} if(mode==='vis'){ir.addTo(map);vis.addTo(map);} if(mode==='radar'){ir.addTo(map);radar.addTo(map);} active.mode=mode; document.querySelectorAll('[data-mode]').forEach(b=>b.classList.toggle('active',b.dataset.mode===mode)); setText('focusTown',mode==='ir'?'IR Máximo':mode==='radar'?'Radar + IR':mode==='vis'?'Visible + IR':'Todo'); refresh();}
    function refresh(){const t=Date.now(); [ir,vis,radar].forEach(l=>{l.setParams({_t:t}); l.redraw();}); setText('mapUpdated',fmt()); setText('lastUpdated',fmt()); setText('diagVersion',VERSION); setText('diagSource','NOAA nowCOAST WMS'); setText('diagRefresh','120s'); setText('diagLayer',active.mode);}
    function bindSlider(id, val, lyr){$(id)?.addEventListener('input',e=>{lyr.setOpacity(Number(e.target.value)); setText(val,pct(e.target.value));});}
    bindSlider('irOpacity','irVal',ir); bindSlider('visOpacity','visVal',vis); bindSlider('radarOpacity','radarVal',radar);
    document.querySelectorAll('[data-mode]').forEach(b=>b.addEventListener('click',()=>show(b.dataset.mode)));
    document.querySelectorAll('[data-base]').forEach(b=>b.addEventListener('click',()=>setBase(b.dataset.base)));
    document.querySelectorAll('[data-town]').forEach(b=>b.addEventListener('click',()=>{const t=TOWNS[b.dataset.town]; if(t){map.flyTo([t[0],t[1]],10,{duration:1.1}); setText('focusTown',t[2]);}}));
    $('refreshBtn')?.addEventListener('click',()=>validate());
    $('kioskBtn')?.addEventListener('click',()=>document.body.classList.toggle('kiosk'));
    $('printBtn')?.addEventListener('click',()=>window.print());
    async function validate(){setText('cloudStatus','Validando imágenes WMS directas…'); const [okIr,okVis,okRadar]=await Promise.all([probe('directIr','RAS_GOES_I4'),probe('directVis','RAS_GOES'),probe('directRadar','RAS_RIDGE_NEXRAD')]); setText('irStatus',okIr?'IR cargó':'IR no cargó'); setText('visStatus',okVis?'Visible cargó':'Visible no cargó'); setText('radarStatus',okRadar?'Radar cargó':'Radar no cargó'); const good=[okIr,okVis,okRadar].filter(Boolean).length; const cls=good>=3?'low':good===2?'med':'high'; const conf=good>=3?'Alta':good===2?'Media':'Baja'; const c=$('cloudConfidence'); if(c){c.textContent=conf; c.className=`risk ${cls}`;} setText('cloudStatus',advice(okIr,okVis,okRadar)); setText('cloudAdvice',advice(okIr,okVis,okRadar)); refresh(); }
    setTimeout(()=>map.invalidateSize(),300);
    show('all'); validate(); setInterval(validate,120000);
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',boot); else boot();
})();