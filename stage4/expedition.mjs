import { ExpeditionForest } from './expedition-render.mjs';
import { WORLD, ACTIVE, MISSIONS, fieldRecord, coordinate } from './world.mjs';
import { STORAGE_KEY, fresh, restore, change, knownPlants, progress, usefulNext } from './expedition-state.mjs';
import { fieldNetwork } from './field-network.mjs';
import { phosphorImage } from './field-media.mjs';

const $=id=>document.getElementById(id);
let state=fresh(), view='forest', busy=false, catalogue=[], humans=[], photos={}, book=null, sort='found', mapPlants=new Set(), mapped=[], currentTab='traces';
let reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
let sensorMap=[],sensorCaption='';
const prototype=new URLSearchParams(location.search).get('mode')||'cases';
function playProgress(){
  const p=progress(state);
  if(prototype==='collection'){
    const plants=knownPlants(state),n=plants.filter(id=>catalogue.find(s=>s.id===id)?.status==='Native').length;
    p[0]={done:n>=10&&plants.length-n>=3,text:`${n}/10 native - ${plants.length-n}/3 invasive`};
  }
  return p;
}
try{state=restore(JSON.parse(localStorage.getItem(STORAGE_KEY)||'null'));}catch{}
const forest=new ExpeditionForest($('landscape'),{select:choose,specimen:meet,qualityChanged:low=>{$('low-detail').checked=low;}});
forest.reducedMotion=reduced;
const network=fieldNetwork({radioFrame,radioBody:$('radio-body'),radioActions:$('radio-actions'),openDialog,toast,visit:async id=>{await camera('overhead');await choose(id);},overlay:async(ids,caption)=>{sensorMap=ids;sensorCaption=caption;mapped=[];await camera('overhead');update();},onChange:update});
const currentWorld=()=>network.world()||WORLD;
globalThis.pyroceneDiagnostics=()=>({...forest.performance(),view,tls:forest.tlsActive,tlsCrop:forest.currentTLS?.id,visited:state.visited.length,plants:knownPlants(state).length,mission:state.mission,completed:state.completed.length,prototype,network:network.stats()});
function el(tag,text,cls){const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(cls)e.className=cls;return e;}
function btn(text,action,cls){const b=el('button',text,cls);b.onclick=action;return b;}
function link(text,url){const a=el('a',text);a.href=url;a.target='_blank';a.rel='noopener';return a;}
function toast(text){$('toast').textContent=text;$('toast').hidden=false;clearTimeout(toast.timer);toast.timer=setTimeout(()=>$('toast').hidden=true,4300);}
function act(type,value){state=change(state,type,value);save();}
function save(){try{localStorage.setItem(STORAGE_KEY,JSON.stringify(state));}catch{toast('This browser cannot save your discoveries. You can still play.');}}
function openDialog(id){for(const d of document.querySelectorAll('dialog[open]'))d.close();closeBook();$(id).showModal();}
for(const b of document.querySelectorAll('[data-close]'))b.onclick=()=>$(b.dataset.close).close();
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!$('plant-guide').hidden)closeBook();});

function update(){
  const known=knownPlants(state), p=playProgress(), id=state.selected;
  $('plant-count').textContent=known.length;
  $('mission-number').textContent=prototype==='wander'?'FIELD WORK':`MISSION ${state.mission+1} / 4`;
  $('mission-title').textContent=prototype==='collection'?`Meet the plants (${known.length}/13)`:MISSIONS[state.mission].title;
  $('radio-open').classList.toggle('incoming',p[state.mission].done&&!state.completed.includes(state.mission));
  $('radio-open').textContent=p[state.mission].done&&!state.completed.includes(state.mission)?'Radio - report ready':'Radio';
  $('place-context').hidden=id===null;
  $('place-coordinate').textContent=id===null?'':`FIELD POSITION ${coordinate(id)}`;
  $('place-description').textContent=busy?'Looking closer.':view==='close'?'Choose a plant name.':'Choose a square, then Close view.';
  document.querySelectorAll('[data-view]').forEach(b=>{b.disabled=busy||(b.dataset.view==='close'&&id===null);b.classList.toggle('active',b.dataset.view===view);b.setAttribute('aria-pressed',String(b.dataset.view===view));});
  forest.setPlots([]);
  forest.setSpecimens(state.visited.includes(id)?WORLD[id].speciesIds.map(sp=>({id:sp,speciesId:sp,label:catalogue.find(s=>s.id===sp)?.name||sp})):[]);
  forest.setFieldVisited(state.visited.includes(id));
  forest.setSettlement(false);
  const matches=ACTIVE.map(c=>({id:c.id,strength:c.speciesIds.filter(sp=>mapped.includes(sp)).length/3})).filter(c=>c.strength);
  forest.showMatches(sensorMap.length?sensorMap.map(id=>({id,strength:.8})):matches);
  $('map-summary').hidden=(!mapped.length&&!sensorMap.length)||view==='close';
  $('match-count').textContent=sensorMap.length?sensorCaption:`${mapped.length} plants - ${matches.length} possible places`;
}
async function choose(id){
  if(busy)return;
  if(!WORLD[id]?.active){toast('There are few measured returns here. Try another place or open Map.');return;}
  closeBook();act('select',id);forest.selectPlot(id);
  if(view==='close')await camera('close');else update();
}
async function camera(next){
  if(busy||next==='close'&&state.selected===null)return;
  closeBook();$('plot-notes').hidden=true;
  busy=true;view=next;update();
  try{
    if(await forest.setView(next,state.selected)===false)return;
    if(next==='close'){
      act('scan');act('visit');
      for(const kind of ['traces','climate','people'])act('read',kind);
      showPlotNotes();
    }
  }catch(e){toast(e.message);}
  finally{busy=false;update();}
}
function showPlotNotes(){
  const body=$('plot-notes-body'),record=fieldRecord(state.selected,currentWorld());
  body.replaceChildren(el('p',record.climate.text+' '+record.climate.wind),el('p',record.traces.text),el('p',record.human.text));
  $('plot-notes').hidden=false;
}
function meet(id){
  if(busy)return;
  try{const first=!knownPlants(state).includes(id);act('find',id);act('use',id);book=id;update();openBook(id);if(first)act('log',`${catalogue.find(s=>s.id===id)?.name} at ${coordinate(state.selected)}.`);}catch(e){toast(e.message);}
}
function openLocalPlants(){
  openDialog('field-notes');$('notes-title').textContent='Plants in this place';$('note-tabs').replaceChildren();const body=$('note-body');body.replaceChildren(el('p','The field team has identified these plants. Choose a name to read its record.'));
  for(const id of WORLD[state.selected].speciesIds)body.append(btn(catalogue.find(s=>s.id===id)?.name||id,()=>{$('field-notes').close();meet(id);},'secondary wide'));
}
function plantSymbol(sp){
  const grass=/grass/i.test(sp.growthForm),palm=/palm/i.test(sp.growthForm),fern=/fern/i.test(sp.growthForm);
  const path=grass?'M50 94 Q35 48 20 23 M50 94 Q60 41 80 12 M50 94 L48 13 M50 94 Q65 65 91 43 M50 94 Q23 74 10 54':palm?'M50 96 L51 35 M51 35 Q15 7 5 45 M51 35 Q88 8 97 45 M51 35 Q24 3 33 1 M51 35 Q70 0 76 11':fern?'M49 96 Q58 54 43 8 M47 25 L23 17 M49 36 L75 22 M50 46 L16 35 M51 58 L85 39 M51 69 L18 56 M50 81 L83 62':'M50 96 L50 48 M50 64 Q14 48 21 20 Q45 19 50 51 Q65 8 83 19 Q87 45 52 64 M50 46 Q34 16 51 4 Q66 18 50 46';
  return `<svg viewBox="0 0 100 105" aria-hidden="true"><path d="${path}" fill="none" stroke="currentColor" stroke-width="2"/></svg>`;
}
function observedDryness(id){
  const places=state.found.filter(k=>k.endsWith(':'+id)).map(k=>Number(k.split(':')[0]));
  return places.length?Math.max(...places.map(p=>1-WORLD[p].moisture)):0;
}
function openBook(id=null){book=id;$('plot-notes').hidden=true;renderBook();$('plant-guide').hidden=false;}
function closeBook(){$('plant-guide').hidden=true;}
function renderBook(){
  const content=$('guide-content');content.replaceChildren();
  $('book-back').hidden=!book;$('guide-tools').hidden=!!book;$('guide-map-actions').hidden=!!book;
  $('guide-title').textContent=book?'Field record':"Plants you've met";
  const known=knownPlants(state);
  if(book){
    const sp=catalogue.find(s=>s.id===book);if(!sp)return;
    const positions=state.found.filter(k=>k.endsWith(':'+sp.id)).map(k=>Number(k.split(':')[0]));
    const here=positions.includes(state.selected)?state.selected:positions[0], c=currentWorld()[here];
    const condition=c?.moisture>.7?'The fallen leaves here are damp.':c?.moisture<.3?'The fallen leaves here are dry and break easily.':'Leaves below the surface are damp. The top layer is drier.';
    const count=ACTIVE.filter(c=>c.speciesIds.includes(sp.id)).length;
    const abundance=count>=6?'It appears in several places on this practice map.':'It appears in only a few places on this practice map.';
    const details=el('div',undefined,'plant-details plain-note');
    const photo=photos[sp.id];
    if(photo){const f=phosphorImage('assets/'+photo.file,sp.name+' reference');f.append(el('figcaption','Species reference - '+photo.author+' / '+photo.license));details.append(f);}
    details.append(el('h2',sp.name),el('p',sp.status==='Invasive'
      ?'This plant is invasive. It can spread into disturbed forest. '+condition+' '+(sp.plainUse||sp.use)+' '+abundance
      :'This plant is native to this region. '+condition+' '+(sp.plainUse||sp.use)+' '+abundance));
    content.append(details);

  }else{
    const native=known.filter(id=>catalogue.find(s=>s.id===id)?.status==='Native').length;
    content.append(el('p',`${native} native plants - ${known.length-native} invasive plants. Optional collection: 10 native and 3 invasive. Keep exploring at your own pace.`,'collection-count'));
    const list=known.map(id=>catalogue.find(s=>s.id===id)).filter(Boolean);
    if(sort==='dry')list.sort((a,b)=>observedDryness(b.id)-observedDryness(a.id));
    if(sort==='native')list.sort((a,b)=>(a.status==='Native'?-1:1)-(b.status==='Native'?-1:1));
    for(const sp of list){
      const row=el('div',undefined,'plant-list-item');row.dataset.species=sp.id;
      const check=el('input');check.type='checkbox';check.checked=mapPlants.has(sp.id);check.setAttribute('aria-label',`Map ${sp.name}`);check.onchange=()=>{if(check.checked)mapPlants.add(sp.id);else mapPlants.delete(sp.id);$('find-plants').disabled=!mapPlants.size;};
      const b=btn('',()=>openBook(sp.id),'plant-open');b.innerHTML=plantSymbol(sp);const info=el('span');info.append(el('strong',sp.name),el('small',sp.status),el('small',observedDryness(sp.id)>.7?'Dry material observed':observedDryness(sp.id)<.3?'Damp material observed':'Mixed litter conditions','condition-mini'));b.append(info);row.append(check,b);content.append(row);
    }
    if(!list.length)content.append(el('p','Choose a square and open Close view. Select a plant name to learn about it.','empty'));
    $('find-plants').disabled=!mapPlants.size;
  }
  content.scrollTop=0;
}

function notes(kind=currentTab){
  if(!state.visited.includes(state.selected)){toast('Send the field team before opening this place’s records.');return;}
  if(!['traces','climate','people','bonus'].includes(kind))kind='traces';
  currentTab=kind;openDialog('field-notes');$('notes-title').textContent=`Field notes - ${coordinate(state.selected)}`;
  const tabs=$('note-tabs');tabs.replaceChildren();
  const record=fieldRecord(state.selected,currentWorld());
  for(const [key,name]of [['traces','Traces'],['climate','Air and litter'],['people','People'],...(record.bonus?[['bonus',record.bonus.kind==='sound'?'Sound log':'Camera trap']]:[])]){const b=btn(name,()=>notes(key));b.classList.toggle('active',kind===key);tabs.append(b);}
  const body=$('note-body');body.replaceChildren();
  const r=kind==='people'?record.human:record[kind];
  if(!r)return;
  if(kind!=='bonus')act('read',kind);
  body.append(el('h2',r.title),el('p',r.text));
  body.append(el('small',network.hasGrant()?`Field day ${network.day()}`:'Opening field survey','observation-boundary'));
  if(currentWorld()[state.selected].scenarioDisturbance)body.append(el('p','The practice canopy comparison records a change here. Check the sensor network for its timing.','field-question'),btn('Open sensor records',network.open,'secondary'));
  if(kind==='climate'){
    const pair=el('div',undefined,'reading-pair');for(const[k,name]of[['morning','Morning'],['afternoon','Afternoon']]){const d=el('div');d.append(el('small',name),el('span',r[k]));pair.append(d);}body.append(pair,el('p',r.wind));
  }
  if(kind==='people'){
    body.append(btn('Read uses of plants you have met',()=>{$('field-notes').close();openBook();},'secondary wide'));
    if(r.tag==='carbon'){const evidence=humans.find(h=>/carbon|verra|vcm/i.test(h.id+' '+h.title));if(evidence)body.append(el('h3',evidence.title),el('p',evidence.summary),...evidence.sources.map(s=>link(s.title,s.url)));}
  }
  if(r.question)body.append(el('p',r.question,'field-question'));
  body.append(el('p','Practice field record. The source explains the relationship, not conditions at this map position.','observation-boundary'),link('Research source',r.source));
  if(kind==='traces')body.append(btn('Check the satellite fire record',async()=>{
    const id=state.selected, result=el('p','Opening the mapped record.');body.append(result);
    try{
      const h=await readJSON('assets/history.json'),layer=h.layers.annual_burned_2023;
      let valid=0,burned=0;
      for(let y=Math.floor(id/6)*5;y<Math.floor(id/6)*5+5;y++)for(let x=id%6*5;x<id%6*5+5;x++){
        const n=y*30+x;if(layer.valid_mask[n]){valid++;if(layer.values[n])burned++;}
      }
      result.textContent=`2023: ${burned} of ${valid} valid 30 m map cells in ${coordinate(id)} were classified as burned. This measured satellite record is separate from our practice field story. The airborne scan is from 2017. It cannot show the later fire damage or its path.`;
      body.append(link('MapBiomas Fire','https://brasil.mapbiomas.org/en/mapbiomas-fogo/'));
    }catch{result.textContent='The satellite record is not available in this copy. It is not needed to continue.';}
  },'related-lead'));
  const next=usefulNext(state);
  body.append(btn('Compare another place',async()=>{$('field-notes').close();await camera('forest');await choose(next);},'related-lead'));
  update();
}

function radioFrame(title,text,kicker='FIELD CALL'){
  openDialog('radio');$('radio-title').textContent=title;$('radio-text').textContent=text;$('radio-kicker').textContent=kicker;$('radio-body').replaceChildren();$('radio-actions').replaceChildren();
}
function radioBrief(){
  const mission=MISSIONS[state.mission], p=playProgress()[state.mission];
  const wander=prototype==='wander',collect=prototype==='collection'&&state.mission===0;
  radioFrame(wander?'Take your time':mission.title,wander?'Choose a place that interests you. Look at plants, ground traces and field records. There is no required route.':p.done?'You have enough findings to compare. You can move on or stay here and explore more.':mission.brief,wander?'OPEN EXPLORATION':`MISSION ${state.mission+1}`);
  if(!wander)$('radio-body').append(el('p',collect?'Find ten native plants and three invasive plants.':mission.task),el('small',p.text));
  $('radio-actions').append(btn('Explore',()=>{act('brief');$('radio').close();},'primary'),btn('Give me a hint',radioHint),btn('Discuss a finding',radioDiscussion));
  if(p.done)$('radio-actions').append(btn(state.mission===3?'Prepare the group map':'Report and choose next mission',()=>{act('complete');$('radio').close();if(state.mission===3)openGM();else{act('mission',state.mission+1);update();radioBrief();}},'secondary'));
  $('radio-actions').append(btn('Choose another mission',missionMenu));
  if(state.visited.length>=3||state.mission===3)$('radio-actions').append(btn(network.hasGrant()?'Compare sensor records':'A field grant is available',network.offer));
}
function radioHint(){
  const mission=MISSIONS[state.mission];radioFrame('A place to look',mission.hint,'FREE FIELD HINT');
  const next=state.selected===null&&state.mission===0?13:usefulNext(state);
  $('radio-body').append(el('p','You can try a suggested place, use Map or choose anywhere in the forest.'));
  $('radio-actions').append(btn('Show me a place',async()=>{$('radio').close();act('brief');await camera('forest');await choose(next);},'primary'),btn('Back',radioBrief));
}
function answerFinding(question){
  const q=question.toLowerCase(),id=state.selected;
  if(id===null||!state.visited.includes(id))return {text:'Choose a place you have visited first. I can discuss its records, not observations we have not collected.',source:null};
  const r=fieldRecord(id,currentWorld()),has=k=>state.reads[k].includes(id);
  if(/carbon|verra|credit|vcm|vmc/.test(q)){
    if(!has('people'))return {text:'Read the local people record first. We do not yet have an account to discuss here.'};
    const evidence=humans.find(h=>/carbon|verra|vcm/i.test(h.id+' '+h.title));
    return {text:evidence?.summary||'A species list is not a carbon credit. A project needs a baseline, additionality, monitoring and checks on leakage and reversal risk. This practice board cannot establish eligibility.',source:evidence?.sources?.[0]?.url};
  }
  if(/sound|animal|tapir|camera|bird|insect/.test(q)&&r.bonus)return {text:r.bonus.text+' This is a practice record. It is not a measurement of fuel moisture.',source:r.bonus.source};
  if(/people|use|food|farm|burn|income|harvest|community/.test(q)&&has('people'))return {text:r.human.text+' Do not infer an ignition just because people use a place.',source:r.human.source};
  if(/damp|dry|moist|wind|gap|heat|air|fire|connect|spread/.test(q)&&has('climate'))return {text:r.climate.text+' '+r.climate.wind+' A route still needs connected fuel and an ignition. Conditions in a nearby patch need checking separately.',source:r.climate.source};
  if(/logging|disturb|char|stump|treefall|happen|fire|gap/.test(q)&&has('traces'))return {text:r.traces.text+' '+r.traces.question,source:r.traces.source};
  const plant=knownPlants(state).map(id=>catalogue.find(s=>s.id===id)).find(sp=>q.includes(sp.name.toLowerCase())||q.includes(sp.scientific.split(' ')[0].toLowerCase()));
  if(plant)return {text:plant.fireNote+' '+(state.uses.includes(plant.id)?plant.use:'Read the field condition as well as the plant name.'),source:plant.sources[0]?.url};
  return {text:'I cannot answer that from the records we have read here. Ask about a recorded disturbance, air and litter, plant use or people. The field notes show what is available.',source:null};
}
function radioDiscussion(){
  radioFrame('What did you find?','Ask about the place you are studying. I can use the field records you have read and their research sources.',`${3-state.calls[state.mission]} DISCUSSION CALLS LEFT`);
  const body=$('radio-body'),label=el('label','Your question'),input=el('textarea');input.id='field-question';input.maxLength=300;input.placeholder='Why might fire spread through this place?';label.htmlFor=input.id;body.append(label,input);
  const reply=el('div',undefined,'reply');reply.hidden=true;body.append(reply);
  const ask=btn('Ask',()=>{
    if(!input.value.trim()){input.focus();return;}
    if(state.selected===null||!state.visited.includes(state.selected)){reply.hidden=false;reply.replaceChildren(el('p','Visit a place first. Free hints can help you start.'));return;}
    try{act('call');const answer=answerFinding(input.value);reply.hidden=false;reply.replaceChildren(el('p',answer.text));if(answer.source)reply.append(link('Research source',answer.source));ask.disabled=state.calls[state.mission]>=3;$('radio-kicker').textContent=`${3-state.calls[state.mission]} DISCUSSION CALLS LEFT`;}
    catch(e){toast(e.message);}
  },'primary');ask.disabled=state.calls[state.mission]>=3;
  $('radio-actions').append(ask,btn('Free hint',radioHint),btn('Back',radioBrief));
}
function missionMenu(){
  openDialog('missions');const list=$('mission-list');list.replaceChildren();
  const p=playProgress();
  MISSIONS.forEach((m,i)=>{const item=el('section',undefined,'mission-option');item.append(btn(`${i+1}. ${m.title}`,()=>{act('mission',i);update();radioBrief();}),el('p',m.task),el('small',`${state.completed.includes(i)?'Reported - ':p[i].done?'Ready to report - ':''}${p[i].text}`));list.append(item);});
}
function bearings(){
  openDialog('map-dialog');const grid=$('bearing-map');grid.replaceChildren();
  for(const c of WORLD){const b=btn(c.active?coordinate(c.id):'',async()=>{$('map-dialog').close();await camera('overhead');await choose(c.id);});b.disabled=!c.active;b.setAttribute('aria-label',c.active?`Explore ${coordinate(c.id)}`:'Outside the scan');b.classList.toggle('visited',state.visited.includes(c.id));b.classList.toggle('selected',state.selected===c.id);grid.append(b);}
}
function openGM(){
  openDialog('gm');$('gm-progress').textContent=`${state.visited.length} places visited. ${knownPlants(state).length} plants met. ${state.completed.length} missions reported. These counts do not decide when a group is ready.`;
  $('gm-prompts').replaceChildren(...MISSIONS.map(m=>{const d=el('section');d.append(el('h2',m.title),el('p',m.recall));return d;}));
  $('gm-prompts').append(el('h2','Bring the field days together'),el('p','Before recall, let teams finish the three field rounds in Sensor network. Pool exports from different equipment. Ask which observations changed and which stayed similar. Everyone will reconstruct the closing Day 3 landscape. An earlier report should stay dated, not be treated as a current observation.'),btn('Open the field grant or network',network.open,'secondary'));
  $('gm-prompts').append(el('h2','Two or three teams'),el('p','Each team keeps one map and gives one explanation before running its simulation. For ten people, use two groups of four or five within the team. Rotate the person at the controls. One group proposes an explanation while the other checks it. Swap after a field round. Do not create extra competing maps for these smaller groups.'),el('p','With two teams, offer camera traps and sound recorders. Air and litter field notes remain available to both. With three teams, the third can compare environmental sensors. No mission requires a third team.'));
}
function sources(){
  openDialog('sources');const body=$('source-content');body.replaceChildren();
  const notes=[['Forest geometry','The airborne view is the measured EBA T_0638 crop from the film. Eleven ground crops vary the understorey. Three separate ForestScan tree references show woody structure and foliage. All now use uniform display scales. The tree references have no confirmed species names. Outside points stay unchanged. These are separate surveys placed together for the exercise, not registered scans of these squares. ForestScan tree data: CC BY 4.0, DOI 10.5285/931973DB09AF41568853702EFE135F29.','https://essd.copernicus.org/articles/18/1243/2026/index.html'],['Field records','Species assignments, crop placement, human accounts, temperatures, humidity, litter moisture, disturbance clues and wildlife encounters are authored practice data. A clickable point is not a measured plant identification. The species map is not a live classifier.'],['Fire comparison','The group lab compares reconstructions against the same training world. It is not an operational forecast or a reproduction of the historical fire. The 2023 mapped scar is shown separately.'],['Lia','A fictional field ecologist with an illustrated portrait and green radio treatment. Calls use local authored answers and cited research, not a live language model. They are not quotations or an endorsement.'],['Images','Real reference photographs use a green terminal treatment. Credits and licenses remain linked. Photos can show a leaf, fruit or flower rather than a whole plant. Green treatments retain the source image license.']];
  for(const [title,text,url]of notes){body.append(el('h2',title),el('p',text));if(url)body.append(link('Source',url));}
  for(const h of humans){body.append(el('h2',h.title),el('p',h.summary));for(const s of h.sources){const p=el('p');p.append(link(s.title,s.url));body.append(p);}}
  for(const sp of catalogue){body.append(el('h2',sp.name));for(const s of sp.sources){const p=el('p');p.append(link(s.title,s.url));body.append(p);}const photo=photos[sp.photoAssetId||sp.id];if(photo){const p=el('p');p.append(link(photo.author,photo.sourcePage),' - ',link(photo.license,photo.licenseUrl));body.append(p);}}
}

$('plot-notes-close').onclick=()=>{$('plot-notes').hidden=true;};$('book-open').onclick=()=>openBook();$('book-close').onclick=closeBook;$('book-back').onclick=()=>openBook();
$('plant-sort').onchange=e=>{sort=e.target.value;renderBook();};
$('find-plants').onclick=async()=>{sensorMap=[];mapped=[...mapPlants];closeBook();await camera('overhead');update();toast('Possible matches. The same species can grow under different moisture conditions.');};
$('clear-map').onclick=()=>{sensorMap=[];mapped=[];mapPlants.clear();update();};
$('radio-open').onclick=radioBrief;$('assignment').onclick=missionMenu;$('menu-open').onclick=()=>openDialog('menu');$('bearings-open').onclick=bearings;$('sources-open').onclick=sources;$('gm-open').onclick=openGM;$('settings-open').onclick=()=>openDialog('settings');
$('network-open').onclick=network.open;
document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>camera(b.dataset.view));
$('low-detail').onchange=e=>forest.setQuality(e.target.checked);$('reduced-motion').checked=reduced;$('reduced-motion').onchange=e=>{reduced=e.target.checked;forest.reducedMotion=reduced;};
$('restart').onclick=()=>{if(confirm('Start again? This clears this browser’s expedition discoveries and sensor notebook.')){state=fresh();network.clear();save();location.reload();}};
async function readJSON(path){const r=await fetch(path);if(!r.ok)throw Error(`Missing field file: ${path}`);return r.json();}
try{
  const [meta,data,oldPhotos,newPhotos]=await Promise.all([forest.load(),readJSON('field-catalogue.json'),readJSON('plant-images.json'),readJSON('field-photos.json')]);
  catalogue=data.species;humans=data.humanEvidence;photos={...oldPhotos.images,...newPhotos.photos};
  if(!Array.isArray(catalogue)||catalogue.length<13)throw Error('The plant catalogue is incomplete.');
  if(state.selected!==null)forest.selectPlot(state.selected);
  $('loading').hidden=true;update();
  if(!state.briefed.includes(state.mission))radioBrief();
}catch(e){$('loading').replaceChildren(el('p','The forest could not load. Check the local server and reload.'));toast(e.message);}
