// Shared projection assumptions for points, fuel and the before-fire recap.
// Values are game scenarios, not measured yields or species growth curves.
import {CONFIG,patch,shadeSupport,fire,removalCycle} from './community_cooperation/model.mjs';
import {planBudget} from './round-model.mjs';
const clamp=x=>Math.max(0,Math.min(1,x));
export const FIRE_END=CONFIG.duration+4; // allow the final front to cool
export function projection(plan,year){
 const y=Math.max(0,Math.min(10,year)),planted=plan.removal===plan.ecology||plan.community==='B'&&plan.removal==='B';
 const weedCover=removalCycle(plan,y);
 return {year:y,restoration:y/10,removalCover:weedCover,repeatClearings:planted?0:Math.floor(y/3),
  shadeHeight:plan.community==='B'?12*clamp(y/10)**.65:0,
  coffeeHeight:plan.community==='B'?2*clamp(y/4):0,
  grazing:plan.community==='C',fireMinutes:plan.community==='C'?FIRE_END*clamp(y/.5):0};
}
export function projectedFire(plan,year){
 // C remains the pasture ignition even when the community chooses another job.
 // With grazing, the burn is in the first season, not replayed every year.
 return fire(plan,plan?.community==='C'?Math.min(year,.5):year,'C',true);
}
export function beforeFire(plan,year=10){
 const p=projection(plan,year),b=planBudget(plan.removal,plan.ecology),investment=CONFIG.opportunities[plan.community].investment;
 const repeatMargin=p.repeatClearings*(patch(plan.removal).income*.65);
 const coffee=plan.community==='B'?Math.max(0,p.year-3)*2*shadeSupport(plan):0;
 const feed=plan.community==='C'?Math.min(p.year,1)*2:0;
 const tending=Math.min(p.year,4)*.4+(plan.community==='B'?p.year*.3:0);
 // Nursery purchase is an internal transfer, not new group earnings.
 const earnings=b.returns-b.totalCost-investment+repeatMargin+coffee+feed-tending;
 const health=60-b.healthLoss+b.healthGain*p.restoration-p.repeatClearings*patch(plan.removal).healthLoss*.3+(plan.community==='B'?3*p.restoration:0);
 return {earnings,health,healthChange:health-60,balance:CONFIG.grant+earnings};
}
export function alternatives(){
 const plans=[];for(const ecology of ['A','B','C'])for(const removal of ['A','B','C'])for(const community of ['A','B','C']){
  if(community===ecology&&community!=='A')continue;
  const plan={ecology,removal,community};plans.push({plan,...beforeFire(plan)});
 }return plans;
}
export function projectionNote(plan,year){
 const p=projection(plan,year),bits=[`Restore ${plan.ecology}: ${year>=8?'canopy closes':'young trees grow'}.`];
 if(plan.removal!==plan.ecology&&!(plan.community==='B'&&plan.removal==='B'))bits.push(`Remove ${plan.removal}: ${p.removalCover<.15?(year<3?'cleared':'cleared again'):'invasives return'}.`);
 if(plan.community==='B')bits.push(year===0?'B: coffee and shade trees planted.':`B: coffee below ${p.shadeHeight.toFixed(0)} m shade trees.`);
 else if(plan.community==='C')bits.push('C: the pasture burn spreads in the first season.');
 else bits.push('A: the nursery supplies plants off-map.');
 return bits.join(' ');
}
