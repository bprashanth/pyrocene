// Shared projection assumptions for points, fuel and the before-fire recap.
// Values are game scenarios, not measured yields or species growth curves.
import {CONFIG,patch,shadeSupport,fire,removalCycle,REMOVAL_CYCLE_YEARS} from './community_cooperation/model.mjs';
import {planBudget} from './round-model.mjs';
const clamp=x=>Math.max(0,Math.min(1,x));
export const FIRE_END=CONFIG.duration+4; // allow the final front to cool
export function projection(plan,year){
 const y=Math.max(0,Math.min(10,year)),planted=plan.removal===plan.ecology||plan.community==='B'&&plan.removal==='B';
 const weedCover=removalCycle(plan,y);
 return {year:y,restoration:y/10,removalCover:weedCover,repeatClearings:planted?0:Math.max(0,Math.floor((y-REMOVAL_CYCLE_YEARS/2)/REMOVAL_CYCLE_YEARS)),
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
 const support=cooperationSupport(plan,p.year);
 const tending=Math.min(p.year,4)*.4+(plan.community==='B'?p.year*.3:0);
 // Local seed purchases retain money in the group rather than creating income.
 // They were included in planting cost upfront; return only the internal share.
 const earnings=b.returns-b.totalCost-investment+repeatMargin+coffee+feed-tending+support.localPurchases+support.careSavings;
 const health=60-b.healthLoss+support.savedNatives+(b.healthGain+support.establishment+support.neighbourShelter)*p.restoration-p.repeatClearings*patch(plan.removal).healthLoss*.3+(plan.community==='B'?3*p.restoration:0);
 return {earnings,health,healthChange:health-60,balance:CONFIG.grant+earnings,support};
}
// Explicit game assumptions, shared by the graph and the map's health score.
export function cooperationSupport(plan,year){
 const matched=plan.community==='A'&&plan.ecology==='A',together=matched&&plan.removal==='A';
 return {matched,together,localPurchases:matched?4*clamp(year/2):0,
  careSavings:together ? .3*Math.min(year,4) : 0,savedNatives:together?4:0,
  establishment:together?10:matched?3:0,
  neighbourShelter:plan.ecology==='C'&&plan.community==='B'?5:0};
}
export function planStory(plan){
 const {matched,together,neighbourShelter}=cooperationSupport(plan,10),parts=[];
 if(together)parts.push('All three teams work on A. The crew clears carefully around healthy natives, and the nursery supplies the plants needed for restoration. The same work supports their income and helps the forest recover.','However, C is still dry and connected to the forest. A fire could still enter there.');
 else if(neighbourShelter)parts.push('Restoring C helps shelter the coffee in B. Restoration costs money now and its return is forest health, while coffee earns later if that shelter holds. However, C is exposed to fire while the trees are young. That danger is not included in this graph.');
 else if(matched)parts.push('The nursery has buyers because restoration happens in A. Seed purchases stay within the group, and the planting mix supports recovery. However, the removal crew is working elsewhere, so clearing and planting need separate visits.');
 else if(plan.community==='A')parts.push('A nursery needs buyers for seeds. Here it prepares plants for A, but restoration happens in '+plan.ecology+'. There is no matching order, so the investment does not bring the expected return.');
 else if(plan.community==='B')parts.push('Coffee costs money now and earns later if it has enough shelter from healthy forests. It can support livelihoods, but a coffee plot does not replace the native forest being restored in '+plan.ecology+'.');
 else parts.push('Grazing saves the cost of bought feed this season. Restoration in '+plan.ecology+' can still help the forest, but grazing in C does not close the gap at the edge. The cost of an escaped fire is not included here.');
 if(plan.removal==='A'&&!together)parts.push('Removal in A brings a large return, but invasives grow among healthy natives there. '+(plan.ecology==='A'?'Restoration follows the clearing, although some of those natives are lost in the work.':'The crew keeps clearing without replanting, so it earns again while native growth is lost.'));
 else if(plan.removal!==plan.ecology&&!(plan.community==='B'&&plan.removal==='B')&&!matched)parts.push('The cleared plot has not been replanted, so invasives return and the crew has to come back.');
 if(beforeFire(plan,0).balance<0)parts.push('Debt lets this plan start, but must be repaid from future earnings. Those earnings are not guaranteed if the forest degrades.');
 return parts;
}

export const TIME_CHOICES=[
 {id:'nursery',name:'Keep the nursery',colour:'#8dbb9e'},
 {id:'coffee',name:'Coffee from the start',colour:'#7db5ce'},
 {id:'sequence',name:'Nursery, then coffee',colour:'#e3c879'}
];
export function timeOutcome(choice,year){
 const y=Math.max(0,Math.min(10,year)),nursery={ecology:'A',removal:'A',community:'A'},coffee={...nursery,community:'B'};
 const result=beforeFire(choice==='coffee'?coffee:nursery,y);
 if(choice!=='sequence'||y<3)return result;
 const age=y-3,harvest=Math.max(0,age-3)*2*shadeSupport(coffee),cost=CONFIG.opportunities.B.investment+age*.3;
 return {...result,earnings:result.earnings-cost+harvest,balance:result.balance-cost+harvest,
  health:result.health+3*clamp(age/10),healthChange:result.healthChange+3*clamp(age/10)};
}
export function timeStory(choice,year){
 if(choice==='nursery')return ['The nursery supplies restoration in A, so there is a buyer for its plants. Careful clearing and shared tending help the natives recover.','After that order is filled, keeping the nursery does not mean orders will keep arriving. The group keeps more money available over these ten years, but has no new source of income once the order is filled.'];
 if(choice==='coffee')return [year<3?'The group pays for coffee in B at the start, as well as restoration in A. Coffee has not started earning yet.':'Coffee in B has begun earning, but its harvest still depends on shelter from the surrounding forest.', 'There was no matching nursery order for A. Plant purchases leave the group, and the restoration does not get the same shared support.'];
 return [year<3?'The nursery starts with an order for restoration in A. Seed purchases stay within the group while the teams clear carefully and tend the young trees.':year<6?'At year three the group spends 6 credits to plant coffee in B. The forest work in A continues, but coffee will take another three years to start earning.':'Coffee in B is now earning alongside the recovering forest in A. The nursery helped the group get started, although the later coffee investment took money away from other work.',
 'Waiting reduces the early spending, but also delays the harvest. This can work if the group can keep tending the land. Fire or a poor harvest could still change the result.'];
}
export function alternatives(){
 const plans=[];for(const ecology of ['A','B','C'])for(const removal of ['A','B','C'])for(const community of ['A','B','C']){
  if(community===ecology&&community!=='A')continue;
  const plan={ecology,removal,community};plans.push({plan,...beforeFire(plan)});
 }return plans;
}
export function projectionNote(plan,year){
 const p=projection(plan,year),bits=[`Restore ${plan.ecology}: ${year>=8?'canopy closes':'young trees grow'}.`];
 if(plan.removal!==plan.ecology&&!(plan.community==='B'&&plan.removal==='B'))bits.push(`Remove ${plan.removal}: ${p.removalCover<.15?(year<REMOVAL_CYCLE_YEARS?'cleared':'cleared again'):year%REMOVAL_CYCLE_YEARS<REMOVAL_CYCLE_YEARS/2&&year<10?'invasives are being cleared':'invasives return'}.`);
 if(plan.community==='B')bits.push(year===0?'B: coffee and shade trees planted.':`B: coffee below ${p.shadeHeight.toFixed(0)} m shade trees.`);
 else if(plan.community==='C')bits.push('C: the pasture burn spreads in the first season.');
 else bits.push('A: the nursery supplies plants off-map.');
 return bits.join(' ');
}
