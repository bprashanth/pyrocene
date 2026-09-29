import {createPrelude} from './play-briefing.mjs';
import {negligenceEnabled,appURL} from './game-features.mjs';
export function fillStageMenu(select,mode,{prelude=false}={}){
 select.replaceChildren(...[['expedition','Start Here'],['play','The Players'],['recap-one','Prelude'],['combined','The Game'],['recap','Recap']].map(([value,label])=>{const option=new Option(label,value);option.disabled=value==='recap-one'&&!prelude;return option;}));select.value=mode;
}
// In-place recap never advances or resets the game behind it.
export function bindRecap(forest,select,currentMode){
 if(!select)return;
 if(!select.querySelector('[value="recap"]'))select.append(new Option('Recap','recap'));
 let recap;
 select.addEventListener('change',event=>{
  if(select.value!=='recap')return;
  event.stopImmediatePropagation();select.value=currentMode();
  if(!forest.geometry&&!forest.airborneSource)return;
  if(!recap)recap=createPrelude(forest,()=>{select.value=currentMode();});
  recap.open();
 },true);
}
// Navigation carries only this game's capability and chosen role in the hash.
export function flowParams(){return new URLSearchParams(location.hash.slice(1));}
export function roleFrom(params=flowParams()){return (negligenceEnabled?['removal','ecology','room']:['removal','ecology','community','room']).includes(params.get('role'))?params.get('role'):'removal';}
export function flowURL(page,credentials,role){const p=new URLSearchParams({...credentials,role}),url=new URL(page,location.href);if(negligenceEnabled)url.searchParams.set('negligence','1');url.hash=p.toString();return url.href;}
export function navigation(mode,role){
 const nav=document.createElement('nav');nav.className='game-navigation';nav.setAttribute('aria-label','Game');
 nav.innerHTML='<select id="game-mode" aria-label="Game mode"></select><select id="role" aria-label="Team view"><option value="removal">Removal</option><option value="ecology">Ecologist</option><option value="room">Room</option></select><button id="teams-open">Teams</button>';
 fillStageMenu(nav.querySelector('#game-mode'),mode);
 if(!negligenceEnabled)nav.querySelector('#role').add(new Option('Community','community'),nav.querySelector('#role [value=room]'));
 else{const option=new Option('Negligence','negligence');option.disabled=true;nav.querySelector('#game-mode').add(option,nav.querySelector('[value=recap-one]'));}
 document.querySelector('header').append(nav);nav.querySelector('#game-mode').value=mode;nav.querySelector('#role').value=role;return nav;
}
// Combined never advances or mutates the shared room.
export async function enterCombined(){
 const target=new URL('strategy.html',location.href);
 // The Game is served beside this page, including behind the public gateway.
 target.hash=new URLSearchParams({seed:'113',fresh:'1',return:location.href}).toString();location.assign(target);
}
export function expeditionNavigation(){
 if(!negligenceEnabled){cooperationExpeditionNavigation();return;}
 let params=flowParams(),role=roleFrom(params),credentials=params.has('session')?{session:params.get('session'),token:params.get('token')}:null,state=null;
 const nav=navigation('expedition',role),mode=nav.querySelector('#game-mode'),roles=nav.querySelector('#role');
 const dialog=document.createElement('dialog');dialog.id='expedition-teams';dialog.innerHTML='<div class="dialog-heading"><h1>Teams</h1><button>Back</button></div><p>Share one link with each team. Explore in Start Here, then choose The Players.</p><div class="team-links"></div>';
 document.body.append(dialog);dialog.querySelector('button').onclick=()=>dialog.close();
 async function session(){
  const r=await fetch(appURL('api/round/'+(credentials?'state':'new')),{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(credentials||{})});const s=await r.json();
  if(!r.ok)throw Error(s.error);state=s;credentials={session:s.id,token:s.token};if(s.role!=='room'){role=s.role;roles.value=role;roles.disabled=true;}
  mode.querySelector('[value=negligence]').disabled=s.mission!=='negligence'&&s.phase!=='committed';
  history.replaceState(null,'',flowURL('expedition.html',credentials,role));return s;
 }
 roles.onchange=()=>{role=roles.value;history.replaceState(null,'',flowURL('expedition.html',credentials||{},role));};
 mode.onchange=async()=>{const target=mode.value;if(target==='combined'){await enterCombined();return;}if(!['play','negligence'].includes(target))return;mode.disabled=true;try{const s=await session(),action=target==='play'&&s.mission==='negligence'?'replay':target==='negligence'&&s.mission!=='negligence'?'advance':'enter';const r=await fetch(appURL('api/round/'+action),{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...credentials,round:s.round,revision:s.revision})});if(!r.ok)throw Error((await r.json()).error);location.assign(flowURL('round.html',credentials,role));}catch(e){mode.value='expedition';mode.disabled=false;alert(e.message);}};
 nav.querySelector('#teams-open').onclick=async()=>{try{const s=await session(),links=dialog.querySelector('.team-links');links.replaceChildren();
  if(s.teams)for(const [team,token]of Object.entries(s.teams)){const label=document.createElement('label');label.textContent=team==='ecology'?'Ecologist team':'Removal team';const input=document.createElement('input');input.readOnly=true;input.value=flowURL('expedition.html',{session:s.id,token},team);input.setAttribute('aria-label',label.textContent+' link');input.onclick=()=>input.select();label.append(input);links.append(label);}
  else dialog.querySelector('p').textContent='Your team explores here, then joins the current mission. The room makes the shared decision.';
  dialog.showModal();
 }catch(e){alert(e.message);}};
 if(credentials)session().catch(()=>{credentials=null;history.replaceState(null,'',flowURL('expedition.html',{},role));});
}

// All three teams keep the same private capability between survey and play.
// Old two-team rooms are only opened through the explicit Negligence flag.
function cooperationExpeditionNavigation(){
 const params=flowParams();let role=roleFrom(params),credentials=params.get('game')==='cooperation'&&params.has('session')?{session:params.get('session'),token:params.get('token'),game:'cooperation'}:null;
 const nav=navigation('expedition',role),mode=nav.querySelector('#game-mode'),roles=nav.querySelector('#role');
 const dialog=document.createElement('dialog');dialog.id='expedition-teams';dialog.innerHTML='<div class="dialog-heading"><h1>Teams</h1><button>Back</button></div><p>Share one link with each team. Explore, then choose The Players.</p><div class="team-links"></div>';
 document.body.append(dialog);dialog.querySelector('button').onclick=()=>dialog.close();
 async function request(action,extra={}){const r=await fetch(appURL('api/community-cooperation/'+action),{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...credentials,...extra})}),s=await r.json();if(!r.ok)throw Error(s.error);return s;}
 async function session(){
  const s=await request(credentials?'state':'new',{screen:'expedition'});
  credentials={session:s.id,token:credentials?.token||s.tokens.room,game:'cooperation'};
  if(s.role!=='room'){role=s.role;roles.value=role;roles.disabled=true;}
  history.replaceState(null,'',flowURL('expedition.html',credentials,role));return s;
 }
 roles.onchange=()=>{role=roles.value;history.replaceState(null,'',flowURL('expedition.html',credentials||{},role));};
 mode.onchange=async()=>{
  if(mode.value==='combined'){await enterCombined();return;}if(mode.value!=='play')return;
  mode.disabled=true;
  try{const s=await session();if(s.screen!=='play')await request('enter',{revision:s.revision});location.assign(flowURL('round.html',credentials,role));}
  catch(e){mode.disabled=false;mode.value='expedition';alert(e.message);}
 };
 nav.querySelector('#teams-open').onclick=async()=>{
  try{const s=await session(),links=dialog.querySelector('.team-links');links.replaceChildren();
   if(s.tokens)for(const team of ['removal','ecology','community']){const label=document.createElement('label');label.textContent=team==='ecology'?'Ecologist team':team==='community'?'Community team':'Removal team';const input=document.createElement('input');input.readOnly=true;input.setAttribute('aria-label',label.textContent+' link');input.value=flowURL('expedition.html',{session:s.id,token:s.tokens[team],game:'cooperation'},team);input.onclick=()=>input.select();label.append(input);links.append(label);}
   else dialog.querySelector('p').textContent='Your team explores here, then proposes in The Players. The room makes the shared decision.';
   dialog.showModal();
  }catch(e){alert(e.message);}
 };
 if(credentials)session().catch(()=>{credentials=null;history.replaceState(null,'',flowURL('expedition.html',{},role));});
}
