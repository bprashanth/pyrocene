// Reproducible visible-information checks, not evidence about real farms.
import {newGame,act,quote,metrics,SCENARIO} from './model.mjs';
export function run(seed,policy){
 const g=newGame(seed,{enterprise:policy==='nursery'?'nursery':'shade'});
 while(g.status==='playing'){
  if(['nursery','shade'].includes(policy)&&g.turn<2){act(g,'partner',SCENARIO.bufferIds[g.turn]);continue;}
  const id=policy==='neglect'?null:SCENARIO.restorationIds.find(id=>g.plots[id].state==='young'&&g.plots[id].grass>=.3&&quote(g,'remove',id).valid);
  act(g,id==null?'wait':'remove',id);
 }
 return {...metrics(g),targetBurns:SCENARIO.restorationIds.filter(id=>g.plots[id].burned>0).length};
}
export function probe(count=100,start=1){return Object.fromEntries(['neglect','manual','nursery','shade'].map(policy=>{const rows=Array.from({length:count},(_,i)=>run(start+i,policy));return[policy,{runs:count,bothRecovered:rows.filter(r=>r.targetCanopies===2).length,targetBurns:rows.reduce((sum,r)=>sum+r.targetBurns,0)}];}));}
if(process.argv[1]?.endsWith('/probes.mjs'))console.log(JSON.stringify(probe(Number(process.argv[2])||100,Number(process.argv[3])||1),null,2));
