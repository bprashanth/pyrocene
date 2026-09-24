import {RoundForest} from '../round-render.mjs';
import {patch} from '../round-model.mjs';
const T=globalThis.THREE;
export class CommunityForest extends RoundForest{
 async load(){
  const result=await super.load();
  this.styleGround(this.cloud?.material);
  return result;
 }
 styleGround(material){
  if(!material)return;
  // Remove the accepted game's authored narrow notch in this prototype only.
  material.vertexShader=material.vertexShader.replace('a*=1.-trialGap(p)*.98;','');
  // Keep the original height palette. Fuel is discovered in the survey, not
  // painted over the airborne scan or used to recolour low native vegetation.
  material.needsUpdate=true;
 }
 _enterTLS(cached){super._enterTLS(cached);this.styleGround(this.detailCloud?.material);}
 makeEmbers(){
  super.makeEmbers();
  if(!this.embers)return;
  const m=this.embers.material;
  // A moving hot front, then muted ash. The whole scar must not stay orange.
  m.blending=T.NormalBlending;
  m.fragmentShader=m.fragmentShader.replace('vec3(.76,.41,.19)','vec3(.25,.22,.18)').replace('vec3(1.,.62,.16)','vec3(1.,.59,.14)');
  m.needsUpdate=true;
 }
 drawFallback(){
  if(!this.airborneSource)return;
  const now=performance.now();if(now-(this.lastCPU||0)<40)return;this.lastCPU=now;
  const key=[this.width,this.height,this.selected,this.detailSector,this.detailBlend.toFixed(2),this.recovery,this.fireTime,this.effectKey,!!this.fire,...this.camera.matrixWorld.elements].join(':');
  if(key===this.cpuKey)return;this.cpuKey=key;
  const ctx=this.fallbackCanvas.getContext('2d'),w=this.width,h=this.height,v=new T.Vector3();ctx.clearRect(0,0,w,h);
  const r=this.plan?patch(this.plan.removal):null,e=this.plan?patch(this.plan.ecology):null;
  const dot=(x,y,z,wood=false,growth=false)=>{
   const id=Math.floor((z+450)/150)*6+Math.floor((x+450)/150),index=Math.floor((z+450)/15)*60+Math.floor((x+450)/15);
   let a=wood?.85:.66,c=wood?'#b4dcca':y<2?'#c75085':y<10?'#519ebc':'#99d6aa';
   if(growth){y*=this.recovery;a*=this.recovery;c='#85dba8';}
   else if(this.plan){if((id===r.id||id===e.id)&&y<3)a*=.15;if(id===r.id&&y>3&&((x+450)%150)/150<r.damage/100)a*=.05;}
   const at=this.fire?.[index];
   if(Number.isFinite(at)&&at<=this.fireTime*this.duration&&y<4)c=this.fireTime*this.duration-at<1.5?'#ffb13f':'#665347';
   v.set(x,y,z).project(this.camera);if(Math.abs(v.x)>1||Math.abs(v.y)>1||Math.abs(v.z)>1)return;
   ctx.fillStyle=c;ctx.globalAlpha=a;ctx.fillRect((v.x*.5+.5)*w,(-v.y*.5+.5)*h,1.7,1.7);
  };
  const raw=this.airborneSource,step=Math.max(1,Math.ceil(raw.length/4/24000));
  for(let n=0;n<raw.length;n+=4*step)dot(raw[n],raw[n+2],-raw[n+1]);
  if(this.detailPositions){const p=this.detailPositions,skip=Math.max(1,Math.ceil(p.length/3/40000));for(let n=0;n<p.length;n+=skip*3)dot(p[n],p[n+1]*this.detailBlend,p[n+2],this.detailKinds[n/3]>.5);}
  if(this.growthPositions)for(let n=0;n<this.growthPositions.length;n+=6)dot(this.growthPositions[n],this.growthPositions[n+1],this.growthPositions[n+2],false,true);
  const scatter=n=>{const x=Math.sin(n*12.9898)*43758.5453;return x-Math.floor(x);};
  if(this.fire)for(let i=0;i<3600;i++){
   const at=this.fire[i];if(!Number.isFinite(at)||at>this.fireTime*this.duration)continue;
   ctx.fillStyle=this.fireTime*this.duration-at<1.5?'#ffb13f':'#665347';ctx.globalAlpha=.8;
   for(let j=0;j<12;j++){v.set(i%60*15-449+13*scatter(i*31+j*103),.7,Math.floor(i/60)*15-449+13*scatter(i*67+j*137)).project(this.camera);if(Math.abs(v.x)<1&&Math.abs(v.y)<1)ctx.fillRect((v.x*.5+.5)*w,(-v.y*.5+.5)*h,1.8,1.8);}
  }
  ctx.globalAlpha=1;
  for(const p of this.candidates){ctx.strokeStyle=p.id===this.selected?'#edce89':'#507c67';ctx.beginPath();const cx=p.id%6*150-375,cz=Math.floor(p.id/6)*150-375;[[-74,-74],[74,-74],[74,74],[-74,74],[-74,-74]].forEach(([x,z],i)=>{v.set(cx+x,2,cz+z).project(this.camera);i?ctx.lineTo((v.x*.5+.5)*w,(-v.y*.5+.5)*h):ctx.moveTo((v.x*.5+.5)*w,(-v.y*.5+.5)*h);});ctx.stroke();}
  this.drawnFireTime=this.fireTime;
 }
}
