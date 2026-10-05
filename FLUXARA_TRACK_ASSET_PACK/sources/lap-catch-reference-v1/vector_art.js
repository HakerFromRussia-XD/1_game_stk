const fs=require('fs'),sharp=require('/Users/motoricallc/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const r=__dirname;
(async()=>{
// Native vector surface tile, periodic on both axes, full bleed with no border.
let patches='';let seed=771;const random=()=>{seed=(seed*1664525+1013904223)>>>0;return seed/4294967296;};
for(let i=0;i<55;i++){const x=random()*256,y=random()*256,rx=3+random()*8,ry=2+random()*5;for(let ox of [-256,0,256])for(let oy of [-256,0,256])patches+=`<ellipse cx="${x+ox}" cy="${y+oy}" rx="${rx}" ry="${ry}" fill="${i%2?'#839f5a':'#779452'}" opacity=".20"/>`;}
let grass=`<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256"><rect width="256" height="256" fill="#7d9b54"/>${patches}</svg>`;fs.writeFileSync(r+'/reference-grass.svg',grass);const tile=await sharp(Buffer.from(grass)).png().toBuffer();fs.writeFileSync(r+'/candidate/lc_reference_grass.png',tile);await sharp({create:{width:768,height:768,channels:3,background:'#7d9b54'}}).composite(Array.from({length:9},(_,i)=>({input:tile,left:i%3*256,top:Math.floor(i/3)*256}))).jpeg().toFile(r+'/reference-grass-repeat.jpg');
let road=`<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256"><rect width="256" height="256" fill="#707477"/><rect x="124" y="42" width="8" height="150" rx="1" fill="#f5f0df"/></svg>`;fs.writeFileSync(r+'/reference-road.svg',road);await sharp(Buffer.from(road)).jpeg({quality:95}).toFile(r+'/candidate/lc_reference_road.jpg');
let waves='';for(let y=-32;y<288;y+=32)waves+=`<path d="M-32 ${y} Q-16 ${y-8} 0 ${y} T32 ${y} T64 ${y} T96 ${y} T128 ${y} T160 ${y} T192 ${y} T224 ${y} T256 ${y} T288 ${y}" stroke="#bcf7ed" stroke-width="3" opacity=".45" fill="none"/>`;
let svg=`<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256"><rect width="256" height="256" fill="#47bfd4"/>${waves}</svg>`;fs.writeFileSync(r+'/portal-flow.svg',svg);await sharp(Buffer.from(svg)).png().toFile(r+'/candidate/noise.png');
const names=['beach','city','desert','electric','gravel','hills','inferno','plains','retro','rock','snow'];for(let i=0;i<names.length;i++){
 const s=`<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128"><rect width="128" height="128" fill="#f5ead4"/></svg>`;fs.writeFileSync(r+'/'+names[i]+'portal.svg',s);await sharp(Buffer.from(s)).png().toFile(r+'/candidate/'+names[i]+'portal.png');
}
})();
