"""Emit the interactive 3D kamea-river artifact (self-contained Canvas engine)."""

from __future__ import annotations

import json

SRC = ("C:/Users/lyfe1/AppData/Local/Temp/claude/C--Projects-Atlas/"
       "cfa90600-011e-4cb7-9299-09514a1662eb/scratchpad/kamea_rivers_3d.json")
OUT = ("C:/Users/lyfe1/AppData/Local/Temp/claude/C--Projects-Atlas/"
       "cfa90600-011e-4cb7-9299-09514a1662eb/scratchpad/kamea_rivers_3d.html")

data = json.load(open(SRC, encoding="utf-8"))

HTML = r"""<title>Kamea Rivers in 3D - the z-axis of a person</title>
<style>
  :root{
    --bg:#f3f1ea;--panel:#fff;--ink:#1a1f24;--muted:#66707a;--line:#e0dccf;--accent:#0e7c86;
    --canvas:#070b12;--serif:"Iowan Old Style",Georgia,serif;
    --mono:ui-monospace,"SF Mono","Cascadia Mono",Menlo,Consolas,monospace;
  }
  @media(prefers-color-scheme:dark){:root{--bg:#080d14;--panel:#0f1620;--ink:#e9edf2;--muted:#8794a1;--line:#1e2833;--accent:#39c6d6;--canvas:#05080e;}}
  :root[data-theme="dark"]{--bg:#080d14;--panel:#0f1620;--ink:#e9edf2;--muted:#8794a1;--line:#1e2833;--accent:#39c6d6;--canvas:#05080e;}
  :root[data-theme="light"]{--bg:#f3f1ea;--panel:#fff;--ink:#1a1f24;--muted:#66707a;--line:#e0dccf;--accent:#0e7c86;--canvas:#070b12;}
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--serif);line-height:1.55}
  .sr-only{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}
  .wrap{max-width:940px;margin:0 auto;padding:3rem 1.2rem 5rem}
  .eyebrow{font-family:var(--mono);font-size:.7rem;letter-spacing:.2em;text-transform:uppercase;color:var(--accent);margin:0 0 .8rem}
  h1{font-size:clamp(1.8rem,4.5vw,2.7rem);line-height:1.06;margin:0 0 .6rem;font-weight:600;letter-spacing:-.01em;text-wrap:balance}
  .sub{color:var(--muted);font-size:1.02rem;max-width:64ch;margin:0 0 1.4rem}
  em{color:var(--accent);font-style:normal}
  .controls{display:flex;flex-wrap:wrap;gap:.5rem 1.3rem;align-items:center;margin:.6rem 0}
  .grp{display:flex;gap:.3rem;align-items:center;flex-wrap:wrap}
  .grp .lab{font-family:var(--mono);font-size:.66rem;text-transform:uppercase;letter-spacing:.12em;color:var(--muted);margin-right:.2rem}
  button.tab{font-family:var(--mono);font-size:.75rem;padding:.28rem .55rem;border:1px solid var(--line);background:var(--panel);color:var(--muted);border-radius:6px;cursor:pointer}
  button.tab.on{color:#fff;border-color:transparent}
  .stage{position:relative;margin:.8rem 0;border:1px solid var(--line);border-radius:12px;overflow:hidden;background:var(--canvas)}
  canvas{display:block;width:100%;height:60vh;min-height:360px;touch-action:none;cursor:grab}
  canvas:active{cursor:grabbing}
  .readout{position:absolute;left:12px;bottom:10px;font-family:var(--mono);font-size:.72rem;color:#c9d4df;text-shadow:0 1px 3px #000;pointer-events:none}
  .hint{position:absolute;right:12px;top:10px;font-family:var(--mono);font-size:.66rem;color:#8794a1;pointer-events:none}
  .frame{font-size:.9rem;color:var(--muted);border-top:1px solid var(--line);margin-top:2rem;padding-top:1.4rem}
  .frame strong{color:var(--ink)}
</style>

<div class="wrap">
  <h2 class="sr-only">Interactive 3D view of a person's kamea river, where revisited cells rise by visit depth into towers.</h2>
  <p class="eyebrow">Temporal Kamea &middot; R1 &middot; visit-depth is the z-axis</p>
  <h1>The river in three dimensions</h1>
  <p class="sub">The flat river was a view from directly above. The representation is natively 3D: each time the path <em>returns to a cell it has already visited</em>, that visit is stacked one step higher &mdash; <em>visit&nbsp;depth</em> is a real z-axis. So a cell the river pools on rises into a tower. Drag to orbit. Then open the <em>window</em>: watch a stationary body's single tall tower (pure stacking) collapse and spread into flow.</p>

  <div class="controls">
    <div class="grp"><span class="lab">who</span><span id="people"></span></div>
    <div class="grp"><span class="lab">kamea</span><span id="bodies"></span></div>
    <div class="grp"><span class="lab">window</span><span id="windows"></span></div>
    <div class="grp"><button class="tab" id="spin">spin</button></div>
  </div>

  <div class="stage">
    <canvas id="cv"></canvas>
    <div class="hint">drag to orbit</div>
    <div class="readout" id="readout"></div>
  </div>

  <div class="frame">
    <p><strong>Reading the shape.</strong> Height = how many times the river pooled on that cell (visit depth). A <em>stationary</em> body at a short window is one needle &mdash; every sample lands on the same cell, stacking to full height. As the window opens the body actually moves, the tower falls, and the figure spreads sideways into a river. Stacking (z) and flow (xy) are the same motion seen at different time-scales &mdash; the distinction between "geometry" and "simple stacking" is a window choice, not two different things.</p>
    <p><strong>What it isn't.</strong> This is each body's honest motion in its own square &mdash; a person's <em>form</em>. Comparing these shapes between historical allies and rivals found no signal (p&nbsp;=&nbsp;0.79). Worth seeing as geometry; not a claim about the life.</p>
  </div>
</div>

<script id="data" type="application/json">__DATA__</script>
<script>
const DATA=JSON.parse(document.getElementById('data').textContent);
const ORDER=["sun","moon","mercury","venus","mars","jupiter","saturn"];
const WINS=["W3D","W30D","W180D","W1Y"];
const WLAB={W3D:"3 days",W30D:"30 days",W180D:"180 days",W1Y:"1 year"};
const GLYPH={sun:"\u2609",moon:"\u263D",mercury:"\u263F",venus:"\u2640",mars:"\u2642",jupiter:"\u2643",saturn:"\u2644"};
const COL={sun:"#e0a53b",moon:"#9fb6c9",mercury:"#e08a4a",venus:"#4bb573",mars:"#d0503f",jupiter:"#e0a53b",saturn:"#9f8fd0"};
const people=Object.keys(DATA);
let S={person:people[0],body:"moon",win:"W30D",yaw:0.7,pitch:0.95,spin:false};

function mk(host,items,cur,on,fmt){host.innerHTML="";items.forEach(it=>{const b=document.createElement('button');b.className='tab'+(it===cur?' on':'');b.innerHTML=fmt?fmt(it):it;if(it===cur)b.style.background=S.body?COL[S.body]:'#39c6d6';b.onclick=()=>on(it);host.appendChild(b);});}
function rebuild(){
  mk(document.getElementById('people'),people,S.person,v=>{S.person=v;rebuild();});
  mk(document.getElementById('bodies'),ORDER,S.body,v=>{S.body=v;rebuild();},b=>`${GLYPH[b]} ${b}`);
  mk(document.getElementById('windows'),WINS,S.win,v=>{S.win=v;rebuild();},w=>WLAB[w]);
  document.getElementById('spin').classList.toggle('on',S.spin);
  document.getElementById('spin').style.background=S.spin?COL[S.body]:'';
}
const cv=document.getElementById('cv'),ctx=cv.getContext('2d');
function resize(){const r=cv.getBoundingClientRect(),dpr=devicePixelRatio||1;cv.width=r.width*dpr;cv.height=r.height*dpr;ctx.setTransform(dpr,0,0,dpr,0,0);}
addEventListener('resize',resize);

let drag=null;
cv.addEventListener('pointerdown',e=>{drag={x:e.clientX,y:e.clientY};cv.setPointerCapture(e.pointerId);});
cv.addEventListener('pointermove',e=>{if(!drag)return;S.yaw+=(e.clientX-drag.x)*0.01;S.pitch=Math.max(0.2,Math.min(1.45,S.pitch+(e.clientY-drag.y)*0.006));drag={x:e.clientX,y:e.clientY};});
addEventListener('pointerup',()=>drag=null);
document.getElementById('spin').onclick=()=>{S.spin=!S.spin;document.getElementById('spin').classList.toggle('on',S.spin);document.getElementById('spin').style.background=S.spin?COL[S.body]:'';};

function scene(){
  const node=DATA[S.person][S.body],grid=node.grid,W=node.windows[S.win];
  let maxT=1;for(const w of WINS){for(const k in node.windows[w].towers)maxT=Math.max(maxT,node.windows[w].towers[k]);}
  return {grid,visits:W.visits,towers:W.towers,maxDepth:W.max_depth,pd:W.path_distance,maxT};
}
function project(p,cx,cy,cz,cyaw,syaw,cpit,spit,camD,base,ox,oy){
  let px=p[0]-cx,py=p[1]-cy,pz=p[2]-cz;
  let X=px*cyaw-py*syaw, Y=px*syaw+py*cyaw, Z=pz;
  let Yc=Y*cpit-Z*spit, Zc=Y*spit+Z*cpit;
  let d=camD+Yc, s=(camD/d)*base;
  return {x:ox+X*s, y:oy-Zc*s, depth:Yc, s};
}
function render(){
  resizeIfNeeded();
  const w=cv.clientWidth,h=cv.clientHeight;
  ctx.clearRect(0,0,w,h);
  const sc=scene(),grid=sc.grid,col=COL[S.body];
  const cx=(grid-1)/2, cy=(grid-1)/2;
  const zScale=(grid)/Math.max(sc.maxT,1)*1.25;
  const cyaw=Math.cos(S.yaw),syaw=Math.sin(S.yaw),cpit=Math.cos(S.pitch),spit=Math.sin(S.pitch);
  const camD=grid*2.4, base=Math.min(w,h)/(grid*1.7), ox=w/2, oy=h*0.58;
  const P=(x,y,z)=>project([x,y,z],cx,cy,0,cyaw,syaw,cpit,spit,camD,base,ox,oy);

  // floor grid
  ctx.lineWidth=1;ctx.strokeStyle='rgba(120,140,160,0.16)';
  for(let i=0;i<grid;i++){
    let a=P(i,0,0),b=P(i,grid-1,0);ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);ctx.stroke();
    let c=P(0,i,0),d=P(grid-1,i,0);ctx.beginPath();ctx.moveTo(c.x,c.y);ctx.lineTo(d.x,d.y);ctx.stroke();
  }
  // collect drawables: towers + path segments
  const draw=[];
  for(const k in sc.towers){const [x,y]=k.split(',').map(Number);const hgt=sc.towers[k]*zScale;
    const b=P(x,y,0),t=P(x,y,hgt);
    draw.push({depth:(b.depth+t.depth)/2,kind:'tower',b,t,h:sc.towers[k]});}
  for(let i=0;i<sc.visits.length-1;i++){
    const A=sc.visits[i],B=sc.visits[i+1];
    const pa=P(A[0],A[1],(A[2]+0.5)*zScale),pb=P(B[0],B[1],(B[2]+0.5)*zScale);
    draw.push({depth:(pa.depth+pb.depth)/2,kind:'seg',pa,pb,t:i/(sc.visits.length-1)});
  }
  draw.sort((a,b)=>b.depth-a.depth);
  for(const o of draw){
    if(o.kind==='tower'){
      ctx.strokeStyle=col;ctx.globalAlpha=0.28+0.5*Math.min(1,o.h/Math.max(sc.maxT,1));
      ctx.lineWidth=Math.max(1,o.b.s*0.06);
      ctx.beginPath();ctx.moveTo(o.b.x,o.b.y);ctx.lineTo(o.t.x,o.t.y);ctx.stroke();
      ctx.globalAlpha=1;ctx.fillStyle=col;
      ctx.beginPath();ctx.arc(o.t.x,o.t.y,Math.max(1.5,o.t.s*0.05),0,7);ctx.fill();
    } else {
      ctx.globalAlpha=0.35+0.65*o.t;ctx.strokeStyle=col;ctx.lineWidth=Math.max(1.4,o.pa.s*0.05);
      ctx.lineCap='round';ctx.beginPath();ctx.moveTo(o.pa.x,o.pa.y);ctx.lineTo(o.pb.x,o.pb.y);ctx.stroke();
    }
  }
  ctx.globalAlpha=1;
  // source marker
  if(sc.visits.length){const v0=sc.visits[0];const s0=P(v0[0],v0[1],(v0[2]+0.5)*zScale);
    ctx.fillStyle='#fff';ctx.beginPath();ctx.arc(s0.x,s0.y,3.5,0,7);ctx.fill();}
  document.getElementById('readout').innerHTML=
    `${GLYPH[S.body]} ${S.body} &middot; ${WLAB[S.win]} &nbsp; max stack ${sc.maxDepth+1} &middot; flow ${sc.pd} &middot; ${sc.maxDepth===0?'no pooling &mdash; pure flow':'towers = pooling'}`;
  if(S.spin&&!drag)S.yaw+=0.004;
  requestAnimationFrame(render);
}
let lastW=0,lastH=0;
function resizeIfNeeded(){const r=cv.getBoundingClientRect();if(r.width!==lastW||r.height!==lastH){lastW=r.width;lastH=r.height;const dpr=devicePixelRatio||1;cv.width=r.width*dpr;cv.height=r.height*dpr;ctx.setTransform(dpr,0,0,dpr,0,0);}}
rebuild();resize();requestAnimationFrame(render);
</script>
"""

html = HTML.replace("__DATA__", json.dumps(data, separators=(",", ":")))
with open(OUT, "w", encoding="utf-8") as h:
    h.write(html)
print(f"wrote {OUT} ({len(html)} bytes)")
