import {RoundForest} from './round-render.mjs';
import {StructureLab} from './structure-lab.mjs';
import {WORLD} from './world.mjs';
import {ADDITIONAL_SPECIES} from './forest-flora.mjs';
import {CONFIG,PATCHES,patch,atSector,studyPlot,review} from './round-model.mjs';
import {navigation,flowParams,roleFrom,flowURL} from './play-flow.mjs';
import {BRIEFINGS} from './play-briefing.mjs';
const $=id=>document.getElementById(id),button=(text,fn,cls='primary')=>{const b=document.createElement('button');b.textContent=text;b.onclick=fn;b.className=cls;return b;};
let state=null,credentials=null,role=roleFrom(),selected=null,view='forest',busy=true,mutating=false,catalogue=[],result=null,mode='survey',clock=0,years=10,showPlan=true,renderedPlan='';
navigation('play',role);
const fireCache=new Map(),briefed=new Set();let typing=null;
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
 if(!previous||previous.round!==state.round){mode='survey';clock=0;years=10;result=null;renderedPlan='';fireCache.clear();forest.setFire(null,CONFIG.duration);forest.setPlan(null);refreshPlants();}
 if(state.phase!=='survey'){
  const key=state.proposals.removal+state.proposals.ecology;
  if(key!==renderedPlan){renderedPlan=key;fireCache.clear();clock=0;mode='recovery';showPlan=true;updateOutcome();}
 }
 render();if(!busy)briefing();
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
 $('task').textContent=locked?'Shared plan':role==='room'?'Bring the plans together.':role==='removal'?'Choose a patch to remove.':'Choose a patch to restore.';
 for(const b of $('patches').children){b.setAttribute('aria-pressed',String(b.dataset.patch===selected));b.disabled=busy;}
 $('patches').hidden=locked;
 $('finding').replaceChildren(document.createTextNode(p?(seen||role==='room'||locked?p.note:'Open Close view to study patch '+p.key+'.'):'Inspect A, B and C. Choose one.'));
 const actions=$('patch-actions');actions.replaceChildren();
 if(!locked&&role!=='room'&&seen&&state.proposals[role]!==selected&&(state.phase==='review'||!state.ready[role]))actions.append(button('Propose',submit));
 if(!locked&&role!=='room'&&view==='close'&&!busy&&p)actions.append(button('Structure',()=>openStructure(),'secondary'));
 const status=$('status'),decision=$('decision');decision.replaceChildren();
 if(locked){
  const s=state.committed;status.textContent=`${s.left} credits left. Forest health: ${(showPlan?result.health:CONFIG.initialHealth).toFixed(0)}/100 at ${years}y.`;
  $('finding').textContent=`Remove ${s.removal}. Restore ${s.ecology}.`;
 }else if(role==='room'){
  if(state.phase==='survey'){
   status.textContent=`Removal ${state.ready.removal?'ready':'not ready'}. Ecology ${state.ready.ecology?'ready':'not ready'}.`;
   const b=button('Reveal plans',()=>act('reveal'));b.disabled=!Object.values(state.ready).every(Boolean)||mutating;decision.append(b);
  }else{
   const s=state.budget;status.textContent=`Starting funds: ${CONFIG.grant} credits. Cost: ${s.totalCost}. Return: ${s.returns}. Left: ${s.left}. Forest health: ${result.health.toFixed(0)}/100 at ${years}y.`;
   $('finding').textContent=`Remove ${state.proposals.removal}. Restore ${state.proposals.ecology}.`;
   const b=button('Commit plan',()=>act('commit'));b.disabled=s.left<0||mutating;decision.append(b);
   if(s.left<0)status.textContent+=' Revise a proposal.';
  }
 }else{
  status.textContent=state.proposals[role]?`Proposed: ${state.proposals[role]}. Explain your choice to the room.`:'';
  if(seen){const span=document.createElement('span');span.className='choice-cost';span.textContent=role==='removal'?` Cost: ${p.removalCost} credits. Return: ${p.income+p.removalCost}. Health: -${p.healthLoss}.`:` Cost: ${p.planting+CONFIG.clearingCost} credits. Health: +${p.healthGain} by 10y.`;$('finding').append(span);}
 }
 for(const b of actions.querySelectorAll('button'))b.disabled=busy||mutating;
 document.querySelectorAll('[data-view]').forEach(b=>{b.disabled=busy||(b.dataset.view==='close'&&!p);b.classList.toggle('active',b.dataset.view===view);});
 $('outcomes').hidden=state.phase==='survey'||role!=='room'&&!locked;$('fire-controls').hidden=!locked;
 $('without').setAttribute('aria-pressed',String(!showPlan));$('with').setAttribute('aria-pressed',String(showPlan));
 $('recovery').value=years;$('recovery-label').textContent=years+'y';$('fire-time').value=clock*CONFIG.duration;$('fire-label').textContent=(clock*CONFIG.duration).toFixed(1).replace(/\.0$/,'')+' min';
 if(result){const arrivals=showPlan?result.future.arrival:result.baseline.arrival,area=arrivals.filter(t=>Number.isFinite(t)&&t<=clock*CONFIG.duration).length*.0225;$('burned').textContent=clock>0?`Burned: ${area.toFixed(1)} ha. ${showPlan?'With':'Without'} plan.`:'';}
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
   history.replaceState(null,'',flowURL('round.html',credentials,role));
   if(role!=='room'&&view==='close'&&!teamVisits().includes(selected))await act('visit',{patch:selected});
  }
  render();
  briefing();
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
function updateOutcome(){
 if(!state||state.phase==='survey')return;
 if(!fireCache.has(years))fireCache.set(years,review(state.proposals,years));result=fireCache.get(years);
 mode=clock>0?'fire':'recovery';forest.setPlan(showPlan?state.proposals:null,years/CONFIG.years);
 const arrival=clock>0?(showPlan?result.future:result.baseline).arrival:null;
 if(forest.fire!==arrival)forest.setFire(arrival,CONFIG.duration);forest.setFireTime(clock);refreshPlants();render();
}
function briefing(){
 if(!state||state.phase!=='survey'||role!=='room'&&state.ready[role])return;
 const key=state.id+':'+state.round+':'+role;if(briefed.has(key))return;briefed.add(key);
 const copy=BRIEFINGS[role],text=copy.paragraphs.join('\n\n');clearInterval(typing);
 $('briefing-role').textContent=role==='ecology'?'ECOLOGIST':role.toUpperCase();$('briefing-title').textContent=copy.title;$('briefing-accessible').textContent=text;
 $('briefing-text').textContent=reduced?text:'';let at=0;if(!reduced)typing=setInterval(()=>{at+=4;$('briefing-text').textContent=text.slice(0,at);if(at>=text.length)clearInterval(typing);},35);
 if(!$('briefing').open)$('briefing').showModal();
}
async function leavePlay(){
 $('game-mode').disabled=true;
 if(state.role==='room'&&!await act('replay')){$('game-mode').value='play';$('game-mode').disabled=false;return;}
 location.assign(flowURL(state.role==='room'?'expedition.html?fresh=1':'expedition.html',credentials,role));
}
function teams(){
 $('teams-note').textContent=state.role==='room'?'Share one link with each team. Use the team selector to test alone.':'Your team has its own proposal. The room reveals and commits both.';
 const links=$('team-links');links.replaceChildren();
 if(state.teams)for(const [name,token]of Object.entries(state.teams)){
  const label=document.createElement('label');label.textContent=name==='removal'?'Removal team':'Ecologist team';const input=document.createElement('input');input.readOnly=true;input.setAttribute('aria-label',label.textContent+' link');input.value=flowURL('expedition.html',{session:state.id,token},name);input.onclick=()=>input.select();label.append(input);links.append(label);
 }
 $('teams').showModal();
}
for(const p of PATCHES){const b=button(p.key,()=>choose(p.key),'');b.dataset.patch=p.key;b.setAttribute('aria-label','Patch '+p.key);$('patches').append(b);}
for(const b of document.querySelectorAll('[data-close]'))b.onclick=()=>$(b.dataset.close).close();
for(const b of document.querySelectorAll('[data-view]'))b.onclick=()=>camera(b.dataset.view);
$('role').onchange=async()=>{role=$('role').value;history.replaceState(null,'',flowURL('round.html',credentials,role));render();if(view==='close'&&role!=='room'&&state.phase!=='committed'&&!teamVisits().includes(selected))await act('visit',{patch:selected});briefing();};
$('teams-open').onclick=()=>state&&teams();$('game-mode').onchange=()=>{if($('game-mode').value==='expedition')leavePlay();};
document.querySelector('.wordmark').onclick=e=>{if(state){e.preventDefault();leavePlay();}};
$('briefing-begin').onclick=()=>{clearInterval(typing);$('briefing').close();};$('briefing').onclose=()=>clearInterval(typing);
$('recovery').oninput=()=>{years=Number($('recovery').value);showPlan=true;updateOutcome();};$('fire-time').oninput=()=>{clock=Number($('fire-time').value)/CONFIG.duration;updateOutcome();};
$('without').onclick=()=>{showPlan=false;updateOutcome();};$('with').onclick=()=>{showPlan=true;updateOutcome();};
globalThis.roundDiagnostics=()=>({state,role,selected,view,busy,mode,clock,years,showPlan,budget:state?.budget,health:result?.health,fire:result?{baseline:result.baseline.burned,future:result.future.burned}:null,growthPoints:forest.growthPositions?.length/3||0,forest:forest.performance(),lab:lab.diagnostics()});
try{
 const [_,data]=await Promise.all([forest.load(),fetch('field-catalogue.json').then(r=>r.json())]);
 catalogue=[...data.species,...ADDITIONAL_SPECIES];forest.setInventory(catalogue,WORLD);forest.setSettlement(false);
 for(const p of PATCHES)if(forest.outlines)forest.outlines.add(forest.square((p.id%6)*150-375,Math.floor(p.id/6)*150-375,148,0x6c9d78,.6));
 const params=flowParams();
 if(params.has('session')){credentials={session:params.get('session'),token:params.get('token')};accept(await request('state'));}
 else{const s=await request('new');credentials={session:s.id,token:s.token};history.replaceState(null,'',flowURL('round.html',credentials,role));accept(s);}
 busy=false;$('loading').hidden=true;render();briefing();
 setInterval(()=>{if(!mutating&&!document.hidden)refresh();},1200);
}catch(e){$('loading').textContent=e.message;$('loading').append(button(e.status===404?'New round':'Retry',()=>{if(e.status===404)history.replaceState(null,'',location.pathname);location.reload();}));toast(e.message);}
