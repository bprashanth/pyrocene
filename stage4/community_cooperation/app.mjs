import {CommunityForest} from './render.mjs';
import {CONFIG,PATCHES,patch,INVENTORY,CLUES,fire,outcome,surveyClue} from './model.mjs';
import {ADDITIONAL_SPECIES} from '../forest-flora.mjs';
import {speciesRecord} from '../species-record.mjs';
import {coordinate} from '../world.mjs';
const $=id=>document.getElementById(id);
const roleName={ecology:'Ecologist',removal:'Removal',community:'Community',room:'Shared plan'};
const params=new URLSearchParams(location.hash.slice(1));
const fireReview=params.get('fire')==='1';
let reviewIgnition='C';
let credentials={session:params.get('session'),token:params.get('token')},state=null;
let role=params.get('role')||'community',selected=13,view='forest',busy=true,mutating=false,catalogue=[],photos={},clock=0,years=10,withPlan=true,running=false,lastFrame=0,result=null,cacheKey='',fireCache=new Map();
if(!roleName[role])role='community';
const btn=(label,fn)=>{const b=document.createElement('button');b.textContent=label;b.className='primary';b.onclick=fn;return b;};
const line=(parent,text,cls='')=>{const p=document.createElement('p');p.textContent=text;p.className=cls;parent.append(p);};
const forest=new CommunityForest($('landscape'),{select:choose,specimen:meet});
forest.reducedMotion=matchMedia('(prefers-reduced-motion: reduce)').matches;
const current=()=>PATCHES.find(p=>p.id===selected);
const proposed=()=>state?.proposals;
function toast(text){$('toast').textContent=text;$('toast').hidden=false;clearTimeout(toast.timer);toast.timer=setTimeout(()=>$('toast').hidden=true,5500);}
async function request(action,extra={}){
 const response=await fetch('/api/community-cooperation/'+action,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...credentials,revision:state?.revision,...extra})});
 const data=await response.json();if(!response.ok){const e=Error(data.error||'Could not reach the room.');e.status=response.status;throw e;}return data;
}
function accept(next){
 if(state&&next.revision<=state.revision&&next.id===state.id)return;
 const changed=state?.phase!==next.phase;state=next;
 if(state.role!=='room')role=state.role;
 if(changed){running=false;clock=0;withPlan=!fireReview;}
 if(state.phase==='committed'&&changed){role=state.role==='room'?'room':role;camera('overhead');}
 updateProjection();render();
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
function saveURL(){history.replaceState(null,'',location.pathname+'#'+new URLSearchParams({...credentials,role}));}
function render(){
 if(!state)return;
 const p=current(),done=state.phase==='committed',host=!fireReview&&state.role==='room',room=role==='room';
 $('round-panel').classList.toggle('is-committed',done);
 $('role').value=role;$('role').disabled=!host||done||mutating;
 $('phase').textContent=done?'SHARED PLAN':state.phase==='review'?'DISCUSS':'SURVEY';
 $('task').textContent=done?'One landscape':room?'Bring the plans together':role==='community'?'Choose a livelihood':role==='ecology'?'Choose a patch to restore':'Choose a patch to remove';
 $('goal').textContent=done?'Explore recovery, then follow the fire.':room?'Resolve land use before committing.':role==='community'?(p?.key==='B'?'You have 2 credits; this needs shared funding.':'You have 2 credits. Choose one opportunity.'):'Inspect A, B and C. Propose one.';
 $('patches').hidden=room||done;
 for(const b of $('patches').children){b.setAttribute('aria-pressed',String(b.dataset.patch===p?.key));b.disabled=busy;}
 $('choice-title').textContent=done||room?'':p?`${p.key} / ${role==='community'?CONFIG.opportunities[p.key].name:p.name==='Narrow link'?'Edge pasture':p.name}`:`${coordinate(selected)} / Surrounding forest`;
 $('finding').textContent=done||room?'':view==='close'||!p?surveyClue(selected):CLUES[role][p.key];
 $('terms').replaceChildren();$('patch-actions').replaceChildren();$('decision').replaceChildren();$('status').textContent='';
 if(room||done){
  for(const team of ['ecology','removal','community']){
   const key=state.proposals[team];
   line($('terms'),`${roleName[team]}: ${key?key+(team==='community'?' / '+CONFIG.opportunities[key].name:''):'waiting'}`,'plan-row');
  }
  if(state.assessment){
   const a=state.assessment;
   line($('terms'),`Funds: ${CONFIG.grant}. Cost: ${a.cost}. Return: ${a.returns}. Left: ${a.left}.`,'investment');
   if(done){const health=document.createElement('p');health.id='forest-health';$('terms').append(health);}
   $('status').textContent=a.issue||(!a.nurseryOrder&&state.proposals.community==='A'?'No restoration order for A. The nursery has no buyer.':'');
  }
  if(host&&!done){const b=btn(state.phase==='survey'?'Reveal plans':'Commit plan',()=>action(state.phase==='survey'?'reveal':'commit'));b.disabled=mutating||!Object.values(state.ready).every(Boolean)||(state.phase==='review'&&!!state.assessment?.issue);$('decision').append(b);}
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
 $('recovery-label').textContent=years+'y';$('recovery').value=years;
 $('livelihood').textContent=result?.livelihood||'';
 $('with').setAttribute('aria-pressed',String(withPlan));$('without').setAttribute('aria-pressed',String(!withPlan));
 for(const b of document.querySelectorAll('[data-view]')){b.classList.toggle('active',b.dataset.view===view);b.disabled=busy;}
 renderFire();
}
let pickerKey='';
function populatePlants(){
 const ids=INVENTORY[selected].speciesIds,key=selected+':'+ids.join(',');if(key===pickerKey)return;pickerKey=key;
 $('plot-plants').replaceChildren(new Option('Choose a plant',''));
 for(const id of ids){const sp=catalogue.find(s=>s.id===id);if(sp)$('plot-plants').append(new Option(sp.name,id));}
}
function closeRecord(){$('plant-guide').hidden=true;$('plot-plants').value='';}
function meet(id){
 const species=catalogue.find(s=>s.id===id);if(!species)return;
 $('guide-content').replaceChildren(speciesRecord({species,photo:photos[species.photoAssetId||id],plot:selected,condition:INVENTORY[selected].moisture>.7?'The litter here is damp.':'Dry litter lies beneath the plants.',seedContext:{plot:INVENTORY[selected],grid:{columns:6,cells:INVENTORY.map(c=>c.active?c:null)}},immersive:true}));
 $('plant-guide').hidden=false;$('plot-plants').value=id;forest.focusSpecimen(id);
}
function specimens(){forest.setSpecimens(view==='close'?INVENTORY[selected].speciesIds.map(id=>({id,speciesId:id,label:catalogue.find(s=>s.id===id)?.name||id})):[]);}
async function choose(id){if(busy||!INVENTORY[id]?.active)return;selected=id;closeRecord();forest.selectPlot(id);if(view==='close')await camera('close');else render();}
async function camera(next){
 if(busy)return;busy=true;view=next;closeRecord();render();
 try{await forest.setView(next,selected);if(next==='close')forest.setFieldVisited(true);specimens();}
 catch(e){toast(e.message);}
 finally{busy=false;render();}
}
function updateProjection(){
 const plan=proposed(),ready=state?.phase==='committed';
 if(!ready){forest.setPlan(null);forest.setFire(null,CONFIG.duration);cacheKey='';result=null;return;}
 result=outcome(plan,years);
 forest.setPlan(withPlan?plan:null,years/10);
 const ignition=fireReview?reviewIgnition:plan.community;
 const key=JSON.stringify([plan,years,withPlan,ignition]);
 if(key!==cacheKey){
  if(!fireCache.has(key))fireCache.set(key,fire(withPlan?plan:null,years,ignition));
  cacheKey=key;forest.setFire(fireCache.get(key).arrival,CONFIG.duration);
 }
 forest.setFireTime(clock/CONFIG.duration);
}
function renderFire(){
 $('fire-time').value=clock;$('fire-label').textContent=clock.toFixed(1).replace(/\.0$/,'')+' min';$('run-fire').textContent=running?'Pause':'Run fire';
 const f=fireCache.get(cacheKey),area=f?f.arrival.filter(t=>Number.isFinite(t)&&t<=clock).length*.0225:0;
 $('burned').textContent=clock>0?`${area.toFixed(1)} ha burned.`:'';
 const health=$('forest-health');if(health)health.textContent=`Forest health: ${Math.max(0,Math.round((withPlan?result?.health||60:60)-area*.8))}/100.`;
 let livelihood=withPlan?result?.livelihood||'':'Same ignition and weather, without the proposed work.';
 if(withPlan&&state?.proposals.community==='B'&&f?.arrival.some((t,i)=>Number.isFinite(t)&&t<=clock&&Math.floor(i/600)*6+Math.floor(i%60/10)===22))livelihood='Fire reached the fruit plot; the harvest is at risk.';
 $('livelihood').textContent=livelihood;
 if(fireReview)$('livelihood').textContent='Same spark and wind, before and after restoring C.';
 $('fire-note').textContent=(fireReview?reviewIgnition:state?.proposals.community)==='C'?'Ignition: patch C.':'Ignition: neighbouring field.';
 $('map-note').hidden=state?.phase!=='committed'||clock===0;
}
function frame(now){
 if(running){clock=Math.min(CONFIG.duration,clock+(lastFrame?Math.min(now-lastFrame,100):0)/1000*1.7);forest.setFireTime(clock/CONFIG.duration);if(clock>=CONFIG.duration)running=false;renderFire();}
 lastFrame=now;requestAnimationFrame(frame);
}
$('role').onchange=()=>{role=$('role').value;closeRecord();saveURL();render();};
for(const b of $('patches').children)b.onclick=()=>choose(patch(b.dataset.patch).id);
for(const b of document.querySelectorAll('[data-view]'))b.onclick=()=>camera(b.dataset.view);
$('plot-plants').onchange=()=>{if($('plot-plants').value)meet($('plot-plants').value);};$('record-close').onclick=closeRecord;
$('recovery').oninput=()=>{years=Number($('recovery').value);running=false;updateProjection();render();};
$('fire-time').oninput=()=>{running=false;clock=Number($('fire-time').value);forest.setFireTime(clock/CONFIG.duration);renderFire();};
$('run-fire').onclick=()=>{if(clock>=CONFIG.duration)clock=0;running=!running;renderFire();};
$('with').onclick=()=>{withPlan=true;updateProjection();render();};$('without').onclick=()=>{withPlan=false;updateProjection();render();};
$('teams-open').onclick=()=>{
 $('teams').querySelector('h1').textContent=fireReview?'Sources':'Teams';
 $('teams').querySelector(':scope > p').hidden=fireReview;
 $('teams').querySelector('details').open=fireReview;
 $('team-links').replaceChildren();
 if(state.tokens)for(const team of ['ecology','removal','community','room']){
  const label=document.createElement('label');label.textContent=roleName[team];const input=document.createElement('input');input.readOnly=true;input.value=new URL('/community-cooperation/#'+new URLSearchParams({session:state.id,token:state.tokens[team],role:team}),location.href).href;input.onclick=()=>input.select();label.append(input);$('team-links').append(label);
 }
 $('new-room').hidden=fireReview||state.role!=='room';$('teams').showModal();
};
$('teams-back').onclick=()=>$('teams').close();
$('new-room').onclick=()=>{location.assign('/community-cooperation/');};
document.addEventListener('keydown',e=>{if(e.key==='Escape')closeRecord();});
globalThis.communityCooperationDiagnostics=()=>({state,role,selected,view,busy,years,clock,result,fire:fireCache.get(cacheKey)?.burned,renderedFireTime:forest.drawnFireTime,forest:forest.performance()});
try{
 const [_,data,oldPhotos,newPhotos]=await Promise.all([forest.load(),fetch('field-catalogue.json').then(r=>r.json()),fetch('plant-images.json').then(r=>r.json()),fetch('field-photos.json').then(r=>r.json())]);
 catalogue=[...data.species,...ADDITIONAL_SPECIES];photos={...oldPhotos.images,...newPhotos.photos};forest.setInventory(catalogue,INVENTORY);forest.setSettlement(false);forest.selectPlot(selected);
 $('fire-time').max=CONFIG.duration;
 const next=fireReview?{id:'fire-review',revision:0,role:'room',phase:'committed',proposals:{ecology:'C',removal:'C',community:'A'},ready:{ecology:true,removal:true,community:true}}:await request(credentials.session?'state':'new');
 if(!fireReview&&!credentials.session)credentials={session:next.id,token:next.tokens.room};
 busy=false;accept(next);if(!fireReview)saveURL();$('loading').hidden=true;render();requestAnimationFrame(frame);
 if(!fireReview)setInterval(async()=>{if(mutating||document.hidden)return;try{accept(await request('state'));}catch(e){toast(e.message);}},1500);
}catch(e){$('loading').textContent=e.message;$('loading').append(btn('New room',()=>location.assign('/community-cooperation/')));}
