from pathlib import Path
import bpy,sys,json,shutil,math,xml.etree.ElementTree as E
from mathutils import Matrix
r=Path(__file__).resolve().parent;w=r/'fidelity-v7';pack=Path('/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK');mod=pack/'models/volcano-remake-fidelity-v7';sources=pack/'sources/volcano-remake-fidelity-v7';native=w/'native'
for folder in [mod,sources,native]:folder.mkdir(exist_ok=True)
reg=json.loads((r/'fidelity-v5-alpha/asset-registration.json').read_text());bpy.ops.wm.open_mainfile(filepath=reg['finalBlend']);bpy.context.preferences.filepaths.save_version=0
sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
missing_materials=[q['name']for q in reg['materials']if any('smoke_huricane'in t for t in q['textures'])and q['name']not in bpy.data.materials]
if missing_materials:
    with bpy.data.libraries.load(str(pack/'blender/FLUXARA_Track_Asset_Library.blend'),link=False)as(src,dest):dest.materials=missing_materials
rows=json.loads((w/'smoke-changes.json').read_text());models={q['model']for q in rows};oldrows=[q for q in reg['objects']if Path(q.get('sourceModel','')).name in models];reg['objects']=[q for q in reg['objects']if q not in oldrows];newrows=[];collection=bpy.data.collections['Volcano Remake Asset Prototypes']
for row in rows:
    name=row['model'];path=w/'candidate'/name;d=parse(path);assert len(d['buffers'])==1;b=d['buffers'][0];texture=d['materials'][0][0];material=next(q['name']for q in reg['materials']if q['textures']==[texture]and not q['name'].endswith('.001'))
    mesh=bpy.data.meshes.new('VRV7_'+Path(name).stem);mesh.from_pydata([(v['position'][0],v['position'][2],v['position'][1])for v in b['vertices']],[],[tuple(reversed(b['indices'][i:i+3]))for i in range(0,len(b['indices']),3)]);mesh.materials.append(bpy.data.materials[material]);mesh.uv_layers.new(name='UVMap')
    for polygon in mesh.polygons:
        polygon.use_smooth=True
        for loop in polygon.loop_indices:mesh.uv_layers['UVMap'].data[loop].uv=b['vertices'][mesh.loops[loop].vertex_index]['uv']
    oldmesh={o.data for o in bpy.data.objects if o.type=='MESH'and Path(o.get('source_model','')).name==name}
    for obj in bpy.data.objects:
        if obj.type=='MESH'and obj.data in oldmesh:obj.data=mesh;obj['source_model']=str(path)
    proto=bpy.data.objects.new('VRV7_Cloud_'+Path(name).stem,mesh);collection.objects.link(proto);proto.hide_set(True);proto.hide_render=True;proto['asset_id']='volcano-fidelity-v7-cloud-'+Path(name).stem.lower();proto['source_model']=str(path)
    q={'id':proto['asset_id'],'name':proto.name,'sourceModel':str(path),'triangles':row['triangles'],'materials':[material],'role':'Spherical world-space smoke billows; original local bounds, origin and axes retained. Reuses pooled plum/warm palette.'};newrows.append(q);reg['objects'].append(q);shutil.copy2(path,mod/name)
layout=json.loads((w/'layout-changes.json').read_text());removed={E.fromstring(s).get('id')for s in layout['consolidatedSpriteInstances']};modified={q['id']for q in layout['modified']};scene=E.parse(w/'candidate/scene.xml').getroot();keep=[]
for row in reg['nativeOriginalObjects']:
    old=E.fromstring(row['sourceXml'])
    if old.get('id')in removed:
        obj=bpy.data.objects.get(row['name'])
        if obj:bpy.data.objects.remove(obj,do_unlink=True)
        continue
    if old.get('id')in modified:
        xml=next(e for e in scene.findall('object')if e.get('id')==old.get('id'));obj=bpy.data.objects[row['name']];xyz=list(map(float,xml.get('xyz').split()));scale=list(map(float,xml.get('scale').split()));matrix=Matrix.Translation((xyz[0],xyz[2],xyz[1]))@Matrix.Diagonal((scale[0],scale[2],scale[1],1));obj.animation_data_clear();obj.rotation_mode='XZY';obj.matrix_world=matrix;row['matrix']=[list(v)for v in matrix];row['sourceXml']=E.tostring(xml,encoding='unicode');obj['source_xml']=row['sourceXml'];row['model']=xml.get('model')
    keep.append(row)
reg['nativeOriginalObjects']=keep
for row in oldrows:
    obj=bpy.data.objects.get(row['name'])
    if obj:bpy.data.objects.remove(obj,do_unlink=True)
for filename in ['scene.xml','materials.xml']:bpy.data.texts[filename].clear();bpy.data.texts[filename].write((w/'candidate'/filename).read_text())
reg.update({'finalBlend':str(native/'Volcano Remake.blend'),'visualLibrary':str(mod/'Volcano Remake Cloud Library.blend'),'newPrototypes':newrows,'reusedPrototypeIds':[q['id']for q in reg['objects']if not q['id'].startswith('volcano-fidelity-v7-')],'status':'V7 smoke draft, production unchanged; eight decorative sprite placements consolidated into three volumetric plumes.'})
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=reg['finalBlend']);bpy.data.libraries.write(reg['visualLibrary'],{bpy.data.objects[q['name']]for q in newrows}|{bpy.data.materials[n]for q in newrows for n in q['materials']},fake_user=True)
(w/'asset-registration.json').write_text(json.dumps(reg,indent=2));print('V7_NATIVE_READY',len(newrows),len(reg['objects']),flush=True)
