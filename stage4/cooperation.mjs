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
<div id="outcomes" hidden><label for="recovery">Projected recovery <output id="recovery-label">10y</output></label><input id="recovery" aria-label="Recovery years" type="range" min="0" max="10" step="1" value="10"><p id="livelihood"></p>
<div id="fire-controls"><div class="fire-heading"><button id="run-fire">Run fire</button><output id="fire-label">0 min</output></div><input id="fire-time" aria-label="Fire progress" type="range" min="0" max="20" step=".1" value="0"><div id="comparison"><button id="without">Without plan</button><button id="with">With plan</button></div><p id="burned"></p><p id="fire-note"></p></div></div>`;
const note=document.createElement('div');note.id='map-note';note.hidden=true;note.innerHTML='<span class="hot-dot"></span> Fire front <span class="ash-dot"></span> Burned ground';document.body.append(note);
document.querySelector('[data-close="teams"]').id='teams-back';
document.getElementById('teams-note').textContent='Share one link per team. Propose separately, then discuss the shared plan.';
const fresh=document.createElement('button');fresh.id='new-room';fresh.textContent='New room';document.getElementById('team-links').after(fresh);
document.querySelector('#teams details').innerHTML=`<summary>Sources</summary>
<p>Measured forest points. Species placement, fuel, costs and recovery are modelled for this game. Credits are game money, not carbon credits.</p>
<p>Pink, blue and green show vegetation height, not fuel load. Inspect plants and litter to find the fuel connections.</p>
<p>The room has 4 credits: 2 project credits and 2 from the community. Nursery payments are within the restoration purchase. Feed savings and future coffee sales cannot pay for today's planting.</p>
<p>The nursery supplies plants for A from outside the restoration square. Coffee and grazing compete with native restoration for land. Crop shelter, yields and the year-three first harvest are scenario assumptions, not measured forecasts.</p>
<p>The simulated fire starts at pasture C if grazing is chosen, or at the neighbouring field otherwise. Each comparison keeps the same ignition and wind. Recovery assumes continued care. This is not a historical burn scar or a fire prediction.</p>
<p><a href="https://www.weforest.org/programmes/special-projects/apui/" target="_blank" rel="noopener">WeForest and IDESAM: coffee with native trees</a></p>
<p><a href="https://www.fundoamazonia.gov.br/pt/projeto/Sementes-do-Portal/" target="_blank" rel="noopener">Amazon Fund: seeds and restoration demand</a></p>
<p><a href="https://www.infoteca.cnptia.embrapa.br/infoteca/bitstream/doc/403419/1/OrientalDoc83.pdf" target="_blank" rel="noopener">Embrapa: pasture management and fire</a></p>
<p><a href="https://pmc.ncbi.nlm.nih.gov/articles/PMC3638439/" target="_blank" rel="noopener">Amazon field experiment: invasive grass and fire</a></p>`;
await import('./community_cooperation/app.mjs');
