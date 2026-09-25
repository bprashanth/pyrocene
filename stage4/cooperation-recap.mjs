import {alternatives,beforeFire,planStory,TIME_CHOICES,timeOutcome,timeStory} from './cooperation-projection.mjs';
const NS='http://www.w3.org/2000/svg';
const tag=(name,attrs={},text='')=>{const n=document.createElementNS(NS,name);for(const [k,v]of Object.entries(attrs))n.setAttribute(k,v);n.textContent=text;return n;};
const same=(a,b)=>['ecology','removal','community'].every(k=>a[k]===b[k]);
const describe=p=>`Restore ${p.ecology}, remove ${p.removal}, ${p.community==='A'?'nursery A':p.community==='B'?'coffee B':'grazing C'}.`;
const extent=values=>{const lo=Math.min(0,...values),hi=Math.max(0,...values),pad=Math.max(1,hi-lo)*.06;return [lo-pad,hi+pad];};
export function chartBounds(points){
 const [xmin,xmax]=extent(points.map(p=>p.earnings)),[ymin,ymax]=extent(points.map(p=>p.healthChange));
 return {xmin,xmax,ymin,ymax};
}
export function createCooperationRecap(){
 const dialog=document.createElement('dialog');dialog.id='cooperation-recap';dialog.setAttribute('aria-label','Recap I');document.body.append(dialog);
 let committed,selected,choice='sequence',year=0;
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
  dialog.setAttribute('aria-label','Recap I');
  dialog.innerHTML=`<section class="prelude-copy"><small>RECAP I</small><h1>What does the group gain?</h1>
   <div id="recap-story" aria-live="polite"></div>
   <p class="recap-note">Choose a dot to explore the plan. Higher means healthier forest; farther right means more group earnings. Yellow is your committed plan.</p>
   <div class="prelude-nav"><button id="recap-one-back">Back to map</button><button class="primary" id="recap-time-open">Recap II: time</button></div></section>
   <figure><svg id="earnings-health" viewBox="0 0 520 390" role="group" aria-label="Ten-year net group earnings versus change in forest health before fire"></svg><figcaption id="recap-plan"></figcaption><p id="recap-values"></p><small>Ten years, without wildfire. Earnings exclude the starting grant and include saved feed costs.</small></figure>`;
  $('recap-one-back').onclick=close;$('recap-time-open').onclick=()=>{choice='sequence';year=0;showTime();};
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
  showPlan(selected||committed);
 }
 function showTime(){
  dialog.setAttribute('aria-label','Recap II: time');
  dialog.innerHTML=`<section class="prelude-copy"><small>RECAP II / TIME</small><h1>What if we do this in steps?</h1>
   <p>Keep removal and restoration in A. Compare three ways for the community to take part. Coffee uses B, so it does not replace the native planting.</p>
   <div id="recap-story" aria-live="polite"></div>
   <div class="prelude-nav"><button id="recap-one-return">Back</button><button class="primary" id="recap-one-back">Back to map</button></div></section>
   <figure><div id="time-choices" aria-label="Compare timing"></div>
   <svg id="recap-time-chart" viewBox="0 0 620 440" role="img" aria-label="Group earnings and forest health over ten years"></svg>
   <label class="time-range" for="recap-year">Year <output id="recap-year-label">0</output></label><input id="recap-year" aria-label="Recap year" type="range" min="0" max="10" step=".1" value="0">
   <p id="recap-values"></p><small>A comparison, not a change to your plan. No wildfire or failed harvest is included.</small></figure>`;
  $('recap-one-back').onclick=close;$('recap-one-return').onclick=showFirst;
  for(const item of TIME_CHOICES){const b=document.createElement('button');b.textContent=item.name;b.dataset.choice=item.id;b.style.setProperty('--line-colour',item.colour);b.onclick=()=>{choice=item.id;drawTime();};$('time-choices').append(b);}
  $('recap-year').oninput=()=>{year=Number($('recap-year').value);drawTime();};drawTime();
 }
 function drawTime(){
  const svg=$('recap-time-chart');svg.replaceChildren();story(timeStory(choice,year));
  $('recap-year-label').textContent=year.toFixed(1).replace(/\.0$/,'');
  for(const b of $('time-choices').children)b.setAttribute('aria-pressed',String(b.dataset.choice===choice));
  const samples=Array.from({length:101},(_,i)=>i/10);samples.push(2.999);samples.sort((a,b)=>a-b);
  const series=TIME_CHOICES.map(c=>({...c,points:samples.map(y=>({year:y,...timeOutcome(c.id,y)}))})),x=y=>60+y/10*530;
  const panels=[{field:'earnings',top:45,bottom:172,label:'Net group earnings (credits)'},{field:'healthChange',top:252,bottom:379,label:'Forest health change (points)'}];
  for(const panel of panels){
   const [min,max]=extent(series.flatMap(s=>s.points.map(p=>p[panel.field]))),y=v=>panel.bottom-(v-min)/(max-min)*(panel.bottom-panel.top);
   svg.append(tag('text',{x:60,y:panel.top-19},panel.label));
   for(let t=0;t<=10;t+=2)svg.append(tag('line',{x1:x(t),y1:panel.top,x2:x(t),y2:panel.bottom,stroke:'#254234'}),tag('text',{x:x(t),y:panel.bottom+18,'text-anchor':'middle'},String(t)));
   for(let v=Math.ceil(min/5)*5;v<=max;v+=5)svg.append(tag('line',{x1:60,y1:y(v),x2:590,y2:y(v),stroke:v===0?'#93a993':'#254234','stroke-dasharray':v===0?'3 4':'none'}),tag('text',{x:47,y:y(v)+4,'text-anchor':'end'},String(v)));
   for(const s of [...series].sort((a,b)=>Number(a.id===choice)-Number(b.id===choice))){
    const d=s.points.map((p,i)=>(i?'L':'M')+x(p.year)+','+y(p[panel.field])).join(' ');
    svg.append(tag('path',{d,fill:'none',stroke:s.colour,'stroke-width':s.id===choice?2.8:1.6,opacity:s.id===choice?1:.45,'data-series':s.id}));
   }
   svg.append(tag('line',{x1:x(year),y1:panel.top,x2:x(year),y2:panel.bottom,stroke:'#e3c879','stroke-dasharray':'2 3'}),tag('circle',{cx:x(year),cy:y(timeOutcome(choice,year)[panel.field]),r:4,fill:TIME_CHOICES.find(c=>c.id===choice).colour}));
  }
  svg.append(tag('text',{x:325,y:433,'text-anchor':'middle'},'Years after the first work'));
  const current=timeOutcome(choice,year);$('recap-values').textContent=`Net earnings: ${current.earnings.toFixed(1)} credits. Forest health: ${current.healthChange>=0?'+':''}${current.healthChange.toFixed(1)} points.`;
 }
 return {dialog,open(plan){committed={...plan};selected={...plan};showFirst();if(!dialog.open)dialog.showModal();}};
}
