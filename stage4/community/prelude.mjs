import {runFire, patch} from '../round-model.mjs';

// Editable narration. No actions, save imports, or changes to either game model.
export const PRELUDE = [
  {
    title: 'Why the edge keeps burning',
    paragraphs: [
      'The scattered fires in Combined disrupted planting around the open edge. They could cross several plots without travelling deep into the forest. Young trees had more shelter among the standing forest.',
      'In the Amazon, fire is also used to maintain pasture and prepare fields. Some of these livelihood fires escape into nearby forest. Not every fire starts this way.',
    ],
    caption: 'Repeated edge fires - illustration',
    description: 'Several separate ignitions along the lower, open part of the point-cloud landscape.',
  },
  {
    title: 'How fire reaches the forest',
    paragraphs: [
      'When dry grass and litter join up, an escaped fire can travel into the forest. Dry weather makes this easier. In Cooperation, restoring the narrow link reduced that connection as the canopy returned.',
      'The edge still needs care while the forest recovers. Who can keep doing that after the grant ends?',
    ],
    caption: 'Cooperation - simulated fire scar',
    description: 'The Cooperation fire scar extends from the lower edge into the forest. The narrow link is outlined in yellow.',
  },
];

export function createPrelude(forest, onFinish) {
  const dialog = document.createElement('dialog');
  dialog.id = 'community-prelude';
  dialog.setAttribute('aria-labelledby', 'prelude-title');
  dialog.innerHTML = `<div class="facilitator-photo"><img src="hazel.png" alt="Hazel"></div>
    <section class="prelude-copy"><small id="prelude-step"></small><h1 id="prelude-title"></h1>
    <div id="prelude-text"></div><div class="prelude-nav"><button id="prelude-back">Back</button><button id="prelude-next" class="primary">Next</button></div>
    <details class="prelude-sources"><summary>Sources</summary><p>Ignition and forest-fire context: <a href="https://science.nasa.gov/earth/earth-observatory/from-forest-to-field-how-fire-is-transforming-the-amazon/" target="_blank" rel="noopener">NASA</a> and <a href="https://ipam.org.br/bibliotecas/technical-note-amazon-on-fire/" target="_blank" rel="noopener">IPAM</a>. The map uses measured points with illustrative ignitions on screen one and Cooperation's simulated scar on screen two. It is not a historical fire record or a replay of your last run.</p></details></section>
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
    } else {
      ctx.fillStyle = '#e29458'; ctx.globalAlpha = .9;
      scar.arrival.forEach((at,i) => {
        if (!Number.isFinite(at)) return;
        const x = 25 + (i % 60) * 590/60, y = 25 + Math.floor(i/60) * 590/60;
        // Retain the dotted scan aesthetic instead of a flat filled polygon.
        for(let k=0;k<5;k++)ctx.fillRect(x+((i*13+k*3)%9),y+((i*7+k*5)%9),2,2);
      });
      const neck = patch('C'), x = 25 + (neck.id % 6) * 590/6, y = 25 + Math.floor(neck.id/6) * 590/6;
      ctx.globalAlpha = 1; ctx.strokeStyle = '#ebd184'; ctx.lineWidth = 2;ctx.strokeRect(x,y,590/6,590/6);
      ctx.fillStyle = '#071710';ctx.fillRect(x+5,y-25,125,23);ctx.fillStyle = '#ebd184';ctx.font = '15px monospace';ctx.fillText('Narrow link',x+10,y-9);
    }
    ctx.globalAlpha = 1;
    if(dialog.open && step===0 && !reduced)frame=requestAnimationFrame(draw);
  }
  function show(index) {
    step=index; clearInterval(typing); cancelAnimationFrame(frame);
    const copy=PRELUDE[step]; el('prelude-step').textContent=`BEFORE COMMUNITY / ${step+1} OF 2`;
    el('prelude-title').textContent=copy.title;el('prelude-caption').textContent=copy.caption;
    canvas.setAttribute('aria-label',copy.description);
    el('prelude-back').hidden=step===0;el('prelude-next').textContent=step===0?'Next':'Continue';
    el('prelude-text').replaceChildren(...copy.paragraphs.map(text=>{const p=document.createElement('p');p.textContent=text;return p;}));
    // Reserve text layout while revealing it. Screen readers receive full text.
    const paragraphs=[...el('prelude-text').children];let at=0;
    if(!reduced){for(const p of paragraphs){const ghost=document.createElement('span'),span=document.createElement('span');ghost.textContent=p.textContent;ghost.style.visibility='hidden';ghost.setAttribute('aria-hidden','true');span.setAttribute('aria-hidden','true');span.className='prelude-reveal';p.setAttribute('aria-label',p.textContent);p.replaceChildren(ghost,span);}
      typing=setInterval(()=>{at+=5;let used=0;for(let i=0;i<paragraphs.length;i++){const p=paragraphs[i],full=copy.paragraphs[i],span=p.lastChild;const chars=Math.max(0,Math.min(full.length,at-used));span.textContent=full.slice(0,chars);used+=full.length;}if(at>=used)clearInterval(typing);},24);
    }
    draw();
  }
  function finish(){clearInterval(typing);cancelAnimationFrame(frame);dialog.close();onFinish();}
  el('prelude-next').onclick=()=>step===0?show(1):finish();el('prelude-back').onclick=()=>show(0);
  dialog.addEventListener('cancel',event=>{event.preventDefault();finish();});
  return {open(){dialog.showModal();show(0);}};
}
