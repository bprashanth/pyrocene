import {alternatives,beforeFire,planStory,TIME_CHOICES,timeOutcome,timeStory,fieldPlots,planHinges} from './cooperation-projection.mjs';
const NS='http://www.w3.org/2000/svg';
const tag=(name,attrs={},text='')=>{const n=document.createElementNS(NS,name);for(const [k,v]of Object.entries(attrs))n.setAttribute(k,v);n.textContent=text;return n;};
const same=(a,b)=>['ecology','removal','community'].every(k=>a[k]===b[k]);
const describe=p=>`Restore ${p.ecology}, remove ${p.removal}, ${p.community==='A'?'nursery A':p.community==='B'?'coffee B':'grazing C'}.`;
const extent=values=>{const lo=Math.min(0,...values),hi=Math.max(0,...values),pad=Math.max(1,hi-lo)*.06;return [lo-pad,hi+pad];};
export function chartBounds(points){
 const [xmin,xmax]=extent(points.map(p=>p.earnings)),[ymin,ymax]=extent(points.map(p=>p.healthChange));
 return {xmin,xmax,ymin,ymax};
}
export function createCooperationRecap(forest,onPlay){
 const dialog=document.createElement('dialog');dialog.id='cooperation-recap';dialog.setAttribute('aria-label','Prelude I');document.body.append(dialog);
 let committed,selected,choice='sequence',spacePlan,yaw=.48,pitch=.3,hinge=2,example=false;
 const $=id=>dialog.querySelector('#'+id);
 const story=paragraphs=>{$('recap-story').replaceChildren(...paragraphs.map(text=>{const p=document.createElement('p');p.textContent=text;return p;}));};
 const close=()=>dialog.close();
 function showPlan(plan){
  selected=plan;const result=beforeFire(plan);
  story(planStory(plan));$('recap-plan').textContent=describe(plan);
  $('recap-values').textContent=`Net earnings: ${result.earnings.toFixed(1)} credits. Forest health: ${result.healthChange>=0?'+':''}${result.healthChange.toFixed(1)} points.`;
  for(const dot of dialog.querySelectorAll('#earnings-health circle')){const active=dot.dataset.plan===plan.ecology+plan.removal+plan.community;dot.setAttribute('stroke',active?'#e8f2e9':'#071b13');dot.setAttribute('aria-pressed',String(active));}
 }
 function showFirst(){
  dialog.dataset.page='one';
  dialog.setAttribute('aria-label','Prelude I');
  dialog.innerHTML=`<section class="prelude-copy"><small>PRELUDE I</small><h1>What does the group gain?</h1>
   <div id="recap-story" aria-live="polite"></div>
   <details class="graph-about"><summary>About this graph</summary><p>Choose a dot to explore the plan. Higher means healthier forest; farther right means more group earnings. Yellow is ${example?'an example plan':'your committed plan'}.</p></details>
   ${example?'<small>Showing an example plan.</small>':''}
   <div class="prelude-nav"><button id="recap-one-back">Back to map</button><button class="primary" id="recap-time-open">Prelude II: time</button></div></section>
   <figure><svg id="earnings-health" viewBox="0 0 520 390" role="group" aria-label="Ten-year net group earnings versus change in forest health before fire"></svg><figcaption id="recap-plan"></figcaption><p id="recap-values"></p><small>Ten years, without wildfire. Earnings exclude the starting grant and include saved feed costs.</small></figure>`;
  $('recap-one-back').onclick=close;$('recap-time-open').onclick=()=>{choice='sequence';showTime();};
  const svg=$('earnings-health'),points=alternatives(),{xmin,xmax,ymin,ymax}=chartBounds(points);
  const x=v=>65+(v-xmin)/(xmax-xmin)*410,y=v=>325-(v-ymin)/(ymax-ymin)*265;
  for(let v=Math.ceil(xmin/5)*5;v<=xmax;v+=5)svg.append(tag('line',{x1:x(v),y1:60,x2:x(v),y2:325,stroke:'#254234'}),tag('text',{x:x(v),y:347,'text-anchor':'middle'},String(v)));
  for(let v=Math.ceil(ymin/2)*2;v<=ymax;v+=2)svg.append(tag('line',{x1:65,y1:y(v),x2:475,y2:y(v),stroke:'#254234'}),tag('text',{x:52,y:y(v)+4,'text-anchor':'end'},String(v)));
  svg.append(tag('line',{x1:x(0),y1:60,x2:x(0),y2:325,stroke:'#93a993','stroke-dasharray':'3 4'}),tag('line',{x1:65,y1:y(0),x2:475,y2:y(0),stroke:'#93a993','stroke-dasharray':'3 4'}));
  svg.append(tag('text',{x:270,y:378,'text-anchor':'middle'},'Net group earnings (credits)'),tag('text',{x:65,y:27},'Forest health change (points)'));
  for(const entry of points.sort((a,b)=>Number(same(a.plan,committed))-Number(same(b.plan,committed)))){
   const own=same(entry.plan,committed),dot=tag('circle',{cx:x(entry.earnings),cy:y(entry.healthChange),r:own?7:4.5,fill:own?'#e3c879':'#77aa90',stroke:'#071b13','stroke-width':2,tabindex:0,role:'button','aria-label':describe(entry.plan),'data-plan':entry.plan.ecology+entry.plan.removal+entry.plan.community});
   dot.append(tag('title',{},describe(entry.plan)));dot.onfocus=dot.onclick=()=>showPlan(entry.plan);
   dot.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();showPlan(entry.plan);}};svg.append(dot);
  }
  showPlan(selected||committed);mountMap();
 }
 function showTime(){
  dialog.dataset.page='time';
  dialog.setAttribute('aria-label','Prelude II: time');
  dialog.innerHTML=`<section class="prelude-copy"><small>PRELUDE II / TIME</small><h1>What if we do this in steps?</h1>
   <p>Keep removal and restoration in A. Coffee uses B, so it does not replace the native planting.</p>
   <div id="recap-story" aria-live="polite"></div>
   <canvas id="recap-map" width="420" height="270" role="img" aria-label="Overhead forest map. A: native restoration and nursery order. B: coffee. C: pasture."></canvas>
   <small class="recap-map-key">A: restoration / nursery order<br>B: coffee &nbsp; C: pasture</small>
   <div class="prelude-nav"><button id="recap-one-return">Back</button><button class="primary" id="recap-space-open">Prelude III: possibilities</button></div></section>
   <figure><div id="time-choices" aria-label="Compare timing"></div>
   <svg id="recap-time-chart" viewBox="0 0 620 440" role="img" aria-label="Community income each year and forest health over ten years"></svg>
   <p id="recap-values"></p><small>Income each year after routine care, not savings. Set-up costs are shown separately. Replacement orders need buyers. No wildfire or failed harvest is included.</small></figure>`;
  $('recap-one-return').onclick=showFirst;$('recap-space-open').onclick=()=>{spacePlan={...selected};hinge=2;showSpace();};
  for(const item of TIME_CHOICES){const b=document.createElement('button');b.textContent=item.name;b.dataset.choice=item.id;b.style.setProperty('--line-colour',item.colour);b.onclick=()=>{choice=item.id;drawTime();};$('time-choices').append(b);}
  drawMap();drawTime();
 }
 function drawTime(){
  const svg=$('recap-time-chart');svg.replaceChildren();story(timeStory(choice));
  for(const b of $('time-choices').children)b.setAttribute('aria-pressed',String(b.dataset.choice===choice));
  const samples=Array.from({length:101},(_,i)=>i/10);samples.push(2.999);samples.sort((a,b)=>a-b);
  const series=TIME_CHOICES.map(c=>({...c,points:samples.map(y=>({year:y,...timeOutcome(c.id,y)}))})),x=y=>60+y/10*530;
  const panels=[{field:'annualIncome',top:45,bottom:172,label:'Community income each year (credits)'},{field:'healthChange',top:252,bottom:379,label:'Forest health change (points)'}];
  for(const panel of panels){
   const [min,max]=extent(series.flatMap(s=>s.points.map(p=>p[panel.field]))),y=v=>panel.bottom-(v-min)/(max-min)*(panel.bottom-panel.top);
   svg.append(tag('text',{x:60,y:panel.top-19},panel.label));
   for(let t=0;t<=10;t+=2)svg.append(tag('line',{x1:x(t),y1:panel.top,x2:x(t),y2:panel.bottom,stroke:'#254234'}),tag('text',{x:x(t),y:panel.bottom+18,'text-anchor':'middle'},String(t)));
   const step=panel.field==='annualIncome'?2:5;
   for(let v=Math.ceil(min/step)*step;v<=max;v+=step)svg.append(tag('line',{x1:60,y1:y(v),x2:590,y2:y(v),stroke:v===0?'#93a993':'#254234','stroke-dasharray':v===0?'3 4':'none'}),tag('text',{x:47,y:y(v)+4,'text-anchor':'end'},String(v)));
   for(const s of [...series].sort((a,b)=>Number(a.id===choice)-Number(b.id===choice))){
    const d=s.points.map((p,i)=>(i?'L':'M')+x(p.year)+','+y(p[panel.field])).join(' ');
    svg.append(tag('path',{d,fill:'none',stroke:s.colour,'stroke-width':s.id===choice?2.8:1.6,opacity:s.id===choice?1:.45,'data-series':s.id}));
   }
   svg.append(tag('circle',{cx:x(10),cy:y(timeOutcome(choice,10)[panel.field]),r:4,fill:TIME_CHOICES.find(c=>c.id===choice).colour}));
  }
  svg.append(tag('text',{x:325,y:433,'text-anchor':'middle'},'Years after the first work'));
  const current=timeOutcome(choice,10),setup=choice==='coffee'?'6 credits now':choice==='nursery'?'2 credits now':'2 credits now + 6 in year three';
  $('recap-values').textContent=`Set-up: ${setup}. Year ten income: ${current.annualIncome.toFixed(1)} credits a year.`;
 }
 function drawMap(){
  const canvas=$('recap-map'),ctx=canvas.getContext('2d'),pos=forest?.geometry?.attributes.position.array,raw=forest?.airborneSource;
  const n=pos?pos.length/3:(raw?.length||0)/4,side=246,left=(canvas.width-side)/2,top=12;
  const x=v=>left+(v+450)/900*side,z=v=>top+(v+450)/900*side;
  ctx.fillStyle='#06150f';ctx.fillRect(0,0,canvas.width,canvas.height);
  for(let i=0;i<n;i+=Math.max(1,Math.ceil(n/90000))){
   const px=pos?pos[i*3]:raw[i*4],pz=pos?pos[i*3+2]:-raw[i*4+1],h=pos?pos[i*3+1]:raw[i*4+2];
   ctx.fillStyle=h<.2?'#3899ab':h<2?'#d1407a':h<10?'#2978a8':'#80bfa0';ctx.globalAlpha=.6;ctx.fillRect(x(px),z(pz),1,1);
  }
  ctx.globalAlpha=1;ctx.strokeStyle='#e3c879';ctx.lineWidth=1.5;ctx.font='bold 17px monospace';
  for(const [label,id]of [['A',13],['B',22],['C',27]]){
   const px=x(id%6*150-450),pz=z(Math.floor(id/6)*150-450);
   ctx.strokeRect(px,pz,side/6,side/6);ctx.fillStyle='#06150f';ctx.fillRect(px+3,pz+3,21,23);ctx.fillStyle='#ffe39d';ctx.fillText(label,px+8,pz+20);
  }
 }
 function mountMap(){
  const canvas=document.createElement('canvas');canvas.id='recap-map';canvas.width=420;canvas.height=270;canvas.setAttribute('role','img');canvas.setAttribute('aria-label','Overhead forest reference map with plots A, B and C.');
  const nav=dialog.querySelector('.prelude-nav');nav.before(canvas);drawMap();
 }
 function selectSpacePlan(plan){spacePlan=plan;hinge=2;drawSpace();}
 function showSpace(){
  dialog.dataset.page='space';dialog.setAttribute('aria-label','Prelude III: possibilities');
  dialog.innerHTML=`<section class="prelude-copy"><small>PRELUDE III / POSSIBILITIES</small><h1>How much can we keep tending?</h1>
   <details class="graph-about"><summary>About this graph</summary><p>These are the same 21 plans from Prelude I, now at the start, year five and year ten. Follow one to see how early costs and later returns change its position. Depth shows time, so a downward turn on screen need not mean lower returns. The axes show group earnings and forest health. Unlike Prelude II, earnings here include costs and accumulate over time. No wildfire is included.</p></details>
   <div id="hinge-choices" aria-label="Turning points"></div><strong id="hinge-title"></strong><div id="recap-story" aria-live="polite"></div><p id="recap-work"></p>
   <div class="prelude-nav"><button id="recap-time-return">Back</button><button class="primary" id="recap-play">Play game</button></div></section>
   <figure><label class="space-select" for="recap-space-plan">Follow a plan <select id="recap-space-plan"></select></label>
   <svg id="recap-space-chart" viewBox="0 0 620 480" role="group" tabindex="0" aria-label="Plans through time. Drag or use arrow keys to turn the graph. Choose a dot to follow a plan."></svg>
   <div class="space-legend"><span style="--line-colour:#8dbb9e">1 field plot</span><span style="--line-colour:#7db5ce">2 field plots</span><span style="--line-colour:#ce93ae">3 field plots</span></div>
   <p id="recap-values"></p><small>Drag to turn - numbered points explain the changes. Colours count field plots to tend; nursery production is off-map.</small></figure>`;
  $('recap-time-return').onclick=showTime;$('recap-play').onclick=()=>{close();onPlay?.();};
  for(const {plan}of alternatives()){const option=document.createElement('option');option.value=plan.ecology+plan.removal+plan.community;option.textContent=describe(plan);$('recap-space-plan').append(option);}
  $('recap-space-plan').onchange=()=>{const [ecology,removal,community]=$('recap-space-plan').value;selectSpacePlan({ecology,removal,community});};
  const activate=target=>{const h=target.closest('[data-hinge]')?.dataset.hinge,key=target.closest('[data-plan]')?.dataset.plan;if(h!==undefined){hinge=Number(h);drawSpace();}else if(key){const [ecology,removal,community]=key;selectSpacePlan({ecology,removal,community});}};
  const svg=$('recap-space-chart');let drag=null,moved=false;
  svg.onpointerdown=e=>{if(e.button!==0)return;drag={x:e.clientX,y:e.clientY,target:e.target};moved=false;svg.setPointerCapture(e.pointerId);};
  svg.onpointermove=e=>{if(!drag)return;const dx=e.clientX-drag.x,dy=e.clientY-drag.y;if(Math.abs(dx)+Math.abs(dy)<3)return;moved=true;yaw=Math.max(-.85,Math.min(.85,yaw+dx*.005));pitch=Math.max(.12,Math.min(.6,pitch+dy*.004));drag={...drag,x:e.clientX,y:e.clientY};drawSpace(false);};
  svg.onpointerup=e=>{const target=!moved&&drag?.target;drag=null;if(svg.hasPointerCapture(e.pointerId))svg.releasePointerCapture(e.pointerId);if(target)activate(target);};svg.onpointercancel=()=>{drag=null;};
  // Assistive technology can activate a point without a pointer sequence.
  svg.onclick=e=>{if(e.detail===0){activate(e.target);svg.focus();}};
  svg.onkeydown=e=>{
   if(e.key==='Enter'||e.key===' '){e.preventDefault();activate(e.target);svg.focus();return;}
   if(!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','Home'].includes(e.key))return;e.preventDefault();
   if(e.key==='Home'){yaw=.48;pitch=.3;}else if(e.key==='ArrowLeft'||e.key==='ArrowRight')yaw=Math.max(-.85,Math.min(.85,yaw+(e.key==='ArrowLeft'?-.1:.1)));else pitch=Math.max(.12,Math.min(.6,pitch+(e.key==='ArrowUp'?-.06:.06)));drawSpace(false);svg.focus();
  };drawSpace();mountMap();
 }
 function drawSpace(updateCopy=true){
  const svg=$('recap-space-chart');svg.replaceChildren();
  const entries=alternatives(),anchors=[0,5,10],points=entries.flatMap(({plan})=>anchors.map(year=>({plan,year,...beforeFire(plan,year)})));
  const {xmin,xmax,ymin,ymax}=chartBounds(points),colours=['','#8dbb9e','#7db5ce','#ce93ae'];
  // Fit the entire box while turning it, including its top/bottom corners.
  const scale=Math.min(160,192/(Math.cos(pitch)+(Math.abs(Math.sin(yaw))+Math.abs(Math.cos(yaw)))*Math.sin(pitch)));
  const project=(earnings,health,year)=>{
   const a=2*(earnings-xmin)/(xmax-xmin)-1,b=2*(health-ymin)/(ymax-ymin)-1,c=year/5-1;
   const xx=a*Math.cos(yaw)+c*Math.sin(yaw),zz=-a*Math.sin(yaw)+c*Math.cos(yaw);
   return {x:310+scale*xx,y:226-scale*(b*Math.cos(pitch)+zz*Math.sin(pitch))};
  };
  const line=(a,b,attrs={})=>svg.append(tag('line',{x1:a.x,y1:a.y,x2:b.x,y2:b.y,stroke:'#355344',...attrs}));
  for(const year of [...anchors].reverse()){
   const corners=[[xmin,ymin],[xmax,ymin],[xmax,ymax],[xmin,ymax]].map(([e,h])=>project(e,h,year));
   svg.append(tag('polygon',{points:corners.map(p=>`${p.x},${p.y}`).join(' '),fill:'#0c2419','fill-opacity':.12,stroke:'#355344'}));
   line(project(xmin,0,year),project(xmax,0,year),{'stroke-dasharray':'3 5'});
   const p=project(xmax,ymin,year);svg.append(tag('text',{x:p.x+8,y:p.y+5},year===0?'Start':`Year ${year}`));
  }
  line(project(xmax,ymin,0),project(xmax,ymin,10),{stroke:'#9eb3a5'});
  for(let v=Math.ceil(xmin/5)*5;v<=xmax;v+=5){const p=project(v,ymin,0);svg.append(tag('text',{x:p.x,y:p.y+20,'text-anchor':'middle'},String(v)));}
  for(let v=Math.ceil(ymin/5)*5;v<=ymax;v+=5){const p=project(xmin,v,0);svg.append(tag('text',{x:p.x-10,y:p.y+4,'text-anchor':'end'},String(v)));}
  svg.append(tag('text',{x:25,y:20},'Forest health change (points)'),tag('text',{x:310,y:466,'text-anchor':'middle'},'Net group earnings (credits)'));
  for(const p of points.filter(p=>!same(p.plan,spacePlan))){
   const xy=project(p.earnings,p.healthChange,p.year),dot=tag('circle',{cx:xy.x,cy:xy.y,r:4.5,fill:colours[fieldPlots(p.plan).length],opacity:.48,'data-plan':p.plan.ecology+p.plan.removal+p.plan.community,tabindex:0,role:'button','aria-label':`${describe(p.plan)} Year ${p.year}.`});
   dot.append(tag('title',{},`${describe(p.plan)} Year ${p.year}.`));svg.append(dot);
  }
  const events=planHinges(spacePlan),samples=[...Array.from({length:101},(_,i)=>i/10),7.499999].sort((a,b)=>a-b);
  const trail=samples.map(year=>{const p=beforeFire(spacePlan,year);return project(p.earnings,p.healthChange,year);});
  svg.append(tag('path',{d:trail.map((p,i)=>`${i?'L':'M'}${p.x},${p.y}`).join(' '),fill:'none',stroke:'#e3c879','stroke-width':2.5,'data-trail':'selected','pointer-events':'none'}));
  for(const year of [0,10]){if(events.some(e=>e.year===year))continue;const p=beforeFire(spacePlan,year),xy=project(p.earnings,p.healthChange,year);svg.append(tag('circle',{cx:xy.x,cy:xy.y,r:4,fill:'#e3c879','pointer-events':'none'}),tag('text',{x:xy.x+10,y:xy.y-9,stroke:'#081b14','stroke-width':4,'paint-order':'stroke','pointer-events':'none'},year===0?'Start':`Year ${year}`));}
  events.forEach((event,i)=>{const p=beforeFire(spacePlan,event.year),xy=project(p.earnings,p.healthChange,event.year),g=tag('g',{'data-hinge':i,tabindex:0,role:'button','aria-label':`Year ${event.year}: ${event.title}`,'aria-pressed':String(hinge===i)});g.append(tag('circle',{cx:xy.x,cy:xy.y,r:10,fill:hinge===i?'#e3c879':'#10251b',stroke:'#e3c879','stroke-width':1.5}),tag('text',{x:xy.x,y:xy.y+4,'text-anchor':'middle',style:`fill:${hinge===i?'#10251b':'#e3c879'};font-weight:bold`},String(i+1)));svg.append(g);});
  if(updateCopy){
   $('recap-space-plan').value=spacePlan.ecology+spacePlan.removal+spacePlan.community;
   $('hinge-choices').replaceChildren(...events.map((e,i)=>{const b=document.createElement('button');b.textContent=`${i+1} / Year ${e.year}`;b.setAttribute('aria-pressed',String(hinge===i));b.onclick=()=>{hinge=i;drawSpace();};return b;}));
   $('hinge-title').textContent=events[hinge].title;story([events[hinge].text]);const sites=fieldPlots(spacePlan);
   $('recap-work').textContent=sites.length===1?`One field plot to tend: ${sites[0]}.`:`${sites.length} field plots to tend: ${sites.join(', ')}.`;
   const end=beforeFire(spacePlan);$('recap-values').textContent=`Year ten: ${end.earnings.toFixed(1)} net credits / ${end.healthChange>=0?'+':''}${end.healthChange.toFixed(1)} forest health.`;
  }
 }
 return {dialog,open(plan,options={}){example=!!options.example;committed={...plan};selected={...plan};showFirst();if(!dialog.open)dialog.showModal();}};
}
