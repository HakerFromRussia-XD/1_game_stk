from pathlib import Path
import sys,struct,json
r=Path(__file__).resolve().parent;sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
d=parse(r/'before/ancient-summits_track.spm');b=d['buffers'][9];white=0
for v in b['vertices']:
 y=(v['normal']>>10)&1023;y=(y-1024 if y>511 else y)/511;snow=y>.32;white+=snow
 struct.pack_into('<2e',d['raw'],v['uv_offset'],.75 if snow else .25,.5)
(r/'candidate/ancient-summits_track.spm').write_bytes(d['raw']);a=json.load(open(r/'reuse.json'));a=[x for x in a if x['target']!='snowrock.jpg'];(r/'reuse.json').write_text(json.dumps(a,indent=2));(r/'snow-cliff-shading.json').write_text(json.dumps({'originalBuffer':9,'material':'snowrock.jpg','source':'Figma 378:49: smooth blue-gray stone with snow on upper shoulders','changedChannels':['UV on snow-cliff buffer only'],'positionsNormalsTopologyExact':True,'allOtherBuffersIncludingIceSnowBridgeZipperAndControlUvExact':True,'snowFacingVertices':white,'vertices':len(b['vertices']),'paletteSource':str(r/'snowrock.jpg.svg')},indent=2));print('SNOW_CLIFF_SHADED',white)
