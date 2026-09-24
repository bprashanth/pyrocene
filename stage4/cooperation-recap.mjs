import {alternatives,beforeFire} from './cooperation-projection.mjs';
const NS='http://www.w3.org/2000/svg';
const tag=(name,attrs={},text='')=>{const n=document.createElementNS(NS,name);for(const [k,v]of Object.entries(attrs))n.setAttribute(k,v);n.textContent=text;return n;};
const same=(a,b)=>['ecology','removal','community'].every(k=>a[k]===b[k]);
const describe=p=>`Restore ${p.ecology}, remove ${p.removal}, ${p.community==='A'?'nursery A':p.community==='B'?'coffee B':'grazing C'}.`;
export function createCooperationRecap(){
 const dialog=document.createElement('dialog');dialog.id='cooperation-recap';dialog.setAttribute('aria-label','Recap I');
 dialog.innerHTML=`<section class="prelude-copy"><small>RECAP I</small><h1>What does the group gain?</h1>
 <p>Removal earns money, but unplanted ground fills with invasives again.</p>
 <ul><li>Restoration costs money now and its return is forest health.</li>
 <li>Coffee costs money now and earns later if it has enough shelter from healthy forests.</li>
 <li>A nursery needs buyers for seeds. These buyers are often ecologists.</li>
 <li>Debt lets you start a plan before you have the money, but must be repaid from future earnings. Those earnings are not guaranteed if the forest degrades.</li></ul>
 <p class="recap-note">Each dot is an allowed plan chosen at the start of the ten-year period, projected without destruction by wildfire. Yellow is yours.</p>
 <div class="prelude-nav"><button class="primary" id="recap-one-back">Back to map</button></div></section>
 <figure><svg id="earnings-health" viewBox="0 0 520 390" role="img" aria-label="Ten-year net group earnings versus change in forest health before fire"></svg><figcaption id="recap-plan"></figcaption><p id="recap-values"></p><small>Earnings exclude the starting grant and include saved feed costs.</small></figure>`;
 document.body.append(dialog);dialog.querySelector('#recap-one-back').onclick=()=>dialog.close();
 return {dialog,open(plan){
  const svg=dialog.querySelector('svg');svg.replaceChildren();const points=alternatives(),chosen=beforeFire(plan),xs=points.map(p=>p.earnings),ys=points.map(p=>p.healthChange);
  const xmin=Math.floor(Math.min(0,...xs)/5)*5-5,xmax=Math.ceil(Math.max(...xs)/5)*5+5,ymin=Math.floor(Math.min(0,...ys)/2)*2-2,ymax=Math.ceil(Math.max(...ys)/2)*2+2;
  const x=v=>65+(v-xmin)/(xmax-xmin)*410,y=v=>325-(v-ymin)/(ymax-ymin)*265;
  for(let v=xmin;v<=xmax;v+=10){svg.append(tag('line',{x1:x(v),y1:60,x2:x(v),y2:325,stroke:'#254234'}),tag('text',{x:x(v),y:347,'text-anchor':'middle'},String(v)));}
  for(let v=ymin;v<=ymax;v+=4){svg.append(tag('line',{x1:65,y1:y(v),x2:475,y2:y(v),stroke:'#254234'}),tag('text',{x:52,y:y(v)+4,'text-anchor':'end'},String(v)));}
  svg.append(tag('line',{x1:x(0),y1:60,x2:x(0),y2:325,stroke:'#93a993','stroke-dasharray':'3 4'}),tag('line',{x1:65,y1:y(0),x2:475,y2:y(0),stroke:'#93a993','stroke-dasharray':'3 4'}));
  svg.append(tag('text',{x:270,y:378,'text-anchor':'middle'},'Net group earnings (credits)'),tag('text',{x:65,y:27},'Forest health change (points)'));
  const show=(p,result)=>{dialog.querySelector('#recap-plan').textContent=describe(p);dialog.querySelector('#recap-values').textContent=`Net earnings: ${result.earnings.toFixed(1)} credits. Forest health: ${result.healthChange>=0?'+':''}${result.healthChange.toFixed(1)} points.`;};
  for(const entry of points.sort((a,b)=>Number(same(a.plan,plan))-Number(same(b.plan,plan)))){
   const selected=same(entry.plan,plan),dot=tag('circle',{cx:x(entry.earnings),cy:y(entry.healthChange),r:selected?7:4.5,fill:selected?'#e3c879':'#77aa90',stroke:'#071b13','stroke-width':2,tabindex:0,role:'button','aria-label':describe(entry.plan)});
   dot.append(tag('title',{},describe(entry.plan)));dot.onmouseenter=dot.onfocus=dot.onclick=()=>show(entry.plan,entry);dot.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();show(entry.plan,entry);}};svg.append(dot);
  }
  svg.onmouseleave=()=>show(plan,chosen);show(plan,chosen);dialog.showModal();
 }};
}
