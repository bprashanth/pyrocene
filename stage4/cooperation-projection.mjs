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
export function projectedFire(plan,year,{atProjectionYear=false}={}){
 // C remains the pasture ignition even when the community chooses another job.
 // With grazing, the burn is in the first season, not replayed every year.
 // The independent Fire slider can instead test a new ignition at any year.
 return fire(plan,plan?.community==='C'&&!atProjectionYear?Math.min(year,.5):year,'C',true);
}
export function tendingCost(year){
 const y=Math.max(0,Math.min(10,year)),later=Math.max(0,y-4);
 // Later annual tending eases from 0.3 to 0.1 as the canopy establishes.
 return Math.min(y,4)*.4+.3*later-later*later/60;
}
export function coffeeHarvest(plan,age){
 const harvestYears=Math.max(0,Math.min(10,age)-3),mature=4.3*shadeSupport(plan);
 return {annual:mature*(1-Math.exp(-harvestYears/2)),total:mature*(harvestYears-2*(1-Math.exp(-harvestYears/2)))};
}
export function beforeFire(plan,year=10){
 const p=projection(plan,year),b=planBudget(plan.removal,plan.ecology),investment=CONFIG.opportunities[plan.community].investment;
 const repeatMargin=p.repeatClearings*(patch(plan.removal).income*.65);
 const coffee=plan.community==='B'?coffeeHarvest(plan,p.year).total:0;
 const feed=plan.community==='C'?Math.min(p.year,1)*2:0;
 const support=cooperationSupport(plan,p.year);
 const tending=tendingCost(p.year)+(plan.community==='B'?p.year*.3:0);
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
 if(together)parts.push('All three teams work on A. Careful clearing and a matching nursery order give the forest a strong start. After that first supply, smaller plant orders and careful weeding bring little income, while tending keeps using credits.','This gives the highest forest health before fire. However, dry fuel in C still connects to the forest, so fire could undo some of that recovery.');
 else if(neighbourShelter)parts.push((plan.removal==='C'?'Remove C first, then restore C and grow coffee in B. The first clearance earns credits that the group can share towards planting and coffee. ':'Restore C and grow coffee in B. ')+ 'As C recovers it shelters B, so later coffee harvests support continued care. This gives a strong balance of health and earnings. However, C remains exposed to fire while its trees are young.');
 else if(matched)parts.push('The nursery has buyers because restoration happens in A. Seed purchases stay within the group, and the planting mix supports recovery. However, the removal crew is working elsewhere, so clearing and planting need separate visits.');
 else if(plan.community==='A')parts.push('A nursery needs buyers for seeds. Here it prepares plants for A, while restoration happens in '+plan.ecology+'. The nursery needs a buyer for those plants before its investment can earn a return.');
 else if(plan.community==='B')parts.push('Coffee costs money now and earns later if it has enough shelter from healthy forests. The crop supports livelihoods alongside the native forest being restored in '+plan.ecology+'.');
 else parts.push('Grazing saves the cost of bought feed this season. Restoration in '+plan.ecology+' can still help the forest, while the open pasture in C leaves a route for fire at the edge. These outcomes show the forest before a wildfire.');
 if(plan.removal==='A'&&!together)parts.push('Removal in A brings a large return, but invasives grow among healthy natives there. '+(plan.ecology==='A'?'Restoration follows the clearing, although some of those natives are lost in the work.':'The crew keeps clearing without replanting, so it earns again while native growth is lost.'));
 else if(plan.removal!==plan.ecology&&!(plan.community==='B'&&plan.removal==='B')&&!matched)parts.push('The cleared plot stays open, so invasives return and the crew has to come back.');
 if(beforeFire(plan,0).balance<0)parts.push('Debt helps the group start planting. Future earnings must repay it, so recovery and later harvests matter to the budget too.');
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
 // Recap II follows COMMUNITY operating income, not the group's accumulated
 // cash. Replacement orders taper as restoration establishes. These payments
 // require buyers; they must not be added to beforeFire as free group revenue.
 const orders=.35+5.65*Math.exp(-.48*y);
 const coffeeIncome=age=>coffeeHarvest(coffee,age).annual-.3;
 const annualIncome=choice==='nursery'?orders:choice==='coffee'?coffeeIncome(y):orders+(y>=3?coffeeIncome(y-3):0);
 const extraHealth=choice==='sequence'?3*clamp((y-3)/10):0;
 return {year:y,annualIncome,healthChange:result.healthChange+extraHealth,
  investment:choice==='coffee'?6:choice==='sequence'&&y>=3?8:2};
}
export function timeStory(choice){
 if(choice==='nursery')return ['The first order for A brings the most income. Smaller replacement orders follow, but as the forest establishes it needs fewer plants. Hence earnings decline unless the nursery finds new buyers.'];
 if(choice==='coffee')return ['Coffee in B costs 6 credits at the start. Harvests begin after year three and grow as the crop establishes. Restoration in A buys its plants elsewhere, while coffee still needs shelter from the surrounding forest.'];
 return ['The nursery starts with an order for A. At year three the group invests 6 credits in coffee in B while smaller plant orders continue. Coffee begins earning after year six, so income grows again as nursery orders decline. However, both sites still need care.'];
}
// A simple site count, not a coordination score or labour-cost estimate.
// Nursery production is off-map; it does not count as a third field plot.
export function fieldPlots(plan){return [...new Set([plan.ecology,plan.removal,...(plan.community==='A'?[]:[plan.community])])].sort();}
export const COORDINATION=[
 {id:'shared',label:'Shared recovery',colour:'#8dbb9e'},
 {id:'partial',label:'Some shared work',colour:'#7db5ce'},
 {id:'separate',label:'Separate work',colour:'#ce93ae'}
];
export function planCoordination(plan){
 const matched=plan.community==='A'&&plan.ecology==='A',sheltered=plan.community==='B'&&plan.ecology==='C';
 if(plan.removal===plan.ecology&&(matched||sheltered))return COORDINATION[0];
 if(projection(plan,10).repeatClearings)return COORDINATION[matched?1:2];
 return COORDINATION[1];
}
export function planHinges(plan){
 const events=[];
 if(plan.community==='A'&&plan.ecology==='A')events.push({year:2,title:'The nursery order is filled',text:'The first large order has been supplied. Replacement orders become smaller and weeding among the saplings brings little return. The early earnings stay in the group, while continued care gradually spends some of those credits.'});
 else if(plan.community==='B')events.push({year:3,title:'Coffee starts earning',text:plan.removal==='C'&&plan.ecology==='C'?'Removal in C earns the first credits. The group can share them towards restoring C and planting coffee in B. Harvests begin after year three, then grow as the restored forest shelters the crop.':'The first harvests begin after year three. Income grows with the crop and helps cover care, although the return still depends on shelter from the surrounding forest.'});
 else if(plan.community==='C')events.push({year:1,title:'The first feed saving ends',text:'Grazing saved the cost of bought feed in the first season. That saving stays in the budget, while continued tending gradually uses some of the money left over.'});
 else events.push({year:2,title:'The nursery still needs a buyer',text:`The nursery prepared plants for A, while restoration is in ${plan.ecology}. Finding a buyer would help recover that investment. Meanwhile planting and tending still need funding.`});
 events.push({year:4,title:'Care continues as the canopy grows',text:'As the canopy grows the work begins to ease. The forest still needs time and credits for care, so the budget keeps changing after the first planting and seed orders.'});
 if(projection(plan,10).repeatClearings){const p=patch(plan.removal);events.push({year:7.5,title:`The crew clears ${plan.removal} again`,text:`The open ground in ${plan.removal} filled with invasives again. Another clearance adds ${(p.income*.65).toFixed(1)} credits, but costs ${(p.healthLoss*.3).toFixed(1)} native-health points. ${plan.removal==='A'?'This is why earnings stay high even though forest health is lower.':'This is why the turn includes a rise in earnings alongside the loss of native growth.'}`});}
 else if(plan.ecology==='A'&&plan.community==='A')events.push({year:10,title:'High recovery still needs protection',text:'Shared work gives A the highest forest health before fire. The first removal and nursery order earned most of the money; later care uses credits as smaller orders taper. However, dry fuel in C still leads into the forest, so a wildfire could undo this recovery.'});
 else events.push({year:10,title:'The planted canopy has grown',text:plan.ecology==='C'&&plan.community==='B'?'Restoration in C now shelters coffee in B. The first clearance helped fund the work, and later harvests help pay for care. This supports both forest health and income, although fire during establishment could still have changed the outcome.':`Recovery in ${plan.ecology} raises forest health${plan.community==='B'?' while coffee keeps earning in B':", but healthier forests don't always mean more credits"}. The group still needs time and money to tend its work.`});
 return events;
}
export function alternatives(){
 const plans=[];for(const ecology of ['A','B','C'])for(const removal of ['A','B','C'])for(const community of ['A','B','C']){
  if(community===ecology&&community!=='A')continue;
  const plan={ecology,removal,community};plans.push({plan,...beforeFire(plan)});
 }return plans;
}
export function projectionNote(plan,year){
 const p=projection(plan,year),bits=[`Restore ${plan.ecology}: ${year>=8?'canopy closes':'young trees grow'}.`];
 if(plan.removal!==plan.ecology&&!(plan.community==='B'&&plan.removal==='B'))bits.push(`Remove ${plan.removal}: ${p.removalCover<.15?(year<REMOVAL_CYCLE_YEARS?'cleared':'cleared again'):p.removalCover>.6?'invasives cover the ground':year%REMOVAL_CYCLE_YEARS<REMOVAL_CYCLE_YEARS/2&&year<10?'invasives are being cleared':'invasives return'}.`);
 if(plan.community==='B')bits.push(year===0?'B: coffee and shade trees planted.':`B: coffee below ${p.shadeHeight.toFixed(0)} m shade trees.`);
 else if(plan.community==='C')bits.push('C: the pasture burn spreads in the first season.');
 else bits.push('A: the nursery supplies plants off-map.');
 return bits.join(' ');
}
