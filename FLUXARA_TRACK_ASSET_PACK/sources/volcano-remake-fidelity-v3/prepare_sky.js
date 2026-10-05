// Technical spherical projection of a generated panorama, no painted image edits.
const fs=require('fs'),path=require('path'),sharp=require('/Users/motoricallc/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
(async()=>{
 const {data,info}=await sharp(path.join(__dirname,'warm-sky-panorama-source.png')).removeAlpha().raw().toBuffer({resolveWithObject:true});
 const n=512,w=info.width,h=info.height;
 const sample=(x,y,z)=>{
  const len=Math.hypot(x,y,z);
  let u=.5+Math.atan2(x,z)/(2*Math.PI),v=.5-Math.asin(y/len)/Math.PI;
  const px=((u*w-.5)%w+w)%w,py=Math.max(0,Math.min(h-1,v*h-.5));
  const x0=Math.floor(px),y0=Math.floor(py),fx=px-x0,fy=py-y0;
  return [0,1,2].map(c=>Math.round([[(1-fx)*(1-fy),x0,y0],[fx*(1-fy),(x0+1)%w,y0],[(1-fx)*fy,x0,Math.min(h-1,y0+1)],[fx*fy,(x0+1)%w,Math.min(h-1,y0+1)]].reduce((s,[weight,a,b])=>s+weight*data[(b*w+a)*3+c],0)));
 };
 // Irrlicht CSkyBoxSceneNode UVs. Vulkan rotates top/bottom on upload.
 const directions={front:(s,t)=>[-s,-t,-1],left:(s,t)=>[1,-t,-s],back:(s,t)=>[s,-t,1],right:(s,t)=>[-1,-t,s],top:(s,t)=>[t,1,-s],bottom:(s,t)=>[t,-1,s]};
 const rows=[];
 for(const [face,direction] of Object.entries(directions)){
  const pixels=Buffer.alloc(n*n*3);
  for(let y=0;y<n;y++)for(let x=0;x<n;x++){
   const rgb=sample(...direction(2*(x+.5)/n-1,2*(y+.5)/n-1));for(let c=0;c<3;c++)pixels[(y*n+x)*3+c]=rgb[c];
  }
  const name=`dp_sky_${face}.jpg`,out=path.join(__dirname,'candidate',name);
  await sharp(pixels,{raw:{width:n,height:n,channels:3}}).jpeg({quality:82,chromaSubsampling:'4:4:4'}).toFile(out);
  rows.push({face,name,bytes:fs.statSync(out).size});
 }
 // Shared cube-edge directions produce exactly equal precompression samples.
 const edges=[['front',-1,'left',1],['front',1,'right',-1],['back',1,'left',-1],['back',-1,'right',1]];
 for(const [a,sa,b,sb] of edges)for(let j=0;j<=64;j++){
  const t=2*j/64-1;const p=sample(...directions[a](sa,t)),q=sample(...directions[b](sb,t));if(p.some((v,i)=>v!==q[i]))throw Error('Cube side seam');
 }
 fs.writeFileSync(path.join(__dirname,'sky-projection.json'),JSON.stringify({sourceWidth:w,sourceHeight:h,resolution:n,faces:rows,totalBytes:rows.reduce((s,r)=>s+r.bytes,0),sideEdgeSamplingVerified:true,method:'Bilinear equirectangular projection matching Irrlicht cube UVs; JPG compression may differ at edges.'},null,2));
})();
