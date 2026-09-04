(() => {
  const VERSION = '6.0.0';
  const API = '/rain/live/satellite/latest';
  const TEST = '/rain/live/satellite/self-test';
  const IMAGE = '/rain/live/satellite/image';
  const LOOP = '/rain/live/satellite/loop';
  const WFO = '/rain/live/satellite/wfo';
  const PROXY = '/rain/live/satellite/proxy';
  const NOWCOAST_WMS = 'https://nowcoast.noaa.gov/wms/com.esri.wms.Esrimap/obs';
  const PR_BOUNDS = [[17.70, -67.70], [18.88, -64.82]];
  const PR_BBOX = '-67.70,17.70,-64.82,18.88';
  const PRODUCTS = {
    band13: { label: 'Banda 13 IR', kind: 'ir', page: 'https://www.star.nesdis.noaa.gov/goes/sector_band.php?band=13&length=12&sat=G19&sector=pr&src=nav' },
    geocolor: { label: 'GeoColor', kind: 'geocolor', page: 'https://www.star.nesdis.noaa.gov/goes/sector_band.php?band=GEOCOLOR&length=12&sat=G19&sector=pr&src=nav' },
    band14: { label: 'Banda 14 IR', kind: 'ir', page: 'https://www.star.nesdis.noaa.gov/goes/sector_band.php?band=14&length=12&sat=G19&sector=pr&src=nav' },
    visible: { label: 'Banda 2 Visible', kind: 'visible', page: 'https://www.star.nesdis.noaa.gov/goes/sector_band.php?band=02&length=12&sat=G19&sector=pr&src=nav' }
  };
  const TOWNS = { juana_diaz:[18.0533,-66.5060,'Juana Díaz'], ponce:[18.0111,-66.6141,'Ponce'], san_juan:[18.4655,-66.1057,'San Juan'], san_german:[18.0816,-67.0449,'San Germán'], mayaguez:[18.2011,-67.1396,'Mayagüez'], fajardo:[18.3258,-65.6524,'Fajardo'], vieques:[18.1263,-65.4401,'Vieques'], culebra:[18.3030,-65.3009,'Culebra'], arecibo:[18.4724,-66.7157,'Arecibo'], humacao:[18.1497,-65.8274,'Humacao'], salinas:[17.9775,-66.2970,'Salinas'], yabucoa:[18.0505,-65.8793,'Yabucoa'] };
  const $ = id => document.getElementById(id);
  const fmt = () => new Date().toLocaleString('es-PR', { dateStyle:'short', timeStyle:'medium' });
  let latestData = null;
  function text(id, val){ const el=$(id); if(el) el.textContent=val; }
  function noCache(url){ return `${url}${url.includes('?')?'&':'?'}v=${VERSION}&t=${Date.now()}`; }
  function activeProduct(){ return document.querySelector('[data-product].active')?.dataset.product || 'band13'; }
  function directCdn(kind){ const p=(latestData?.products||{})[kind]; return (p?.urls||[]).filter(u => /^https:\/\/cdn\.star\.nesdis\.noaa\.gov\//i.test(u)); }
  function directLoops(kind){ const p=(latestData?.products||{})[kind]; return (p?.loops||[]).filter(u => /^https:\/\/cdn\.star\.nesdis\.noaa\.gov\//i.test(u)); }
  function imageUrl(kind){ return `${IMAGE}/${kind}.jpg`; }
  function loopUrl(kind){ return `${LOOP}/${kind}.gif`; }
  function wfoUrl(kind){ return `${WFO}/${kind}.jpg`; }
  function proxyUrl(kind){ return `${PROXY}/${kind}`; }
  function imageSources(kind){ return [...directCdn(kind), imageUrl(kind), wfoUrl(kind), proxyUrl(kind), PRODUCTS[kind]?.page].filter(Boolean).map(noCache); }
  function loopSources(kind){ return [...directLoops(kind), loopUrl(kind), imageUrl(kind), wfoUrl(kind)].filter(Boolean).map(noCache); }
  function setRisk(ok){ const c=$('cloudConfidence'); if(c){ c.textContent=ok?'Alta':'Diagnóstico'; c.className=`risk ${ok?'low':'med'}`; } }
  function loadInto(img, urls, onStatus){ if(!img) return; let i=0; const next=()=>{ if(i>=urls.length){ onStatus?.(false,'Sin fuente visual disponible'); setRisk(false); return; } const src=urls[i++]; img.onload=()=>{ onStatus?.(true,src); setRisk(true); }; img.onerror=next; img.src=src; }; next(); }
  function renderUrls(kind){ const box=$('urlResults'); if(!box) return; const urls=[...loopSources(kind), ...imageSources(kind)].slice(0,16); box.innerHTML = urls.map((u,i)=>`<div><strong>${i+1}.</strong> <a href="${u}" target="_blank" rel="noopener">${u.replace(/\?.*$/,'')}</a></div>`).join(''); }
  function openProduct(kind){ const p=PRODUCTS[kind]||PRODUCTS.band13; document.querySelectorAll('[data-product]').forEach(b=>b.classList.toggle('active', b.dataset.product===kind)); text('satProduct', p.label); text('satProductTitle', p.label); text('focusTown', 'Animación + CDN directo'); const frame=$('satFrame'); if(frame) frame.className=`imageFrame ${p.kind}`; const official=$('officialLink'); if(official) official.href=p.page; text('satStatus','Cargando imagen fija desde CDN/PR-WX…'); loadInto($('satMain'), imageSources(kind), (ok,msg)=>text('satStatus', ok?'Imagen fija cargada desde: '+String(msg).replace(/\?.*$/,''):'No cargó imagen fija; revise debug.'));
    text('loopStatus','Cargando loop animado de nubes…'); loadInto($('satLoop'), loopSources(kind), (ok,msg)=>text('loopStatus', ok?'Loop animado cargado desde: '+String(msg).replace(/\?.*$/,''):'No cargó loop; usando imagen fija/respaldo.'));
    ['imgA','imgB','imgC','imgD'].forEach((id,idx)=>{ const img=$(id); const src=[...directCdn(kind), imageUrl(kind), wfoUrl(kind), proxyUrl(kind)][idx]; if(img&&src) img.src=noCache(src); });
    renderUrls(kind); text('lastUpdated',fmt()); }
  function thumbs(){ ['band13','geocolor','band14','visible'].forEach(k=>{ const img=$(k+'Thumb'); if(img) loadInto(img, imageSources(k)); }); }
  async function latest(){ try{ const r=await fetch(noCache(API), {cache:'no-store'}); if(!r.ok) throw new Error(String(r.status)); const j=await r.json(); latestData=j; text('resolverStatus','Activo'); text('resolverTime',j.generated_utc||fmt()); return j; } catch(e){ text('resolverStatus','Pendiente/Render'); text('resolverTime',fmt()); return null; } }
  async function selfTest(){ text('cloudStatus','Ejecutando self-test con loop animado + CDN directo…'); try{ const r=await fetch(noCache(TEST), {cache:'no-store'}); if(!r.ok) throw new Error(String(r.status)); const j=await r.json(); const box=$('testResults'); if(box){ box.innerHTML=Object.entries(j.products||{}).map(([k,v])=>`<div class="diagItem"><span>${v.label||k}</span><strong class="${v.ok?'ok':'bad'}">IMG ${v.ok?'OK':'DIAG'} · LOOP ${v.loop_ok?'OK':'DIAG'} · ${v.bytes||0} bytes</strong></div>`).join(''); } text('cloudStatus','Self-test completado. La vista principal ahora muestra imagen fija y loop animado.'); } catch(e){ text('cloudStatus','Self-test no respondió. Render puede estar redeployando.'); } }
  function wmsUrl(layer,width='900',height='540'){ const p=new URLSearchParams({SERVICE:'WMS',VERSION:'1.1.1',REQUEST:'GetMap',FORMAT:'image/png',TRANSPARENT:'true',SRS:'EPSG:4326',LAYERS:layer,STYLES:'',BBOX:PR_BBOX,WIDTH:width,HEIGHT:height,_t:String(Date.now())}); return `${NOWCOAST_WMS}?${p}`; }
  async function probe(id, layer){ const img=$(id); if(!img) return false; return new Promise(resolve=>{ img.onload=()=>resolve(true); img.onerror=()=>resolve(false); img.src=wmsUrl(layer); }); }
  function bootMap(){ if(!window.L){ text('mapUpdated','Leaflet no cargó'); return; } const map=L.map('rainMap',{zoomControl:true,attributionControl:true}).fitBounds(PR_BOUNDS); L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'OpenStreetMap'}).addTo(map); const ir=L.tileLayer.wms(NOWCOAST_WMS,{layers:'RAS_GOES_I4',format:'image/png',transparent:true,version:'1.1.1',opacity:.78,zIndex:420,attribution:'NOAA nowCOAST'}).addTo(map); const radar=L.tileLayer.wms(NOWCOAST_WMS,{layers:'RAS_RIDGE_NEXRAD',format:'image/png',transparent:true,version:'1.1.1',opacity:.35,zIndex:510,attribution:'NOAA nowCOAST'}).addTo(map); Object.values(TOWNS).forEach(([lat,lon,name])=>L.circleMarker([lat,lon],{radius:6,color:'#fed141',fillColor:'#007b5f',fillOpacity:.85,weight:2}).bindPopup(`<strong>${name}</strong><br>Referencia municipal.`).addTo(map)); document.querySelectorAll('[data-town]').forEach(b=>b.addEventListener('click',()=>{ const t=TOWNS[b.dataset.town]; if(t){ map.flyTo([t[0],t[1]],10,{duration:1}); text('focusTown',t[2]); } })); const refresh=()=>{ const t=Date.now(); [ir,radar].forEach(l=>{l.setParams({_t:t}); l.redraw();}); text('mapUpdated',fmt()); }; setTimeout(()=>map.invalidateSize(),250); refresh(); setInterval(refresh,120000); }
  async function validate(){ const [okIr,okVis,okRadar]=await Promise.all([probe('directIr','RAS_GOES_I4'), probe('directVis','RAS_GOES'), probe('directRadar','RAS_RIDGE_NEXRAD')]); text('irStatus',okIr?'WMS IR cargó':'WMS IR no cargó'); text('visStatus',okVis?'WMS visible cargó':'WMS visible no cargó'); text('radarStatus',okRadar?'Radar cargó':'Radar no cargó'); }
  async function clearCache(){ if('serviceWorker' in navigator){ const regs=await navigator.serviceWorker.getRegistrations(); await Promise.all(regs.map(r=>r.unregister())); } if(window.caches){ const keys=await caches.keys(); await Promise.all(keys.map(k=>caches.delete(k))); } text('cloudStatus','Cache visual limpiado. Recargando…'); setTimeout(()=>location.reload(),650); }
  async function boot(){ text('diagVersion',VERSION); text('diagSource','Loop GIF + CDN directo NOAA STAR + backend PR-WX'); text('diagRefresh','120s'); document.querySelectorAll('[data-product]').forEach(b=>b.addEventListener('click',()=>openProduct(b.dataset.product))); $('refreshBtn')?.addEventListener('click',async()=>{ await latest(); openProduct(activeProduct()); thumbs(); validate(); selfTest(); }); $('testBtn')?.addEventListener('click',selfTest); $('clearCacheBtn')?.addEventListener('click',clearCache); $('kioskBtn')?.addEventListener('click',()=>document.body.classList.toggle('kiosk')); $('printBtn')?.addEventListener('click',()=>window.print()); await latest(); openProduct('band13'); thumbs(); bootMap(); validate(); selfTest(); setInterval(async()=>{ await latest(); openProduct(activeProduct()); },120000); }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',boot); else boot();
})();
