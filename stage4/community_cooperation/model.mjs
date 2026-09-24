import {WORLD} from '../world.mjs';
import {INVASIVE_IDS} from '../forest-flora.mjs';
import {PATCHES,patch,planBudget} from '../round-model.mjs';
import {referenceWorld,snapshot,setWorld,simulate} from '../memory-model.mjs';
import CANOPY from '../canopy-grid.json' with {type:'json'};
import CONFIG from './config.json' with {type:'json'};
export {CONFIG,PATCHES,patch};
const clamp=n=>Math.max(0,Math.min(1,n));
const mix=(a,b,t)=>a+(b-a)*t;
const footprint=(id,x,z)=>{
 const cx=id%6*10+4.5,cz=Math.floor(id/6)*10+4.5;
 const rough=.35*Math.sin(x*.8+z*.4)+.2*Math.cos(z*.9);
 return clamp((5.7+rough-Math.max(Math.abs(x-cx),Math.abs(z-cz)))/1.8);
};
// Scenario cover, not inferred species identification from height or colour.
// C's west/east neighbours are intact. The invasion continues north through
// several openings, rather than being a line drawn for the fire renderer.
const cover=[.03,.04,.12,.35,.06,0,.04,.12,.82,.87,.20,0,.5,.91,.18,.89,.12,0,0,.4,.20,.88,.86,.10,0,0,.02,.86,.02,.08,0,0,.50,.98,.35,.12];
export const INVENTORY=WORLD.map(c=>{
 let speciesIds=c.speciesIds.filter(id=>cover[c.id]>.4||!INVASIVE_IDS.has(id));
 if(cover[c.id]>.7)speciesIds=[...new Set(['urochloa_brizantha','megathyrsus_maximus',...speciesIds])];
 return {...c,speciesIds,invasive:speciesIds.some(id=>INVASIVE_IDS.has(id)),fuel:.28+.65*cover[c.id],moisture:.94-.78*cover[c.id],exposure:.12+.7*cover[c.id]};
});
export function surveyClue(id){
 const c=INVENTORY[id];
 if(!c.invasive)return 'Damp litter and little fuel; no invasive grass was found here.';
 return c.fuel>.7?'Grass occurs beneath this opening. Dry stems form a continuous layer.':'Grass occurs beneath this opening, but the fuel is scattered.';
}
export function fineField(plan=null,years=10){
 const growth=clamp(years/10),r=plan&&patch(plan.removal).id,e=plan&&patch(plan.ecology).id;
 return CANOPY.cells.map(([count,height],i)=>{
  const x=i%60,z=Math.floor(i/60),id=Math.floor(z/10)*6+Math.floor(x/10);
  // Interpolated cover with fixed irregularity: broad islands, damp pockets,
  // uneven boundaries. These are hidden surface conditions, not LiDAR colours.
  const gx=(x-4.5)/10,gz=(z-4.5)/10,cx=Math.floor(gx),cz=Math.floor(gz),fx=gx-cx,fz=gz-cz;
  const v=(a,b)=>cover[Math.max(0,Math.min(5,b))*6+Math.max(0,Math.min(5,a))];
  let inv=clamp((v(cx,cz)*(1-fx)+v(cx+1,cz)*fx)*(1-fz)+(v(cx,cz+1)*(1-fx)+v(cx+1,cz+1)*fx)*fz);
  const grain=.07*Math.sin(x*.61+z*.24)+.05*Math.cos(z*.73-x*.17)+.035*Math.sin(x*1.7+z*.9);
  inv=clamp(inv+grain);
  // Do not clip to survey boundaries: dry native litter can carry a little
  // lateral spread into a mostly damp neighbour, even without invasive plants.
  const shelter=height===null?0:clamp(height/32)*.04;
  const dryness=inv**1.8;
  let fuel=.25+.7*inv,moisture=clamp(.98-.9*dryness+shelter),exposure=.1+.8*inv;
  if(plan){
   const cleared=r===e?0:footprint(r,x,z),restored=footprint(e,x,z);
   fuel=mix(fuel,.10+.20*growth,cleared);moisture=mix(moisture,.28,cleared);exposure=mix(exposure,.65,cleared);
   moisture=mix(moisture,.28+.65*growth,restored);exposure=mix(exposure,.65-.5*growth,restored);fuel=mix(fuel,.10+.16*growth,restored);
  }
  if(plan?.community==='B'){const influence=footprint(22,x,z),shade=clamp(years/5)*shadeSupport(plan);fuel=mix(fuel,.22,influence);moisture=mix(moisture,.30+.46*shade,influence);exposure=mix(exposure,.65-.4*shade,influence);}
  return {active:INVENTORY[id].active,fuel,moisture,exposure,invasion:inv};
 });
}
export function shadeSupport(plan){
 // C is a neighbouring shelter opportunity; clearing it without planting
 // exposes B. Explicit scenario dependency, not a crop-yield equation.
 return clamp(.55+(plan.ecology==='C'?.30:0)-(plan.removal==='C'&&plan.ecology!=='C'?.20:0));
}
export function fire(plan=null,years=10,community=plan?.community||'C'){
 const old=referenceWorld(),saved=snapshot(),ignition=community==='C'?27:33;
 try{
  setWorld(INVENTORY.map(c=>({...c,ignition:c.id===ignition})),{day:0,version:'community-cooperation-1'});
  const result=simulate(null,{duration:CONFIG.duration,fineField:fineField(plan,years),wind:{x:0,y:-1,strength:.82}});
  return {...result,burned:result.arrival.filter(Number.isFinite).length*.0225};
 }finally{setWorld(old,saved);}
}
export function outcome(plan,years=10){
 const b=planBudget(plan.removal,plan.ecology),op=CONFIG.opportunities[plan.community];
 const left=CONFIG.grant+b.returns-b.totalCost-op.investment;
 const conflict=plan.community===plan.ecology&&plan.community!=='A';
 const livelihood=plan.community==='A'?(plan.ecology==='A'?'The nursery has a buyer: the restoration order for A.':'No order for A, so the nursery has no return.'):
  plan.community==='B'?(years<3?'Cupuaçu is establishing; fruit income has not started.':shadeSupport(plan)>.7?'Nearby restoration shelters the cupuaçu; harvest prospects improve.':shadeSupport(plan)<.4?'Nearby clearance exposes the cupuaçu; harvest prospects fall.':'Cupuaçu can earn from fruit, but nearby openings leave it exposed.'):
  'Grazing saves bought feed this season; it does not fund restoration.';
 return {left,conflict,livelihood,health:60-b.healthLoss+b.healthGain*clamp(years/10)};
}
export const CLUES={
 ecology:{A:'Native stems remain among the grasses; clearing them all would damage recovery.',B:'An old opening can recover, but its southern neighbour affects shelter.',C:'Dry grass joins the southern edge to openings north; the plots on either side are damp.'},
 removal:{A:'The largest harvest is mixed with native stems.',B:'Dry grass covers open ground with few native stems.',C:'A smaller harvest crosses the gap between the field and the forest.'},
 community:{A:'Raise the native plants needed to restore A.',B:'Grow cupuaçu fruit beneath mixed shade trees.',C:'Burn old pasture growth so cattle can graze the regrowth.'}
};
