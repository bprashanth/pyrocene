import {RoundForest} from './round-render.mjs';
import {StructureLab} from './structure-lab.mjs';
import {WORLD} from './world.mjs';
import {ADDITIONAL_SPECIES} from './forest-flora.mjs';
import {CONFIG,PATCHES,patch,atSector,studyPlot,review} from './round-model.mjs';
const $=id=>document.getElementById(id),button=(text,fn,cls='primary')=>{const b=document.createElement('button');b.textContent=text;b.onclick=fn;b.className=cls;return b;};
let state=null,credentials=null,role='removal',selected=null,view='forest',busy=true,mutating=false,catalogue=[],result=null,mode='survey',playing=false,clock=0,lastFrame=0,showPlan=true,renderedPlan='';
let specimenKey='';
const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
const forest=new RoundForest($('landscape'),{select:async id=>{const p=atSector(id);if(p)await choose(p.key);},specimen:meet});forest.reducedMotion=reduced;
const lab=new StructureLab({forest,catalogue:()=>catalogue});
function toast(text){$('toast').textContent=text;$('toast').hidden=false;clearTimeout(toast.timer);toast.timer=setTimeout(()=>$('toast').hidden=true,5500);}
async function request(action,extra={}){
 const r=await fetch('/api/round/'+action,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...credentials,revision:state?.revision,round:state?.round,phase:state?.phase,prior:state?.proposals[role],team:role,...extra})});
 const body=await r.json();if(!r.ok){const error=Error(body.error||'Cannot reach this round.');error.status=r.status;throw error;}return body;
}
function accept(next){
 if(state&&next.revision<=state.revision)return;
 const previous=state;state=next;
 $('role').disabled=state.role!=='room';if(state.role!=='room')role=state.role;$('role').value=role;
 if(!previous||previous.round!==state.round){mode='survey';playing=false;result=null;renderedPlan='';forest.setFire(null,CONFIG.duration);forest.setPlan(null);refreshPlants();$('playback').hidden=true;}
 if(state.phase!=='survey'){
  const key=state.proposals.removal+state.proposals.ecology;
  if(key!==renderedPlan){renderedPlan=key;result=review(state.proposals);startRecovery();}
 }
 render();
}
async function act(action,extra={}){
 if(mutating)return false;mutating=true;render();
 try{accept(await request(action,extra));return true;}
 catch(e){toast(e.message);if(e.status===409)await refresh();return false;}
 finally{mutating=false;render();}
}
async function refresh(){try{accept(await request('state'));}catch(e){toast(e.message);}}
function teamVisits(){return state?.visited[role]||[];}
function render(){
 if(!state)return;
 const p=patch(selected),seen=p&&teamVisits().includes(p.key),locked=state.phase==='committed';
 $('phase').textContent=locked?'COMMITTED':state.phase==='review'?'DISCUSS':'SURVEY';
 $('task').textContent=locked?'One shared plan.':role==='room'?'Bring the plans together.':role==='removal'?'Choose a patch to remove.':'Choose a patch to restore.';
 for(const b of $('patches').children){b.setAttribute('aria-pressed',String(b.dataset.patch===selected));b.dataset.visited=String(teamVisits().includes(b.dataset.patch));b.disabled=busy;}
 $('finding').textContent=p?(seen||role==='room'||locked?p.note:'Open Close view to study patch '+p.key+'.'):'Inspect A, B and C. Choose one.';
 const actions=$('patch-actions');actions.replaceChildren();
 if(view==='close'&&!busy&&p){actions.append(button(mode==='survey'?'Structure':'Original structure',()=>openStructure(),'secondary'));}
 if(!locked&&role!=='room'&&seen&&state.proposals[role]!==selected)actions.append(button('Propose '+selected,submit));
 const status=$('status'),decision=$('decision');decision.replaceChildren();
 if(locked){
  const s=state.committed;status.textContent=`${s.left} credits left. Native cover lost: ${s.damage}% of ${s.removal}.`;
  if(mode==='fire')$('finding').textContent=`Burned area: ${result.baseline.burned.toFixed(1)} ha without the plan; ${result.future.burned.toFixed(1)} ha with it.`;
  else $('finding').textContent=`Remove ${s.removal}. Restore ${s.ecology}. Projected recovery over ${CONFIG.years} years.`;
  decision.append(button(mode==='fire'?'See recovery':'Run fire',()=>mode==='fire'?startRecovery():startFire()));
 }else if(role==='room'){
  if(state.phase==='survey'){
   status.textContent=`Removal ${state.ready.removal?'ready':'not ready'}. Ecology ${state.ready.ecology?'ready':'not ready'}.`;
   const b=button('Reveal plans',()=>act('reveal'));b.disabled=!Object.values(state.ready).every(Boolean)||mutating;decision.append(b);
  }else{
   const s=state.budget;status.textContent=`${CONFIG.grant} grant + ${s.income} earned - ${s.cost} restoration = ${s.left} credits left.`;
   $('finding').textContent=`Remove ${state.proposals.removal}. Restore ${state.proposals.ecology}. ${s.shared?'Clearing is paid once.':'Separate sites need extra clearing.'}`;
   const b=button('Commit plan',()=>act('commit'));b.disabled=s.left<0||mutating;decision.append(b);
   if(s.left<0)status.textContent+=' Revise a proposal.';
  }
 }else{
  status.textContent=seen?(role==='removal'?`${p.income} credits earned. ${p.damage}% of native cover lost here.`:`Restoration: ${p.planting+CONFIG.clearingCost} credits, or ${p.planting} after shared removal.`):'';
  if(state.proposals[role])status.textContent+=` Proposed: ${state.proposals[role]}.`;
 }
 for(const b of actions.querySelectorAll('button'))b.disabled=busy||mutating;
 document.querySelectorAll('[data-view]').forEach(b=>{b.disabled=busy||(b.dataset.view==='close'&&!p);b.classList.toggle('active',b.dataset.view===view);});
 $('comparison').hidden=mode!=='fire';$('without').setAttribute('aria-pressed',String(!showPlan));$('with').setAttribute('aria-pressed',String(showPlan));
 $('playback').hidden=mode==='survey';$('time').setAttribute('aria-label',mode==='fire'?'Fire progress':'Recovery time');$('play').textContent=playing?'Pause':'Play';
}
async function choose(key){
 if(busy)return;selected=key;const p=patch(key);forest.selectPlot(p.id);
 if(view==='close')await camera('close');else render();
}
async function camera(next){
 if(busy||next==='close'&&!selected)return;busy=true;render();
 try{
  view=next;await forest.setView(next,patch(selected)?.id);
  if(next==='close'){
   forest.setFieldVisited(true);specimenKey='';refreshPlants();
   if(state.phase!=='committed'&&role!=='room'&&!teamVisits().includes(selected))await act('visit',{patch:selected});
  }else forest.setSpecimens([]);
 }catch(e){toast(e.message);view=forest.tlsActive?'close':'forest';}
 finally{busy=false;render();}
}
async function submit(){
 if(await act('propose',{patch:selected})){
  if(state.role==='room'){
   role=state.ready.removal&&state.ready.ecology?'room':state.ready.removal?'ecology':'removal';$('role').value=role;
   if(role!=='room'&&view==='close'&&!teamVisits().includes(selected))await act('visit',{patch:selected});
  }
  render();
 }
}
function meet(id){
 const s=catalogue.find(s=>s.id===id);if(!s)return;
 $('plant-name').textContent=s.name;$('plant-note').textContent=`${s.status}. ${s.description||s.growthForm}.`;
 $('plant-structure').onclick=()=>{$('plant').close();openStructure(id);};$('plant').showModal();
}
function openStructure(id=null){
 lab.open(studyPlot(selected),id);
 const note=document.createElement('p');note.textContent='Fixed restoration mix: '+patch(selected).mix.map(id=>catalogue.find(s=>s.id===id)?.name||id).join(', ')+'. Projected points show generic native cover, not these species identified in a scan.';
 lab.dialog.querySelector('.structure-sources').append(note);
}
function refreshPlants(){
 if(view!=='close'||!selected)return;
 const p=patch(selected),restored=forest.plan?.ecology===selected&&forest.recovery>.5;
 const key=selected+restored;if(key===specimenKey)return;specimenKey=key;
 forest.setSpecimens((restored?p.mix:WORLD[p.id].speciesIds).map(id=>({id,speciesId:id,label:catalogue.find(s=>s.id===id)?.name||id})));
}
function startRecovery(){
 mode='recovery';showPlan=true;clock=reduced?1:0;playing=!reduced;forest.setFire(null,CONFIG.duration);forest.setPlan(state.proposals,clock);updatePlayback();render();
}
async function startFire(){
 if(state.phase!=='committed')return;
 if(view==='close')await camera('forest');
 mode='fire';showPlan=true;clock=0;playing=true;forest.setPlan(state.proposals,1);forest.setFire(result.future.arrival,CONFIG.duration);updatePlayback();render();
}
function compare(withPlan){
 showPlan=withPlan;forest.setPlan(withPlan?state.proposals:null,1);forest.setFire((withPlan?result.future:result.baseline).arrival,CONFIG.duration);forest.setFireTime(clock);refreshPlants();render();
}
function updatePlayback(){
 $('time').value=clock;
 if(mode==='recovery'){forest.setPlan(state.proposals,clock);$('time-label').textContent=`Projected recovery: ${Math.round(clock*CONFIG.years)} years`;}
 else if(mode==='fire'){forest.setFireTime(clock);$('time-label').textContent=`Practice fire: ${Math.round(clock*CONFIG.duration)} min`;}
 $('play').textContent=playing?'Pause':'Play';
 refreshPlants();
}
function tick(now){
 const dt=Math.min(80,now-(lastFrame||now));lastFrame=now;
 if(playing&&!document.hidden&&!lab.dialog.open){clock=Math.min(1,clock+dt/(mode==='fire'?18000:6500));if(clock===1)playing=false;updatePlayback();}
 requestAnimationFrame(tick);
}
function teams(){
 $('teams-note').textContent=state.role==='room'?'Share one link with each team. Use the team selector to test alone.':'Your team has its own proposal. The room reveals and commits both.';
 const links=$('team-links');links.replaceChildren();
 if(state.teams)for(const [name,token]of Object.entries(state.teams)){
  const label=document.createElement('label');label.textContent=name==='removal'?'Removal team':'Ecology team';const input=document.createElement('input');input.readOnly=true;input.setAttribute('aria-label',label.textContent+' link');input.value=new URL('round.html',location.href).href+'#'+new URLSearchParams({session:state.id,token});input.onclick=()=>input.select();label.append(input);links.append(label);
 }
 $('replay').hidden=state.role!=='room';$('teams').showModal();
}
for(const p of PATCHES){const b=button(p.key,()=>choose(p.key),'');b.dataset.patch=p.key;b.setAttribute('aria-label','Patch '+p.key);$('patches').append(b);}
for(const b of document.querySelectorAll('[data-close]'))b.onclick=()=>$(b.dataset.close).close();
for(const b of document.querySelectorAll('[data-view]'))b.onclick=()=>camera(b.dataset.view);
$('role').onchange=async()=>{role=$('role').value;render();if(view==='close'&&role!=='room'&&state.phase!=='committed'&&!teamVisits().includes(selected))await act('visit',{patch:selected});};
$('teams-open').onclick=()=>state&&teams();$('replay').onclick=async()=>{if(await act('replay')){$('teams').close();role='removal';$('role').value=role;render();}};
$('time').oninput=()=>{clock=Number($('time').value);playing=false;updatePlayback();};$('play').onclick=()=>{if(clock===1)clock=0;playing=!playing;updatePlayback();};$('without').onclick=()=>compare(false);$('with').onclick=()=>compare(true);
globalThis.roundDiagnostics=()=>({state,role,selected,view,busy,mode,clock,playing,showPlan,budget:state?.budget,fire:result?{baseline:result.baseline.burned,future:result.future.burned}:null,growthPoints:forest.growthPositions?.length/3||0,forest:forest.performance(),lab:lab.diagnostics()});
try{
 const [_,data]=await Promise.all([forest.load(),fetch('field-catalogue.json').then(r=>r.json())]);
 catalogue=[...data.species,...ADDITIONAL_SPECIES];forest.setInventory(catalogue,WORLD);forest.setSettlement(false);
 for(const p of PATCHES)if(forest.outlines)forest.outlines.add(forest.square((p.id%6)*150-375,Math.floor(p.id/6)*150-375,148,0x6c9d78,.6));
 const params=new URLSearchParams(location.hash.slice(1));
 if(params.has('session')){credentials={session:params.get('session'),token:params.get('token')};accept(await request('state'));}
 else{const s=await request('new');credentials={session:s.id,token:s.token};history.replaceState(null,'','#'+new URLSearchParams(credentials));accept(s);}
 busy=false;$('loading').hidden=true;render();requestAnimationFrame(tick);
 setInterval(()=>{if(!mutating&&!document.hidden)refresh();},1200);
}catch(e){$('loading').textContent=e.message;$('loading').append(button(e.status===404?'New round':'Retry',()=>{if(e.status===404)history.replaceState(null,'',location.pathname);location.reload();}));toast(e.message);}
