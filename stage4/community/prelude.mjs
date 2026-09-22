import {runFire} from '../round-model.mjs';

// Editable narration. No actions, save imports, or changes to either game model.
export const PRELUDE = [
  {
    title: 'Why the edge keeps burning',
    paragraphs: [
      'The scattered fires in the last stage disrupted planting around the open edge. They could cross several plots without travelling deep into the forest. Young trees had more shelter among the standing forest.',
      'Indian forestry estimates put the human-caused share of forest fires at roughly 95%. Many are linked to livelihoods. In Maharashtra, Farmers for Forests works with tribal communities on forest protection and supports fire-free Mahua collection. Mahua collectors sometimes burn litter to make fallen flowers easier to gather. Where litter is damp and fuel is sparse, a burn may stay low. Dense dry invasives can make the same ignition much more destructive. In Telangana, fires are also used in collecting tendu leaves for beedis. In the Amazon, fire is used to maintain cattle pasture. Understanding these needs matters as much as understanding the fuel.',
    ],
    caption: 'Repeated edge fires - illustration',
    description: 'Several separate ignitions along the lower, open part of the point-cloud landscape.',
    sources: [
      ['NIDM: Forest Fire Disaster Management', 'https://nidm.gov.in/PDF/pubs/Forest%20Fire%202013.pdf', 'The roughly 95% estimate is a widely cited historical estimate. The report identifies livelihood uses of fire, but does not quantify their national share.'],
      ['Farmers for Forests: forest protection', 'https://wb-v2.farmersforforests.in/forest-protection', 'Work with rural and tribal households in Gadchiroli, Maharashtra.'],
      ['Farmers for Forests: public updates', 'https://www.linkedin.com/company/farmersforforests', 'F4F describes paid fire-free forest-floor clearing for Mahua collection and tendu trimming, not a programme promoting burning.'],
      ['Telangana Chief Wildlife Warden: report to the NGT', 'https://www.greentribunal.gov.in/sites/default/files/news_updates/OA%20205%20of%202024%20Report%20by%20R1.pdf', 'Documents Mahua collection, tendu leaf production and grazing-related ignitions in Eturnagaram.'],
      ['NASA: From Forest to Field', 'https://science.nasa.gov/earth/earth-observatory/from-forest-to-field-how-fire-is-transforming-the-amazon/', 'Agricultural fires escaping into nearby Amazon forest. Ignition, dry weather and forest condition all matter.'],
      ['ATREE: Lantana and fire', 'https://archived.atree.org/sites/default/files/articles/ja_2015_27-46.pdf', 'Dense Lantana can add fuel and increase damage. A litter fire is not automatically safe beneath closed canopy.'],
    ],
  },
  {
    title: 'How fire reaches the forest',
    paragraphs: [
      'When fuel builds up as dry grass and litter, an escaped fire can travel into the forest. Invasive grasses and shrubs can join with the surrounding vegetation to create continuous fuel, both across the ground and up into taller plants. You may have noticed these connections in the close-up views of each plot.',
      'Identifying and breaking a fuel corridor can help stop a wildfire spreading. This is the idea behind a fire line. Its effectiveness still depends on maintenance, wind and how dry the forest has become.',
      'This means the edge still needs care while the forest recovers. Who can keep doing that after the grant ends?',
    ],
    caption: 'Cooperation - simulated fire scar',
    description: 'The Cooperation fire scar extends into the forest. Yellow connecting lines highlight the fuel corridor from the edge into the interior.',
    sources: [
      ['ATREE: Lantana and fire', 'https://archived.atree.org/sites/default/files/C%2526S_ankila_vol.3_no.1_2005.pdf', 'Discusses how invasive vegetation changes fuel structure and can connect surface fire with the canopy.'],
      ['World Agroforestry: fuelbreaks and greenbreaks', 'https://apps.worldagroforestry.org/Units/Library/Books/Book%2082/imperata%20grassland/html/3.3_grass.htm?n=16', 'Reducing fuel continuity can slow spread and help control fire. Even wide fuelbreaks can be crossed.'],
      ['NASA: From Forest to Field', 'https://science.nasa.gov/earth/earth-observatory/from-forest-to-field-how-fire-is-transforming-the-amazon/', 'Forest damage, drying and repeated fire in the Amazon.'],
    ],
  },
  {
    title: 'Forest Stewards',
    paragraphs: [
      'People already depend on these forests. Can earning a living also support the care that keeps them standing?',
      'Non-timber forest products, or NTFPs, and agroforestry share this idea. Honey, resin and other forest produce can provide recurring supplemental income without felling the forest. That depends on careful harvesting and a healthy forest that can replenish what is taken.',
      'Agroforestry combines trees with crops, often under shade and sometimes along forest edges. When suitable plants replace dry invasive growth and people keep tending the ground, these areas can become living fuelbreaks. They can slow fire, but they are not fireproof.',
      'Aadhimalai Pazhangudiyinar Producer Company was formed in 2013 with support from Keystone Foundation. Owned by tribal producers in the Nilgiri Biosphere Reserve, it collects and processes forest and farm produce. Its market partners include Last Forest, an Indian social enterprise that connects producers with domestic and international markets.',
    ],
    caption: 'Forest and its edge',
    description: 'The point-cloud forest without fire overlays, closing the recap on the landscape that needs continuing care.',
    sources: [
      ['Aadhimalai: history and purpose', 'https://aadhimalai.in/', 'Founded in April 2013 with Keystone support. A producer-owned collective handling forest and agricultural produce.'],
      ['Keystone Foundation: our story', 'https://keystone-foundation.org/our-story/', 'The formation of Aadhimalai in 2013 and Last Forest in 2010.'],
      ['Last Forest: our ecosystem', 'https://lastforest.in/pages/about-us', 'Describes Last Forest as a social enterprise and market partner of Aadhimalai, not as a multinational corporation.'],
      ['World Agroforestry: productive greenbreaks', 'https://apps.worldagroforestry.org/Units/Library/Books/Book%2082/imperata%20grassland/html/3.3_grass.htm?n=16', 'Maintained strips of less-flammable vegetation can reduce fire spread and also provide useful products. Results depend on species, fuel and continued care.'],
    ],
  },
];

export function createPrelude(forest, onFinish) {
  const dialog = document.createElement('dialog');
  dialog.id = 'community-prelude';
  dialog.setAttribute('aria-labelledby', 'prelude-title');
  dialog.innerHTML = `<section class="prelude-copy"><small id="prelude-step"></small><h1 id="prelude-title"></h1>
    <div id="prelude-text"></div><div class="prelude-nav"><button id="prelude-back">Back</button><button id="prelude-next" class="primary">Next</button></div>
    <details class="prelude-sources"><summary>Sources</summary><div id="prelude-sources-body"></div><p>The map uses measured points. Ignition marks are illustrative and the scar is Cooperation's simulation, not a historical fire record or a replay of your last run.</p></details></section>
    <figure><figcaption id="prelude-caption"></figcaption><canvas id="prelude-map" width="640" height="640" role="img"></canvas></figure>`;
  document.body.append(dialog);
  const el = id => dialog.querySelector('#' + id);
  const canvas = el('prelude-map'), ctx = canvas.getContext('2d');
  const base = document.createElement('canvas'); base.width = base.height = 640;
  const b = base.getContext('2d');
  const pos = forest.geometry?.attributes.position.array, raw = forest.airborneSource;
  const n = pos ? pos.length / 3 : raw.length / 4;
  const px = x => 25 + (x + 450) / 900 * 590;
  const py = z => 25 + (z + 450) / 900 * 590;
  b.fillStyle = '#071710'; b.fillRect(0, 0, 640, 640);
  for (let i = 0; i < n; i += Math.max(1, Math.ceil(n / 100000))) {
    const x = pos ? pos[i * 3] : raw[i * 4];
    const z = pos ? pos[i * 3 + 2] : -raw[i * 4 + 1];
    const h = pos ? pos[i * 3 + 1] : raw[i * 4 + 2];
    b.fillStyle = h < .2 ? '#398b98' : h < 2 ? '#bb4274' : h < 10 ? '#39765d' : '#80bfa0';
    b.globalAlpha = h < 2 ? .8 : .55; b.fillRect(px(x), py(z), 1.3, 1.3);
  }
  b.globalAlpha = 1;
  // Same baseline used by Cooperation, not an invented path or historical NBR.
  const scar = runFire();
  let step = 0, frame = null, typing = null;
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const sparks = [[55,300],[110,405],[170,275],[240,365],[320,310],[380,410]];
  function draw(time = 0) {
    ctx.globalAlpha = 1; ctx.drawImage(base, 0, 0);
    if (step === 0) {
      sparks.forEach(([x,z],i) => {
        const pulse = reduced ? .8 : .5 + .5 * Math.sin(time / 850 + i * 2.4);
        ctx.fillStyle = '#ffca78'; ctx.globalAlpha = .8 + pulse * .2;
        for (let j = 0; j < 28; j++) {
          const a = j * 2.4, radius = 2 + ((j*j + i*3) % 11);
          ctx.fillRect(px(x) + Math.cos(a)*radius, py(z) + Math.sin(a)*radius, 3, 3);
        }
        ctx.strokeStyle = '#ffddad'; ctx.lineWidth = 1.4; ctx.globalAlpha = .75;
        ctx.beginPath();ctx.arc(px(x),py(z),14 + pulse*4,0,Math.PI*2);ctx.stroke();
        ctx.globalAlpha=1;ctx.fillStyle='#fff3c7';ctx.fillRect(px(x)-2,py(z)-2,4,4);
      });
    } else if (step === 1) {
      ctx.fillStyle = '#e29458'; ctx.globalAlpha = .9;
      scar.arrival.forEach((at,i) => {
        if (!Number.isFinite(at)) return;
        const x = 25 + (i % 60) * 590/60, y = 25 + Math.floor(i/60) * 590/60;
        // Retain the dotted scan aesthetic instead of a flat filled polygon.
        for(let k=0;k<5;k++)ctx.fillRect(x+((i*13+k*3)%9),y+((i*7+k*5)%9),2,2);
      });
      // The authored corridor used by round-model.mjs, shown as connectivity,
      // not a second fire trajectory or an instruction to clear every segment.
      ctx.globalAlpha=.95;
      for(const [colour,width,dashes] of [['#102018',6,[]],['#ffe8a1',2.5,[6,4]]]){
        ctx.strokeStyle=colour;ctx.lineWidth=width;ctx.setLineDash(dashes);
        for(const route of [[33,27,21,15,9,8,13],[21,22]]){
          ctx.beginPath();route.forEach((id,j)=>{const x=25+(id%6+.5)*590/6,y=25+(Math.floor(id/6)+.5)*590/6;j?ctx.lineTo(x,y):ctx.moveTo(x,y);});ctx.stroke();
        }
      }
      ctx.setLineDash([]);ctx.globalAlpha=1;
      ctx.fillStyle='#071710';ctx.fillRect(355,437,190,26);ctx.fillStyle='#ebd184';ctx.font='16px monospace';ctx.fillText('Fuel connectivity',362,456);
    }
    ctx.globalAlpha = 1;
    if(dialog.open && step===0 && !reduced)frame=requestAnimationFrame(draw);
  }
  function show(index) {
    step=index; clearInterval(typing); cancelAnimationFrame(frame);
    const copy=PRELUDE[step]; el('prelude-step').textContent=`RECAP / ${step+1} OF ${PRELUDE.length}`;
    el('prelude-title').textContent=copy.title;el('prelude-caption').textContent=copy.caption;
    canvas.setAttribute('aria-label',copy.description);
    el('prelude-back').hidden=step===0;el('prelude-next').textContent=step===PRELUDE.length-1?'Finish':'Next';
    dialog.querySelector('.prelude-sources').open=false;
    el('prelude-sources-body').replaceChildren(...copy.sources.map(([title,url,note])=>{const p=document.createElement('p'),a=document.createElement('a');a.textContent=title;a.href=url;a.target='_blank';a.rel='noopener';p.append(a,document.createTextNode(': '+note));return p;}));
    el('prelude-text').replaceChildren(...copy.paragraphs.map(text=>{const p=document.createElement('p');p.textContent=text;return p;}));
    // Reserve text layout while revealing it. Screen readers receive full text.
    const paragraphs=[...el('prelude-text').children];let at=0;
    if(!reduced){for(const p of paragraphs){const ghost=document.createElement('span'),span=document.createElement('span');ghost.textContent=p.textContent;ghost.style.visibility='hidden';ghost.setAttribute('aria-hidden','true');span.setAttribute('aria-hidden','true');span.className='prelude-reveal';p.setAttribute('aria-label',p.textContent);p.replaceChildren(ghost,span);}
      typing=setInterval(()=>{at+=5;let used=0;for(let i=0;i<paragraphs.length;i++){const p=paragraphs[i],full=copy.paragraphs[i],span=p.lastChild;const chars=Math.max(0,Math.min(full.length,at-used));span.textContent=full.slice(0,chars);used+=full.length;}if(at>=used)clearInterval(typing);},24);
    }
    draw();
  }
  function finish(){clearInterval(typing);cancelAnimationFrame(frame);dialog.close();onFinish();}
  el('prelude-next').onclick=()=>step<PRELUDE.length-1?show(step+1):finish();el('prelude-back').onclick=()=>show(Math.max(0,step-1));
  dialog.addEventListener('cancel',event=>{event.preventDefault();finish();});
  return {open(){dialog.showModal();show(0);}};
}
