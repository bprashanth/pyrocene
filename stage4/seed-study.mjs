import {SEED_RECORDS,seedLayers,level} from './seed-model.mjs';
import {coordinate} from './world.mjs';
import {patch} from './round-model.mjs';

export class SeedStudy{
 constructor(host,onSpecies){
  this.host=host;this.onSpecies=onSpecies;
  host.innerHTML=`<label class="seed-picker">Compare seeds <select aria-label="Seed species"></select></label><div class="seed-tabs" role="tablist" aria-label="Seed study"><button id="seed-dispersal" role="tab" aria-controls="seed-panel">Dispersal</button><button id="seed-germination" role="tab" aria-controls="seed-panel">Germination</button></div><section id="seed-panel" role="tabpanel" tabindex="0"><p class="seed-copy"></p><figure><canvas width="336" height="336" role="img"></canvas><figcaption></figcaption></figure><p class="seed-clue"></p></section><details class="seed-sources"><summary>Sources</summary><p class="seed-limit"></p><p>Six-month teaching maps. Seed supply, animal use and growing conditions are modelled, not surveyed. These clues do not change the survival projection.</p><a target="_blank" rel="noopener"></a></details>`;
  this.select=host.querySelector('select');
  for(const [id,s]of Object.entries(SEED_RECORDS)){const o=document.createElement('option');o.value=id;o.textContent=s.name;this.select.append(o);}
  this.select.onchange=()=>onSpecies(this.select.value,this.tab);
  this.tabs=[...host.querySelectorAll('[role=tab]')];
  this.tabs.forEach((b,i)=>{b.onclick=()=>this.showTab(i?'germination':'dispersal');b.onkeydown=e=>{if(['ArrowLeft','ArrowRight','Home','End'].includes(e.key)){e.preventDefault();const n=e.key==='Home'?0:e.key==='End'?1:1-i;this.tabs[n].click();this.tabs[n].focus();}};});
 }
 open(species,plot,previous,tab='dispersal'){
  this.host.hidden=!SEED_RECORDS[species];if(this.host.hidden)return;
  this.species=species;this.plot=plot;this.previous=previous;this.select.value=species;this.showTab(tab);
 }
 showTab(tab){
  this.tab=tab;const record=SEED_RECORDS[this.species],germ=tab==='germination',values=seedLayers(this.species,this.previous),field=germ?'establishment':'arrival',selected=values[this.plot];
  this.tabs.forEach((b,i)=>{const active=(i===1)===germ;b.setAttribute('aria-selected',String(active));b.tabIndex=active?0:-1;});
  this.host.querySelector('[role=tabpanel]').setAttribute('aria-labelledby',germ?'seed-germination':'seed-dispersal');
  this.host.querySelector('.seed-copy').textContent=record[tab];
  const title=germ?'Establishment conditions':'Possible seed arrival';
  this.host.querySelector('figcaption').textContent=`Six-month model: ${title.toLowerCase()}. Dim to bright: low to high.`;
  const key=['A','B','C','D','E'].find(k=>patch(k).id===this.plot);
  this.host.querySelector('.seed-clue').textContent=`Patch ${key} (${coordinate(this.plot)}): ${selected?level(selected[field]):'unknown'} ${germ?'suitability for establishment':'seed arrival'}. ${germ?'Germination alone does not ensure survival.':this.species==='cecropia_obtusa'?'Bat presence does not prove seed delivery.':'Shoots can also regrow from surviving stems.'}`;
  this.host.querySelector('.seed-limit').textContent=record.limit;
  const link=this.host.querySelector('.seed-sources a');link.href=record.source;link.textContent=record.citation;
  this.host.querySelector('.seed-extra-source')?.remove();if(record.extraSource){const p=document.createElement('p');p.className='seed-extra-source';const a=document.createElement('a');a.href=record.extraSource;a.textContent=record.extraCitation;a.target='_blank';a.rel='noopener';p.append(a);link.after(p);}
  const canvas=this.host.querySelector('canvas'),ctx=canvas.getContext('2d');ctx.clearRect(0,0,336,336);ctx.fillStyle='#071711';ctx.fillRect(0,0,336,336);ctx.font='12px monospace';ctx.textAlign='center';
  for(let j=0;j<6;j++){ctx.fillStyle='#8da799';ctx.fillText(j+1,53+j*48,19);ctx.fillText(String.fromCharCode(65+j),14,57+j*48);}
  values.forEach((v,id)=>{const x=29+id%6*48,y=29+Math.floor(id/6)*48;for(let a=0;a<8;a++)for(let b=0;b<8;b++){ctx.fillStyle=v?`rgba(123,224,166,${.08+.85*v[field]})`:'#1b2722';ctx.fillRect(x+4+a*5,y+4+b*5,2.5,2.5);}if(id===this.plot){ctx.strokeStyle='#e3c879';ctx.lineWidth=1.5;ctx.strokeRect(x,y,46,46);}});
  canvas.setAttribute('aria-label',`${title}. Selected plot ${coordinate(this.plot)}: ${selected?level(selected[field]):'unknown'}. Brighter green means higher. Yellow border marks the selected plot. Unscanned cells have no estimate.`);
 }
}
