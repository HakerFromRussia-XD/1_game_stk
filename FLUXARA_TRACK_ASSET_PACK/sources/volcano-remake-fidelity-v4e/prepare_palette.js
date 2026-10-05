const fs=require('fs'),path=require('path'),sharp=require('/Users/motoricallc/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
(async()=>{
  for(const [name,colors] of [['Rock13_col.jpg',['#988592','#7eaa57']],['blackrock.jpg',['#69596f','#69596f']]]){
    const svg=`<svg xmlns="http://www.w3.org/2000/svg" width="64" height="32"><rect width="32" height="32" fill="${colors[0]}"/><rect x="32" width="32" height="32" fill="${colors[1]}"/></svg>`;
    fs.writeFileSync(path.join(__dirname,name+'.svg'),svg);
    await sharp(Buffer.from(svg)).jpeg({quality:100,chromaSubsampling:'4:4:4'}).toFile(path.join(__dirname,name));
  }
})();
