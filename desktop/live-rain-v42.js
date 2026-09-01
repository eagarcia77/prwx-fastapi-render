(() => {
  const VERSION = '4.2.0';
  const MUNICIPIOS = [
    ['Juana Díaz',18.0533,-66.5060],['Ponce',18.0111,-66.6141],['San Juan',18.4655,-66.1057],['San Germán',18.0816,-67.0449],['Mayagüez',18.2011,-67.1396],['Fajardo',18.3258,-65.6524],['Vieques',18.1263,-65.4401],['Culebra',18.3030,-65.3009]
  ];
  const $ = id => document.getElementById(id);
  const fmt = (d=new Date()) => d.toLocaleString('es-PR',{dateStyle:'short',timeStyle:'short'});
  const label = v => v>=75?'Alto crítico':v>=55?'Alto':v>=35?'Moderado':'Bajo';
  const statusClass = v => v>=75?'high':v>=55?'warn':'';
  async function json(url){ const r=await fetch(url,{headers:{Accept:'application/json, application/geo+json, application/ld+json'}}); if(!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); }
  async function townRisk([name,lat,lon]){
    try{
      const p = await json(`https://api.weather.gov/points/${lat},${lon}`);
      const h = await json(p.properties.forecastHourly);
      const periods = (h.properties.periods||[]).slice(0,4);
      const pops = periods.map(x=>x.probabilityOfPrecipitation?.value ?? 0);
      const peak = Math.max(...pops,0);
      const avg = Math.round(pops.reduce((a,b)=>a+b,0) / Math.max(1,pops.length));
      return {name, ok:true, peak, avg, pops, forecast: periods[0]?.shortForecast || '—'};
    }catch(err){ return {name, ok:false, peak:0, avg:0, pops:[], forecast:'Sin dato', error:String(err.message||err)}; }
  }
  async function alerts(){
    try{
      const data = await json('https://api.weather.gov/alerts/active?area=PR');
      const list = (data.features||[]).map(f=>f.properties||{});
      return {ok:true, list, flood:list.filter(a=>/flood|inund/i.test(`${a.event||''} ${a.headline||''}`))};
    }catch(err){ return {ok:false, list:[], flood:[], error:String(err.message||err)}; }
  }
  function ensurePanel(){
    if($('aurora42Panel')) return;
    const center = document.querySelector('.center') || document.querySelector('main') || document.body;
    const article = document.createElement('article');
    article.className = 'card';
    article.style.marginTop = '14px';
    article.innerHTML = `
      <h2>Centro operacional AURORA v4.2</h2>
      <div id="aurora42Panel"><p class="muted">Cargando centro operacional…</p></div>
    `;
    const after = $('aurora41DecisionPanel')?.closest('.card') || $('impactBoard')?.closest('.card');
    if(after && after.parentNode) after.parentNode.insertBefore(article, after.nextSibling); else center.appendChild(article);
  }
  function rows(items){
    return `<table class="aurora42-table"><thead><tr><th>Municipio</th><th>Riesgo pico</th><th>Promedio</th><th>Lectura</th></tr></thead><tbody>${items.map(i=>`<tr><td><strong>${i.name}</strong></td><td>${i.peak}%</td><td>${i.avg}%</td><td>${i.forecast}</td></tr>`).join('')}</tbody></table>`;
  }
  function buildReport(items, alertData){
    const ok = items.filter(i=>i.ok);
    const sorted = [...ok].sort((a,b)=>b.peak-a.peak);
    const critical = sorted[0];
    const avg = ok.length ? Math.round(ok.reduce((n,i)=>n+i.avg,0)/ok.length) : 0;
    const flood = alertData.flood.length;
    const active = alertData.list.length;
    const decision = critical?.peak>=75 || flood>0 ? 'Vigilancia alta' : critical?.peak>=55 ? 'Vigilancia preventiva' : 'Vigilancia normal';
    return [
      `PR-WX AURORA RainCast PR v4.2 - Reporte Operacional`,
      `Fecha/hora: ${fmt()}`,
      `Decisión sugerida: ${decision}`,
      `Municipio crítico: ${critical?.name || 'No disponible'} (${critical?.peak ?? 0}% pico 0-3h)`,
      `Promedio municipal: ${avg}%`,
      `Alertas activas NWS PR: ${active}`,
      `Alertas de inundación: ${flood}`,
      `Top municipal 0-3h: ${sorted.slice(0,5).map(i=>`${i.name} ${i.peak}%`).join(' | ') || 'Sin datos'}`,
      `Acciones: revisar mapa vivo, verificar alertas oficiales, monitorear carreteras propensas a inundación y actualizar antes de desplazamientos.`,
      `Nota: lectura experimental; validar con NOAA/NWS/NHC y manejo de emergencias.`
    ].join('\n');
  }
  function downloadJSON(items, alertData){
    const payload = {version:VERSION, model:'AURORA RainCast PR Operations Cockpit', generated_at:new Date().toISOString(), municipalities:items, alerts:{active:alertData.list.length, flood:alertData.flood.length}};
    const blob = new Blob([JSON.stringify(payload,null,2)], {type:'application/json'});
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `prwx-aurora-raincast-v42-${new Date().toISOString().slice(0,10)}.json`;
    a.click();
    setTimeout(()=>URL.revokeObjectURL(a.href),1000);
  }
  function render(items, alertData){
    const panel = $('aurora42Panel'); if(!panel) return;
    const ok = items.filter(i=>i.ok);
    const sorted = [...ok].sort((a,b)=>b.peak-a.peak);
    const critical = sorted[0] || {name:'—',peak:0,avg:0};
    const avg = ok.length ? Math.round(ok.reduce((n,i)=>n+i.avg,0)/ok.length) : 0;
    const decision = critical.peak>=75 || alertData.flood.length>0 ? 'Vigilancia alta' : critical.peak>=55 ? 'Vigilancia preventiva' : 'Vigilancia normal';
    const report = buildReport(items, alertData);
    panel.innerHTML = `
      <div class="aurora42-cockpit">
        <section class="aurora42-card"><span class="aurora42-tag">Decisión</span><h4>Estado operacional</h4><span class="aurora42-value">${decision}</span><span class="aurora42-status ${statusClass(critical.peak)}">${label(critical.peak)}</span></section>
        <section class="aurora42-card"><span class="aurora42-tag">Municipio crítico</span><h4>${critical.name}</h4><span class="aurora42-value">${critical.peak}%</span><p class="muted">Pico 0–3 horas</p></section>
        <section class="aurora42-card"><span class="aurora42-tag">Alertas</span><h4>NWS Puerto Rico</h4><span class="aurora42-value">${alertData.list.length}</span><p class="muted">${alertData.flood.length} relacionadas con inundación</p></section>
      </div>
      <div class="aurora42-banner"><strong>Lectura ejecutiva:</strong> ${critical.name} es el punto de mayor vigilancia con ${critical.peak}% de riesgo pico. El promedio de los municipios monitoreados es ${avg}% y se detectan ${alertData.flood.length} alertas de inundación activas.</div>
      <h3>Matriz operacional 0–3 horas</h3>${rows(sorted)}
      <h3>Checklist decisional</h3><ul class="aurora42-checklist">
        <li><strong>1. Confirmar alertas oficiales</strong><span class="muted">Revisar NWS/NHC antes de tomar decisiones críticas.</span></li>
        <li><strong>2. Priorizar el municipio crítico</strong><span class="muted">Observar lluvia, carreteras, quebradas y zonas bajas.</span></li>
        <li><strong>3. Actualizar antes de movilizar personal</strong><span class="muted">La lectura cambia cada 60 segundos.</span></li>
      </ul>
      <h3>Reporte operacional</h3><pre id="aurora42Report" class="aurora42-pre">${report}</pre>
      <div class="aurora42-actions"><button type="button" id="copyAurora42">Copiar reporte v4.2</button><button type="button" id="jsonAurora42">Exportar JSON</button><button type="button" id="printAurora42">Imprimir</button></div>
    `;
    $('copyAurora42')?.addEventListener('click',()=>navigator.clipboard?.writeText(report));
    $('jsonAurora42')?.addEventListener('click',()=>downloadJSON(items, alertData));
    $('printAurora42')?.addEventListener('click',()=>window.print());
  }
  async function boot(){
    ensurePanel();
    const panel = $('aurora42Panel'); if(panel) panel.innerHTML = '<p class="muted">Actualizando centro operacional v4.2…</p>';
    const [items, alertData] = await Promise.all([Promise.all(MUNICIPIOS.map(townRisk)), alerts()]);
    render(items, alertData);
  }
  window.addEventListener('DOMContentLoaded',()=>{ boot(); setInterval(boot,60000); });
})();