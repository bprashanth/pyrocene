import {appURL} from '../game-features.mjs';
import {CommunityForest} from './render.mjs';
import {CONFIG,PATCHES,patch,INVENTORY,CLUES,fire,outcome,surveyClue} from './model.mjs';
import {ADDITIONAL_SPECIES} from '../forest-flora.mjs';
import {speciesRecord} from '../species-record.mjs';
import {coordinate} from '../world.mjs';
import {RoundForest} from '../round-render.mjs';
import {StructureLab} from '../structure-lab.mjs';
import {bindRecap,flowURL,enterCombined} from '../play-flow.mjs';
import {COOPERATION_BRIEFINGS} from '../cooperation-briefing.mjs';
import {installProjection} from '../cooperation-growth.mjs';
import {projection,projectedFire,projectionNote,beforeFire,FIRE_END} from '../cooperation-projection.mjs';
import {createCooperationRecap} from '../cooperation-recap.mjs';
const $=id=>document.getElementById(id);
const integrated=document.body.classList.contains('integrated-cooperation');
const entry=integrated?'round.html':'community-cooperation/';
const roleName={ecology:'Ecologist',removal:'Removal',community:'Community',room:'Shared plan'};
const params=new URLSearchParams(location.hash.slice(1));
const fireReview=!integrated&&params.get('fire')==='1';
let reviewIgnition='C';
let credentials={session:params.get('session'),token:params.get('token')},state=null;
let role=params.get('role')||(integrated?'removal':'community'),selected=13,view='forest',busy=true,mutating=false,catalogue=[],photos={},clock=0,years=10,withPlan=true,running=false,lastFrame=0,result=null,cacheKey='',fireCache=new Map();
if(!roleName[role])role='community';
const btn=(label,fn)=>{const b=document.createElement('button');b.textContent=label;b.className='primary';b.onclick=fn;return b;};
const line=(parent,text,cls='')=>{const p=document.createElement('p');p.textContent=text;p.className=cls;parent.append(p);};
const forest=new (integrated?RoundForest:CommunityForest)($('landscape'),{select:choose,specimen:meet});
forest.reducedMotion=matchMedia('(prefers-reduced-motion: reduce)').matches;
const lab=integrated?new StructureLab({forest,catalogue:()=>catalogue}):null;
const recapOne=integrated?createCooperationRecap(forest,enterCombined):null;let manualFire=false;
const briefed=new Set();let typing=null;
if(integrated){
 years=0;installProjection(forest);
 bindRecap(forest,$('game-mode'),()=>'play');
 $('recap-open').onclick=()=>recapOne.open(state.proposals);
 $('briefing-begin').onclick=()=>{$('briefing').close();clearInterval(typing);};$('briefing').onclose=()=>clearInterval(typing);
 $('game-mode').onchange=async()=>{
  if($('game-mode').value==='recap-one'){$('game-mode').value='play';recapOne.open(state.proposals);return;}
  if($('game-mode').value==='combined'){await enterCombined();return;}
  if($('game-mode').value==='expedition')await leaveForExpedition();
 };
 document.querySelector('.wordmark').onclick=async e=>{e.preventDefault();await leaveForExpedition();};
}
async function leaveForExpedition(){
 if(mutating||!state)return;
 if(state.role==='room'){await action('reset');return;}
 location.assign(flowURL('expedition.html',{...credentials,game:'cooperation'},role));
}
function briefing(){
 if(!integrated||!state||state.phase!=='survey'||busy||state.ready[role])return;
 const key=[state.id,state.generation,role].join(':');if(briefed.has(key))return;briefed.add(key);
 const copy=COOPERATION_BRIEFINGS[role],text=copy.paragraphs.join('\n\n');clearInterval(typing);
 $('briefing-role').textContent='Role: '+roleName[role].toLowerCase();$('briefing-title').textContent=copy.title;$('briefing-accessible').textContent=text;
 $('briefing-text').textContent=forest.reducedMotion?text:'';let at=0;
 if(!forest.reducedMotion)typing=setInterval(()=>{at+=4;$('briefing-text').textContent=text.slice(0,at);if(at>=text.length)clearInterval(typing);},35);
 if(!$('briefing').open)$('briefing').showModal();
}
const current=()=>PATCHES.find(p=>p.id===selected);
const proposed=()=>state?.proposals;
function toast(text){$('toast').textContent=text;$('toast').hidden=false;clearTimeout(toast.timer);toast.timer=setTimeout(()=>$('toast').hidden=true,5500);}
async function request(action,extra={}){
 const response=await fetch(appURL('api/community-cooperation/'+action),{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...credentials,revision:state?.revision,...extra})});
 const data=await response.json();if(!response.ok){const e=Error(data.error||'Could not reach the room.');e.status=response.status;throw e;}return data;
}
function accept(next){
 if(state&&next.revision<=state.revision&&next.id===state.id)return;
 const changed=state?.phase!==next.phase;state=next;
 if(integrated&&state.screen==='expedition'){location.assign(flowURL('expedition.html?fresh=1',{...credentials,game:'cooperation'},role));return;}
 if(state.role!=='room')role=state.role;
 if(changed){running=false;clock=0;manualFire=false;withPlan=!fireReview;cacheKey='';}
 if(state.phase==='committed'&&changed){role=state.role==='room'?'room':role;if(integrated)years=0;camera('overhead');}
 if(integrated&&changed&&state.phase==='review'){selected=patch(state.proposals.ecology).id;forest.selectPlot(selected);}
 updateProjection();render();briefing();
}
async function action(name,extra={}){
 if(mutating)return;mutating=true;render();
 const phase=state.phase,prior=state.proposals[extra.team];
 try{
  try{accept(await request(name,extra));}
  catch(e){
   if(e.status!==409||name!=='propose')throw e;
   // Another team's independent proposal must not make this team's click fail.
   // Never retry across a phase change or overwrite a changed same-team choice.
   accept(await request('state'));
   if(state.phase!==phase||state.proposals[extra.team]!==prior)throw e;
   accept(await request(name,extra));
  }
 }
 catch(e){toast(e.message);try{accept(await request('state'));}catch{}}
 finally{mutating=false;render();}
}
function saveURL(){history.replaceState(null,'',location.pathname+location.search+'#'+new URLSearchParams({...credentials,role,...(integrated?{game:'cooperation'}:{})}));}
function render(){
 if(!state)return;
 const p=current(),done=state.phase==='committed',host=!fireReview&&state.role==='room',room=role==='room';
 $('round-panel').classList.toggle('is-committed',done);
 $('role').value=role;$('role').disabled=!host||done||mutating;
 $('phase').textContent=done?'SHARED PLAN':room||state.phase==='review'?'DISCUSS':'SURVEY';
 $('task').textContent=done?'Shared plan':room?'Bring the plans together':role==='community'?'Choose a livelihood':role==='ecology'?'Choose a patch to restore':'Choose a patch to remove';
 $('goal').textContent=done?'':room?'Discuss and commit the plan.':role==='community'?(p?.key==='B'?'You have 2 credits; the group can borrow more.':'You have 2 credits. Choose one opportunity.'):'Inspect A, B and C. Propose one.';
 $('patches').hidden=done||room;
 for(const b of $('patches').children){b.setAttribute('aria-pressed',String(b.dataset.patch===p?.key));b.disabled=busy;}
 $('choice-title').textContent=done||room?'':p?`${p.key} / ${role==='community'?CONFIG.opportunities[p.key].name:p.name==='Narrow link'?'Edge pasture':p.name}`:`${coordinate(selected)} / Surrounding forest`;
 $('finding').textContent=done||room?'':view==='close'||!p?surveyClue(selected):CLUES[role][p.key];
 $('terms').replaceChildren();$('patch-actions').replaceChildren();$('decision').replaceChildren();$('status').textContent='';
 if(room||done){
  for(const team of ['ecology','removal','community']){
   const key=state.proposals[team];
   if(integrated){
    const label=document.createElement('label');label.className='room-choice';label.textContent=roleName[team];
    const select=document.createElement('select');select.id='plan-'+team;select.setAttribute('aria-label',roleName[team]+' choice');
    if(!key){const waiting=new Option('Choose','');waiting.disabled=true;select.append(waiting);}
    for(const choice of ['A','B','C'])select.append(new Option(choice+(team==='community'?' / '+(choice==='A'?'Nursery':choice==='B'?'Coffee':'Grazing'):''),choice));
    select.value=key||'';select.disabled=!host||done||mutating;select.onchange=()=>action('propose',{team,patch:select.value});label.append(select);$('terms').append(label);
   }else line($('terms'),`${roleName[team]}: ${key?key+(team==='community'?' / '+CONFIG.opportunities[key].name:''):'waiting'}`,'plan-row');
  }
  if(state.assessment){
   const a=state.assessment;
   line($('terms'),`Funds: ${CONFIG.grant}. Cost: ${a.cost}. Return: ${a.returns}. ${a.left<0?'Debt: '+(-a.left):'Left: '+a.left}.`,'investment');
   if(done){const health=document.createElement('p');health.id='forest-health';$('terms').append(health);}
   $('status').textContent=a.issue||(!a.nurseryOrder&&state.proposals.community==='A'?'No restoration order for A. The nursery has no buyer.':'');
  }
  if(integrated&&done)$('finding').textContent='Simulation: choices on the map over time.';
  if(host&&!done){const reveal=!integrated&&state.phase==='survey';const b=btn(reveal?'Reveal plans':'Commit plan',()=>action(reveal?'reveal':'commit'));b.disabled=mutating||!Object.values(state.ready).every(Boolean)||(!reveal&&!!state.assessment?.issue);$('decision').append(b);}
  if(host&&done)$('decision').append(btn('Revise plan',()=>action('revise')));
 }else{
  if(p){
   if(role==='community'){
    const o=CONFIG.opportunities[p.key];line($('terms'),`Investment: ${o.investment} ${o.investment===1?'credit':'credits'}.`,'investment');line($('terms'),`Return: ${o.returns}`);line($('terms'),`Forest health: ${o.health}`);
   }else if(role==='ecology')line($('terms'),`Cost: ${p.planting+3} credits. Health: +${p.healthGain} by 10y.`,'investment');
   else line($('terms'),`Cost: ${p.removalCost} credits. Return: ${p.income+p.removalCost}. Health: -${p.healthLoss}.`,'investment');
   const b=btn(state.proposals[role]===p.key?'Proposed':'Propose',()=>action('propose',{team:role,patch:p.key}));b.disabled=mutating||busy||state.proposals[role]===p.key;$('patch-actions').append(b);
  }
  if(state.proposals[role])$('status').textContent=`Proposed ${state.proposals[role]}. Bring your reasons to the room.`;
  if(integrated&&view==='close'&&!busy){const b=btn('Structure',()=>openStructure());b.className='secondary';$('patch-actions').append(b);}
 }
 if(fireReview){
  $('phase').textContent='REVIEW';$('task').textContent='Follow the fire';$('goal').textContent='';$('status').textContent='';$('terms').replaceChildren();
  const label=document.createElement('label');label.className='round-plant-picker';label.textContent='Ignition';
  const select=document.createElement('select');select.id='review-ignition';select.append(new Option('Patch C','C'),new Option('Neighbouring field','A'));select.value=reviewIgnition;
  select.onchange=()=>{reviewIgnition=select.value;clock=0;running=false;updateProjection();render();};label.append(select);$('terms').append(label);
  $('with').textContent='Restored C';$('without').textContent='Current forest';$('teams-open').textContent='Sources';
  $('role').hidden=true;document.querySelector('label[for=role]').hidden=true;
  $('review-link').textContent='Back to Community';$('review-link').href='community/';$('review-link').removeAttribute('target');
 }
 $('plant-label').hidden=room||done;populatePlants();
 $('outcomes').hidden=!done;$('map-note').hidden=!done||clock===0;
 if(integrated){$('fire-controls').hidden=!done;$('game-mode').querySelector('[value=recap-one]').disabled=!done;}
 $('recovery-label').textContent=years+'y';$('recovery').value=years;
 $('livelihood').textContent=result?.livelihood||'';
 $('with')?.setAttribute('aria-pressed',String(withPlan));$('without')?.setAttribute('aria-pressed',String(!withPlan));
 for(const b of document.querySelectorAll('[data-view]')){b.classList.toggle('active',b.dataset.view===view);b.disabled=busy;}
 renderFire();
}
let pickerKey='';
function populatePlants(){
 const planting=integrated&&current()&&forest.plan?.ecology===current().key?current().mix||[]:[];
 const ids=[...new Set([...INVENTORY[selected].speciesIds,...planting])],key=selected+':'+ids.join(',');if(key===pickerKey)return;pickerKey=key;
 $('plot-plants').replaceChildren(new Option('Choose a plant',''));
 for(const id of ids){const sp=catalogue.find(s=>s.id===id);if(sp)$('plot-plants').append(new Option(sp.name,id));}
}
function closeRecord(){$('plant-guide').hidden=true;$('plot-plants').value='';}
function meet(id){
 const species=catalogue.find(s=>s.id===id);if(!species)return;
 const recovery=integrated&&current()&&forest.plan?.ecology===current().key?years:null;
 $('guide-content').replaceChildren(speciesRecord({species,photo:photos[species.photoAssetId||id],plot:selected,condition:(recovery!==null?recovery>=7:INVENTORY[selected].moisture>.7)?'The litter here is damp.':'Dry litter lies beneath the plants.',seedContext:{plot:INVENTORY[selected],recovery,grid:{columns:6,cells:INVENTORY.map(c=>c.active?c:null)}},immersive:true,onStructure:integrated&&view==='close'?()=>{closeRecord();openStructure(id);}:null}));
 $('plant-guide').hidden=false;$('plot-plants').value=id;forest.focusSpecimen(id);
}
function openStructure(id=null){lab?.open({...INVENTORY[selected],fieldNote:surveyClue(selected)},id);}
function specimens(){const ids=integrated&&current()&&forest.plan?.ecology===current().key&&years>5?current().mix:INVENTORY[selected].speciesIds;forest.setSpecimens(view==='close'?ids.map(id=>({id,speciesId:id,label:catalogue.find(s=>s.id===id)?.name||id})):[]);}
async function choose(id){if(busy||!INVENTORY[id]?.active)return;selected=id;closeRecord();forest.selectPlot(id);if(integrated&&state?.phase==='review')updateProjection();if(view==='close')await camera('close');else render();}
async function camera(next){
 if(busy)return;busy=true;view=next;closeRecord();render();
 try{await forest.setView(next,selected);if(next==='close')forest.setFieldVisited(true);specimens();}
 catch(e){toast(e.message);}
 finally{busy=false;render();}
}
function updateProjection(){
 let plan=proposed();const ready=state?.phase==='committed';
 if(!ready){if(integrated)forest.setProjection(null);else forest.setPlan(null);forest.setFire(null,CONFIG.duration);cacheKey='';result=null;return;}
 result=outcome(plan,years);
 if(integrated){forest.setProjection(withPlan?plan:null,years);result={...result,...beforeFire(plan,years)};if(plan.community==='C'&&!manualFire)clock=projection(plan,years).fireMinutes;}
 else forest.setPlan(withPlan?plan:null,years/10);
 const ignition=integrated?'C':fireReview?reviewIgnition:plan.community;
 const key=JSON.stringify([plan,years,withPlan,ignition,integrated&&manualFire]);
 if(key!==cacheKey){
  if(!fireCache.has(key))fireCache.set(key,integrated?projectedFire(withPlan?plan:null,years,{atProjectionYear:manualFire}):fire(withPlan?plan:null,years,ignition));
  cacheKey=key;forest.setFire(fireCache.get(key).arrival,integrated?FIRE_END:CONFIG.duration);
 }
 forest.setFireTime(clock/(integrated?FIRE_END:CONFIG.duration));
 if(integrated&&view==='close')specimens();
}
function renderFire(){
 $('fire-time').value=clock;$('fire-label').textContent=clock.toFixed(1).replace(/\.0$/,'')+' min';if($('run-fire'))$('run-fire').textContent=running?'Pause':'Run fire';
 const f=fireCache.get(cacheKey),area=f?f.arrival.filter(t=>Number.isFinite(t)&&t<=clock).length*.0225:0;
 $('burned').textContent=clock>0?`${area.toFixed(1)} ha burned.`:'';
 const health=$('forest-health');if(health)health.textContent=`Forest health: ${Math.max(0,Math.round((withPlan?result?.health||60:60)-area*.8))}/100.`;
 let livelihood=withPlan?result?.livelihood||'':'Same ignition and weather, without the proposed work.';
 if(withPlan&&state?.proposals.community==='B'&&f?.arrival.some((t,i)=>Number.isFinite(t)&&t<=clock&&Math.floor(i/600)*6+Math.floor(i%60/10)===22))livelihood='Fire reached the coffee plot; the harvest is at risk.';
 $('livelihood').textContent=livelihood;
 if(integrated&&withPlan&&state?.phase==='committed')$('livelihood').textContent=projectionNote(state.proposals,years)+(livelihood.startsWith('Fire reached')?' '+livelihood:'');
 if(fireReview)$('livelihood').textContent='Same spark and wind, before and after restoring C.';
 $('fire-note').textContent=integrated?`Ignition: pasture C, ${state?.proposals.community==='C'&&!manualFire?'first season':'year '+years}.`:(fireReview?reviewIgnition:state?.proposals.community)==='C'?'Ignition: patch C.':'Ignition: neighbouring field.';
 $('map-note').hidden=state?.phase!=='committed'||clock===0;
}
function frame(now){
 if(running){clock=Math.min(CONFIG.duration,clock+(lastFrame?Math.min(now-lastFrame,100):0)/1000*1.7);forest.setFireTime(clock/CONFIG.duration);if(clock>=CONFIG.duration)running=false;renderFire();}
 lastFrame=now;requestAnimationFrame(frame);
}
$('role').onchange=()=>{role=$('role').value;closeRecord();saveURL();render();briefing();};
for(const b of $('patches').children)b.onclick=()=>choose(patch(b.dataset.patch).id);
for(const b of document.querySelectorAll('[data-view]'))b.onclick=()=>camera(b.dataset.view);
$('plot-plants').onchange=()=>{if($('plot-plants').value)meet($('plot-plants').value);};$('record-close').onclick=closeRecord;
$('recovery').oninput=()=>{years=Number($('recovery').value);running=false;manualFire=false;updateProjection();render();};
$('fire-time').oninput=()=>{running=false;clock=Number($('fire-time').value);if(integrated){manualFire=true;updateProjection();}else forest.setFireTime(clock/CONFIG.duration);renderFire();};
if($('run-fire'))$('run-fire').onclick=()=>{if(clock>=CONFIG.duration)clock=0;running=!running;renderFire();};
if($('with'))$('with').onclick=()=>{withPlan=true;updateProjection();render();};if($('without'))$('without').onclick=()=>{withPlan=false;updateProjection();render();};
$('teams-open').onclick=()=>{
 $('teams').querySelector('h1').textContent=fireReview?'Sources':'Teams';
 $('teams').querySelector(':scope > p').hidden=fireReview;
 $('teams').querySelector('details').open=fireReview;
 $('team-links').replaceChildren();
 if(state.tokens)for(const team of ['ecology','removal','community','room']){
  const label=document.createElement('label');label.textContent=roleName[team];const input=document.createElement('input');input.readOnly=true;input.setAttribute('aria-label',roleName[team]+' link');input.value=new URL(appURL(entry)+'#'+new URLSearchParams({session:state.id,token:state.tokens[team],role:team,...(integrated?{game:'cooperation'}:{})}),location.href).href;input.onclick=()=>input.select();label.append(input);$('team-links').append(label);
 }
 $('new-room').hidden=fireReview||state.role!=='room';$('teams').showModal();
};
$('teams-back').onclick=()=>$('teams').close();
$('new-room').onclick=()=>{location.assign(appURL(entry));};
document.addEventListener('keydown',e=>{if(e.key==='Escape')closeRecord();});
globalThis.communityCooperationDiagnostics=()=>({state,role,selected,view,busy,years,clock,result,fire:fireCache.get(cacheKey)?.burned,ignition:fireCache.get(cacheKey)?.ignition,projection:forest.projectedVegetation,renderedFireTime:forest.drawnFireTime,forest:forest.performance(),renderer:forest.constructor.name,previewPlan:forest.plan,lab:lab?.diagnostics(),inventory:INVENTORY[selected]});
if(integrated)globalThis.roundDiagnostics=globalThis.communityCooperationDiagnostics;
try{
 const [_,data,oldPhotos,newPhotos]=await Promise.all([forest.load(),fetch('field-catalogue.json').then(r=>r.json()),fetch('plant-images.json').then(r=>r.json()),fetch('field-photos.json').then(r=>r.json())]);
 catalogue=[...data.species,...ADDITIONAL_SPECIES];photos={...oldPhotos.images,...newPhotos.photos};forest.setInventory(catalogue,INVENTORY);forest.setSettlement(false);forest.selectPlot(selected);
 $('fire-time').max=integrated?FIRE_END:CONFIG.duration;
 const next=fireReview?{id:'fire-review',revision:0,role:'room',phase:'committed',proposals:{ecology:'C',removal:'C',community:'A'},ready:{ecology:true,removal:true,community:true}}:await request(credentials.session?'state':'new');
 if(!fireReview&&!credentials.session)credentials={session:next.id,token:next.tokens.room};
 busy=false;accept(next);if(!fireReview)saveURL();$('loading').hidden=true;render();requestAnimationFrame(frame);
 if(!fireReview)setInterval(async()=>{if(mutating||document.hidden)return;try{accept(await request('state'));}catch(e){toast(e.message);}},1500);
}catch(e){$('loading').textContent=e.message;$('loading').append(btn('New room',()=>location.assign(appURL(entry))));}
