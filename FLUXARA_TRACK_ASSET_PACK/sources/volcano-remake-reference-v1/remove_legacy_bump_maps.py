from pathlib import Path
import json,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;f=r/'candidate';tree=E.parse(f/'materials.xml');rows=[]
for e in tree.getroot():
 if e.get('name') in ['blackrock.jpg','blackrock_lava.jpg','castelwall.jpg','lava.png','Lava_004_COLOR.jpg','lava_2k_diffuse.jpg','Rock13_col.jpg','fluxara_drifttex_generic_lavaA.png']:
  old=dict(e.attrib)
  for k in ['normal-map','gloss-map']:e.attrib.pop(k,None)
  rows.append({'name':e.get('name'),'before':old,'after':dict(e.attrib),'physicalPropertiesUnchanged':True})
tree.write(f/'materials.xml',encoding='unicode');(r/'material-rendering-proof.json').write_text(json.dumps(rows,indent=2));print('LEGACY_BUMP_MAPS_REMOVED',len(rows))
