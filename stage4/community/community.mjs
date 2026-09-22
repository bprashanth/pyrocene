import {CommunityForest} from './render.mjs';
import {newGame,clone,act,quote,ledger,metrics,studyPlot,replay,VERSION,CONFIG,WORLD,GRID,coordinate,inspect,SCENARIO,ENTERPRISES} from './model.mjs';
import {ADDITIONAL_SPECIES} from '../forest-flora.mjs';
import {speciesRecord} from '../species-record.mjs';
import {createPrelude} from './prelude.mjs';
const $=id=>document.getElementById(id),params=new URLSearchParams(location.hash.slice(1));
// The live prototype has its own process so no in-memory shared room restarts.
// Portable and test servers keep this link on their own origin.
if(location.port==='8035')for(const a of document.querySelectorAll('a[href="strategy.html"]')){const u=new URL(a.href);u.port='8033';a.href=u;}
let seed=Number(params.get('seed'))||991,enterprise=params.get('enterprise')==='nursery'?'nursery':'shade';
let game=newGame(seed,{enterprise}),moves=[],selected=SCENARIO.bufferIds[0],view='forest',busy=true,catalogue=[],photos={},pins=[],started=false,celebrated=false;
const saveKey='pyrocene-community:'+VERSION;
try{const s=JSON.parse(sessionStorage.getItem(saveKey)||'null');if(!params.has('fresh')&&s?.seed===seed&&Array.isArray(s.moves)&&s.moves.length<=CONFIG.turns){enterprise=s.enterprise==='nursery'?'nursery':'shade';game=replay(seed,s.moves,{enterprise});moves=s.moves;selected=game.plots[s.selected]?s.selected:selected;for(const id of s.inspected||[])if(game.plots[id])inspect(game,id);started=!!s.started;celebrated=!!s.celebrated;}}catch{}
if(params.has('fresh')){params.delete('fresh');history.replaceState(null,'',location.pathname+'#'+params);}
const forest=new CommunityForest($('landscape'),{select:id=>choose(id),specimen:meet});
forest.reducedMotion=matchMedia('(prefers-reduced-motion: reduce)').matches;
forest.setBuffers(SCENARIO.bufferIds);
function save(){try{sessionStorage.setItem(saveKey,JSON.stringify({seed,enterprise,moves,selected,started,celebrated,inspected:Object.values(game.plots).filter(p=>p.inspected).map(p=>p.id)}));}catch{}}
function button(text,fn,cls='secondary'){const b=document.createElement('button');b.textContent=text;b.className=cls;b.onclick=fn;return b;}
function toast(text){$('toast').textContent=text;$('toast').hidden=false;clearTimeout(toast.timer);toast.timer=setTimeout(()=>$('toast').hidden=true,4500);}
function closeRecord(){$('plant-guide').hidden=true;$('plot-plants').value='';}
function livePlot(){const p={...WORLD[selected],...studyPlot(game,selected)};if(!game.plots[selected].clearings&&p.state==='invaded')delete p.succession;return p;}
function specimens(){const p=livePlot(),priority=['theobroma_grandiflorum','urochloa_brizantha','urochloa_decumbens'];const ids=p.community?.cycles?[...p.speciesIds].sort((a,b)=>(priority.includes(a)?priority.indexOf(a):99)-(priority.includes(b)?priority.indexOf(b):99)):p.speciesIds;forest.setSpecimens(ids.map(id=>({id,speciesId:id,label:catalogue.find(s=>s.id===id)?.name||id})));forest.setFieldVisited(true);}
const percent=p=>Math.min(p.state==='closed'?100:99,Math.floor(p.canopy*100));
const ledgerPercent=p=>p.community?.active?Math.min(100,Math.floor(p.canopy/(ENTERPRISES[p.community.enterprise].canopyCap*.8)*100)):percent(p);
const money=n=>Number(n||0).toFixed(1);
const isBuffer=p=>!!(p.community?.cycles&&(p.community.active||!['young','closed'].includes(p.state)));
const targetsClosed=()=>SCENARIO.restorationIds.filter(id=>game.plots[id].state==='closed').length;
function render(){
 const p=game.plots[selected],m=metrics(game),known=p.visited||p.inspected,open=ledger(game),c=p.community?.cycles&&(p.community.active||!['young','closed'].includes(p.state))?p.community:null;
 $('enterprise-name').textContent=enterprise==='shade'?'Shade crops':'Seed nursery';
 $('season').textContent=`YEAR ${game.seasonMonths/12} / ${CONFIG.turns/2}`;
 $('funds').textContent=game.credits;$('forest-health').textContent=m.health.toFixed(1)+' / 100';
 const state=c?(p.failedPlanting?'damaged buffer':c.active&&p.canopy>=ENTERPRISES[c.enterprise].canopyCap*.8?'working buffer':'young buffer'):p.failedPlanting?'burned planting':p.state==='young'?'young forest':p.state==='cleared'?'open ground':p.state==='closed'?'standing forest':'invasives';
 $('patch-title').textContent=coordinate(selected)+(known?' - '+state:'');
 let line=!known?'Close view lets you inspect before paying for a crew visit.':p.failedPlanting?'Fire damaged the planting. Rebuild before weeds take the opening.':c?`Shade ${percent(p)}%. Weeds ${Math.round(p.grass*100)}%. ${c.lastCare?'The association paid for tending this season.':'The buffer still needs attention while income develops.'}`:SCENARIO.bufferIds.includes(selected)&&p.state==='cleared'?'This gap sits between dry fuel and young forest. Plant native trees here, or help the association start a buffer.':p.state==='young'?`Canopy ${percent(p)}%. Weeds ${Math.round(p.grass*100)}%. ${SCENARIO.restorationIds.includes(selected)?'The young forest needs shelter at its exposed edge.':'Return before the weeds overtake the planting.'}`:p.state==='invaded'?'Clearing earns credits, but leaves another plot needing care.':p.state==='cleared'?'Plant this opening before the weeds return.':'Standing forest supplies shade and native seed.';
 $('finding').textContent=line;
 $('patch-actions').replaceChildren();
 const verbs=['remove','restore'];if(SCENARIO.bufferIds.includes(selected)&&(!c||!c.active))verbs.push('partner');
 for(const verb of verbs){const q=quote(game,verb,selected),choice=document.createElement('div'),cost=document.createElement('div');choice.className='action-choice'+(verb==='partner'?' partner-choice':'');cost.className='action-cost';
  const label=verb==='partner'?(c?'Rebuild buffer':'Start partnership'):verb==='remove'&&(p.state==='young'||p.state==='cleared'||p.state==='agroforestry')?'Weed':verb==='remove'?'Remove':'Restore';
  const b=button(label,()=>take(verb),'primary');b.dataset.action=verb;b.disabled=busy||game.status!=='playing'||!q.valid;b.title=q.reason||'';
  if(verb==='partner')cost.textContent=q.localContribution?`Cost: ${money(q.cost)} project + ${money(q.localContribution)} local credits.`:`Cost: ${q.cost??5} credits. Income pays local care.`;
  else if(verb==='restore'&&!q.valid&&p.state!=='cleared')cost.textContent=p.community?.active?'Managed buffer':p.state==='young'?'Already planted':p.state==='closed'?'Canopy intact':'Clear first';
  else cost.textContent=`Cost: ${q.cost}${verb==='remove'?` - ${p.receipt?.verb==='remove'?'Last return: '+p.receipt.returns:'Return: '+(p.state==='invaded'?'?':'0')}`:''}`;
  choice.append(b,cost);$('patch-actions').append(choice);
 }
 $('community-account').hidden=!c;if(c)$('community-account').textContent=`Local income: ${money(c.earned)} - care paid: ${money(c.carePaid)}. Reserve: ${money(c.reserve)}.`;
 $('next-season').disabled=busy||game.status!=='playing';
 $('progress').textContent=`${targetsClosed()} / ${SCENARIO.restorationIds.length} edge plots recovered - ${m.burnedPlots} plots burned`;
 $('ledger-count').textContent=`${open.length} / ${CONFIG.commitmentCap}`;$('ledger-blocks').replaceChildren();
 for(const entry of open){const p=game.plots[entry.id],b=button('',()=>choose(p.id),'ledger-block');b.style.setProperty('--fill',ledgerPercent(p)+'%');b.setAttribute('aria-pressed',String(p.id===selected));b.setAttribute('aria-label',`${coordinate(p.id)}, ${ledgerPercent(p)}% ${isBuffer(p)?'buffer establishment':'canopy'}`);b.dataset.plot=p.id;
  const title=document.createElement('strong'),sub=document.createElement('span');title.textContent=coordinate(p.id)+' - '+ledgerPercent(p)+'%';sub.textContent=p.failedPlanting?'Burned - replant':isBuffer(p)?'Community buffer':p.state==='young'?Math.round(p.grass*100)+'% weeds':'Needs planting';b.classList.toggle('failed',p.failedPlanting);b.classList.toggle('community',isBuffer(p));b.append(title,sub);b.disabled=busy;$('ledger-blocks').append(b);}
 if(!open.length){const span=document.createElement('span');span.className='ledger-empty';span.textContent='No unstable plots';$('ledger-blocks').append(span);}
 const ids=Object.values(game.plots).filter(p=>p.visited||p.id===selected||SCENARIO.ignitionIds.includes(p.id)).map(p=>p.id);
 if(pins.map(p=>p.id).join(',')!==ids.join(',')){pins=ids.map(id=>({id,el:button(coordinate(id),()=>choose(id))}));forest.setPins(pins);}
 for(const {id,el}of pins){const p=game.plots[id];el.classList.toggle('chosen',id===selected);el.classList.toggle('community',isBuffer(p));el.classList.toggle('burned',!!p.failedPlanting);el.disabled=busy;el.title=coordinate(id)+(isBuffer(p)?' - community buffer':'');}
 $('phase-label').textContent=busy?'SEASON CHANGING':game.status==='playing'?'YOUR MOVE':'FINISHED';
 document.querySelectorAll('[data-view]').forEach(b=>{b.disabled=busy;b.classList.toggle('active',b.dataset.view===view);});
 const picker=$('plot-plants'),species=livePlot().speciesIds,key=selected+':'+species.join(',');picker.disabled=busy||!known;picker.closest('label').hidden=!known;
 if(picker.dataset.key!==key){picker.dataset.key=key;picker.replaceChildren(new Option('Choose a plant',''));for(const id of species){const s=catalogue.find(s=>s.id===id);if(s)picker.append(new Option(s.name,id));}}
}
async function choose(id){if(busy||!game.plots[id])return;selected=id;closeRecord();forest.selectPlot(id);save();if(view==='close')await changeView('close');else render();}
async function changeView(next){if(busy)return;busy=true;view=next;closeRecord();render();try{await forest.setView(view,selected);if(view==='close'){inspect(game,selected);specimens();save();}else forest.setSpecimens([]);}catch(e){toast(e.message);}finally{busy=false;render();}}
function meet(id){if(busy)return;const s=catalogue.find(s=>s.id===id);if(!s)return;const p=livePlot();$('guide-content').replaceChildren(speciesRecord({species:s,photo:photos[s.photoAssetId||s.id],plot:p,condition:p.community?.cycles?(s.status==='Invasive'?'Still present here. Tending keeps it from overtaking the planting.':'Grown with native trees in this managed buffer.'):'',seedContext:{plot:p,grid:{columns:GRID,cells:WORLD.map(w=>game.plots[w.id]?{...game.plots[w.id],active:true}:null)}},immersive:true}));$('plant-guide').hidden=false;}
// A season may contain an interior fire and an escaped boundary fire. Show both.
function seasonFire(events){
 const fires=events.filter(e=>e.type==='fire');if(!fires.length)return null;
 const out={origins:[],burned:[],arrival:{},coverage:{},entering:{},paths:[]};
 for(const fire of fires){out.origins.push(...fire.origins);out.paths.push(...fire.paths);for(const id of fire.burned){out.burned.push(id);out.arrival[id]=Math.min(out.arrival[id]??Infinity,fire.arrival[id]??0);out.coverage[id]=Math.min(1,(out.coverage[id]||0)+(fire.coverage[id]||0));if(fire.entering[id]!=null)out.entering[id]=fire.entering[id];}}
 out.origins=[...new Set(out.origins)];out.burned=[...new Set(out.burned)];return out;
}
function noteFor(events){const fire=seasonFire(events),community=events.filter(e=>e.type==='community'),closed=events.find(e=>e.type==='closed'),lost=events.find(e=>e.type==='reinvaded');
 if(fire){const hit=SCENARIO.restorationIds.filter(id=>fire.burned.includes(id));return hit.length?`Fire reached the young forest at ${hit.map(coordinate).join(' and ')}. ${game.plots[hit[0]].failedPlanting?'The planting needs replacing.':'Some planting survived.'}`:`Fire crossed ${fire.burned.length} plots. The young forest was not reached this time.`;}
 if(lost)return `${coordinate(lost.plot)} filled with weeds before its canopy closed.`;
 if(closed)return `${coordinate(closed.plot)} ${game.plots[closed.plot].community?.active?'now has established shade. Local tending continues.':'closed its canopy and left Unstable plots.'}`;
 if(community.length)return community.find(e=>e.plot===selected)?.text||community[0].text;
 if(game.turn===1)return 'Watch the open edge as you tend the young forest behind it.';
 return 'Six months passed. Check the unstable plots before opening another.';
}
async function take(verb){if(busy)return;busy=true;closeRecord();render();try{const next=clone(game),events=act(next,verb,verb==='wait'?null:selected);game=next;moves.push(verb==='wait'?'wait':verb+':'+coordinate(selected));save();forest.setState(game);forest.setInventory(catalogue,WORLD.map(w=>game.plots[w.id]||w));const fire=seasonFire(events);forest.setFireEvent(fire||null);$('season-note').textContent=noteFor(events);
 if(fire&&view==='close'){view='forest';forest.setSpecimens([]);await forest.setView(view,selected);}render();
 await new Promise(resolve=>{const duration=forest.reducedMotion?120:fire?3000:450,start=performance.now();function frame(now){forest.animateFire(Math.min(1,(now-start)/duration));if(now-start>=duration)resolve();else requestAnimationFrame(frame);}requestAnimationFrame(frame);});if(view==='close')specimens();
 }catch(e){toast(e.message);}finally{busy=false;render();}if(game.status!=='playing')showReplay();else if(targetsClosed()===SCENARIO.restorationIds.length&&!celebrated){celebrated=true;save();showReplay();}}
function showReplay(){$('replay-title').textContent=targetsClosed()===SCENARIO.restorationIds.length?'The young forest has recovered.':'Try another approach?';$('replay-back').textContent=game.status==='playing'?'Keep exploring':'Back';$('run-summary').textContent=`${targetsClosed()} of ${SCENARIO.restorationIds.length} young edge plots recovered. ${metrics(game).burnedPlots} plots burned. ${game.credits} credits remain. Local income paid ${metrics(game).communityCare||0} credits of tending.`;$('replay-dialog').showModal();}
function reset(newWeather=false){if(busy)return;if(newWeather)seed=crypto.getRandomValues(new Uint32Array(1))[0];game=newGame(seed,{enterprise});moves=[];selected=SCENARIO.bufferIds[0];started=false;celebrated=false;closeRecord();forest.setState(game,true);forest.setInventory(catalogue,WORLD.map(w=>game.plots[w.id]||w));forest.selectPlot(selected);forest.setFireEvent(null);$('season-note').textContent='The dashed squares mark gaps along the exposed edge.';history.replaceState(null,'',location.pathname+'#'+new URLSearchParams({seed,enterprise}));save();render();$('replay-dialog').close();$('strategy-intro').showModal();}
function enterpriseCards(){document.querySelectorAll('[data-enterprise]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.enterprise===enterprise)));}
document.querySelectorAll('[data-enterprise]').forEach(b=>b.onclick=()=>{enterprise=b.dataset.enterprise;game=newGame(seed,{enterprise});moves=[];selected=SCENARIO.bufferIds[0];forest.setState(game,true);forest.setInventory(catalogue,WORLD.map(w=>game.plots[w.id]||w));forest.selectPlot(selected);enterpriseCards();save();render();});
document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>changeView(b.dataset.view));
$('begin').onclick=$('intro-back').onclick=()=>{started=true;save();$('strategy-intro').close();};$('next-season').onclick=()=>take('wait');$('record-close').onclick=closeRecord;$('plot-plants').onchange=()=>meet($('plot-plants').value);$('replay-open').onclick=showReplay;$('replay-back').onclick=()=>$('replay-dialog').close();$('retry').onclick=()=>reset();$('new-weather').onclick=()=>reset(true);
globalThis.communityDiagnostics=()=>({game,selected,view,busy,moves,enterprise,scenario:SCENARIO,forest:forest.diagnostics()});
try{const[_,data,oldPhotos,newPhotos]=await Promise.all([forest.load(),fetch('field-catalogue.json').then(r=>r.json()),fetch('plant-images.json').then(r=>r.json()),fetch('field-photos.json').then(r=>r.json())]);catalogue=[...data.species,...ADDITIONAL_SPECIES];photos={...oldPhotos.images,...newPhotos.photos};forest.setInventory(catalogue,WORLD.map(w=>game.plots[w.id]||w));forest.setState(game,true);forest.setSettlement(false);forest.pins.classList.add('round-labels');forest.selectPlot(selected);busy=false;$('loading').hidden=true;$('season-note').textContent='The dashed squares mark gaps along the exposed edge.';enterpriseCards();render();if(!started||params.has('prelude'))createPrelude(forest,()=>{if(!started)$('strategy-intro').showModal();}).open();save();}catch(e){$('loading').textContent='Could not open Community: '+e.message;console.error(e);}
