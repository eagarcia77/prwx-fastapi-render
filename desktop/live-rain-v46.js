(() => {
  const VERSION = '4.6.0';
  const NOWCOAST_WMS = 'https://nowcoast.noaa.gov/wms/com.esri.wms.Esrimap/obs';
  const PR_BOUNDS = [[17.76,-67.46],[18.72,-65.05]];
  const PR_BBOX = '-67.46,17.76,-65.05,18.72';
  const TOWNS = {
    juana_diaz:[18.0533,-66.5060,'Juana Díaz'], ponce:[18.0111,-66.6141,'Ponce'], san_juan:[18.4655,-66.1057,'San Juan'], san_german:[18.0816,-67.0449,'San Germán'], fajardo:[18.3258,-65.6524,'Fajardo'], mayaguez:[18.2011,-67.1396,'Mayagüez'], vieques:[18.1263,-65.4401,'Vieques'], culebra:[18.3030,-65.3009,'Culebra']
  };
  const $ = id => document.getElementById(id);
  const fmt = (d=new Date()) => d.toLocaleString('es-PR',{dateStyle:'short',timeStyle:'short'});
  function setText(id, text){ const el=$(id); if(el) el.textContent = text; }
  function wmsImage(layer){
    const params = new URLSearchParams({
      SERVICE:'WMS', VERSION:'1.1.1', REQUEST:'GetMap', FORMAT:'image/png', TRANSPARENT:'true', SRS:'EPSG:4326',
      LAYERS:layer, STYLES:'', BBOX:PR_BBOX, WIDTH:'1100', HEIGHT:'620', _t:String(Date.now())
    });
    return `${NOWCOAST_WMS}?${params.toString()}`;
  }
  function addCloudRevealPanel(){
    const center = document.querySelector('.center');
    if(!center || $('cloudMap46')) return;
    const card = document.createElement('article');
    card.className = 'card cloud46-card';
    card.style.marginTop = '14px';
    card.innerHTML = `
      <h2><span class="cloud46-badge">v4.6</span> Mapa nubes REVEAL sobre Puerto Rico</h2>
      <p>Esta versión usa dos métodos al mismo tiempo: capa WMS en Leaflet y una imagen WMS directa de respaldo. Así se puede comprobar si las nubes están pasando por PR aunque una capa del mapa salga muy clara.</p>
      <div class="cloud46-grid">
        <div>
          <div class="cloud46-mapFrame">
            <div class="cloud46-chip">GOES IR Reveal + Visible + Radar</div>
            <div class="cloud46-pulse" aria-hidden="true"></div>
            <div class="cloud46-flow" aria-hidden="true"></div>
            <div id="cloudMap46" class="cloud46-map" role="img" aria-label="Mapa Reveal de nubes GOES sobre Puerto Rico"></div>
            <div class="cloud46-clock">Actualizado: <span id="cloud46Updated">—</span></div>
            <div class="cloud46-toast" id="cloud46Toast">Modo recomendado: IR Reveal al 100% para ver nubes aunque la capa visible esté débil.</div>
          </div>
          <div class="cloud46-imageWrap" style="margin-top:12px">
            <div class="cloud46-imageLabel">Imagen WMS directa · GOES IR</div>
            <img id="cloud46RawImage" alt="Imagen directa WMS GOES infrarroja de Puerto Rico" src="" />
          </div>
        </div>
        <aside class="cloud46-side">
          <div class="cloud46-mini"><h3>Controles de visualización</h3><div class="cloud46-btns"><button data-cloud46="reveal" class="active">IR Reveal</button><button data-cloud46="all">Todo</button><button data-cloud46="visible">Visible</button><button data-cloud46="radar">Radar</button></div></div>
          <div class="cloud46-mini cloud46-slider"><h3>Opacidad</h3><label>IR Reveal <span id="cloud46IrVal">100%</span></label><input id="cloud46Ir" type="range" min="0" max="1" step="0.05" value="1"><label>Visible <span id="cloud46VisVal">55%</span></label><input id="cloud46Vis" type="range" min="0" max="1" step="0.05" value="0.55"><label>Radar <span id="cloud46RadarVal">58%</span></label><input id="cloud46Radar" type="range" min="0" max="1" step="0.05" value="0.58"></div>
          <div class="cloud46-mini"><h3>Enfoque rápido</h3><div class="cloud46-btns"><button data-cloud46-town="juana_diaz">Juana Díaz</button><button data-cloud46-town="ponce">Ponce</button><button data-cloud46-town="san_juan">San Juan</button><button data-cloud46-town="san_german">San Germán</button><button data-cloud46-town="vieques">Vieques</button><button data-cloud46-town="culebra">Culebra</button></div></div>
          <div class="cloud46-mini cloud46-legend"><h3>Leyenda</h3><div class="cloud46-row"><span class="cloud46-swatch" style="background:#94a3b8"></span>GOES IR: nubes día/noche</div><div class="cloud46-row"><span class="cloud46-swatch" style="background:#e2e8f0"></span>GOES visible: mejor de día</div><div class="cloud46-row"><span class="cloud46-swatch" style="background:#38bdf8"></span>Radar: lluvia observada</div></div>
          <div class="cloud46-mini"><h3>Diagnóstico</h3><p class="cloud46-status" id="cloud46Status">Inicializando capas de nubes…</p><p class="cloud46-status">Si no se ven nubes en el mapa, revise la imagen WMS directa debajo; eso separa un fallo visual de un fallo de servicio.</p></div>
        </aside>
      </div>`;
    const mapCard = document.querySelector('.mapCard');
    if(mapCard && mapCard.parentNode) mapCard.parentNode.insertBefore(card, mapCard.nextSibling); else center.prepend(card);
  }
  function bootCloudReveal(){
    if(!window.L || !$('cloudMap46')) return;
    const map = L.map('cloudMap46', { zoomControl:true, attributionControl:true }).fitBounds(PR_BOUNDS);
    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {maxZoom:18, attribution:'Esri'}).addTo(map);
    L.tileLayer('https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}', {maxZoom:18, attribution:'Esri Labels'}).addTo(map);
    const cloudsIR = L.tileLayer.wms(NOWCOAST_WMS, { layers:'RAS_GOES_I4', format:'image/png', transparent:true, version:'1.1.1', opacity:1, zIndex:430, attribution:'NOAA nowCOAST GOES IR', className:'cloud46-tile-ir' }).addTo(map);
    const cloudsVisible = L.tileLayer.wms(NOWCOAST_WMS, { layers:'RAS_GOES', format:'image/png', transparent:true, version:'1.1.1', opacity:.55, zIndex:440, attribution:'NOAA nowCOAST GOES Visible', className:'cloud46-tile-vis' });
    const radar = L.tileLayer.wms(NOWCOAST_WMS, { layers:'RAS_RIDGE_NEXRAD', format:'image/png', transparent:true, version:'1.1.1', opacity:.58, zIndex:510, attribution:'NOAA nowCOAST Radar', className:'cloud46-tile-radar' }).addTo(map);
    Object.values(TOWNS).forEach(([lat,lon,name])=>L.circleMarker([lat,lon],{radius:6,color:'#fed141',weight:2,fillColor:'#007b5f',fillOpacity:.9}).bindPopup(`<strong>${name}</strong><br/>Referencia municipal para nubes y lluvia.`).addTo(map));
    const layers = {cloudsIR, cloudsVisible, radar};
    function mode(name){
      Object.values(layers).forEach(layer=>{ if(map.hasLayer(layer)) map.removeLayer(layer); });
      if(name==='reveal'){ cloudsIR.addTo(map); radar.addTo(map); setText('cloud46Toast','IR Reveal activo: máximo contraste para ver nubosidad sobre PR.'); }
      if(name==='all'){ cloudsIR.addTo(map); cloudsVisible.addTo(map); radar.addTo(map); setText('cloud46Toast','Todas las capas activas: IR + visible + radar.'); }
      if(name==='visible'){ cloudsIR.addTo(map); cloudsVisible.addTo(map); setText('cloud46Toast','Visible + IR: útil principalmente durante horas de luz.'); }
      if(name==='radar'){ cloudsIR.addTo(map); radar.addTo(map); setText('cloud46Toast','Radar + IR: lluvia observada con nubes de contexto.'); }
      document.querySelectorAll('[data-cloud46]').forEach(btn=>btn.classList.toggle('active', btn.dataset.cloud46===name));
      refresh();
    }
    function refresh(){
      const stamp = Date.now();
      Object.values(layers).forEach(layer=>{ layer.setParams({_t:stamp}); layer.redraw(); });
      const raw = $('cloud46RawImage'); if(raw) raw.src = wmsImage('RAS_GOES_I4');
      setText('cloud46Updated', fmt());
      setText('cloud46Status', 'Capas GOES IR, GOES visible y radar solicitadas a NOAA nowCOAST. Imagen directa actualizada para verificación.');
    }
    $('cloud46Ir')?.addEventListener('input', e=>{ cloudsIR.setOpacity(Number(e.target.value)); setText('cloud46IrVal', `${Math.round(Number(e.target.value)*100)}%`); });
    $('cloud46Vis')?.addEventListener('input', e=>{ cloudsVisible.setOpacity(Number(e.target.value)); setText('cloud46VisVal', `${Math.round(Number(e.target.value)*100)}%`); });
    $('cloud46Radar')?.addEventListener('input', e=>{ radar.setOpacity(Number(e.target.value)); setText('cloud46RadarVal', `${Math.round(Number(e.target.value)*100)}%`); });
    document.querySelectorAll('[data-cloud46]').forEach(btn=>btn.addEventListener('click',()=>mode(btn.dataset.cloud46)));
    document.querySelectorAll('[data-cloud46-town]').forEach(btn=>btn.addEventListener('click',()=>{ const t=TOWNS[btn.dataset.cloud46Town]; if(t) map.flyTo([t[0],t[1]], 10, {duration:1.1}); }));
    setTimeout(()=>map.invalidateSize(), 350);
    setInterval(refresh, 120000);
    mode('reveal');
  }
  function boot(){ addCloudRevealPanel(); bootCloudReveal(); }
  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
})();