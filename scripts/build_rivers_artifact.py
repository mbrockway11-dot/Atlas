"""Emit the kamea-rivers artifact HTML with the geometry embedded."""

from __future__ import annotations

import json

SRC = ("C:/Users/lyfe1/AppData/Local/Temp/claude/C--Projects-Atlas/"
       "cfa90600-011e-4cb7-9299-09514a1662eb/scratchpad/kamea_rivers.json")
OUT = ("C:/Users/lyfe1/AppData/Local/Temp/claude/C--Projects-Atlas/"
       "cfa90600-011e-4cb7-9299-09514a1662eb/scratchpad/kamea_rivers.html")

data = json.load(open(SRC, encoding="utf-8"))

HTML = """<title>The Shape of a Person - Kamea Rivers</title>
<style>
  :root{
    --bg:#f3f1ea; --panel:#ffffff; --ink:#1a1f24; --muted:#66707a; --line:#e0dccf;
    --accent:#0e7c86; --accent2:#c98a2b; --raw:#b9c2cc;
    --serif:"Iowan Old Style",Georgia,"Times New Roman",serif;
    --mono:ui-monospace,"SF Mono","Cascadia Mono",Menlo,Consolas,monospace;
  }
  @media (prefers-color-scheme:dark){:root{
    --bg:#080d14; --panel:#0f1620; --ink:#e9edf2; --muted:#8794a1; --line:#1e2833;
    --accent:#39c6d6; --accent2:#e6b45a; --raw:#33414f;
  }}
  :root[data-theme="dark"]{--bg:#080d14;--panel:#0f1620;--ink:#e9edf2;--muted:#8794a1;--line:#1e2833;--accent:#39c6d6;--accent2:#e6b45a;--raw:#33414f;}
  :root[data-theme="light"]{--bg:#f3f1ea;--panel:#ffffff;--ink:#1a1f24;--muted:#66707a;--line:#e0dccf;--accent:#0e7c86;--accent2:#c98a2b;--raw:#b9c2cc;}
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--serif);line-height:1.6;-webkit-font-smoothing:antialiased}
  .sr-only{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}
  .wrap{max-width:1000px;margin:0 auto;padding:3.5rem 1.4rem 6rem}
  .eyebrow{font-family:var(--mono);font-size:.7rem;letter-spacing:.2em;text-transform:uppercase;color:var(--accent);margin:0 0 .9rem}
  h1{font-size:clamp(2rem,5vw,3.1rem);line-height:1.05;margin:0 0 .7rem;font-weight:600;letter-spacing:-.01em;text-wrap:balance}
  .sub{color:var(--muted);font-size:1.06rem;max-width:64ch;margin:0}
  header{border-bottom:1px solid var(--line);padding-bottom:2rem;margin-bottom:1.5rem}
  p{margin:0 0 1rem}
  em{color:var(--accent2);font-style:italic}
  .legend{display:flex;gap:1.4rem;flex-wrap:wrap;font-family:var(--mono);font-size:.74rem;color:var(--muted);margin:1.2rem 0 .5rem}
  .legend b{color:var(--ink);font-weight:600}
  .swatch{display:inline-block;width:26px;height:0;vertical-align:middle;margin-right:.4rem}
  .person{margin:2.6rem 0;padding-top:1.4rem;border-top:1px solid var(--line)}
  .person.lead{border-top:none}
  .pname{font-size:1.4rem;font-weight:600;margin:0 0 .1rem}
  .pmeta{font-family:var(--mono);font-size:.74rem;color:var(--muted);margin:0 0 1rem}
  .rivers{display:grid;grid-template-columns:repeat(auto-fill,minmax(112px,1fr));gap:.7rem;align-items:start}
  .tile{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:.5rem .5rem .35rem}
  .tile.big{grid-column:span 2}
  .tlabel{font-family:var(--mono);font-size:.66rem;color:var(--muted);display:flex;justify-content:space-between;margin-bottom:.15rem}
  .glyph{font-size:.95rem}
  svg{width:100%;height:auto;display:block}
  .frame{font-size:.9rem;color:var(--muted);border-top:1px solid var(--line);margin-top:3rem;padding-top:1.6rem}
  .frame strong{color:var(--ink)}
  @media(max-width:560px){.rivers{grid-template-columns:repeat(auto-fill,minmax(92px,1fr))}}
</style>

<div class="wrap">
  <h2 class="sr-only">Each person's seven kamea flow trajectories drawn as rivers, at raw, pruned-and-reduced, and normalized-composite levels.</h2>
  <header>
    <p class="eyebrow">Temporal Kamea &middot; R1 &middot; one-year window</p>
    <h1>The shape of a person, like a river flowing</h1>
    <p class="sub">Each of the seven classical bodies walks its own magic square as the sky turns. Over a year, every one traces a figure &mdash; a <em>river</em>. Below, for each person, the seven rivers at three depths: the <b>raw</b> current with all its doubling-back, the <b>pruned &amp; reduced</b> channel it settles into, and a <b>normalized composite</b> that lays all seven on one frame &mdash; the single shape they compose.</p>
  </header>

  <div class="legend">
    <span><span class="swatch" style="border-top:2px solid var(--raw)"></span><b>raw</b> path (dwell &amp; reversals)</span>
    <span><span class="swatch" style="border-top:3px solid var(--accent)"></span><b>pruned + reduced</b> river</span>
    <span><b>&#9673;</b> source &nbsp;&middot;&nbsp; <b>&#9711;</b> mouth</span>
    <span>pd = path distance travelled on the grid</span>
  </div>

  <div id="gallery"></div>

  <div class="frame">
    <p><strong>What this is.</strong> These are the real R1 trajectories over a one-year window centred on each birth &mdash; the window matters: at three days only the Moon flows, over a year all seven do (Saturn barely &mdash; it needs decades to fill its little 3&times;3 square). There is no single canonical river; the figure is a function of the window you observe it through.</p>
    <p><strong>What it isn't.</strong> A person's river-shape is their <em>form</em>, not their fortune. Comparing these shapes between historical partners and rivals (Moon and all-seven, against a null of random pairs) found no signal &mdash; allies and enemies scatter through the noise alike (positive vs negative p&nbsp;=&nbsp;0.79 / 0.77). The rivers are worth seeing as what they are: each body's honest motion, drawn. Not a claim about the life.</p>
  </div>
</div>

<script id="data" type="application/json">__DATA__</script>
<script>
const DATA = JSON.parse(document.getElementById('data').textContent);
const ORDER = ["sun","moon","mercury","venus","mars","jupiter","saturn"];
const GLYPH = {sun:"&#9737;",moon:"&#9789;",mercury:"&#9791;",venus:"&#9792;",mars:"&#9794;",jupiter:"&#9795;",saturn:"&#9796;"};
const COL = {sun:"#e0a53b",moon:"#9fb6c9",mercury:"#e08a4a",venus:"#4bb573",mars:"#d0503f",jupiter:"#c98a2b",saturn:"#8f7fb0"};

function smooth(pts){ // Catmull-Rom -> cubic bezier path
  if(pts.length<2) return pts.length?`M${pts[0][0]},${pts[0][1]}`:"";
  let d=`M${pts[0][0]},${pts[0][1]}`;
  for(let i=0;i<pts.length-1;i++){
    const p0=pts[i-1]||pts[i], p1=pts[i], p2=pts[i+1], p3=pts[i+2]||p2;
    const c1x=p1[0]+(p2[0]-p0[0])/6, c1y=p1[1]+(p2[1]-p0[1])/6;
    const c2x=p2[0]-(p3[0]-p1[0])/6, c2y=p2[1]-(p3[1]-p1[1])/6;
    d+=` C${c1x},${c1y} ${c2x},${c2y} ${p2[0]},${p2[1]}`;
  }
  return d;
}
function mapPts(coords,grid,S,pad){
  const inner=S-2*pad, g=Math.max(grid-1,1);
  return coords.map(([x,y])=>[pad+x/g*inner, pad+y/g*inner]);
}
function river(body,cell,S){
  const grid=cell.grid, pad=S*0.14;
  const raw=mapPts(cell.raw,grid,S,pad), ren=mapPts(cell.render,grid,S,pad);
  const c=COL[body];
  let s=`<svg viewBox="0 0 ${S} ${S}" role="img"><title>${body} river</title>`;
  // faint grid dots
  for(let i=0;i<grid;i++)for(let j=0;j<grid;j++){const p=mapPts([[i,j]],grid,S,pad)[0];
    s+=`<circle cx="${p[0].toFixed(1)}" cy="${p[1].toFixed(1)}" r="0.8" fill="var(--line)"/>`;}
  s+=`<path d="${smooth(raw)}" fill="none" stroke="var(--raw)" stroke-width="1" opacity="0.8"/>`;
  s+=`<path d="${smooth(ren)}" fill="none" stroke="${c}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>`;
  if(ren.length){const a=ren[0],b=ren[ren.length-1];
    s+=`<circle cx="${a[0].toFixed(1)}" cy="${a[1].toFixed(1)}" r="3" fill="${c}"/>`;
    s+=`<circle cx="${b[0].toFixed(1)}" cy="${b[1].toFixed(1)}" r="2" fill="none" stroke="${c}" stroke-width="1.5"/>`;}
  s+=`</svg>`;
  return s;
}
function composite(bodies,S){
  const pad=S*0.1, inner=S-2*pad;
  let s=`<svg viewBox="0 0 ${S} ${S}" role="img"><title>normalized composite of all seven</title>`;
  for(const body of ORDER){
    const cs=bodies[body].core_shape; if(!cs||!cs.length) continue;
    const xs=cs.map(p=>p[0]),ys=cs.map(p=>p[1]);
    const mnx=Math.min(...xs),mny=Math.min(...ys);
    const ext=Math.max(Math.max(...xs)-mnx,Math.max(...ys)-mny,1);
    const pts=cs.map(([x,y])=>[pad+(x-mnx)/ext*inner, pad+(y-mny)/ext*inner]);
    s+=`<path d="${smooth(pts)}" fill="none" stroke="${COL[body]}" stroke-width="1.8" opacity="0.62" stroke-linecap="round"/>`;
  }
  s+=`</svg>`;
  return s;
}
const names=Object.keys(DATA);
const g=document.getElementById('gallery');
names.forEach((name,idx)=>{
  const bodies=DATA[name];
  const div=document.createElement('div');
  div.className='person'+(idx===0?' lead':'');
  const total=ORDER.reduce((a,b)=>a+(bodies[b]?bodies[b].path_distance:0),0);
  let html=`<div class="pname">${name}${idx===0?' &mdash; your river-shape':''}</div>`;
  html+=`<div class="pmeta">seven kamea rivers &middot; one-year window &middot; total flow ${total}</div>`;
  html+=`<div class="rivers">`;
  const S=110;
  for(const body of ORDER){const cell=bodies[body];
    html+=`<div class="tile"><div class="tlabel"><span class="glyph" style="color:${COL[body]}">${GLYPH[body]} ${body}</span><span>pd ${cell.path_distance}</span></div>${river(body,cell,S)}</div>`;}
  html+=`<div class="tile big"><div class="tlabel"><span>&#9670; normalized composite</span><span>all 7</span></div>${composite(bodies,S*2+12)}</div>`;
  html+=`</div>`;
  div.innerHTML=html;
  g.appendChild(div);
});
</script>
"""

html = HTML.replace("__DATA__", json.dumps(data, separators=(",", ":")))
with open(OUT, "w", encoding="utf-8") as h:
    h.write(html)
print(f"wrote {OUT} ({len(html)} bytes)")
