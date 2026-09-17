import {CONFIG,patch,studyPlot,runFire,healthAt} from './round-model.mjs';
import {WORLD} from './world.mjs';
const F=CONFIG.followup,clamp=n=>Math.max(0,Math.min(1,n));
// Declared teaching trajectories, not fitted survival or cover measurements.
export function succession(years,maintained){
 const year=Math.max(F.startYear,Math.min(CONFIG.years,years)),t=(year-F.startYear)/(CONFIG.years-F.startYear);
 const takeover=(1-Math.exp(-2.66*t))/(1-Math.exp(-2.66));
 const alive=F.initialSurvival+(maintained?F.caredSurvival-F.initialSurvival:F.neglectedSurvival-F.initialSurvival)*(maintained?t:takeover);
 const invasive=F.initialInvasive+(maintained?F.caredInvasive-F.initialInvasive:F.neglectedInvasive-F.initialInvasive)*(maintained?t:takeover);
 const ideal=F.initialSurvival+(F.caredSurvival-F.initialSurvival)*t,nativeFraction=alive/ideal;
 return {year,maintained,alive,invasive,nativeFraction,heightScale:year/CONFIG.years*(.3+.7*nativeFraction),lost:ideal-alive};
}
export function followupCandidates(previous){return [patch(previous.ecology),...F.newPatches];}
export function followupBudget(previous,choice){
 if(!followupCandidates(previous).some(p=>p.key===choice))throw Error('Choose a follow-up patch.');
 const care=choice===previous.ecology,p=patch(choice),cost=care?F.careCost:p.removalCost,returns=care?F.careReturn:p.removalCost+p.income;
 return {care,cost,returns,left:previous.left+F.grant+returns-cost,starting:previous.left+F.grant};
}
export function followupStudy(previous,key,forecast){
 const p=studyPlot(key);
 if(key!==previous.ecology)return p;
 return {...p,speciesIds:[...new Set([...patch(key).mix,...WORLD[p.id].speciesIds])],succession:forecast};
}
export function followupReview(previous,choice,years,maintained=choice===previous.ecology){
 const forecast=succession(years,maintained),promised=succession(years,true),extra=maintained||choice===previous.ecology?null:choice;
 return {...followupBudget(previous,choice),forecast,promised,
  health:healthAt(previous,years)-patch(previous.ecology).healthGain*(1-forecast.nativeFraction)-(extra?patch(extra).healthLoss:0),
  baseline:runFire(previous,{years,succession:promised}),future:runFire(previous,{years,succession:forecast,extraRemoval:extra})};
}
