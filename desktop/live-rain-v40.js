(() => {
  const VERSION = '4.0.0';
  const MODEL = 'AURORA RainCast PR 4D';
  const TOWNS = [
    ['juana_diaz','Juana Díaz',18.0533,-66.5060],['ponce','Ponce',18.0111,-66.6141],['san_juan','San Juan',18.4655,-66.1057],['san_german','San Germán',18.0816,-67.0449],['mayaguez','Mayagüez',18.2011,-67.1396],['fajardo','Fajardo',18.3258,-65.6524],['vieques','Vieques',18.1263,-65.4401],['culebra','Culebra',18.3030,-65.3009]
  ].map(([key,name,lat,lon])=>({key,name,lat,lon}));
  const $ = id => document.getElementById(id);
  const fmt = (d=new Date()) => d.toLocaleString('es-PR',{dateStyle:'short',timeStyle:'short'});
  const safe = v => (v ?? '').toString();
  const color = v => v>=75?'#ef4444':v>=55?'#fb923c':v>=35?'#facc15':'#38bdf8';
  async function json(url){ const r=await fetch(url,{headers:{Accept:'application/json, application/geo+json, application/ld+json'}}); if(!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); }
  async function town(t){ const p=await json(`https://api.weather.gov/points/${t.lat},${t.lon}`); const u=p?.properties?.forecastHourly; let periods=[]; if(u){ const h=await json(u); periods=h?.properties?.periods?.slice(0,6)||[]; } return {town:t,periods}; }
  function pops(item){ return item.periods.map(p=>p.probabilityOfPrecipitation?.value ?? 0); }
  function avg(a){ return a.length?Math.round(a.reduce((x,y)=>x+y,0)/a.length):0; }
  function card(title, big, note, cls=''){ return `<article class="aurora4dCard ${cls}"><h4>${title}</h4><strong class="big">${big}</strong><p class="small muted">${note}</p></article>`; }
  function timeline(results){
    const ranked=[...results].sort((a,b)=>avg(pops(b))-avg(pops(a))).slice(0,5);
    return ranked.map(r=>{ const v=avg(pops(r)); return `<div class="auroraTimelineRow"><span>${r.town.name}</span><b><i style="width:${Math.max(6,v)}%;background:${color(v)}"></i></b><strong>${v}%</strong></div>`; }).join('');
  }
  function narrative(results, alerts){
    const ranked=[...results].sort((a,b)=>avg(pops(b))-avg(pops(a))); const top=ranked[0]; const second=ranked[1];
    const topAvg=top?avg(pops(top)):0; const flood=(alerts||[]).filter(a=>/flood|inund|rain|lluv/i.test(`${a.event} ${a.headline||''}`)).length;
    let level='vigilancia normal'; if(topAvg>=70||flood>0) level='vigilancia alta'; else if(topAvg>=45) level='vigilancia preventiva';
    return `<div class="auroraNarrative"><strong>${MODEL}:</strong> lectura ${level}. La señal de lluvia más alta está en <strong>${top?.town?.name||'—'}</strong> (${topAvg}%). La segunda zona de atención es <strong>${second?.town?.name||'—'}</strong>. Alertas relacionadas con lluvia/inundación: <strong>${flood}</strong>. Esta lectura combina pronóstico horario, radar/nubes ya cargados en el mapa y ranking municipal experimental.</div>`;
  }
  function quality(results, alerts, ok){
    const cls = ok && results.length>=6 ? 'ok' : results.length>=3 ? 'warn' : 'bad';
    const label = cls==='ok'?'operacional':cls==='warn'?'parcial':'limitado';
    return `<article class="aurora4dCard auroraQuality ${cls}"><h4>Calidad de datos</h4><strong class="big">${label}</strong><p class="small muted">Pueblos: ${results.length}/${TOWNS.length} · Alertas: ${(alerts||[]).length} · Actualizado: ${fmt()}</p></article>`;
  }
  function clouds(){
    const frame=document.querySelector('.mapFrame'); if(!frame || frame.querySelector('.aurora4dBand')) return;
    const band=document.createElement('div'); band.className='aurora4dBand'; band.setAttribute('aria-hidden','true');
    for(let i=0;i<13;i++){ const c=document.createElement('span'); c.className='auroraCloudBlob '+(i%4===0?'hot':''); c.style.top=(8+(i*7)%76)+'%'; c.style.left=(-(i*23)%120)+'px'; c.style.animationDelay=(-(i*1.9))+'s'; c.style.transform=`scale(${0.75+(i%5)*0.11})`; band.appendChild(c); }
    frame.appendChild(band);
  }
  function render(results, alerts){
    const panel=$('aurora4dPanel'), tl=$('rainTimeline4d'), nar=$('rainNarrative4d'), q=$('rainQuality4d');
    const ranked=[...results].sort((a,b)=>avg(pops(b))-avg(pops(a))); const top=ranked[0]; const island=avg(results.flatMap(r=>pops(r).slice(0,3))); const topAvg=top?avg(pops(top)):0;
    if(panel) panel.innerHTML=`<div class="aurora4dGrid">${card('Modelo', VERSION, MODEL)}${card('Promedio 0–3h', island+'%', 'Promedio de lluvia a corto plazo')}${card('Zona líder', top?.town?.name||'—', topAvg+'% promedio cercano')}</div>`;
    if(tl) tl.innerHTML=`<div class="auroraTimeline">${timeline(results)}</div>`;
    if(nar) nar.innerHTML=narrative(results, alerts);
    if(q) q.innerHTML=quality(results, alerts, true);
  }
  async function refresh(){
    clouds();
    const settled=await Promise.allSettled(TOWNS.map(town));
    const results=settled.filter(x=>x.status==='fulfilled').map(x=>x.value);
    let alerts=[]; try{ const a=await json('https://api.weather.gov/alerts/active?area=PR'); alerts=(a.features||[]).map(f=>f.properties); }catch(e){}
    render(results, alerts);
  }
  function boot(){ refresh(); setInterval(refresh,60000); }
  window.AURORA_RAINCAST_4D = { version: VERSION, refresh };
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',boot); else boot();
})();