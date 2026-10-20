import json
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="AeroShield EG", page_icon="🛡️", layout="wide",
                   initial_sidebar_state="expanded")
st.markdown("""<style>
.stApp{background:radial-gradient(circle at 15% 0%,#0b1a38,#060913 60%);color:#e0e6ed}
[data-testid="stSidebar"]{background:#0a0f20!important;border-right:1px solid #16324f;box-shadow:4px 0 30px #00f2fe14}
[data-testid="stSidebar"] h1{color:#00f2fe;letter-spacing:2px;text-shadow:0 0 12px #00f2fe99}
[data-testid="stSidebar"] h3{color:#7fc8ff;border-bottom:1px solid #16324f;padding-bottom:4px}
.block-container{padding:.4rem .6rem 0 .6rem;max-width:100%}
footer{visibility:hidden}
header[data-testid="stHeader"]{background:transparent!important}
[data-testid="stToolbar"],[data-testid="stDecoration"]{display:none!important}
iframe{border:1px solid #16324f!important;border-radius:12px;box-shadow:0 0 50px #00f2fe1f}
</style>""", unsafe_allow_html=True)

# ---------------- Airports (coordinates verified) ----------------
AIRPORTS = {
    "Sphinx Intl (SPX) [PRIMARY]": (30.1147, 30.8967, "SPX"),
    "Cairo Intl (CAI)": (30.1219, 31.4056, "CAI"),
    "Borg El Arab (HBE)": (30.9177, 29.6964, "HBE"),   # corrected (was 31.18)
    "Sharm El Sheikh (SSH)": (27.9773, 34.3950, "SSH"),
    "Hurghada Intl (HRG)": (27.1783, 33.7994, "HRG"),
    "Luxor Intl (LXR)": (25.6710, 32.7066, "LXR"),
    "Aswan Intl (ASW)": (23.9644, 32.8200, "ASW"),
}

# ---------------- Sidebar ----------------
st.sidebar.title("🛡️ AeroShield EG")
st.sidebar.caption("National Air Defense & Anti-Drone Platform")
name = st.sidebar.selectbox("🎯 Defense sector", list(AIRPORTS.keys()))
lat, lon, code = AIRPORTS[name]

st.sidebar.subheader("🗺️ Map")
style = st.sidebar.radio("Base map", ["Satellite (ESRI)", "Dark vector (CARTO)"])
labels = st.sidebar.checkbox("Place names overlay", True)
zoom = st.sidebar.slider("Start zoom", 8.0, 15.0, 11.0, 0.5)

st.sidebar.subheader("🛸 Low-altitude drone zone")
zone = st.sidebar.checkbox("Show zone (cage)", True)
amin, amax = st.sidebar.slider("Altitude band (m AGL)", 0, 500, (50, 150))
zr = st.sidebar.slider("Zone radius (km)", 1.0, 10.0, 4.0, 0.5)
zscale = st.sidebar.slider("Altitude exaggeration ×", 1, 15, 4)

st.sidebar.subheader("📡 Radar & simulation")
rpm = st.sidebar.slider("Radar speed (rpm)", 2, 30, 10)
ts = st.sidebar.slider("Time scale ×", 1, 20, 6)

st.sidebar.subheader("✈️ Traffic, weather & security")
nair = st.sidebar.slider("Number of aircraft", 3, 30, 8)
dust = st.sidebar.slider("Dust storm / haze", 0.0, 1.0, 0.25, 0.05)
roads = st.sidebar.checkbox("Real roads overlay", True)
sites = st.sidebar.checkbox("Protected landmarks", True)
sectors = st.sidebar.checkbox("N/E/S/W defense sectors", True)

LANDMARKS = [("Grand Egyptian Museum", 29.9942, 31.1190),
             ("Giza Pyramids", 29.9792, 31.1342),
             ("Egyptian Museum (Tahrir)", 30.0478, 31.2336)]

cfg = dict(
    hub=dict(lat=lat, lon=lon, code=code, name=name),
    airports=[dict(lat=v[0], lon=v[1], code=v[2]) for k, v in AIRPORTS.items() if v[2] != code],
    sat=style.startswith("Sat"), labels=labels, zoom=zoom,
    zone=zone, amin=amin, amax=amax, zr=zr, zscale=zscale, rpm=rpm, ts=ts,
    nair=nair, dust=dust, roads=roads, sites=sites, sectors=sectors,
    lm=[dict(name=n, lat=a, lon=b) for n, a, b in LANDMARKS],
)

HTML = r"""
<!DOCTYPE html><html><head><meta charset="utf-8">
<script src="https://unpkg.com/deck.gl@8.9.35/dist.min.js"></script>
<style>
html,body{margin:0;height:100%;background:#060913;font-family:Menlo,Consolas,monospace;color:#cfe9ff;overflow:hidden}
#map{position:absolute;inset:0}
.panel{position:absolute;background:rgba(8,14,30,.78);border:1px solid #16324f;border-radius:10px;
 backdrop-filter:blur(6px);padding:10px 12px;font-size:12px}
.panel{z-index:4}
#tick{bottom:0;left:0;right:0;border-radius:0;border-width:1px 0 0 0;padding:8px 14px;color:#7fc8ff;font-size:12px;white-space:nowrap;overflow:hidden}
#haze{position:absolute;inset:0;pointer-events:none;z-index:2;opacity:0;background:radial-gradient(circle,rgba(190,140,70,.35),rgba(190,140,70,.9))}
#top{top:0;left:0;right:0;height:46px;border-radius:0;border-width:0 0 1px 0;display:flex;align-items:center;gap:12px;padding:0 14px;box-sizing:border-box}
.logo{font-size:15px;color:#00f2fe;letter-spacing:2px;font-weight:bold;text-shadow:0 0 10px #00f2fe;white-space:nowrap}
.pill{border:1px solid #1d4f7a;border-radius:20px;padding:3px 10px;font-size:11px;color:#8fc4ee;white-space:nowrap}
.pill i{display:inline-block;width:7px;height:7px;border-radius:50%;background:#22c55e;margin-right:6px;box-shadow:0 0 8px #22c55e;animation:bl 1.4s infinite}
@keyframes bl{50%{opacity:.25}}
#lvl{margin-left:auto;font-weight:bold;padding:4px 12px;border-radius:6px;background:#06332a;color:#34d399;border:1px solid #34d399;white-space:nowrap}
#lvl.hi{background:#3b0f14;color:#fca5a5;border-color:#ef4444;animation:p 1s infinite}
#clk{color:#7fa6c9;white-space:nowrap}
#scan{position:absolute;inset:0;pointer-events:none;z-index:3;background:repeating-linear-gradient(0deg,rgba(0,255,200,.035) 0 1px,transparent 1px 3px)}
#vig{position:absolute;inset:0;pointer-events:none;z-index:3;opacity:0;box-shadow:inset 0 0 170px 30px rgba(239,68,68,.55)}
#vig.on{animation:vg 1s infinite alternate}
@keyframes vg{from{opacity:.3}to{opacity:1}}
#ban{position:absolute;top:60px;left:50%;transform:translateX(-50%);z-index:5;display:none;background:rgba(120,10,20,.88);border:2px solid #ef4444;color:#fff;padding:8px 22px;border-radius:8px;font-size:15px;letter-spacing:2px;animation:p 1s infinite;white-space:nowrap}
@media(max-width:820px){
 .pill{display:none}#top .pill:first-of-type{display:inline-block}
 .logo{font-size:12px}#lvl{font-size:10px;padding:3px 6px}#clk{display:none}
 #hud{width:46%;font-size:10px;padding:6px;top:54px;max-height:42%}
 .k b{font-size:15px}table{display:none}
 #ctl{left:6px;right:6px;max-width:none;bottom:42px;gap:4px}button{padding:6px 7px;font-size:11px}
 #tick{font-size:10px;padding:6px 8px}#ban{font-size:11px;padding:6px 10px}
}
#boot{position:absolute;inset:0;background:#02050c;z-index:99;padding:40px;box-sizing:border-box;color:#00f2fe;font-size:13px;transition:opacity 1s}
#bt{margin:0;font:inherit;line-height:1.8;text-shadow:0 0 8px #00f2fe}
#ctl{bottom:48px;left:12px;display:flex;gap:6px;flex-wrap:wrap;max-width:60%}
button{background:#0f1d36;color:#cfe9ff;border:1px solid #24527a;border-radius:6px;padding:8px 10px;
 cursor:pointer;font:inherit}
button:hover{background:#17335c}
button.r{border-color:#ef4444;color:#fca5a5}
#hud{top:58px;right:12px;width:290px;max-height:calc(100% - 130px);overflow:auto}
.k{display:flex;gap:8px;margin-bottom:8px}
.k div{flex:1;background:#0b1a33;border-radius:6px;padding:6px;text-align:center;color:#7fa6c9}
.k b{display:block;font-size:20px;color:#00f2fe}
.al{padding:5px 7px;margin:3px 0;border-radius:5px;background:#0b1a33;border-left:3px solid #00f2fe}
.al.warn{border-color:#f59e0b;color:#fcd34d}
.al.danger{border-color:#ef4444;color:#fca5a5;animation:p 1s infinite}
@keyframes p{50%{background:#3b0f14}}
table{width:100%;border-collapse:collapse;font-size:11px;margin-top:6px}
td,th{padding:2px 3px;text-align:left;border-bottom:1px solid #12273f}th{color:#5f86a8}
.sec{color:#5f86a8;margin:8px 0 3px;letter-spacing:1px}
</style></head><body>
<div id="map"></div>
<div id="haze"></div><div id="scan"></div><div id="vig"></div><div id="ban"></div>
<div id="boot"><pre id="bt"></pre></div>
<div id="top" class="panel">
 <span class="logo">🛡️ AEROSHIELD EG</span>
 <span class="pill"><i></i>RADAR ONLINE</span>
 <span class="pill"><i></i>UAV SWARM <b id="pu">0</b></span>
 <span class="pill"><i></i>SAT LINK</span>
 <span class="pill" id="hubn"></span>
 <span class="pill" id="wx">WX ...</span>
 <span id="lvl">THREAT LEVEL: NOMINAL</span>
 <span id="clk"></span>
</div>
<div id="tick" class="panel"><span id="tk"></span></div>
<div id="ctl" class="panel">
 <button class="r" onclick="act('hostile')">🔴 Hostile drone</button>
 <button class="r" onclick="act('swarm')">🐝 Swarm x10</button>
 <button onclick="act('tcas')">⚠️ TCAS</button>
 <button onclick="act('lost')">📡 Lost link</button>
 <button onclick="act('reset')">🔄 Reset</button>
 <button onclick="auto()" style="border-color:#00f2fe;color:#00f2fe">▶ AUTO DEMO</button>
</div>
<div id="hud" class="panel">
 <div class="k"><div>SHIELD<b id="sh">100%</b></div><div>TARGETS<b id="nt">0</b></div><div>LOW-ALT<b id="nz">0</b></div></div>
 <div class="sec">SECTORS</div><div id="sc"></div>
 <div class="sec">ALERTS</div><div id="al"></div>
 <div class="sec">TELEMETRY</div><table id="tb"></table>
</div>
<script>
const C = __CFG__;
const KM=111.32, hub=C.hub, cosH=Math.cos(hub.lat*Math.PI/180), Z=C.zscale;
const rad=d=>d*Math.PI/180, rnd=(a,b)=>a+Math.random()*(b-a);
const toLL=(km,b)=>{const r=rad(b);return [hub.lon+km*Math.sin(r)/(KM*cosH),hub.lat+km*Math.cos(r)/KM];};
const dist=e=>Math.hypot((e.lon-hub.lon)*KM*cosH,(e.lat-hub.lat)*KM);
const dd=(a,b)=>Math.hypot((a.lon-b.lon)*KM*cosH,(a.lat-b.lat)*KM);
const brg=e=>(Math.atan2((e.lon-hub.lon)*cosH,e.lat-hub.lat)*180/Math.PI+360)%360;
const ring=(km,z=0,n=72)=>Array.from({length:n+1},(_,i)=>{const p=toLL(km,i*360/n);return [p[0],p[1],z];});
const inz=e=>e.alt>=C.amin&&e.alt<=C.amax&&dist(e)<=C.zr;
const secOf=b=>(b>=315||b<45)?'N':b<135?'E':b<225?'S':'W';
function secThreat(){const o={N:0,E:0,S:0,W:0};ents.forEach(e=>{if(e.type==='rogue')o[secOf(brg(e))]++;});return o;}
const compass=d=>['N','NE','E','SE','S','SW','W','NW'][Math.round(d/45)%8];
const ringAt=(la,lo,km)=>Array.from({length:49},(_,i)=>{const r=rad(i*7.5);return [lo+km*Math.sin(r)/(KM*Math.cos(rad(la))),la+km*Math.cos(r)/KM,0];});
C.lm.forEach(m=>m.tip='<b>'+m.name+'</b><br>PROTECTED SITE');
const ann=['NOTAM: UAV activity authorised 50-150 m AGL inside the zone','Runway operations normal','Security sectors N / E / S / W: all posts manned','Counter-UAV RF jamming on standby'];
let wx=null;
fetch('https://api.open-meteo.com/v1/forecast?latitude='+hub.lat+'&longitude='+hub.lon+'&current=temperature_2m,wind_speed_10m,wind_direction_10m,visibility')
 .then(r=>r.json()).then(j=>{wx=j.current;}).catch(()=>{});
document.getElementById('haze').style.opacity=C.dust*0.6;
document.getElementById('hubn').textContent=hub.name+'  |  '+hub.lat.toFixed(4)+'N '+hub.lon.toFixed(4)+'E';

let ents=[],logs=[],T=0,sweep=0,tcas=false,ac,demo=[];
const HUBP={lat:hub.lat,lon:hub.lon};
function L(msg,lvl){const d=new Date().toTimeString().slice(0,8);logs.unshift({d,msg,lvl:lvl||''});logs=logs.slice(0,7);}
function mk(id,type,lat,lon,alt,hdg,spd,color,x){return Object.assign({id,type,lat,lon,alt,hdg,spd,color,c0:color,status:'NOMINAL',trail:[],seen:-99},x||{});}
function aimAt(e,t){e.hdg=(Math.atan2((t.lon-e.lon)*cosH,t.lat-e.lat)*180/Math.PI+360)%360;}
function move(e,dt){const s=e.spd/3600*dt*C.ts,r=rad(e.hdg);e.lat+=s*Math.cos(r)/KM;e.lon+=s*Math.sin(r)/(KM*cosH);}
function place(e,km,b){const p=toLL(km,b);e.lon=p[0];e.lat=p[1];const q=toLL(rnd(-6,6),rnd(0,360));aimAt(e,{lon:q[0],lat:q[1]});e.trail=[];}

function beep(k){try{ac=ac||new (window.AudioContext||window.webkitAudioContext)();
 const seq=k==='hostile'?[[950,0],[1200,.15],[950,.3],[1200,.45]]:k==='tcas'?[[880,0],[660,.2],[880,.4],[660,.6]]:[[520,0],[520,.3]];
 seq.forEach(([f,d])=>{const o=ac.createOscillator(),g=ac.createGain(),t=ac.currentTime+d;
  o.type=k==='hostile'?'square':'sawtooth';o.frequency.value=f;g.gain.setValueAtTime(.25,t);
  g.gain.exponentialRampToValueAtTime(.001,t+.15);o.connect(g);g.connect(ac.destination);o.start(t);o.stop(t+.16);});}catch(e){}}

function focus(la,lo,z,p,b){deckgl.setProps({initialViewState:{longitude:lo,latitude:la,zoom:z,pitch:p,bearing:b,maxPitch:80,transitionDuration:2500,transitionInterpolator:new deck.FlyToInterpolator()}});}
function auto(){demo.forEach(clearTimeout);demo=[];init();focus(hub.lat,hub.lon,C.zoom,62,-25);
 [[2,()=>act('hostile')],[72,()=>act('tcas')],[92,()=>act('lost')],[105,()=>act('swarm')],[170,()=>{L('Demo complete - airspace secure');focus(hub.lat,hub.lon,C.zoom,62,-25);}]]
  .forEach(([t,f])=>demo.push(setTimeout(f,t*1000)));}
function init(){
 ents=[];logs=[];tcas=false;
 [['MSR-702',2800,420,[0,242,254]],['DLH-580',3900,510,[0,255,157]],['UAE-923',7500,680,[0,242,254]],
  ['AFR-504',1800,310,[168,85,247]],['SVA-114',5200,560,[234,179,8]]].slice(0,Math.max(3,C.nair)).forEach(a=>{
   const e=mk(a[0],'air',0,0,a[1],0,a[2],a[3]);place(e,rnd(10,48),rnd(0,360));ents.push(e);});
 const pre=['THY','QTR','ETD','KLM','BAW','RJA','MSC','KAC','GFA','FDB'],pal=[[0,242,254],[0,255,157],[168,85,247],[234,179,8]];
 for(let i=5;i<C.nair;i++){const e=mk(pre[i%10]+'-'+Math.floor(rnd(100,999)),'air',0,0,rnd(1500,10000),0,rnd(300,800),pal[i%4]);place(e,rnd(8,48),rnd(0,360));ents.push(e);}
 [['UAV-ALPHA',60,.9,0,'Runway thermal scan'],['UAV-BETA',90,1.6,120,'Perimeter patrol'],['UAV-GAMMA',130,2.4,240,'Aero-radar picket']]
  .forEach(d=>ents.push(mk(d[0],'uav',hub.lat,hub.lon,d[1],0,40,[0,255,157],{orb:d[2],ang:d[3],base:d[1],task:d[4]})));
 L('Shield online - airspace secure');
}

function act(k){
 if(k==='reset'){demo.forEach(clearTimeout);demo=[];init();return;}
 if(k==='swarm'){
  if(ents.some(e=>e.id.startsWith('SWARM')))return;
  const b0=rnd(0,360);
  for(let i=0;i<10;i++){const e=mk('SWARM-'+String(i+1).padStart(2,'0'),'rogue',0,0,rnd(60,140),0,rnd(220,270),[239,68,68],{status:'SWARM'});
   const p=toLL(30+rnd(-1.5,1.5),b0+rnd(-14,14));e.lon=p[0];e.lat=p[1];aimAt(e,HUBP);ents.push(e);}
  L('SWARM: 10 unidentified drones, bearing '+Math.round(b0)+' deg','danger');beep('hostile');
  focus(hub.lat,hub.lon,Math.max(C.zoom,10),62,b0);return;}
 if(k==='hostile'){
  if(ents.some(e=>e.id==='UNKNOWN-09'))return;
  const e=mk('UNKNOWN-09','rogue',0,0,rnd(70,120),0,260,[239,68,68],{status:'NO TRANSPONDER'});
  const p=toLL(30,rnd(0,360));e.lon=p[0];e.lat=p[1];aimAt(e,HUBP);ents.push(e);focus(hub.lat,hub.lon,Math.max(C.zoom,10.5),65,rnd(-60,60));
  L('RADAR CONTACT: unknown low-alt drone, no transponder','danger');beep('hostile');return;}
 const a=ents.find(e=>e.id==='MSR-702'),b=ents.find(e=>e.id==='DLH-580');
 if(k==='tcas'&&a&&b){
  let p=toLL(5,90);a.lon=p[0];a.lat=p[1];a.hdg=270;a.alt=3100;
  p=toLL(5,270);b.lon=p[0];b.lat=p[1];b.hdg=90;b.alt=3120;a.trail=[];b.trail=[];
  [a,b].forEach(x=>{x.color=[239,68,68];x.status='TCAS WARN';});tcas=true;
  L('TCAS conflict MSR-702 / DLH-580','danger');beep('tcas');}
 if(k==='lost'&&a){
  a.status='LOST LINK';a.color=[245,158,11];
  ents.push(mk('SAR-01','uav',hub.lat,hub.lon,100,0,400,[255,170,0],{chase:'MSR-702',task:'SAR vector',status:'SAR'}));
  L('MSR-702 lost link - SAR drone dispatched','warn');beep('lost');}
}

function step(dt){
 T+=dt;sweep=(sweep+C.rpm*6*dt)%360;
 const rogue=ents.find(e=>e.type==='rogue');
 ents.forEach(e=>{
  if(e.orb){e.ang+=35*dt;const p=toLL(e.orb,e.ang);e.lon=p[0];e.lat=p[1];e.hdg=(e.ang+90)%360;e.alt=e.base+8*Math.sin(T*1.3+e.orb);}
  else if(e.chase){
   const t=ents.find(x=>x.id===e.chase);
   if(!t){e.chase=null;e.ttl=T+5;e.status='RTB';}
   else{aimAt(e,t);e.alt+=Math.max(-40*dt,Math.min(40*dt,t.alt-e.alt));
    if(dd(e,t)>0.2)move(e,dt);
    else if(t.type==='rogue'){ents=ents.filter(x=>x!==t);e.chase=null;e.ttl=T+6;e.status='JAMMED - NEUTRALIZED';
     L('TARGET NEUTRALIZED (RF jamming)','');beep('lost');}}}
  else{
   if(e.type==='rogue'){aimAt(e,HUBP);
    const d=dist(e);
    if(d<20&&!e.f20){e.f20=1;L('Threat inside 20 km tactical zone','warn');}
    if(d<6&&!e.fl){e.fl=1;ents.push(mk('INT-'+e.id.slice(-2),'uav',hub.lat,hub.lon,20,0,220,[255,255,255],{chase:e.id,status:'ENGAGING',task:'Intercept'}));
     L('Interceptor scrambled','warn');beep('lost');}
    if(d<0.3){L('PERIMETER BREACH','danger');ents=ents.filter(x=>x!==e);}}
   move(e,dt);
   if(e.type==='air'&&dist(e)>62)place(e,55,rnd(0,360));
   const z=e.type!=='uav'&&inz(e);
   if(z&&!e.inz){e.inz=true;L(e.id+' entered low-alt zone '+C.amin+'-'+C.amax+'m','danger');}
   if(!z)e.inz=false;}
  if(e.type!=='uav'||e.chase){const d=((sweep-brg(e))+360)%360;if(d<10)e.seen=T;}
  if(Math.floor(T*20)!==e.lt){e.lt=Math.floor(T*20);e.trail.push([e.lon,e.lat,e.alt*Z]);if(e.trail.length>50)e.trail.shift();}
  e.tip='<b>'+e.id+'</b><br>ALT '+Math.round(e.alt)+' m<br>SPD '+Math.round(e.spd)+' km/h<br>'+e.status;
 });
 ents=ents.filter(e=>!(e.ttl&&T>e.ttl));
 if(tcas){const a=ents.find(e=>e.id==='MSR-702'),b=ents.find(e=>e.id==='DLH-580');
  if(a&&b){a.alt+=25*dt;b.alt-=25*dt;if(a.alt-b.alt>350){tcas=false;[a,b].forEach(x=>{x.color=x.c0;x.status='RESOLVED';});L('TCAS resolved - separation restored');}}}
}

const tile=(id,url)=>new deck.TileLayer({id,data:url,minZoom:0,maxZoom:18,tileSize:256,
 renderSubLayers:p=>{const b=p.tile.bbox;return new deck.BitmapLayer(p,{data:null,image:p.data,bounds:[b.west,b.south,b.east,b.north],parameters:{depthTest:false}});}});
const flat={depthTest:false};
const ESRI='https://server.arcgisonline.com/ArcGIS/rest/services/';
function layers(){
 const out=[];
 out.push(tile('base',C.sat?ESRI+'World_Imagery/MapServer/tile/{z}/{y}/{x}':'https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png'));
 if(C.labels&&C.sat)out.push(tile('lbl',ESRI+'Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}'));
 if(C.roads&&C.sat)out.push(tile('rd',ESRI+'Reference/World_Transportation/MapServer/tile/{z}/{y}/{x}'));
 if(C.sectors){const th=secThreat(),pl=0.5+0.5*Math.sin(T*5);
  const wd=['N','E','S','W'].map((k,i)=>{const pts=[[hub.lon,hub.lat]];for(let a=i*90-45;a<=i*90+45;a+=9)pts.push(toLL(50,a));
   return {p:pts,c:th[k]?[239,68,68,Math.round(35+45*pl)]:[0,242,254,12]};});
  out.push(new deck.PolygonLayer({id:'sec',data:wd,getPolygon:d=>d.p,getFillColor:d=>d.c,stroked:false,parameters:flat}));
  out.push(new deck.PathLayer({id:'secl',data:[45,135,225,315],getPath:a=>[[hub.lon,hub.lat],toLL(50,a)],getColor:[0,242,254,120],widthMinPixels:1,parameters:flat}));
  const posts=[['N',0],['E',90],['S',180],['W',270]].map(([k,a])=>{const p=toLL(12,a);return {lon:p[0],lat:p[1],k,t:th[k]};});
  out.push(new deck.ScatterplotLayer({id:'post',data:posts,getPosition:d=>[d.lon,d.lat,0],getRadius:500,radiusMinPixels:8,getFillColor:d=>d.t?[239,68,68]:[0,242,254],stroked:true,getLineColor:[255,255,255],lineWidthMinPixels:2,parameters:flat}));
  out.push(new deck.TextLayer({id:'postt',data:posts,getPosition:d=>[d.lon,d.lat,0],getText:d=>d.k+' SECTOR POST',getSize:11,getColor:[255,255,255],getPixelOffset:[0,-16],fontFamily:'Menlo,monospace',outlineWidth:2,outlineColor:[0,0,0,255],fontSettings:{sdf:true},parameters:flat}));}
 if(C.sites){
  out.push(new deck.PathLayer({id:'lmr',data:C.lm,getPath:m=>ringAt(m.lat,m.lon,1.2),getColor:[255,200,60,230],widthMinPixels:2,parameters:flat}));
  out.push(new deck.ScatterplotLayer({id:'lmd',data:C.lm,pickable:true,getPosition:m=>[m.lon,m.lat,0],getRadius:200,radiusMinPixels:7,getFillColor:[255,200,60],stroked:true,getLineColor:[255,255,255],lineWidthMinPixels:2,parameters:flat}));
  out.push(new deck.TextLayer({id:'lmt',data:C.lm,getPosition:m=>[m.lon,m.lat,0],getText:m=>'🏛 '+m.name,getSize:12,getColor:[255,230,150],getPixelOffset:[0,-18],fontFamily:'Menlo,monospace',outlineWidth:2,outlineColor:[0,0,0,255],fontSettings:{sdf:true},parameters:flat}));}
 // range rings
 const rings=[[10,[0,242,254,90]],[20,[245,158,11,230]],[30,[0,242,254,90]],[40,[0,242,254,90]],[50,[239,68,68,230]]];
 out.push(new deck.PathLayer({id:'rings',data:rings,getPath:r=>ring(r[0]),getColor:r=>r[1],widthMinPixels:2,parameters:flat}));
 out.push(new deck.TextLayer({id:'ringt',data:rings,getPosition:r=>{const p=toLL(r[0],0);return [p[0],p[1],0];},getText:r=>r[0]+' km',
  getSize:11,getColor:[255,255,255,220],fontFamily:'Menlo,monospace',outlineWidth:2,outlineColor:[0,0,0,255],fontSettings:{sdf:true},parameters:flat}));
 // radar sweep wedge with fading trail
 const wedge=[];for(let i=0;i<16;i++){const a1=sweep-i*3,a0=a1-3,pts=[[hub.lon,hub.lat]];
  for(let k=0;k<=3;k++){pts.push(toLL(50,a0+(a1-a0)*k/3));}wedge.push({p:pts,a:Math.round(95*(1-i/16))});}
 out.push(new deck.PolygonLayer({id:'wedge',data:wedge,getPolygon:d=>d.p,getFillColor:d=>[0,255,120,d.a],stroked:false,parameters:flat}));
 out.push(new deck.PathLayer({id:'sweep',data:[0],getPath:()=>[[hub.lon,hub.lat],toLL(50,sweep)],getColor:[120,255,170,255],widthMinPixels:2,parameters:flat}));
 // blips (lit when sweep passes, then fade)
 const per=60/C.rpm,bl=ents.filter(e=>T-e.seen<per);
 out.push(new deck.ScatterplotLayer({id:'blips',data:bl,getPosition:e=>[e.lon,e.lat,0],radiusMinPixels:5,getRadius:350,
  getFillColor:e=>{const a=Math.max(0,1-(T-e.seen)/per);return e.type==='rogue'?[255,60,60,255*a]:[120,255,170,255*a];},parameters:flat}));
 // low-alt cage
 if(C.zone){const a=C.amin*Z,b=C.amax*Z;
  out.push(new deck.PolygonLayer({id:'zt',data:[0],getPolygon:()=>ring(C.zr,b),getFillColor:[168,85,247,30],getLineColor:[168,85,247,255],lineWidthMinPixels:2,parameters:flat}));
  out.push(new deck.PolygonLayer({id:'zb',data:[0],getPolygon:()=>ring(C.zr,a),getFillColor:[0,255,157,30],getLineColor:[0,255,157,255],lineWidthMinPixels:2,parameters:flat}));
  const w=Array.from({length:24},(_,i)=>{const p=toLL(C.zr,i*15);return [[p[0],p[1],a],[p[0],p[1],b]];});
  out.push(new deck.PathLayer({id:'zw',data:w,getPath:d=>d,getColor:[0,255,157,110],widthMinPixels:1,parameters:flat}));}
 // other airports
 out.push(new deck.ScatterplotLayer({id:'apt',data:C.airports,getPosition:a=>[a.lon,a.lat,0],getRadius:1500,radiusMinPixels:5,getFillColor:[0,242,254,180],stroked:true,getLineColor:[255,255,255],lineWidthMinPixels:1,parameters:flat}));
 out.push(new deck.TextLayer({id:'aptt',data:C.airports,getPosition:a=>[a.lon,a.lat,0],getText:a=>a.code,getSize:12,getColor:[255,255,255],getPixelOffset:[0,-14],fontFamily:'Menlo,monospace',outlineWidth:2,outlineColor:[0,0,0,255],fontSettings:{sdf:true},parameters:flat}));
 // entities
 out.push(new deck.PathLayer({id:'trail',data:ents,getPath:e=>e.trail,getColor:e=>e.color.concat([140]),widthMinPixels:2,parameters:flat}));
 out.push(new deck.LineLayer({id:'stem',data:ents,getSourcePosition:e=>[e.lon,e.lat,0],getTargetPosition:e=>[e.lon,e.lat,e.alt*Z],getColor:e=>e.color.concat([160]),getWidth:1,parameters:flat}));
 out.push(new deck.LineLayer({id:'lead',data:ents,getSourcePosition:e=>[e.lon,e.lat,e.alt*Z],getTargetPosition:e=>{const r=rad(e.hdg),k=e.type==='air'?2.5:0.35;return [e.lon+k*Math.sin(r)/(KM*cosH),e.lat+k*Math.cos(r)/KM,e.alt*Z];},getColor:e=>e.color,getWidth:3,parameters:flat}));
 const eng=ents.filter(e=>e.chase&&ents.find(x=>x.id===e.chase&&x.type==='rogue'));
 out.push(new deck.LineLayer({id:'eng',data:eng,getSourcePosition:e=>[e.lon,e.lat,e.alt*Z],getTargetPosition:e=>{const t=ents.find(x=>x.id===e.chase);return [t.lon,t.lat,t.alt*Z];},getColor:[255,60,60],getWidth:3,parameters:flat}));
 const pulse=2+Math.abs(Math.sin(T*4))*2;
 out.push(new deck.ScatterplotLayer({id:'thr',data:ents.filter(e=>e.type==='rogue'),getPosition:e=>[e.lon,e.lat,e.alt*Z],getRadius:200*pulse,radiusMinPixels:12,filled:false,stroked:true,getLineColor:[255,60,60],lineWidthMinPixels:2,parameters:flat,updateTriggers:{getRadius:T}}));
 out.push(new deck.ScatterplotLayer({id:'dots',data:ents,pickable:true,getPosition:e=>[e.lon,e.lat,e.alt*Z],getRadius:e=>e.type==='air'?90:45,radiusMinPixels:7,
  getFillColor:e=>e.type==='uav'?[255,255,255]:e.color,stroked:true,getLineColor:e=>e.type==='uav'?[0,255,157]:[255,255,255],lineWidthMinPixels:2,parameters:flat}));
 out.push(new deck.TextLayer({id:'lbl2',data:ents,getPosition:e=>[e.lon,e.lat,e.alt*Z],getText:e=>e.id,getSize:12,getColor:[235,245,255],getPixelOffset:[0,-18],fontFamily:'Menlo,monospace',outlineWidth:2,outlineColor:[0,0,0,255],fontSettings:{sdf:true},parameters:flat}));
 return out;
}

const deckgl=new deck.Deck({parent:document.getElementById('map'),controller:true,views:[new deck.MapView({repeat:true})],
 initialViewState:{longitude:hub.lon,latitude:hub.lat,zoom:C.zoom,pitch:62,bearing:-25,maxPitch:80},
 getTooltip:({object})=>object&&object.tip?{html:object.tip,style:{background:'#0f172a',color:'#00f2fe',border:'1px solid #00f2fe',fontFamily:'Menlo,monospace',fontSize:'12px'}}:null,
 layers:[]});

let hudT=0;
function hud(){
 const nr=ents.filter(e=>e.type==='rogue').length,rg=nr>0,zn=ents.filter(inz).length;
 const sh=100-(rg?Math.min(55,20+nr*4):0)-(tcas?20:0)-(ents.some(e=>e.status==='LOST LINK')?10:0);
 const hot=rg||tcas,lv=document.getElementById('lvl'),bn=document.getElementById('ban');
 lv.textContent=hot?'THREAT LEVEL: CRITICAL':'THREAT LEVEL: NOMINAL';lv.className=hot?'hi':'';
 document.getElementById('vig').className=hot?'on':'';
 bn.style.display=hot?'block':'none';bn.textContent=rg?'⚠ '+nr+' HOSTILE DRONE(S) - COUNTER-UAV ENGAGED':'⚠ TCAS CONFLICT';
 document.getElementById('clk').textContent=new Date().toISOString().slice(11,19)+' UTC';
 document.getElementById('pu').textContent=ents.filter(e=>e.type==='uav').length;
 const th=secThreat();
 document.getElementById('sc').innerHTML=['N','E','S','W'].map(k=>'<span class="pill" style="margin-right:4px;'+(th[k]?'color:#fca5a5;border-color:#ef4444':'')+'">'+k+' '+(th[k]?th[k]+' THREAT':'CLEAR')+'</span>').join('');
 const vis=((wx&&wx.visibility!=null?wx.visibility/1000:10)*(1-0.8*C.dust)).toFixed(1);
 document.getElementById('wx').textContent=wx?(Math.round(wx.temperature_2m)+'°C · wind '+Math.round(wx.wind_speed_10m)+' km/h '+compass(wx.wind_direction_10m)+' · vis '+vis+' km'):('WX (sim) · vis '+vis+' km');
 document.getElementById('tk').textContent='📢 '+(hot&&logs[0]?logs[0].msg:ann[Math.floor(T/8)%ann.length])+'   [SIMULATED FEED]';
 document.getElementById('sh').textContent=sh+'%';
 document.getElementById('sh').style.color=sh>75?'#00f2fe':'#ef4444';
 document.getElementById('nt').textContent=ents.filter(e=>e.type!=='uav').length;
 document.getElementById('nz').textContent=zn;
 document.getElementById('al').innerHTML=logs.map(l=>'<div class="al '+l.lvl+'">'+l.d+' '+l.msg+'</div>').join('');
 document.getElementById('tb').innerHTML='<tr><th>ID</th><th>ALT</th><th>SPD</th><th>STATUS</th></tr>'+
  ents.slice().sort((a,b)=>(b.type==='rogue')-(a.type==='rogue')).slice(0,14).map(e=>'<tr><td>'+e.id+'</td><td>'+Math.round(e.alt)+'</td><td>'+Math.round(e.spd)+'</td><td>'+e.status+'</td></tr>').join('');
}
init();
const bl=['AEROSHIELD EG v2.0 - BOOT SEQUENCE','[ OK ] Satellite imagery link (ESRI World Imagery)','[ OK ] Radar array calibration ........ 50 km','[ OK ] UAV defense swarm handshake .... 3 units','[ OK ] ADS-B transponder feed ......... ONLINE','[ OK ] Threat classifier .............. READY','>> SYSTEM ARMED - '+hub.name.toUpperCase()];
let bi=0;const bt=document.getElementById('bt');
const bin=setInterval(()=>{bt.textContent+=bl[bi++]+'\n';if(bi>=bl.length){clearInterval(bin);setTimeout(()=>{const b=document.getElementById('boot');b.style.opacity=0;setTimeout(()=>b.remove(),1000);},700);}},380);
let last=performance.now();
function loop(now){const dt=Math.min(.1,(now-last)/1000);last=now;step(dt);
 hudT+=dt;if(hudT>.3){hudT=0;hud();}
 deckgl.setProps({layers:layers()});requestAnimationFrame(loop);}
requestAnimationFrame(loop);
</script></body></html>
"""

components.html(HTML.replace("__CFG__", json.dumps(cfg)), height=900, scrolling=False)
st.caption("Imagery © Esri, Maxar, Earthstar Geographics · Simulation / training platform – not a real tracking system.")
