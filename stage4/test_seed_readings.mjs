import test from 'node:test';
import assert from 'node:assert/strict';
import {WORLD} from './world.mjs';
import {occurrenceStudy,patchReadings,germinationAssessment,GERMINATION_EVIDENCE} from './seed-model.mjs';

test('all inventoried taxa get an occurrence map, without inventing seed arrival',()=>{
 const before=JSON.stringify(WORLD);
 for(const id of new Set(WORLD.flatMap(p=>p.speciesIds))){
  const study=occurrenceStudy(id,13);assert.equal(study.cells.length,36);assert(study.nearby<=study.total);
  study.cells.forEach((c,i)=>WORLD[i].active?assert.equal(c.present,WORLD[i].speciesIds.includes(id)):assert.equal(c,null));
 }
 assert.equal(JSON.stringify(WORLD),before);
});
test('readings vary by patch and disclose simulated follow-up and canopy cases',()=>{
 const before=JSON.stringify(WORLD),open=patchReadings(13,{removal:'A',ecology:'C'}),normal=patchReadings(13);
 assert.notDeepEqual(open,normal);assert(open.temperature>open.closed.temperature);assert(open.light>open.closed.light);assert.match(open.caption,/Six-month.*simulated/);
 assert.notDeepEqual(patchReadings(13),patchReadings(14));assert.equal(patchReadings(-1),null);assert.equal(JSON.stringify(WORLD),before);
});
test('study bands distinguish species and retain unknowns',()=>{
 assert.deepEqual(GERMINATION_EVIDENCE.urochloa_brizantha.temperature,[20,35]);
 assert.deepEqual(GERMINATION_EVIDENCE.urochloa_decumbens.temperature,[28,28]);
 for(const evidence of Object.values(GERMINATION_EVIDENCE)){
  assert(evidence.sources.every(s=>s.url.startsWith('https://')));
  for(const key of ['water','light'])if(evidence[key])assert(evidence[key][0]>=0&&evidence[key][1]<=2);
 }
 assert.equal(GERMINATION_EVIDENCE.melinis_minutiflora.temperature,null);
 assert.match(germinationAssessment('doliocarpus_dentatus',patchReadings(13)),/not yet documented/);
});
test('native pioneer germination does not falsely improve with canopy closure',()=>{
 assert.match(germinationAssessment('cecropia_obtusa',{light:1.9}),/closing shade can reduce/);
 assert.match(germinationAssessment('piper_aduncum',{light:.2}),/Shade may limit/);
 assert.match(germinationAssessment('carapa_guianensis',{water:.2}),/canopy shelter/);
});
