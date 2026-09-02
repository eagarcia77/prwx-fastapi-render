(() => {
  const VERSION = '5.1.0';
  const NOWCOAST_WMS = 'https://nowcoast.noaa.gov/wms/com.esri.wms.Esrimap/obs';
  const PR_BOUNDS = [[17.70,-67.70],[18.88,-64.82]];
  const PR_BBOX = '-67.70,17.70,-64.82,18.88';
  const TOWNS = {
    juana_diaz:[18.0533,-66.5060,'Juana Díaz'], ponce:[18.0111,-66.6141,'Ponce'], san_juan:[18.4655,-66.1057,'San Juan'], san_german:[18.0816,-67.0449,'San Germán'], mayaguez:[18.2011,-67.1396,'Mayagüez'], fajardo:[18.3258,-65.6524,'Fajardo'], vieques:[18.1263,-65.4401,'Vieques'], culebra:[18.3030,-65.3009,'Culebra'], arecibo:[18.4724,-66.7157,'Arecibo'], humacao:[18.1497,-65.8274,'Humacao'], guayama:[17.9841,-66.1138,'Guayama'], aguadilla:[18.4274,-67.1541,'Aguadilla'], salinas:[17.9775,-66.2970,'Salinas'], yabucoa:[18.0505,-65.8793,'Yabucoa']
  };
  const STAR_IMAGES = {
    geocolor: {
      label:'GOES-19 GeoColor Puerto Rico',
      note:'Imagen satelital directa. De día luce natural; de noche usa IR multispectral.',
      urls:['https://cdn.star.nesdis.noaa.gov/GOES19/ABI/SECTOR/pr/GEOCOLOR/1200x1200.jpg','https://cdn.star.nesdis.noaa.gov/GOES19/ABI/SECTOR/pr/GEOCOLOR/600x600.jpg','https://cdn.star.nesdis.noaa.gov/GOES16/ABI/SECTOR/pr/GEOCOLOR/600x600.jpg']
    },
    band13: {
      label:'GOES-19 Banda 13 IR limpia',
      note:'Infrarrojo fuerte para ver nubes altas y nubosidad de día o de noche.',
      urls:['https://cdn.star.nesdis.noaa.gov/GOES19/ABI/SECTOR/pr/13/1200x1200.jpg','https://cdn.star.nesdis.noaa.gov/GOES19/ABI/SECTOR/pr/13/600x600.jpg','https://cdn.star.nesdis.noaa.gov/GOES16/ABI/SECTOR/pr/13/600x600.jpg']
    },
    band14: {
      label:'GOES-19 Banda 14 IR larga',
      note:'Alternativa IR cuando la banda 13 o nowCOAST se ve débil.',
      urls:['https://cdn.star.nesdis.noaa.gov/GOES19/ABI/SECTOR/pr/14/1200x1200.jpg','https://cdn.star.nesdis.noaa.gov/GOES19/ABI/SECTOR/pr/14/600x600.jpg','https://cdn.star.nesdis.noaa.gov/GOES16/ABI/SECTOR/pr/14/600x600.jpg']
    },
    band02: {
      label:'GOES-19 Banda 2 visible',
      note:'Visible de alta resolución. Funciona mejor de día.',
      urls:['https://cdn.star.nesdis.noaa.gov/GOES19/ABI/SECTOR/pr/02/1200x1200.jpg','https://cdn.star.nesdis.noaa.gov/GOES19/ABI/SECTOR/pr/02/600x600.jpg','https://cdn.star.nesdis.noaa.gov/GOES16/ABI/SECTOR/pr/02/600x600.jpg']
    }
  };
  const $ = id => document.getElementById(id);
  const fmt = (d=new Date()) => d.toLocaleString('es-PR',{dateStyle:'short',timeStyle:'medium'});
  function setText(id,text){const el=$(id); if(el) el.textContent=text;}
  function pct(v){return `${Math.round(Number(v)*100)}%`;}
  function wmsUrl(layer,width='1280',height='760'){
    const p = new URLSearchParams({SERVICE:'WMS',VERSION:'1.1.1',REQUEST:'GetMap',FORMAT:'image/png',TRANSPARENT:'true',SRS:'EPSG:4326',LAYERS:layer,STYLES:'',BBOX:PR_BBOX,WIDTH:width,HEIGHT:height,_t:String(Date.now())});
    return `${NOWCOAST_WMS}?${p.toString()}`;
  }
  async function setImageWithFallback(img, urls){
    if(!img) return false;
    let index = 0;
    return new Promise(resolve => {
      const tryNext = () => {
        if(index >= urls.length){ resolve(false); return; }
        const src = `${urls[index++]}?t=${Date.now()}`;
        img.onload = () => resolve(true);
        img.onerror = tryNext;
        img.src = src;
      };
      tryNext();
    });
  }
  function layer(map,name,opacity,z){return L.tileLayer.wms(NOWCOAST_WMS,{layers:name,format:'image/png',transparent:true,version:'1.1.1',opacity,zIndex:z,attribution:'NOAA nowCOAST'});}
  function setSatellite(kind){
    const item = STAR_IMAGES[kind] || STAR_IMAGES.band13;
    setText('satProduct', item.label);
    setText('satNote', item.note);
    document.querySelectorAll('[data-sat]').forEach(b=>b.classList.toggle('active',b.dataset.sat===kind));
    setImageWithFallback($('satMain'), item.urls).then(ok=>{
      setText('satStatus', ok ? 'Imagen satelital directa cargó correctamente.' : 'La imagen directa no cargó. Use el enlace oficial NOAA en el panel.');
      setText('cloudConfidence', ok ? 'Alta' : 'Baja');
      const cc=$('cloudConfidence'); if(cc) cc.className=`risk ${ok?'low':'high'}`;
    });
  }
  async function probe(id, layerName){const img=$(id); if(!img) return false; return new Promise(resolve=>{img.onload=()=>resolve(true);img.onerror=()=>resolve(false);img.src=wmsUrl(layerName);});}
  function boot(){
    setText('diagVersion', VERSION); setText('diagSource','NOAA STAR + nowCOAST'); setText('diagRefresh','120s');
    setSatellite('band13');
    ['geocolor','band13','band14','band02'].forEach(k=>setImageWithFallback($(k+'Thumb'), STAR_IMAGES[k].urls));
    document.querySelectorAll('[data-sat]').forEach(btn=>btn.addEventListener('click',()=>setSatellite(btn.dataset.sat)));
    if(window.L){
      const map = L.map('rainMap',{zoomControl:true,attributionControl:true}).fitBounds(PR_BOUNDS);
      const bases={sat:L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',{maxZoom:18,attribution:'Esri'}),topo:L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',{maxZoom:17,attribution:'OpenTopoMap'}),streets:L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'OpenStreetMap'})};
      bases.sat.addTo(map);
      const labels=L.tileLayer('https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',{maxZoom:18,attribution:'Esri Labels'}).addTo(map);
      const ir=layer(map,'RAS_GOES_I4',.78,420).addTo(map), vis=layer(map,'RAS_GOES',.45,430), radar=layer(map,'RAS_RIDGE_NEXRAD',.38,510).addTo(map);
      Object.values(TOWNS).forEach(([lat,lon,name])=>L.circleMarker([lat,lon],{radius:6,weight:2,fillOpacity:.85,color:'#fed141',fillColor:'#007b5f'}).bindPopup(`<strong>${name}</strong><br>Referencia municipal.`).addTo(map));
      let activeMode='radar';
      function refresh(){const t=Date.now(); [ir,vis,radar].forEach(l=>{l.setParams({_t:t});l.redraw();}); setText('mapUpdated',fmt()); setText('lastUpdated',fmt()); setText('diagLayer',activeMode);}
      function show(mode){[ir,vis,radar].forEach(l=>map.hasLayer(l)&&map.removeLayer(l)); if(mode==='ir')ir.addTo(map); if(mode==='vis'){ir.addTo(map);vis.addTo(map);} if(mode==='radar'){ir.addTo(map);radar.addTo(map);} if(mode==='all'){ir.addTo(map);vis.addTo(map);radar.addTo(map);} activeMode=mode; document.querySelectorAll('[data-mode]').forEach(b=>b.classList.toggle('active',b.dataset.mode===mode)); refresh();}
      function setBase(key){Object.values(bases).forEach(b=>map.removeLayer(b)); bases[key].addTo(map); labels.addTo(map); document.querySelectorAll('[data-base]').forEach(b=>b.classList.toggle('active',b.dataset.base===key));}
      document.querySelectorAll('[data-mode]').forEach(b=>b.addEventListener('click',()=>show(b.dataset.mode)));
      document.querySelectorAll('[data-base]').forEach(b=>b.addEventListener('click',()=>setBase(b.dataset.base)));
      document.querySelectorAll('[data-town]').forEach(b=>b.addEventListener('click',()=>{const t=TOWNS[b.dataset.town]; if(t){map.flyTo([t[0],t[1]],10,{duration:1.1}); setText('focusTown',t[2]);}}));
      const bind=(id,val,lyr)=>$(id)?.addEventListener('input',e=>{lyr.setOpacity(Number(e.target.value)); setText(val,pct(e.target.value));});
      bind('irOpacity','irVal',ir); bind('visOpacity','visVal',vis); bind('radarOpacity','radarVal',radar);
      $('refreshBtn')?.addEventListener('click',()=>validate()); $('kioskBtn')?.addEventListener('click',()=>document.body.classList.toggle('kiosk')); $('printBtn')?.addEventListener('click',()=>window.print());
      async function validate(){setText('cloudStatus','Validando STAR y nowCOAST…'); setSatellite(document.querySelector('[data-sat].active')?.dataset.sat || 'band13'); const [okIr,okVis,okRadar]=await Promise.all([probe('directIr','RAS_GOES_I4'),probe('directVis','RAS_GOES'),probe('directRadar','RAS_RIDGE_NEXRAD')]); setText('irStatus',okIr?'nowCOAST IR cargó':'nowCOAST IR no cargó'); setText('visStatus',okVis?'nowCOAST visible cargó':'nowCOAST visible no cargó'); setText('radarStatus',okRadar?'Radar cargó':'Radar no cargó'); setText('cloudStatus','Use el panel superior Imagen satelital directa NOAA STAR. Esa es la corrección principal cuando la capa WMS no muestra nubes.'); refresh();}
      setTimeout(()=>map.invalidateSize(),300); show('radar'); validate(); setInterval(validate,120000);
    } else { setText('cloudStatus','Leaflet no cargó. La imagen satelital directa STAR debe verse arriba aunque el mapa falle.'); }
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',boot); else boot();
})();