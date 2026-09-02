(() => {
  const VERSION = '4.4.0';
  const NOWCOAST_WMS = 'https://nowcoast.noaa.gov/wms/com.esri.wms.Esrimap/obs';
  const PR_BOUNDS = [[17.80,-67.35],[18.62,-65.20]];
  const TOWNS = {
    juana_diaz:[18.0533,-66.5060,'Juana Díaz'], ponce:[18.0111,-66.6141,'Ponce'], san_juan:[18.4655,-66.1057,'San Juan'], san_german:[18.0816,-67.0449,'San Germán'], fajardo:[18.3258,-65.6524,'Fajardo'], mayaguez:[18.2011,-67.1396,'Mayagüez']
  };
  const $ = (id) => document.getElementById(id);
  const fmt = (d=new Date()) => d.toLocaleString('es-PR',{dateStyle:'short',timeStyle:'short'});
  function setText(id, text){ const el=$(id); if(el) el.textContent = text; }
  function addPanel(){
    const center = document.querySelector('.center');
    if(!center || $('cloudMap44')) return;
    const card = document.createElement('article');
    card.className = 'card cloud44-card';
    card.style.marginTop = '14px';
    card.innerHTML = `
      <h2>Mapa real de nubes sobre Puerto Rico · v4.4</h2>
      <p>Esta vista fuerza la capa GOES infrarroja de NOAA nowCOAST para que las nubes se vean claramente sobre PR, aun cuando la capa visible esté débil o sea de noche.</p>
      <div class="cloud44-grid">
        <div class="cloud44-mapFrame"><div class="cloud44-chip">GOES IR + Visible + Radar</div><div class="cloud44-pulse">Nubes activas</div><div id="cloudMap44" class="cloud44-map" role="img" aria-label="Mapa dedicado de nubes GOES infrarrojas y visibles sobre Puerto Rico"></div></div>
        <aside class="cloud44-side">
          <div class="cloud44-mini"><h3>Estado de capas</h3><p id="cloud44Status" class="cloud44-status">Inicializando mapa de nubes…</p><p class="cloud44-status">Actualizado: <span id="cloud44Updated">—</span></p></div>
          <div class="cloud44-mini cloud44-controls"><h3>Opacidad</h3><label>Nubes infrarrojas <span id="cloud44IrVal">82%</span></label><input id="cloud44Ir" type="range" min="0" max="1" step="0.05" value="0.82"><label>Nubes visibles <span id="cloud44VisVal">45%</span></label><input id="cloud44Vis" type="range" min="0" max="1" step="0.05" value="0.45"><label>Radar lluvia <span id="cloud44RadarVal">58%</span></label><input id="cloud44Radar" type="range" min="0" max="1" step="0.05" value="0.58"></div>
          <div class="cloud44-mini"><h3>Capas rápidas</h3><div class="cloud44-btns"><button data-cloud44="all" class="active">Todo</button><button data-cloud44="ir">Solo IR</button><button data-cloud44="visible">Visible</button><button data-cloud44="radar">Radar</button></div></div>
          <div class="cloud44-mini"><h3>Pueblos</h3><div class="cloud44-btns"><button data-cloud44-town="juana_diaz">Juana Díaz</button><button data-cloud44-town="ponce">Ponce</button><button data-cloud44-town="san_juan">San Juan</button><button data-cloud44-town="san_german">San Germán</button><button data-cloud44-town="fajardo">Fajardo</button><button data-cloud44-town="mayaguez">Mayagüez</button></div></div>
          <div class="cloud44-mini cloud44-legend"><h3>Leyenda</h3><div class="cloud44-row"><span class="cloud44-swatch" style="background:#94a3b8"></span>Nubes infrarrojas</div><div class="cloud44-row"><span class="cloud44-swatch" style="background:#e2e8f0"></span>Nubes visibles</div><div class="cloud44-row"><span class="cloud44-swatch" style="background:#38bdf8"></span>Radar de lluvia</div></div>
        </aside>
      </div>`;
    const mapCard = document.querySelector('.mapCard');
    if(mapCard && mapCard.parentNode) mapCard.parentNode.insertBefore(card, mapCard.nextSibling); else center.prepend(card);
  }
  function bootCloudMap(){
    if(!window.L || !$('cloudMap44')) return;
    const map = L.map('cloudMap44', { zoomControl:true, attributionControl:true }).fitBounds(PR_BOUNDS);
    const satellite = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {maxZoom:18, attribution:'Esri'}).addTo(map);
    const labels = L.tileLayer('https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}', {maxZoom:18, attribution:'Esri Labels'}).addTo(map);
    const cloudsIR = L.tileLayer.wms(NOWCOAST_WMS, { layers:'RAS_GOES_I4', format:'image/png', transparent:true, version:'1.1.1', opacity:.82, zIndex:420, attribution:'NOAA nowCOAST GOES IR' }).addTo(map);
    const cloudsVisible = L.tileLayer.wms(NOWCOAST_WMS, { layers:'RAS_GOES', format:'image/png', transparent:true, version:'1.1.1', opacity:.45, zIndex:430, attribution:'NOAA nowCOAST GOES Visible' }).addTo(map);
    const radar = L.tileLayer.wms(NOWCOAST_WMS, { layers:'RAS_RIDGE_NEXRAD', format:'image/png', transparent:true, version:'1.1.1', opacity:.58, zIndex:500, attribution:'NOAA nowCOAST Radar' }).addTo(map);
    Object.values(TOWNS).forEach(([lat,lon,name])=>L.marker([lat,lon]).bindPopup(`<strong>${name}</strong><br/>Referencia para ver nubes y lluvia cercana.`).addTo(map));
    const layers = {cloudsIR, cloudsVisible, radar};
    function show(mode){
      [['cloudsIR',cloudsIR],['cloudsVisible',cloudsVisible],['radar',radar]].forEach(([_,layer])=>{ if(map.hasLayer(layer)) map.removeLayer(layer); });
      if(mode==='all'){cloudsIR.addTo(map); cloudsVisible.addTo(map); radar.addTo(map);}
      if(mode==='ir'){cloudsIR.addTo(map);}
      if(mode==='visible'){cloudsVisible.addTo(map); cloudsIR.addTo(map);}
      if(mode==='radar'){cloudsIR.addTo(map); radar.addTo(map);}
      document.querySelectorAll('[data-cloud44]').forEach(b=>b.classList.toggle('active', b.dataset.cloud44===mode));
      setText('cloud44Status', mode==='all' ? 'Mostrando nubes infrarrojas, visibles y radar.' : `Modo activo: ${mode}.`);
      refresh();
    }
    function refresh(){
      const stamp = Date.now();
      Object.values(layers).forEach(layer=>{ layer.setParams({_t:stamp}); layer.redraw(); });
      setText('cloud44Updated', fmt());
    }
    $('cloud44Ir')?.addEventListener('input', e=>{ cloudsIR.setOpacity(Number(e.target.value)); setText('cloud44IrVal', `${Math.round(Number(e.target.value)*100)}%`); });
    $('cloud44Vis')?.addEventListener('input', e=>{ cloudsVisible.setOpacity(Number(e.target.value)); setText('cloud44VisVal', `${Math.round(Number(e.target.value)*100)}%`); });
    $('cloud44Radar')?.addEventListener('input', e=>{ radar.setOpacity(Number(e.target.value)); setText('cloud44RadarVal', `${Math.round(Number(e.target.value)*100)}%`); });
    document.querySelectorAll('[data-cloud44]').forEach(btn=>btn.addEventListener('click',()=>show(btn.dataset.cloud44)));
    document.querySelectorAll('[data-cloud44-town]').forEach(btn=>btn.addEventListener('click',()=>{ const t=TOWNS[btn.dataset.cloud44Town]; if(t) map.flyTo([t[0],t[1]], 10, {duration:1.1}); }));
    setTimeout(()=>map.invalidateSize(), 350);
    setInterval(refresh, 120000);
    refresh();
  }
  function boot(){ addPanel(); bootCloudMap(); }
  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
})();