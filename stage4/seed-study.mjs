import {SEED_RECORDS,seedLayers,level} from './seed-model.mjs';
import {coordinate} from './world.mjs';
import {patch} from './round-model.mjs';

// One pane within the shared field record. Navigation belongs to that record.
export class SeedStudy{
 constructor(host){
  this.host=host;
  host.innerHTML='<p class="seed-copy"></p><figure><canvas width="336" height="336" role="img"></canvas><figcaption></figcaption></figure><p class="seed-clue"></p><details class="seed-sources"><summary>Sources</summary><p class="seed-limit"></p><p>Teaching maps, not surveyed seed or animal densities. Establishment conditions are not germination probabilities or survival forecasts.</p><div class="seed-links"></div></details>';
 }
 open(species,plot,previous,tab='dispersal'){
  const record=SEED_RECORDS[species],germ=tab==='germination',values=record&&seedLayers(species,previous),field=germ?'establishment':'arrival',selected=values?.[plot];
  this.host.querySelector('figure').hidden=!record;
  this.host.querySelector('.seed-sources').hidden=!record;
  this.host.querySelector('.seed-copy').textContent=record?record[tab]:`${germ?'Germination conditions':'Dispersal'} have not been added for this species yet.`;
  this.host.querySelector('.seed-clue').textContent=record?'':'Its height and native status do not tell us how its seeds travel or germinate.';
  if(!record)return;
  const title=germ?'Establishment conditions':'Possible seed arrival';
  this.host.querySelector('figcaption').textContent=`${previous?'Six-month model':'Study model'}: ${title.toLowerCase()}. Dim to bright: low to high.`;
  const key=previous&&['A','B','C','D','E'].find(k=>patch(k).id===plot),label=key?`Patch ${key} (${coordinate(plot)})`:coordinate(plot);
  this.host.querySelector('.seed-clue').textContent=`${label}: ${selected?level(selected[field]):'unknown'} ${germ?'suitability for establishment':'seed arrival'}. ${germ?'Germination alone does not ensure survival.':species==='cecropia_obtusa'?'Bat presence does not prove seed delivery.':'New growth may also come from surviving plants.'}`;
  this.host.querySelector('.seed-limit').textContent=record.limit;
  const links=this.host.querySelector('.seed-links');links.replaceChildren();
  for(const [url,title]of [[record.source,record.citation],[record.extraSource,record.extraCitation]])if(url){const p=document.createElement('p'),a=document.createElement('a');a.href=url;a.textContent=title;a.target='_blank';a.rel='noopener';p.append(a);links.append(p);}
  const canvas=this.host.querySelector('canvas'),ctx=canvas.getContext('2d');ctx.clearRect(0,0,336,336);ctx.fillStyle='#071711';ctx.fillRect(0,0,336,336);ctx.font='12px monospace';ctx.textAlign='center';
  for(let j=0;j<6;j++){ctx.fillStyle='#8da799';ctx.fillText(j+1,53+j*48,19);ctx.fillText(String.fromCharCode(65+j),14,57+j*48);}
  values.forEach((v,id)=>{const x=29+id%6*48,y=29+Math.floor(id/6)*48;for(let a=0;a<8;a++)for(let b=0;b<8;b++){ctx.fillStyle=v?`rgba(123,224,166,${.08+.85*v[field]})`:'#1b2722';ctx.fillRect(x+4+a*5,y+4+b*5,2.5,2.5);}if(id===plot){ctx.strokeStyle='#e3c879';ctx.lineWidth=1.5;ctx.strokeRect(x,y,46,46);}});
  canvas.setAttribute('aria-label',`${title}. Selected plot ${coordinate(plot)}: ${selected?level(selected[field]):'unknown'}. Brighter green means higher. Yellow border marks this plot. Unscanned cells have no estimate.`);
 }
}
