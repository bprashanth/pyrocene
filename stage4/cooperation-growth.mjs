// Add projected vegetation to the existing renderer. No map recolouring or
// replacement fire material. New vegetation also reuses measured fragments.
import {patch} from './round-model.mjs';
import {projection} from './cooperation-projection.mjs';
const T=globalThis.THREE;
export function installProjection(forest){
 forest.organicRegrowth=true;
 let cloud=null,positions=null,lastShade=-1,lastCoffee=-1,active=false;
 const setFire=forest.setFire.bind(forest),setTime=forest.setFireTime.bind(forest),draw=forest.drawFallback.bind(forest);
 forest.setFire=(...args)=>{setFire(...args);if(cloud){cloud.material.uniforms.fire.value=forest.arrivalTexture;cloud.material.uniforms.hasFire.value=forest.fire?1:0;}};
 forest.setFireTime=f=>{setTime(f);if(cloud)cloud.material.uniforms.fireTime.value=f*240;};
 forest.setProjection=(plan,year)=>{
  if(!plan){forest.setPlan(null);forest.setSuccession(null);forest.projectedVegetation=null;active=false;if(cloud)cloud.visible=false;forest.cpuKey=null;return;}
  const p=projection(plan,year);forest.setPlan(plan,p.restoration);
  const cycling=plan.removal!==plan.ecology&&!(plan.community==='B'&&plan.removal==='B');
  forest.setSuccession(null,cycling?{key:plan.removal,invasive:p.removalCover,nativeFraction:1,moisture:.3-.1*p.removalCover,exposure:.65}:null);
  active=plan.community==='B'&&year>0;if(cloud)cloud.visible=active;
  if(active&&(p.shadeHeight!==lastShade||p.coffeeHeight!==lastCoffee||!positions)){
   lastShade=p.shadeHeight;lastCoffee=p.coffeeHeight;
   // Sparse shade crowns above a continuous low coffee layer. Keep the
   // irregular measured crown silhouettes instead of generated tree meshes.
   const source=forest.growthSource||[],out=[],cx=patch('B').id%6*150-375,cz=Math.floor(patch('B').id/6)*150-375;
   let height=1;for(let i=1;i<source.length;i+=3)height=Math.max(height,source[i]);
   for(let i=0;i<source.length;i+=3){
    const x=source[i],y=source[i+1],z=source[i+2],cell=Math.floor((x+75)/25)+6*Math.floor((z+75)/25);
    if(cell%3===0)out.push(x+cx,y/height*p.shadeHeight,z+cz);
    if(i%6===0)out.push(x+cx,y/height*p.coffeeHeight,z+cz);
   }
   positions=new Float32Array(out);
   if(!forest.fallback){
    if(!cloud){
     const material=forest.growthCloud.material.clone();material.uniforms.recovery={value:1};material.uniforms.successionActive={value:0};
     material.vertexShader='varying float projectedHeight;'+material.vertexShader.replace('vec4 mv=modelViewMatrix*vec4(p,1.);','projectedHeight=p.y;vec4 mv=modelViewMatrix*vec4(p,1.);');
     material.fragmentShader='varying float projectedHeight;'+material.fragmentShader.replace('vec3 c=vec3(.51,.88,.66);','vec3 c=projectedHeight<3.?vec3(.78,.31,.52):projectedHeight<10.?vec3(.32,.62,.74):vec3(.60,.83,.66);');
     cloud=new T.Points(new T.BufferGeometry(),material);cloud.frustumCulled=false;forest.scene.add(cloud);
    }
    cloud.geometry.dispose();cloud.geometry=new T.BufferGeometry();cloud.geometry.setAttribute('position',new T.BufferAttribute(positions,3));cloud.visible=true;
   }
  }
  forest.projectedVegetation={...p,coffeePoints:active?(positions?.length||0)/3:0};forest.cpuKey=null;
 };
 forest.drawFallback=()=>{
  const before=forest.cpuKey;draw();if(!active||!positions||forest.cpuKey===before)return;
  const ctx=forest.fallbackCanvas.getContext('2d'),v=new T.Vector3(),w=forest.width,h=forest.height;
  ctx.globalAlpha=.75;
  for(let i=0;i<positions.length;i+=6){
   const x=positions[i],y=positions[i+1],z=positions[i+2],id=Math.floor((z+450)/15)*60+Math.floor((x+450)/15),at=forest.fire?.[id];
   ctx.fillStyle=y<3?'#c75085':y<10?'#519ebc':'#99d6aa';
   if(y<4&&Number.isFinite(at)&&at<=forest.fireTime*forest.duration)ctx.fillStyle=forest.fireTime*forest.duration-at<1.33?'#ffb34d':'#bd7139';
   v.set(x,y,z).project(forest.camera);if(Math.abs(v.x)<=1&&Math.abs(v.y)<=1&&Math.abs(v.z)<=1)ctx.fillRect((v.x*.5+.5)*w,(-v.y*.5+.5)*h,1.6,1.6);
  }ctx.globalAlpha=1;
 };
}
