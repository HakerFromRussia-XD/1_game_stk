from pathlib import Path
import bpy,json,xml.etree.ElementTree as E
from mathutils import Matrix
r=Path(__file__).resolve().parent;w=r/'fidelity-v11';native=w/'native';native.mkdir(exist_ok=True);a=json.loads((r/'fidelity-v10b/asset-registration.json').read_text());bpy.ops.wm.open_mainfile(filepath=a['finalBlend']);bpy.context.preferences.filepaths.save_version=0;changes=json.loads((w/'smoke-placement-changes.json').read_text());updated=[]
for change in changes:
 row=next(q for q in a['nativeOriginalObjects']if E.fromstring(q['sourceXml']).get('id')==change['id']);xml=E.fromstring(change['candidateXml']);o=bpy.data.objects[row['name']];xyz=list(map(float,xml.get('xyz').split()));scale=list(map(float,xml.get('scale').split()));o.matrix_world=Matrix.Translation((xyz[0],xyz[2],xyz[1]))@Matrix.Diagonal((scale[0],scale[2],scale[1],1));row['matrix']=[list(v)for v in o.matrix_world];row['sourceXml']=change['candidateXml'];o['source_xml']=row['sourceXml'];updated.append(row['name'])
for o in bpy.data.objects:
 if o.get('source_model')and str(r/'fidelity-v10b/candidate')in o['source_model']:o['source_model']=o['source_model'].replace('fidelity-v10b/candidate','fidelity-v11/candidate')
bpy.data.texts['scene.xml'].clear();bpy.data.texts['scene.xml'].write((w/'candidate/scene.xml').read_text());a.update({'finalBlend':str(native/'Volcano Remake.blend'),'newPrototypes':[],'smokeTransformUpdatedObjects':updated,'status':'V11 smaller three smoke plumes connected to original volcano vents. All models and textures unchanged from V10B; no new assets.'});bpy.ops.wm.save_as_mainfile(filepath=a['finalBlend']);(w/'asset-registration.json').write_text(json.dumps(a,indent=2));print('V11_NATIVE_SAVED',updated,flush=True)
