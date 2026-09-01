(() => {
  const VERSION = '4.3.0';
  const MUNICIPIOS = [
    ['Juana Díaz',18.0533,-66.5060,'Sur'],['Ponce',18.0111,-66.6141,'Sur'],['San Juan',18.4655,-66.1057,'Metro'],['San Germán',18.0816,-67.0449,'Oeste'],['Mayagüez',18.2011,-67.1396,'Oeste'],['Fajardo',18.3258,-65.6524,'Este'],['Vieques',18.1263,-65.4401,'Este'],['Culebra',18.3030,-65.3009,'Este']
  ];
  const $ = id => document.getElementById(id);
  const fmt = (d=new Date()) => d.toLocaleString('es-PR',{dateStyle:'short',timeStyle:'short'});
  const level = v => v>=75?'ALTA':v>=55?'PREVENTIVA':v>=35?'MONITOREO':'NORMAL';
  const cls = v => v>=75?'critical':v>=55?'watch':'ready';
  async function json(url){ const r=await fetch(url,{headers:{Accept:'application/json, application/geo+json, application/ld+json'}}); if(!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); }
  async function risk([name,lat,lon,region]){
    try{
      const p=await json(`https://api.weather.gov/points/${lat},${lon}`);
      const u=p?.properties?.forecastHourly;
      let periods=[];
      if(u){ const h=await json(u); periods=h?.properties?.periods?.slice(0,4)||[]; }
      const vals=periods.map(x=>x.probabilityOfPrecipitation?.value??0);
      const p0=vals[0]??0, p1=vals[1]??p0, p2=vals[2]??p1, p3=vals[3]??p2;
      const max=Math.max(p0,p1,p2,p3);
      const trend=p3>p0+12?'subiendo':p3<p0-12?'bajando':'estable';
      const impact=Math.min(100,Math.round(max*.78+(p2*.12)+(p3*.10)));
      return {name,lat,lon,region,p0,p1,p2,p3,max,trend,impact,status:level(impact),ok:true};
    }catch(e){ return {name,lat,lon,region,p0:0,p1:0,p2:0,p3:0,max:0,trend:'sin datos',impact:0,status:'SIN DATOS',ok:false,error:e.message}; }
  }
  function buildReport(rows, alerts){
    const sorted=[...rows].sort((a,b)=>b.impact-a.impact);
    const top=sorted[0];
    const flood=(alerts||[]).filter(a=>/flood|inund/i.test(`${a.event} ${a.headline||''}`));
    const action=top?.impact>=75?'Activar vigilancia alta y validar alertas oficiales antes de movilizar personas.':top?.impact>=55?'Mantener vigilancia preventiva y revisar condiciones antes de desplazamientos.':'Continuar monitoreo regular y refrescar el radar.';
    return `PR-WX AURORA RainCast PR v${VERSION}\nReporte operacional rápido\nHora: ${fmt()}\n\nMunicipio crítico: ${top?.name||'—'}\nImpacto estimado: ${top?.impact??'—'}/100\nEstado decisional: ${top?.status||'—'}\nTendencia: ${top?.trend||'—'}\n\nAlertas activas: ${(alerts||[]).length}\nAlertas de inundación: ${flood.length}\n\nAcción recomendada:\n${action}\n\nTop municipios 0–3 horas:\n${sorted.slice(0,5).map((r,i)=>`${i+1}. ${r.name} — ${r.impact}/100 — ${r.status} — ${r.trend}`).join('\n')}\n\nNota: lectura experimental. Validar con NWS San Juan, NOAA, NHC y manejo de emergencias.`;
  }
  async function loadAlerts(){
    try{ const a=await json('https://api.weather.gov/alerts/active?area=PR'); return (a.features||[]).map(f=>f.properties); }catch(e){ return []; }
  }
  function render(rows, alerts){
    const box=$('aurora43Center'); if(!box) return;
    const sorted=[...rows].sort((a,b)=>b.impact-a.impact);
    const top=sorted[0];
    const avg=Math.round(rows.reduce((n,r)=>n+r.impact,0)/Math.max(1,rows.length));
    const flood=(alerts||[]).filter(a=>/flood|inund/i.test(`${a.event} ${a.headline||''}`));
    const report=buildReport(rows, alerts);
    box.innerHTML = `
      <div class="aurora43Banner"><strong>Centro de briefing AURORA v4.3:</strong> preparado para copiar, imprimir y utilizar como lectura rápida antes de tomar decisiones operacionales.</div>
      <div class="aurora43Grid">
        <article class="aurora43Card ${cls(top?.impact||0)}"><h4>Municipio crítico</h4><p><strong>${top?.name||'—'}</strong></p><p>Impacto: <strong>${top?.impact??'—'}/100</strong></p><p>Estado: <strong>${top?.status||'—'}</strong></p></article>
        <article class="aurora43Card ${cls(avg)}"><h4>Estado general</h4><p>Promedio operacional: <strong>${avg}/100</strong></p><p>Alertas activas: <strong>${alerts.length}</strong></p><p>Inundación: <strong>${flood.length}</strong></p></article>
      </div>
      <div class="aurora43Actions"><button type="button" id="aurora43Copy">Copiar briefing</button><button type="button" id="aurora43Json">Exportar JSON</button><button type="button" id="aurora43Kiosk">Modo kiosco</button><button type="button" onclick="window.print()">Imprimir</button></div>
      <h3>Matriz 0–3 horas</h3>
      <table class="aurora43Table"><thead><tr><th>Municipio</th><th>Región</th><th>Ahora</th><th>+1h</th><th>+2h</th><th>+3h</th><th>Impacto</th><th>Estado</th></tr></thead><tbody>${sorted.map(r=>`<tr><td>${r.name}</td><td>${r.region}</td><td>${r.p0}%</td><td>${r.p1}%</td><td>${r.p2}%</td><td>${r.p3}%</td><td>${r.impact}/100</td><td>${r.status}</td></tr>`).join('')}</tbody></table>
      <h3>Briefing automático</h3><pre class="aurora43Report" id="aurora43Report">${report}</pre>`;
    $('aurora43Copy')?.addEventListener('click',()=>navigator.clipboard?.writeText(report));
    $('aurora43Json')?.addEventListener('click',()=>{
      const payload={version:VERSION,generated_at:new Date().toISOString(),municipal_risks:sorted,alert_count:alerts.length,flood_alert_count:flood.length};
      const blob=new Blob([JSON.stringify(payload,null,2)],{type:'application/json'});
      const a=document.createElement('a'); a.href=URL.createObjectURL(blob); a.download='prwx-aurora-v43-briefing.json'; a.click(); URL.revokeObjectURL(a.href);
    });
    $('aurora43Kiosk')?.addEventListener('click',()=>document.body.classList.toggle('kioskMode'));
  }
  async function boot(){
    const box=$('aurora43Center'); if(box) box.innerHTML='<p class="muted">Cargando briefing operacional v4.3…</p>';
    const [rows,alerts]=await Promise.all([Promise.all(MUNICIPIOS.map(risk)), loadAlerts()]);
    render(rows, alerts);
  }
  window.addEventListener('DOMContentLoaded',boot);
})();
