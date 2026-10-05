from pathlib import Path
import shutil,json,sys,struct,math,xml.etree.ElementTree as E
import numpy as np
from PIL import Image
r=Path(__file__).resolve().parent;f=r/'candidate';f.mkdir(exist_ok=True);pack=Path('/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK')
for p in (r/'before').iterdir():
 if p.is_file():shutil.copy2(p,f/p.name)
source=Path('/Users/motoricallc/.codex/generated_images/01a0ed9b-a75e-74c3-a40c-1713421a0a70/exec-9bb0ab23-96d5-4bb1-9a10-882fdbdf3a4d.png');shutil.copy2(source,r/'references/sunny-panorama.png')
im=np.array(Image.open(source).convert('RGB'));h,w,_=im.shape;n=512;u,v=np.meshgrid((np.arange(n)+.5)/n,(np.arange(n)+.5)/n);ones=np.ones_like(u);a=2*u-1;b=1-2*v
faces={'front':(-a,b,-ones),'back':(a,b,ones),'left':(ones,b,-a),'right':(-ones,b,a),'top':(-b,ones,-a),'bottom':(-b,-ones,a)}
for face,(x,y,z) in faces.items():
 norm=np.sqrt(x*x+y*y+z*z);lon=np.arctan2(x,z);lat=np.arcsin(y/norm);ix=((lon/(2*np.pi)+.5)*w).astype(int)%w;iy=np.clip(((.5-lat/np.pi)*h).astype(int),0,h-1);Image.fromarray(im[iy,ix]).save(f/('dp_sky_'+face+'.jpg'),quality=87,optimize=True)
# Reused seamless grass image; format conversion only. Road/grass physics names retained.
grass=pack/'textures/shared/fluxara_grassy_island_v1/fluxara_island_grass.png'
for p in (r/'before').glob('*.jpg'):
 if 'grass' in p.name.lower() or p.name=='kusaiwa.jpg':Image.open(grass).convert('RGB').save(f/p.name,quality=94)
# Native vector palette for mesh material assignment, one 4x4 atlas.
colors=['#fff1d4','#f45f50','#378bd1','#1d465f','#6ab336','#99cc43','#37843c','#c17c43','#e8b775','#fbc94d','#6397b3','#d9e6ec','#393e4b','#ffffff','#85b349','#acd95b']
svg='<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256">'+''.join(f'<rect x="{i%4*64}" y="{i//4*64}" width="64" height="64" fill="{c}"/>' for i,c in enumerate(colors))+'</svg>'
(r/'dp_palette.svg').write_text(svg)
# Clean vector signs and barrier stripes; these are intentionally non-tiling graphic decals.
for name in ['msl2-sign001.jpg','msl2-sign002.jpg','sa_Sign01-02.jpg','sa_Sign01-03.jpg','sa_Sign01-04.jpg','sa_Sign01-05.jpg','sa_Sign02-01.jpg','msl2_tent01-01-sigin.jpg']:
 body=''
 for j in range(4):
  y=j*64;body+=f'<rect y="{y}" width="256" height="64" fill="#f9c744"/><rect x="2" y="{y+2}" width="252" height="60" rx="7" fill="none" stroke="#fff0aa" stroke-width="3"/>'
  for x in [35,100,165]:body+=f'<path d="M{x+35} {y+9}H{x+15}L{x-7} {y+32}L{x+15} {y+55}H{x+35}L{x+13} {y+32}Z" fill="#283b45"/>'
 (r/(name+'.svg')).write_text('<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256">'+body+'</svg>')
(r/'curbs_Albedo_B.jpg.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256"><rect width="256" height="256" fill="#f46b54"/><rect x="128" width="128" height="256" fill="#fff0d3"/><path d="M0 5H256M0 250H256" stroke="#ffffff" opacity=".15" stroke-width="8"/></svg>')
scene=E.parse(r/'before/scene.xml');sky=scene.getroot().find('sky-box');sky.set('texture',' '.join('dp_sky_'+x+'.jpg' for x in ['top','bottom','left','right','front','back']));sky.set('texture-size','512');sky.attrib.pop('sh-texture',None)
E.SubElement(scene.getroot(),'sun',{'xyz':'-130 210 -80','sun-diffuse':'255 242 218','ambient':'158 169 177','sun-specular':'45 45 45','fog':'false'})
E.SubElement(scene.getroot(),'object',{'id':'DP_ReferenceScenery','type':'animation','model':'dp_scenery.spm','xyz':'0 0 0','hpr':'0 0 0','scale':'1 1 1','interaction':'ghost'})
scene.write(f/'scene.xml',encoding='unicode');(r/'palette.json').write_text(json.dumps(colors));print('STAGED')
