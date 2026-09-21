import {StrategyForest} from '../strategy-render.mjs';
import {centre,CELL} from '../strategy-model.mjs';
const T=globalThis.THREE;
// Outlines communicate work locations, not an invisible protective force field.
// Both renderers use these projected SVG edges; no extra point-cloud buffers.
export class CommunityForest extends StrategyForest{
 constructor(host,options={}){super(host,options);this.bufferIds=[];this.bufferNodes=[];this.bufferOverlay=document.createElementNS('http://www.w3.org/2000/svg','svg');this.bufferOverlay.classList.add('buffer-outlines');this.bufferOverlay.setAttribute('aria-hidden','true');host.append(this.bufferOverlay);}
 setBuffers(ids){this.bufferIds=ids;this.bufferNodes=ids.map(()=>document.createElementNS('http://www.w3.org/2000/svg','polygon'));this.bufferOverlay.replaceChildren(...this.bufferNodes);}
 setState(game,instant=false){
  // Mixed working shade is not native forest. Reuse only the point-height
  // transform, so a newly planted buffer does not appear fully grown.
  const plots=Object.fromEntries(Object.entries(game.plots).map(([id,p])=>[id,p.state==='agroforestry'?{...p,state:'young'}:p]));
  super.setState({...game,plots},instant);
 }
 _positionExploreLabels(){super._positionExploreLabels();if(!this.bufferOverlay)return;this.bufferOverlay.setAttribute('viewBox',`0 0 ${this.width} ${this.height}`);this.bufferIds.forEach((id,i)=>{const c=centre(id),half=CELL/2;let visible=true;const points=[[-1,-1],[1,-1],[1,1],[-1,1]].map(([x,z])=>{const p=new T.Vector3(c.x+x*half,.4,c.z+z*half).project(this.camera);if(p.z>1||p.z< -1)visible=false;return `${(p.x*.5+.5)*this.width},${(-p.y*.5+.5)*this.height}`;});const node=this.bufferNodes[i],plot=this.currentState?.[id];node.setAttribute('points',points.join(' '));node.style.display=visible?'':'none';node.classList.toggle('managed',!!plot?.community?.cycles);node.classList.toggle('damaged',!!plot?.community?.cycles&&!!plot.failedPlanting);});}
}
