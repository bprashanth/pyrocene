import {WORLD} from './world.mjs';
import {patch} from './round-model.mjs';
const clamp=n=>Math.max(0,Math.min(1,n));
export const SEED_RECORDS={
 urochloa_brizantha:{name:'Marandu grass',
  dispersal:'Seeds from nearby stands can reach cleared ground. Removing plants here leaves those sources in place.',
  germination:'Temperature and seed dormancy affect germination. Darkness alone does not reliably prevent it.',
  source:'https://pmc.ncbi.nlm.nih.gov/articles/PMC8302751/',citation:'Urochloa seed experiments, 2021',
  limit:'Nearby seed supply and establishment in openings are modelled. This is not a measured dispersal route or a laboratory germination forecast.'},
 megathyrsus_maximus:{name:'Guinea grass',
  dispersal:'Check neighbouring grass stands as possible seed sources. This map does not establish how the seeds travelled.',
  germination:'Seeds can germinate in light or darkness. Temperature and water availability affect the result.',
  source:'https://www.scielo.br/j/pd/a/qFLcJjyMPCWsxjf5mFYY46r/',citation:'Megathyrsus germination experiments, 2020',
  limit:'Germination experiments were in Argentina, not this forest. The seed-supply map is an authored local-source scenario.'},
 melinis_minutiflora:{name:'Molasses grass',
  dispersal:'Nearby seed-producing grass is a possible source. Clearing one square leaves other sources nearby.',
  germination:'Fresh seeds can be dormant. Germination changes with storage time and test conditions.',
  source:'https://doi.org/10.1590/S0101-31222010000400008',citation:'Melinis dormancy experiments, 2010',
  limit:'Local seed supply is modelled, not a measured dispersal mechanism. Storage experiments do not establish persistence in this soil.'},
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
 const sources=WORLD.filter(c=>c.active&&(native?c.habitat:c.speciesIds.includes(species)));
 return WORLD.map(c=>{
  if(!c.active)return null;
  const arrival=clamp(sources.reduce((sum,s)=>sum+Math.exp(-distance(c.id,s.id)/(native?1.6:.85))*(cleared.has(s.id)&&!native?.2:1),0)/(native?3:1.8));
  const opening=cleared.has(c.id)?.9:clamp(.25+c.exposure*.6+(c.disturbance?.15:0));
  const establishment=native?clamp(opening*(.45+.55*c.moisture)):clamp(opening*(.9-.2*c.moisture));
  return {arrival,establishment};
 });
}
export const level=value=>value<.33?'low':value<.66?'moderate':'high';
