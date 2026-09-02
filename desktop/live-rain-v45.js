(() => {
  const VERSION = '4.5.0';
  const NOWCOAST_WMS = 'https://nowcoast.noaa.gov/wms/com.esri.wms.Esrimap/obs';
  const PR_BOUNDS = [[17.78,-67.42],[18.66,-65.16]];
  const TOWNS = {
    juana_diaz:[18.0533,-66.5060,'Juana Díaz'], ponce:[18.0111,-66.6141,'Ponce'], san_juan:[18.4655,-66.1057,'San Juan'], san_german:[18.0816,-67.0449,'San Germán'], fajardo:[18.3258,-65.6524,'Fajardo'], mayaguez:[18.2011,-67.1396,'Mayagüez'], vieques:[18.1263,-65.4401,'Vieques'], culebra:[18.3030,-65.3009,'Culebra']
  };
  const $ = id => document.getElementById(id);
  const fmt = (d=new Date()) => d.toLocaleString('es-PR',{dateStyle:'short',timeStyle:'short'});
  function setText(id, text){ const el=$(id); if(el) el.textContent = text; }
  function addCloudBoostPanel(){
    const center = document.querySelector('.center');
    if(!center || $('cloudMap45')) return;
    const card = document.createElement('article');
    card.className = 'card cloud45-card';
    card.style.marginTop = '14px';
    card.innerHTML = `
      <h2><span class="cloud45-badge">v4.5</span> Mapa reforzado de nubes sobre Puerto Rico</h2>
      <p>Esta vista sube el contraste de GOES infrarrojo y visible, coloca el radar encima y añade una lectura visual para identificar por dónde están pasando las nubes sobre PR.</p>
      <div class="cloud45-mapFrame">
        <div class="cloud45-chip">GOES IR alto contraste + Visible + Radar</div>
        <div class="cloud45-flow" aria-hidden="true"></div>
        <div class="cloud45-pulse">Nubes reforzadas · <span id="cloud45Updated">—</span></div>
        <div id="cloudMap45" class="cloud45-map" role="img" aria-label="Mapa reforzado de nubes GOES y radar sobre Puerto Rico"></div>
        <aside class="cloud45-panel">
          <strong>Controles de visibilidad</strong>
          <div class="cloud45-controls"><button data-cloud45-mode="all" class="active">Todo</button><button data-cloud45-mode="ir">Solo IR</button><button data-cloud45-mode="visible">Visible + IR</button><button data-cloud45-mode="radar">Radar + IR</button></div>
          <div class="cloud45-range"><label for="cloud45Ir">Nubes IR alto contraste <span id="cloud45IrVal">92%</span></label><input id="cloud45Ir" type="range" min="0" max="1" step="0.05" value="0.92"></div>
          <div class="cloud45-range"><label for="cloud45Vis">Nubes visibles <span id="cloud45VisVal">60%</span></label><input id="cloud45Vis" type="range" min="0" max="1" step="0.05" value="0.60"></div>
          <div class="cloud45-range"><label for="cloud45Radar">Radar lluvia <span id="cloud45RadarVal">52%</span></label><input id="cloud45Radar" type="range" min="0" max="1" step="0.05" value="0.52"></div>
          <div class="cloud45-townBtns"><button data-cloud45-town="juana_diaz">Juana Díaz</button><button data-cloud45-town="ponce">Ponce</button><button data-cloud45-town="san_juan">San Juan</button><button data-cloud45-town="san_german">San Germán</button><button data-cloud45-town="vieques">Vieques</button><button data-cloud45-town="culebra">Culebra</button></div>
        </aside>
      </div>
      <div class="cloud45-legend"><div><span class="cloud45-swatch" style="background:#93c5fd"></span>GOES infrarrojo reforzado</div><div><span class="cloud45-swatch" style="background:#e5e7eb"></span>GOES visible</div><div><span class="cloud45-swatch" style="background:#38bdf8"></span>Radar de lluvia</div></div>
      <div class="cloud45-note"><strong>Uso:</strong> mantenga “Todo” activo para ver nubosidad y lluvia. Use “Solo IR” cuando la capa visible salga débil o durante la noche.</div>`;
    const mapCard = document.querySelector('.mapCard');
    if(mapCard?.parentNode) mapCard.parentNode.insertBefore(card, mapCard.nextSibling); else center.prepend(card);
  }
  function bootCloud45(){
    if(!window.L || !$('cloudMap45')) return;
    const map = L.map('cloudMap45',{zoomControl:true,attributionControl:true}).fitBounds(PR_BOUNDS);
    map.createPane('cloud45BasePane'); map.getPane('cloud45BasePane').style.zIndex = 200;
    map.createPane('cloud45IRPane'); map.getPane('cloud45IRPane').style.zIndex = 430; map.getPane('cloud45IRPane').classList.add('cloud45-ir-pane');
    map.createPane('cloud45VisPane'); map.getPane('cloud45VisPane').style.zIndex = 440; map.getPane('cloud45VisPane').classList.add('cloud45-vis-pane');
    map.createPane('cloud45RadarPane'); map.getPane('cloud45RadarPane').style.zIndex = 520; map.getPane('cloud45RadarPane').classList.add('cloud45-radar-pane');
    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',{maxZoom:18,attribution:'Esri',pane:'cloud45BasePane'}).addTo(map);
    L.tileLayer('https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',{maxZoom:18,attribution:'Esri Labels'}).addTo(map);
    const ir = L.tileLayer.wms(NOWCOAST_WMS,{layers:'RAS_GOES_I4',format:'image/png',transparent:true,version:'1.1.1',opacity:.92,pane:'cloud45IRPane',attribution:'NOAA nowCOAST GOES IR'}).addTo(map);
    const vis = L.tileLayer.wms(NOWCOAST_WMS,{layers:'RAS_GOES',format:'image/png',transparent:true,version:'1.1.1',opacity:.60,pane:'cloud45VisPane',attribution:'NOAA nowCOAST GOES Visible'}).addTo(map);
    const radar = L.tileLayer.wms(NOWCOAST_WMS,{layers:'RAS_RIDGE_NEXRAD',format:'image/png',transparent:true,version:'1.1.1',opacity:.52,pane:'cloud45RadarPane',attribution:'NOAA nowCOAST Radar'}).addTo(map);
    Object.entries(TOWNS).forEach(([key,[lat,lon,name]], i)=>{
      L.marker([lat,lon],{icon:L.divIcon({className:'cloud45-cloud-marker',html:i%2?'☁️':'🌧️',iconSize:[34,34],iconAnchor:[17,17]})}).bindPopup(`<strong>${name}</strong><br>Referencia para verificar nubosidad y lluvia cercana.`).addTo(map);
    });
    function refresh(){ const s=Date.now(); [ir,vis,radar].forEach(layer=>{ layer.setParams({_t:s}); layer.redraw(); }); setText('cloud45Updated',fmt()); }
    function mode(name){
      [ir,vis,radar].forEach(layer=>{ if(map.hasLayer(layer)) map.removeLayer(layer); });
      if(name==='all'){ir.addTo(map); vis.addTo(map); radar.addTo(map);} else if(name==='ir'){ir.addTo(map);} else if(name==='visible'){ir.addTo(map); vis.addTo(map);} else if(name==='radar'){ir.addTo(map); radar.addTo(map);}
      document.querySelectorAll('[data-cloud45-mode]').forEach(btn=>btn.classList.toggle('active', btn.dataset.cloud45Mode===name)); refresh();
    }
    $('cloud45Ir')?.addEventListener('input', e=>{ ir.setOpacity(Number(e.target.value)); setText('cloud45IrVal', `${Math.round(Number(e.target.value)*100)}%`); });
    $('cloud45Vis')?.addEventListener('input', e=>{ vis.setOpacity(Number(e.target.value)); setText('cloud45VisVal', `${Math.round(Number(e.target.value)*100)}%`); });
    $('cloud45Radar')?.addEventListener('input', e=>{ radar.setOpacity(Number(e.target.value)); setText('cloud45RadarVal', `${Math.round(Number(e.target.value)*100)}%`); });
    document.querySelectorAll('[data-cloud45-mode]').forEach(btn=>btn.addEventListener('click',()=>mode(btn.dataset.cloud45Mode)));
    document.querySelectorAll('[data-cloud45-town]').forEach(btn=>btn.addEventListener('click',()=>{ const t=TOWNS[btn.dataset.cloud45Town]; if(t) map.flyTo([t[0],t[1]],10,{duration:1.1}); }));
    setTimeout(()=>map.invalidateSize(),400); refresh(); setInterval(refresh,120000);
  }
  function boot(){ addCloudBoostPanel(); bootCloud45(); }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',boot); else boot();
})();