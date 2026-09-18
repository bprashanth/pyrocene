import {WORLD} from './world.mjs';
import {patch} from './round-model.mjs';
const clamp=n=>Math.max(0,Math.min(1,n));
export const SEED_RECORDS={
 urochloa_decumbens:{name:'Signal grass',status:'Invasive pasture grass',
  dispersal:'Nearby grass can supply new seeds. Clearing one patch does not remove those sources.',
  germination:'Seed supply and an open canopy help this grass establish. An opening alone does not guarantee invasion.',
  source:'https://doi.org/10.1098/rstb.2012.0427',citation:'Silvério et al. 2013',
  extraSource:'https://doi.org/10.1111/gfs.12347',extraCitation:'Dantas-Junior et al. 2018 - seed longevity',
  limit:'The map models local seed supply, not wind direction. Signal grass can form a short-lived seed bank. This does not establish a six-month seed reserve here. Surviving stems can also regrow.'},
 cecropia_obtusa:{name:'Cecropia',status:'Native pioneer tree',
  dispersal:'Fruit bats carry the fruits. Seeds can reach openings away from the parent tree.',
  germination:'Seeds can persist in the soil. This tree establishes in forest openings.',
  source:'https://doi.org/10.3732/ajb.90.3.388',citation:'Lobova et al. 2003',
  limit:'The map models possible bat use. It is not a record of animal sightings.'}
};
const distance=(a,b)=>Math.hypot(a%6-b%6,Math.floor(a/6)-Math.floor(b/6));
// Small teaching layers, not fitted seed kernels or germination probabilities.
// Kept separate from the accepted survival trajectories and money model.
export function seedLayers(species,previous){
 if(!SEED_RECORDS[species])return null;
 const native=species==='cecropia_obtusa',cleared=new Set(previous?[patch(previous.removal).id,patch(previous.ecology).id]:[]);
 const sources=WORLD.filter(c=>c.active&&(native?c.habitat:[13,15,27,28,33].includes(c.id)));
 return WORLD.map(c=>{
  if(!c.active)return null;
  const arrival=clamp(sources.reduce((sum,s)=>sum+Math.exp(-distance(c.id,s.id)/(native?1.6:.85))*(cleared.has(s.id)&&!native?.2:1),0)/(native?3:1.8));
  const opening=cleared.has(c.id)?.9:clamp(.25+c.exposure*.6+(c.disturbance?.15:0));
  const establishment=native?clamp(opening*(.45+.55*c.moisture)):clamp(opening*(.9-.2*c.moisture));
  return {arrival,establishment};
 });
}
export const level=value=>value<.33?'low':value<.66?'moderate':'high';
