(() => {
  const VERSION = '4.7.0';
  const NOWCOAST_WMS = 'https://nowcoast.noaa.gov/wms/com.esri.wms.Esrimap/obs';
  const ALERTS_URL = 'https://api.weather.gov/alerts/active?area=PR';
  const PR_BOUNDS = [[17.74,-67.50],[18.75,-65.02]];
  const PR_BBOX = '-67.50,17.74,-65.02,18.75';
  const TOWNS = {
    juana_diaz:[18.0533,-66.5060,'Juana Díaz'], ponce:[18.0111,-66.6141,'Ponce'], san_juan:[18.4655,-66.1057,'San Juan'], san_german:[18.0816,-67.0449,'San Germán'], mayaguez:[18.2011,-67.1396,'Mayagüez'], fajardo:[18.3258,-65.6524,'Fajardo'], vieques:[18.1263,-65.4401,'Vieques'], culebra:[18.3030,-65.3009,'Culebra']
  };
  const $ = id => document.getElementById(id);
  const fmt = (d=new Date()) => d.toLocaleString('es-PR',{dateStyle:'short',timeStyle:'short'});
  const setText = (id,v) => { const el=$(id); if(el) el.textContent = v; };
  function wmsUrl(layer){
    const params = new URLSearchParams({SERVICE:'WMS',VERSION:'1.1.1',REQUEST:'GetMap',LAYERS:layer,STYLES:'',FORMAT:'image/png',TRANSPARENT:'true',SRS:'EPSG:4326',BBOX:PR_BBOX,WIDTH:'1200',HEIGHT:'720',_t:String(Date.now())});
    return `${NOWCOAST_WMS}?${params.toString()}`;
  }
  async function json(url){ const r = await fetch(url,{headers:{Accept:'application/json, application/geo+json, application/ld+json'}}); if(!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); }
  function buildMap(){
    if(!window.L || !$('rainMap')){ setText('cloudStatus','Leaflet no cargó. Verifique conexión del navegador.'); return; }
    const map = L.map('rainMap',{zoomControl:true,attributionControl:true}).fitBounds(PR_BOUNDS);
    const sat = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',{maxZoom:18,attribution:'Esri World Imagery'}).addTo(map);
    const labels = L.tileLayer('https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',{maxZoom:18,attribution:'Esri Labels'}).addTo(map);
    const topo = L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',{maxZoom:17,attribution:'OpenTopoMap'});
    const streets = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:18,attribution:'OpenStreetMap'});
    const ir = L.tileLayer.wms(NOWCOAST_WMS,{layers:'RAS_GOES_I4',format:'image/png',transparent:true,version:'1.1.1',opacity:.95,zIndex:460,attribution:'NOAA nowCOAST GOES IR'}).addTo(map);
    const vis = L.tileLayer.wms(NOWCOAST_WMS,{layers:'RAS_GOES',format:'image/png',transparent:true,version:'1.1.1',opacity:.55,zIndex:470,attribution:'NOAA nowCOAST GOES Visible'}).addTo(map);
    const radar = L.tileLayer.wms(NOWCOAST_WMS,{layers:'RAS_RIDGE_NEXRAD',format:'image/png',transparent:true,version:'1.1.1',opacity:.64,zIndex:540,attribution:'NOAA nowCOAST Radar'}).addTo(map);
    Object.entries(TOWNS).forEach(([key,[lat,lon,name]])=>{
      L.marker([lat,lon],{icon:L.divIcon({className:'',html:'<div class="pin47"></div>',iconSize:[18,18],iconAnchor:[9,9]})}).bindPopup(`<strong>${name}</strong><br>Referencia municipal para nubosidad y lluvia.`).addTo(map);
    });
    const overlays = {'Nubes IR GOES':ir,'Nubes visibles GOES':vis,'Radar lluvia':radar,'Etiquetas':labels};
    const bases = {'Satélite':sat,'Topográfico':topo,'Calles':streets};
    L.control.layers(bases,overlays,{collapsed:false}).addTo(map);
    L.control.scale({imperial:false}).addTo(map);
    function refresh(){
      const t=Date.now(); [ir,vis,radar].forEach(layer=>{ layer.setParams({_t:t}); layer.redraw(); });
      setText('lastUpdated',fmt()); setText('mapUpdated',fmt()); setText('cloudStatus','GOES IR activo con opacidad reforzada. Radar sobre las nubes.');
      const a=$('directIr'); if(a) a.src=wmsUrl('RAS_GOES_I4');
      const b=$('directVis'); if(b) b.src=wmsUrl('RAS_GOES');
    }
    function mode(m){
      [ir,vis,radar].forEach(layer=>map.hasLayer(layer)&&map.removeLayer(layer));
      if(m==='ir'){ir.addTo(map);} else if(m==='vis'){ir.addTo(map); vis.addTo(map);} else if(m==='radar'){ir.addTo(map); radar.addTo(map);} else {ir.addTo(map); vis.addTo(map); radar.addTo(map);} 
      document.querySelectorAll('[data-mode]').forEach(btn=>btn.classList.toggle('active',btn.dataset.mode===m)); refresh();
    }
    document.querySelectorAll('[data-mode]').forEach(btn=>btn.addEventListener('click',()=>mode(btn.dataset.mode)));
    document.querySelectorAll('[data-town]').forEach(btn=>btn.addEventListener('click',()=>{ const t=TOWNS[btn.dataset.town]; if(t) map.flyTo([t[0],t[1]],11,{duration:1.1}); }));
    $('refreshBtn')?.addEventListener('click',refresh);
    $('kioskBtn')?.addEventListener('click',()=>document.body.classList.toggle('kiosk'));
    $('printBtn')?.addEventListener('click',()=>window.print());
    $('irOpacity')?.addEventListener('input',e=>{ir.setOpacity(Number(e.target.value)); setText('irVal',Math.round(Number(e.target.value)*100)+'%');});
    $('visOpacity')?.addEventListener('input',e=>{vis.setOpacity(Number(e.target.value)); setText('visVal',Math.round(Number(e.target.value)*100)+'%');});
    $('radarOpacity')?.addEventListener('input',e=>{radar.setOpacity(Number(e.target.value)); setText('radarVal',Math.round(Number(e.target.value)*100)+'%');});
    refresh(); setInterval(refresh,120000); setTimeout(()=>map.invalidateSize(),300);
  }
  async function loadAlerts(){
    try{ const data=await json(ALERTS_URL); const all=data.features||[]; const flood=all.filter(f=>/flood|inund|lluv|rain/i.test(`${f.properties?.event||''} ${f.properties?.headline||''}`)); setText('alertCount',all.length); setText('floodCount',flood.length); setText('cloudAdvice',flood.length?'Hay alertas relacionadas a lluvia/inundación. Validar con NWS San Juan.':'Sin alerta de inundación activa en este momento de consulta.'); }
    catch(e){ setText('alertCount','—'); setText('floodCount','—'); setText('cloudAdvice','No se pudieron cargar alertas NWS en esta consulta.'); }
  }
  function boot(){ buildMap(); loadAlerts(); setInterval(loadAlerts,120000); }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',boot); else boot();
})();