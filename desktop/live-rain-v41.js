(() => {
  const VERSION = '4.1.0';
  const MUNICIPIOS = [
    ['Juana Díaz',18.0533,-66.5060],['Ponce',18.0111,-66.6141],['San Juan',18.4655,-66.1057],['San Germán',18.0816,-67.0449],['Mayagüez',18.2011,-67.1396],['Fajardo',18.3258,-65.6524],['Vieques',18.1263,-65.4401],['Culebra',18.3030,-65.3009]
  ];
  const $ = (id) => document.getElementById(id);
  const fmt = (d=new Date()) => d.toLocaleString('es-PR',{dateStyle:'short',timeStyle:'short'});
  const riskColor = (v) => v >= 75 ? '#ef4444' : v >= 55 ? '#fb923c' : v >= 35 ? '#facc15' : '#34d399';
  const label = (v) => v >= 75 ? 'Alto crítico' : v >= 55 ? 'Alto' : v >= 35 ? 'Moderado' : 'Bajo';
  async function json(url){ const r = await fetch(url,{headers:{Accept:'application/json, application/geo+json, application/ld+json'}}); if(!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); }
  async function readMunicipio([name,lat,lon]){
    try{
      const pt = await json(`https://api.weather.gov/points/${lat},${lon}`);
      const hourlyUrl = pt?.properties?.forecastHourly;
      let periods=[];
      if(hourlyUrl){ const h=await json(hourlyUrl); periods=h?.properties?.periods?.slice(0,4)||[]; }
      const p0 = periods[0]?.probabilityOfPrecipitation?.value ?? 0;
      const p1 = periods[1]?.probabilityOfPrecipitation?.value ?? p0;
      const p2 = periods[2]?.probabilityOfPrecipitation?.value ?? p1;
      const p3 = periods[3]?.probabilityOfPrecipitation?.value ?? p2;
      const forecast = periods[0]?.shortForecast || 'Sin dato';
      const impact = Math.min(100, Math.round((p1*.45)+(p2*.30)+(p3*.15)+(/thunder|storm|torment|aguacero|rain|shower/i.test(forecast)?12:0)));
      const trend = p2 > p0 + 10 ? 'en aumento' : p2 < p0 - 10 ? 'disminuyendo' : 'estable';
      return {name,lat,lon,p0,p1,p2,p3,forecast,impact,trend,ok:true};
    }catch(err){ return {name,lat,lon,p0:0,p1:0,p2:0,p3:0,forecast:'No disponible',impact:0,trend:'sin lectura',ok:false,error:err.message}; }
  }
  async function alerts(){
    try{ const data = await json('https://api.weather.gov/alerts/active?area=PR'); return (data.features||[]).map(f=>f.properties); }
    catch{ return []; }
  }
  function ensurePanel(){
    if($('aurora41DecisionPanel')) return $('aurora41DecisionPanel');
    const center = document.querySelector('.center') || document.querySelector('main') || document.body;
    const card = document.createElement('article');
    card.className = 'card aurora41Action';
    card.style.marginTop = '14px';
    card.innerHTML = `<h2><span class="aurora41Tag">AURORA v4.1</span> Centro de decisiones</h2><div id="aurora41DecisionPanel"><p class="muted">Cargando apoyo decisional…</p></div>`;
    center.appendChild(card);
    return $('aurora41DecisionPanel');
  }
  function buildReport(rows, alertRows){
    const ranked = [...rows].sort((a,b)=>b.impact-a.impact);
    const top = ranked[0];
    const flood = alertRows.filter(a => /flood|inund/i.test(`${a.event} ${a.headline||''}`));
    const critical = ranked.filter(r => r.impact >= 55).slice(0,5).map(r=>`${r.name} (${r.impact}/100)`).join(', ') || 'sin áreas críticas inmediatas';
    return `AURORA RainCast PR v4.1 — Resumen operacional\nFecha/hora: ${fmt()}\n\nPueblo principal de vigilancia: ${top?.name || '—'}\nImpacto estimado principal: ${top ? top.impact + '/100' : '—'}\nTendencia principal: ${top?.trend || '—'}\nPronóstico corto: ${top?.forecast || '—'}\n\nÁreas de atención: ${critical}\nAlertas activas NWS: ${alertRows.length}\nAlertas de inundación: ${flood.length}\n\nRecomendación: ${top && top.impact >= 75 ? 'vigilancia alta; evitar zonas inundables y validar con NWS/Manejo de Emergencias.' : top && top.impact >= 55 ? 'monitoreo preventivo; revisar radar y alertas antes de desplazarse.' : 'seguimiento normal con actualización cada minuto.'}\n\nNota: lectura experimental; no sustituye información oficial.`;
  }
  function copyReport(){ const el=$('aurora41Report'); if(!el) return; navigator.clipboard?.writeText(el.textContent || ''); }
  function printReport(){ window.print(); }
  function render(rows, alertRows){
    const panel = ensurePanel();
    const ranked = [...rows].sort((a,b)=>b.impact-a.impact);
    const top = ranked[0];
    const avg = rows.length ? Math.round(rows.reduce((n,r)=>n+r.impact,0)/rows.length) : 0;
    const flood = alertRows.filter(a => /flood|inund/i.test(`${a.event} ${a.headline||''}`));
    const table = ranked.map(r => `<tr><td><strong>${r.name}</strong></td><td>${r.p1}%</td><td>${r.p2}%</td><td><span style="color:${riskColor(r.impact)};font-weight:900">${r.impact}/100</span></td><td>${r.trend}</td></tr>`).join('');
    const report = buildReport(rows, alertRows);
    panel.innerHTML = `<section class="aurora41Shell">
      <div class="aurora41Grid">
        <article class="aurora41Card ${top?.impact>=75?'aurora41Danger aurora41Pulse':top?.impact>=55?'aurora41Warn':'aurora41Good'}"><h4>Pueblo crítico</h4><strong class="big">${top?.name || '—'}</strong><p>${top ? label(top.impact) + ' · ' + top.impact + '/100' : 'Sin lectura'}</p></article>
        <article class="aurora41Card"><h4>Impacto promedio</h4><strong class="big">${avg}/100</strong><div class="aurora41Bar"><span style="width:${avg}%;background:${riskColor(avg)}"></span></div></article>
        <article class="aurora41Card ${flood.length?'aurora41Warn':'aurora41Good'}"><h4>Alertas inundación</h4><strong class="big">${flood.length}</strong><p>Total alertas activas: ${alertRows.length}</p></article>
      </div>
      <article class="aurora41Card"><h4>Matriz municipal 0–3 horas</h4><table class="aurora41Table"><thead><tr><th>Pueblo</th><th>+1h</th><th>+2h</th><th>Impacto</th><th>Tendencia</th></tr></thead><tbody>${table}</tbody></table></article>
      <article class="aurora41Card"><h4>Reporte listo para copiar</h4><div id="aurora41Report" class="aurora41Report">${report}</div><div class="aurora41Controls"><button id="aurora41Copy" type="button">Copiar reporte</button><button id="aurora41Print" type="button">Imprimir</button></div><p class="aurora41Small">Actualizado: ${fmt()} · versión ${VERSION}</p></article>
    </section>`;
    $('aurora41Copy')?.addEventListener('click', copyReport);
    $('aurora41Print')?.addEventListener('click', printReport);
  }
  async function refresh(){
    const panel = ensurePanel();
    panel.innerHTML = '<p class="muted">Actualizando centro de decisiones v4.1…</p>';
    const [rows, alertRows] = await Promise.all([Promise.all(MUNICIPIOS.map(readMunicipio)), alerts()]);
    render(rows, alertRows);
  }
  window.addEventListener('DOMContentLoaded', () => { setTimeout(refresh, 1800); setInterval(refresh, 60000); });
})();
