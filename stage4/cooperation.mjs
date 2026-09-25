// Main-game shell. Shares three-role rules with the experiment, but deliberately
// uses the accepted RoundForest renderer, not the prototype's fire styling.
import {navigation,roleFrom} from './play-flow.mjs';
document.body.classList.add('community-cooperation','integrated-cooperation');
const css=document.createElement('link');css.rel='stylesheet';css.href='community_cooperation/style.css';document.head.append(css);
navigation('play',roleFrom());
document.querySelector('header').append(document.querySelector('.game-navigation'));
document.getElementById('round-panel').innerHTML=`
<small id="phase">SURVEY</small><h1 id="task"></h1><p id="goal"></p>
<div id="patches" aria-label="Candidate patches"><button data-patch="A" aria-label="Patch A">A</button><button data-patch="B" aria-label="Patch B">B</button><button data-patch="C" aria-label="Patch C">C</button></div>
<h2 id="choice-title"></h2><p id="finding"></p><div id="terms"></div>
<label class="round-plant-picker" id="plant-label">Plants in this plot<select id="plot-plants" aria-label="Plants in this plot"></select></label>
<div id="patch-actions"></div><p id="status" role="status"></p><div id="decision"></div>
<div id="outcomes" hidden><label for="recovery">Projection <output id="recovery-label">0y</output></label><input id="recovery" aria-label="Projection" type="range" min="0" max="10" step=".1" value="0"><p id="livelihood"></p>
<div id="fire-controls"><label for="fire-time">Fire <output id="fire-label">0 min</output></label><input id="fire-time" aria-label="Fire progress" type="range" min="0" max="24" step=".1" value="0"></div><p id="burned"></p><p id="fire-note"></p></div>`;
const note=document.createElement('div');note.id='map-note';note.hidden=true;note.innerHTML='<span class="hot-dot"></span> Fire front <span class="ash-dot"></span> Burned ground';document.body.append(note);
document.querySelector('[data-close="teams"]').id='teams-back';
document.getElementById('teams-note').textContent='Share one link per team. Propose separately, then discuss the shared plan.';
const fresh=document.createElement('button');fresh.id='new-room';fresh.textContent='New room';document.getElementById('team-links').after(fresh);
document.querySelector('#teams details').innerHTML=`<summary>Sources</summary>
<p>Measured forest points. Species placement, fuel, costs and recovery are modelled for this game. Credits are game money, not carbon credits.</p>
<p>Pink, blue and green show vegetation height, not fuel load. Inspect plants and litter to find the fuel connections.</p>
<p>The room has 4 credits and may borrow more. Negative funds are debt. Nursery payments stay inside the group. Later harvests are not cash in hand today.</p>
<p>The nursery supplies plants for A from outside the restoration square. Coffee and grazing compete with native restoration for land. Crop shelter, yields and the year-three first harvest are scenario assumptions, not measured forecasts.</p>
<p>Fire always starts at pasture C. With grazing, Projection includes a first-season fire. Otherwise, Fire tests the landscape at the projection year. Both comparisons keep the same spark and wind. The last four minutes let the front cool. This is not a historical burn scar or a forecast.</p>
<p>Unplanted ground shows two gradual clearance-and-return cycles in ten years. The first clearance is the initial paid work; the next returns 65% of the first margin and adds 30% of the first native damage. Tree care costs 0.4 credits a year for four years. Coffee care costs 0.3 a year; earnings after year three are 2 credits a year times the shelter score. Grazing saves 2 credits in feed in the first year. These timings and amounts are game assumptions, not real prices or measured yields.</p>
<p>Coffee reaches a pruned height of 2 m in this model; shade trees reach 12 m by year ten. The timing and shade-tree height are illustrative, not calibrated growth forecasts. Points reuse measured forest fragments.</p>
<p>Cooperation benefits are explicit scenario assumptions. A nursery matched to restoration in A retains 4 credits of seed purchases within the group over two years. All three teams in A also save 0.3 credits of care per year for four years, preserve 4 native-health points during clearing and add 10 recovery points over ten years. Matching nursery and restoration without the removal crew adds 3 recovery points instead. Restoration in C beside coffee in B adds 5 shelter points by year ten. These scores represent careful clearing, appropriate planting and continued care; a nursery does not guarantee those outcomes in the field.</p>
<p>Recap II holds removal and restoration in A fixed. It compares keeping the nursery, coffee in B from the start, and the nursery followed by coffee in B at year three. The later coffee investment costs 6 credits, with 0.3 annual care and no harvest for three years. No extra nursery order is assumed. Both recap graphs exclude wildfire and failed harvests. They are comparisons, not changes to the committed plan.</p>
<p><a href="https://www.fao.org/4/ad219e/ad219e06.htm" target="_blank" rel="noopener">FAO: pruning coffee to 1.5–2 m</a></p>
<p><a href="https://www.weforest.org/programmes/special-projects/apui/" target="_blank" rel="noopener">WeForest and IDESAM: coffee with native trees</a></p>
<p><a href="https://www.fundoamazonia.gov.br/pt/projeto/Sementes-do-Portal/" target="_blank" rel="noopener">Amazon Fund: seeds and restoration demand</a></p>
<p><a href="https://www.infoteca.cnptia.embrapa.br/infoteca/bitstream/doc/403419/1/OrientalDoc83.pdf" target="_blank" rel="noopener">Embrapa: pasture management and fire</a></p>
<p><a href="https://pmc.ncbi.nlm.nih.gov/articles/PMC3638439/" target="_blank" rel="noopener">Amazon field experiment: invasive grass and fire</a></p>`;
await import('./community_cooperation/app.mjs');
