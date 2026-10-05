from pathlib import Path
import xml.etree.ElementTree as E,shutil
r=Path(__file__).resolve().parent;f=r/'candidate';old=E.parse(r/'before/scene.xml').getroot();scene=E.parse(f/'scene.xml')
for a,b in zip(old.find('track').findall('static-object'),scene.getroot().find('track').findall('static-object')):
 assert all(a.get(k)==b.get(k) for k in ['xyz','hpr','scale'])
 b.attrib.pop('lod_instance',None);b.attrib.pop('lod_group',None);b.set('model','treeMod1_LOD80.spm');b.set('interaction','physics-only')
# This is the engine's static collision-only path: it creates the original triangle
# collision mesh then removes the render node. It needs no transparent substitute.
for n in ['treeMod1_LOD80.spm','treeMod1_LOD170.spm','tree_1.png']:shutil.copy2(r/'before'/n,f/n)
mat=E.parse(f/'materials.xml')
for m in list(mat.getroot()):
 if m.get('name')=='sr_tree_collision.png':mat.getroot().remove(m)
mat.write(f/'materials.xml',encoding='unicode');scene.write(f/'scene.xml',encoding='unicode')
print('ORIGINAL_TREE_COLLIDERS_RETAINED',32,'render nodes removed by engine physics-only path')
