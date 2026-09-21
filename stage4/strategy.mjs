import {StrategyForest} from './strategy-render.mjs';
import {newGame,clone,act,quote,ledger,metrics,studyPlot,replay,WORKABLE_IDS,VERSION} from './strategy-model.mjs';
import {WORLD,coordinate} from './world.mjs';
import {ADDITIONAL_SPECIES} from './forest-flora.mjs';
import {speciesRecord} from './species-record.mjs';
import {StructureLab} from './structure-lab.mjs';
const $=id=>document.getElementById(id);
const strategies=[
 {name:'Rush',line:'Clear and plant across the landscape.',weak:'However, old work can fill with weeds while you move on.'},
 {name:'One at a time',line:'Stay with one planting until its canopy closes.',weak:'Your planting gets attention, but fire can spread through the land left waiting.'},
 {name:'Anchor',line:'Start beside standing forest, then grow outwards.',weak:'Neighbours shelter young trees. However, planting still costs money and young trees can burn.'}
];
const params=new URLSearchParams(location.hash.slice(1));
let foundation=null,seed=Number(params.get('seed'))||113;
try{const f=JSON.parse(params.get('foundation')||'null'),valid=id=>Number.isInteger(id)&&WORLD[id]?.active;if(f&&valid(f.restored)&&valid(f.cleared)&&Number.isFinite(f.credits))foundation={restored:f.restored,cleared:f.cleared,...(valid(f.previousCleared)?{previousCleared:f.previousCleared}:{}),cared:!!f.cared,credits:Math.max(0,Math.min(100,f.credits))};}catch{}
let returnURL=new URL('round.html',location.href);
try{const u=new URL(params.get('return'));if(['http:','https:'].includes(u.protocol)&&u.hostname===location.hostname&&/\/(round|expedition)\.html$/.test(u.pathname))returnURL=u;}catch{}
const saveKey='pyrocene-strategy:'+VERSION+':'+JSON.stringify(foundation);
let game=newGame(seed,foundation),moves=[],approach=0,selected=foundation?.restored??WORKABLE_IDS[0],view='forest',busy=true,catalogue=[],photos={},pins=[],skipPhase=null;
let restoredSave=false;
try{const saved=JSON.parse(sessionStorage.getItem(saveKey)||'null');if(saved&&saved.seed===seed&&Array.isArray(saved.moves)&&saved.moves.length<=24){game=replay(seed,saved.moves,foundation);moves=saved.moves;approach=Math.max(0,Math.min(2,saved.approach||0));selected=game.plots[saved.selected]?saved.selected:selected;restoredSave=true;}}catch{}
const forest=new StrategyForest($('landscape'),{playable:WORKABLE_IDS,select:id=>choose(id),specimen:meet});
forest.reducedMotion=matchMedia('(prefers-reduced-motion: reduce)').matches;
class StrategyStructureLab extends StructureLab{
 sync(){super.sync();if(!this.models||!this.plot?.strategy)return;const p=this.plot;this.panels[1].panel.querySelector('h2').textContent='Selected patch - '+coordinate(p.id);this.panels[1].caption.textContent=`${Math.round(p.canopy*100)}% canopy closure. ${Math.round(p.grass*100)}% weeds. ${p.state==='young'?'Young planting.':p.state==='cleared'?'Not planted yet.':p.state==='invaded'?'Invasive cover.':'Standing forest.'}`;}
}
const lab=new StrategyStructureLab({forest,catalogue:()=>catalogue});
function save(){try{sessionStorage.setItem(saveKey,JSON.stringify({seed,moves,approach,selected}));}catch{}}
function toast(message){$('toast').textContent=message;$('toast').hidden=false;clearTimeout(toast.timer);toast.timer=setTimeout(()=>$('toast').hidden=true,5000);}
function button(text,fn,cls='secondary'){const b=document.createElement('button');b.textContent=text;b.className=cls;b.onclick=fn;return b;}
function closeRecord(){$('plant-guide').hidden=true;$('plot-plants').value='';}
function livePlot(){const p={...WORLD[selected],...studyPlot(game,selected),strategy:true};if(!game.plots[selected].clearings&&p.state==='invaded')delete p.succession;return p;}
function specimens(){const p=livePlot();forest.setSpecimens(p.speciesIds.map(id=>({id,speciesId:id,label:catalogue.find(s=>s.id===id)?.name||id})));forest.setFieldVisited?.(true);}
function newCanopies(){return metrics(game).restoredCanopies;}
const canopyPercent=p=>p.state==='closed'?Math.round(p.canopy*100):Math.min(99,Math.floor(p.canopy*100));
function eventText(e){
 if(e.type==='fire')return `Fire started at ${e.origins.map(coordinate).join(', ')} and burned ${e.burned.length} patch${e.burned.length===1?'':'es'}.`;
 if(e.type==='closed')return `${coordinate(e.plot)} has closed its canopy and left the ledger.`;
 if(e.type==='reinvaded')return `Weeds have overtaken ${coordinate(e.plot)}. It leaves the ledger, but its fuel remains.`;
 if(e.type==='fireDamage')return game.plots[e.plot].state==='cleared'?`Fire killed the young planting at ${coordinate(e.plot)}. It needs planting again.`:`Fire damaged the ${game.plots[e.plot].state==='young'?'young trees':'canopy'} at ${coordinate(e.plot)}.`;
 return e.text;
}
function report(events=game.lastEvents){
 const important=events.filter(e=>['fire','reinvaded','closed','closure','reinvasion','fireDamage'].includes(e.type));
 const e=important.find(e=>e.type==='reinvaded')||important.find(e=>e.type==='fireDamage'&&game.plots[e.plot].state!=='closed')||important.find(e=>e.type==='closed')||important.find(e=>e.type==='fireDamage')||important.find(e=>e.type==='fire')||events.at(-1),fire=important.find(e=>e.type==='fire');
 $('season-message').textContent=e?(eventText(e)+(fire&&fire!==e?' '+eventText(fire):'')):'Choose a patch on the map. Looking takes no time.';
 $('event-list').replaceChildren(...events.filter(e=>e.text).map(e=>{const p=document.createElement('p');p.textContent=eventText(e);return p;}));
 $('season-details').hidden=!events.length;
}
function render(){
 const p=game.plots[selected],m=metrics(game),open=ledger(game);
 $('season').textContent=`YEAR ${game.seasonMonths/12} / 12`;
 $('patch-title').textContent=coordinate(selected)+(p.state==='young'?' - young planting':p.state==='cleared'?' - cleared':p.state==='closed'?' - closed canopy':' - invasives');
 const note=studyPlot(game,selected);
 $('finding').textContent=p.state==='young'?`Canopy ${canopyPercent(p)}%. Weeds ${Math.round(p.grass*100)}%. ${note.shelter>.35?'Nearby forest shelters the young trees.':'Open surroundings leave this planting exposed.'}`:p.state==='invaded'?'Removal earns credits, but cleared ground needs planting before the weeds return.':p.state==='cleared'?'The ground is open. Plant here before the invasives take it back.':'The canopy is closed. This forest shelters nearby planting, though a severe fire can still reach it.';
 $('funds').textContent=`${game.credits} credits`;
 $('patch-actions').replaceChildren();
 for(const verb of ['remove','restore']){const q=quote(game,verb,selected),b=button(verb==='remove'?'Remove':'Restore',()=>take(verb), 'primary');const cost=document.createElement('small');cost.textContent=q.productive?`${q.cost} cost${q.returns?' - '+q.returns+' return':''}`:p.state==='closed'?'No work needed':verb==='restore'?(p.state==='young'?'Already planted':'Clear first'):p.state==='invaded'&&open.length>=5?'Ledger full':'No weeds to remove';b.append(cost);b.disabled=busy||game.status!=='playing'||!q.valid;b.title=q.reason||'';$('patch-actions').append(b);}
 $('wait').disabled=busy||game.status!=='playing';$('structure').disabled=busy;$('plot-plants').disabled=busy;
 const lost=game.ledgerHistory.filter(e=>e.outcome==='reinvaded').length;
 $('progress').textContent=`${newCanopies()}/3 canopies closed - ${m.burnedPlots} plots burned${lost?' - '+lost+' reinvasions':''}`;
 $('ledger-count').textContent=`${open.length} / 5`;$('ledger-blocks').replaceChildren();
 for(const entry of open){const p=game.plots[entry.id],b=button('',()=>choose(p.id),'ledger-block');b.style.setProperty('--fill',canopyPercent(p)+'%');b.setAttribute('aria-pressed',String(p.id===selected));b.setAttribute('aria-label',`${coordinate(p.id)}, canopy ${canopyPercent(p)}%, ${p.state}`);const title=document.createElement('strong');title.textContent=coordinate(p.id)+' - '+canopyPercent(p)+'%';const state=document.createElement('span');state.textContent=p.state==='young'?`${Math.round(p.grass*100)}% weeds`:'Needs planting';b.append(title,state);b.disabled=busy;$('ledger-blocks').append(b);}
 for(let i=open.length;i<5;i++){const empty=document.createElement('span');empty.className='ledger-empty';empty.textContent=i===open.length?'Open slot':'';$('ledger-blocks').append(empty);}
 for(const {id,el} of pins){const p=game.plots[id];el.classList.toggle('chosen',id===selected);el.classList.toggle('closed',p.state==='closed');el.classList.toggle('burned',p.burned>0);el.disabled=busy;el.title=coordinate(id)+' - '+p.state;}
 $('approach-open').textContent=(approach+1)+'. '+strategies[approach].name;
 $('phase-label').textContent=busy?'SEASON PASSING':game.status==='playing'?'YOUR MOVE':'TWELVE YEARS LATER';
 document.querySelectorAll('[data-view]').forEach(b=>{b.disabled=busy;b.classList.toggle('active',b.dataset.view===view);});
 const picker=$('plot-plants'),ids=livePlot().speciesIds,key=selected+':'+ids.join(',');if(picker.dataset.key!==key){picker.dataset.key=key;picker.replaceChildren(new Option('Choose a plant',''));for(const id of ids){const s=catalogue.find(s=>s.id===id);if(s)picker.append(new Option(s.name,id));}}
}
async function choose(id){if(busy||!game.plots[id])return;selected=id;closeRecord();forest.selectPlot(id);save();if(view==='close')await changeView('close');else render();}
async function changeView(next){if(busy)return;busy=true;view=next;closeRecord();render();try{await forest.setView(view,selected);if(view==='close')specimens();else forest.setSpecimens([]);}catch(e){toast(e.message);}finally{busy=false;render();}}
function meet(id){if(busy)return;const s=catalogue.find(s=>s.id===id);if(!s)return;const p=livePlot();$('guide-content').replaceChildren(speciesRecord({species:s,photo:photos[s.photoAssetId||s.id],plot:p,condition:p.moisture>.6?'The ground is damp here.':'The opening lets the ground dry.',seedContext:{plot:p},immersive:true,onStructure:()=>openStructure(id)}));$('plant-guide').hidden=false;}
async function openStructure(id=null){closeRecord();if(view!=='close')await changeView('close');if(!busy)lab.open(livePlot(),id);}
async function take(verb){
 if(busy)return;closeRecord();busy=true;render();
 try{const next=clone(game),events=act(next,verb,verb==='wait'?null:selected);game=next;moves.push(verb==='wait'?'wait':verb+':'+coordinate(selected));save();forest.setState(game);report(events);const fire=events.find(e=>e.type==='fire');forest.setFireEvent(fire||null);
  if(fire&&view==='close'){view='forest';forest.setSpecimens([]);await forest.setView(view,selected);}
  render();$('phase-label').textContent=fire?'FIRE SEASON':'SIX MONTHS LATER';
  await new Promise(resolve=>{const duration=forest.reducedMotion?150:fire?4200:600,start=performance.now();let ended=false;const finish=()=>{if(ended)return;ended=true;forest.animateFire(1);$('skip').hidden=true;skipPhase=null;resolve();};skipPhase=finish;$('skip').hidden=!fire;function frame(now){if(ended)return;forest.animateFire(Math.min(1,(now-start)/duration));if(now-start>=duration)finish();else requestAnimationFrame(frame);}requestAnimationFrame(frame);});
  if(view==='close')specimens();
 }catch(e){toast(e.message);}finally{busy=false;render();}
 if(game.status!=='playing')showReplay();
}
function showIntro(){const cards=$('strategy-cards');cards.replaceChildren();strategies.forEach((s,i)=>{const b=button('',()=>{approach=i;save();showCards();});const title=document.createElement('strong');title.textContent=(i+1)+'. '+s.name;const line=document.createElement('span');line.textContent=s.line;const weak=document.createElement('em');weak.textContent=s.weak;b.append(title,line,weak);b.dataset.strategy=i;cards.append(b);});showCards();$('foundation-note').textContent=foundation?`Your shared planting at ${coordinate(foundation.restored)} carries forward. You start with ${newGame(seed,foundation).credits} credits. From here, your decisions are private.`:'Start with 12 credits. Try closing three canopies before twelve years have passed.';$('strategy-intro').showModal();}
function showCards(){document.querySelectorAll('[data-strategy]').forEach(b=>b.setAttribute('aria-pressed',String(Number(b.dataset.strategy)===approach)));render();}
function showReplay(){$('run-summary').textContent=`${game.seasonMonths/12} years: ${newCanopies()} new canopies, ${metrics(game).burnedPlots} plots burned and ${ledger(game).length} plots still vulnerable. ${game.credits} credits remain.`;$('replay-dialog').showModal();}
function restart(newWeather){if(busy)return;if(newWeather)seed=crypto.getRandomValues(new Uint32Array(1))[0];game=newGame(seed,foundation);moves=[];forest.setState(game,true);forest.setFireEvent(null);save();const p=new URLSearchParams(location.hash.slice(1));p.set('seed',seed);history.replaceState(null,'',location.pathname+'#'+p);$('replay-dialog').close();report();render();showIntro();}
$('begin').onclick=$('intro-back').onclick=()=>$('strategy-intro').close();$('approach-open').onclick=showIntro;$('replay-open').onclick=showReplay;$('replay-back').onclick=()=>$('replay-dialog').close();$('retry').onclick=()=>restart(false);$('new-weather').onclick=()=>restart(true);$('wait').onclick=()=>take('wait');$('skip').onclick=()=>skipPhase?.();$('structure').onclick=()=>openStructure();$('record-close').onclick=closeRecord;$('plot-plants').onchange=()=>meet($('plot-plants').value);
document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>changeView(b.dataset.view));$('stage').onchange=()=>{if($('stage').value==='shared')location.assign(returnURL);};document.querySelector('.wordmark').onclick=e=>{e.preventDefault();location.assign(returnURL);};
document.addEventListener('keydown',e=>{if(e.key==='Escape')closeRecord();});
globalThis.strategyDiagnostics=()=>({game,selected,view,busy,approach,moves,forest:forest.diagnostics(),lab:lab.diagnostics()});
try{const [_,data,oldPhotos,newPhotos]=await Promise.all([forest.load(),fetch('field-catalogue.json').then(r=>r.json()),fetch('plant-images.json').then(r=>r.json()),fetch('field-photos.json').then(r=>r.json())]);catalogue=[...data.species,...ADDITIONAL_SPECIES];photos={...oldPhotos.images,...newPhotos.photos};forest.setInventory(catalogue,WORLD);forest.setSettlement(false);forest.setState(game,true);pins=WORKABLE_IDS.map(id=>({id,el:button(coordinate(id),()=>choose(id))}));forest.setPins(pins);forest.pins.classList.add('round-labels');forest.selectPlot(selected);busy=false;$('loading').hidden=true;report();render();if(!restoredSave)showIntro();}catch(e){$('loading').textContent='Could not open Strategy: '+e.message;$('loading').append(button('Retry',()=>location.reload()));console.error(e);}
