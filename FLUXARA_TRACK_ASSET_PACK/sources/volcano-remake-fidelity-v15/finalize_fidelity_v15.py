from pathlib import Path
import bpy,json,sys,hashlib,math,xml.etree.ElementTree as E
from mathutils import Matrix,Vector
r=Path(__file__).resolve().parent;w=r/'fidelity-v15';pack=Path('/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK');mod=pack/'models/volcano-remake-fidelity-v15';mod.mkdir(exist_ok=True);native=w/'native';native.mkdir(exist_ok=True);a=json.loads((r/'fidelity-v14/asset-registration.json').read_text());proof=json.loads((w/'castle-atmosphere-changes.json').read_text());bpy.ops.wm.open_mainfile(filepath=a['finalBlend']);bpy.context.preferences.filepaths.save_version=0;sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
helper=(r/'finalize_fidelity_v9.py').read_text();exec(helper[helper.index('def mesh_from_buffer'):helper.index('updates=a')])
def native_mesh(name,b,mats):
 mesh=mesh_from_buffer(name,b,mats);norm=[]
 for loop in mesh.loops:
  p=b['vertices'][loop.vertex_index].get('normal',0);v=[]
  for shift in [0,10,20]:
   q=(p>>shift)&1023;v.append((q-1024 if q>511 else q)/511)
  n=Vector((v[0],v[2],v[1]));n.normalize();norm.append(n)
 mesh.normals_split_custom_set(norm);mesh.update();return mesh
newrows=[];newmats=[];newnativechanged=[];newlibrarymodels=[];proto_col=bpy.data.collections['Volcano Remake Asset Prototypes'];inst_col=bpy.data.collections['Volcano Remake Shared Instances'];protected_col=next(c for c in bpy.data.collections if 'Protected'in c.name)
# Existing brick pixels, with unique material variants so older library assets remain intact.
texture=Path(proof['globalBrickTexture']);target=pack/'textures/volcano-remake-fidelity-v15'/texture.name;target.parent.mkdir(exist_ok=True);target.write_bytes(texture.read_bytes());image=bpy.data.images.load(str(target),check_existing=False);image.name=texture.name;image.pack();oldrows=[q for q in a['materials']if 'castelwall.jpg'in q.get('textures',[])];mapping={}
for i,row in enumerate(oldrows):
 mat=bpy.data.materials[row['name']].copy();mat.name=f'VRV15_BrickAlias_{i}';mat['asset_id']=f'volcano-fidelity-v15-brick-material-{i}'
 for node in mat.node_tree.nodes:
  if node.type=='TEX_IMAGE'and node.image and 'castelwall.jpg'in node.image.name:node.image=image
 mapping[row['name']]=mat;newmats.append({'id':mat['asset_id'],'name':mat.name,'textures':[texture.name],'sourceMaterialId':row['id'],'adaptation':'Existing gray castle masonry pixels and original shader settings; global runtime alias.'})
for mesh in bpy.data.meshes:
 for i,mat in enumerate(mesh.materials):
  if mat and mat.name in mapping:mesh.materials[i]=mapping[mat.name]
a['materials']=[q for q in a['materials']if q not in oldrows]+newmats
oldtex=a['textures'].pop('castelwall.jpg');a['textures'][texture.name]={'source':str(texture),'packPath':str(target),'bytes':texture.stat().st_size,'sha256':hashlib.sha256(texture.read_bytes()).hexdigest(),'poolId':'volcano-fidelity-v15-brick-texture-alias','reusedPixelsSource':oldtex['packPath'],'reusedPixelsSha256':oldtex['sha256']}
# Shared tower skin supports actual per-vertex tint and dark windows.
mat=bpy.data.materials.new('VRV15_CastleBodyVertexBrick');mat.use_nodes=True;mat['asset_id']='volcano-fidelity-v15-body-material';nt=mat.node_tree;bsdf=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED');tex=nt.nodes.new('ShaderNodeTexImage');tex.image=image;col=nt.nodes.new('ShaderNodeVertexColor');col.layer_name='Color';mul=nt.nodes.new('ShaderNodeMixRGB');mul.blend_type='MULTIPLY';mul.inputs[0].default_value=1.;nt.links.new(tex.outputs['Color'],mul.inputs[1]);nt.links.new(col.outputs['Color'],mul.inputs[2]);nt.links.new(mul.outputs[0],bsdf.inputs['Base Color']);bsdf.inputs['Roughness'].default_value=.88;bodymat=mat;row={'id':mat['asset_id'],'name':mat.name,'textures':[texture.name],'adaptation':'Existing brick image multiplied by tower vertex colors.'};newmats.append(row);a['materials'].append(row)
mat=bpy.data.materials.new('VRV15_CastleVertexRoof');mat.use_nodes=True;mat['asset_id']='volcano-fidelity-v15-roof-material';bsdf=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');col=mat.node_tree.nodes.new('ShaderNodeVertexColor');col.layer_name='Color';mat.node_tree.links.new(col.outputs['Color'],bsdf.inputs['Base Color']);bsdf.inputs['Roughness'].default_value=.8;roofmat=mat;row={'id':mat['asset_id'],'name':mat.name,'textures':[],'adaptation':'No texture image; original SPM vertex colors for red roof, flag and roof tiles.'};newmats.append(row);a['materials'].append(row)
def prototype(name,ident,path,mats,role):
 d=parse(path);assert len(d['buffers'])==1;mesh=native_mesh(name+'Mesh',d['buffers'][0],mats);o=bpy.data.objects.new(name,mesh);proto_col.objects.link(o);o.hide_set(True);o.hide_render=True;o['asset_id']=ident;o['source_model']=str(path);row={'id':ident,'name':name,'sourceModel':str(path),'triangles':len(d['buffers'][0]['indices'])//3,'materials':[m.name for m in mats],'role':role};newrows.append(row);newlibrarymodels.append(Path(path));return o
body=prototype('VRV15_Prototype_CastleBody','volcano-fidelity-v15-castle-body',proof['newTowerBody'],[bodymat],'Shared gray masonry body; local horizontal dimensions, origin and axes retained.')
roof=prototype('VRV15_Prototype_CastleRoof','volcano-fidelity-v15-castle-roof',proof['newTowerRoof'],[roofmat],'Red conical roof and pennant, one physical cap used by all roofed towers.')
flag=prototype('VRV15_Prototype_CastleFlag','volcano-fidelity-v15-castle-flag',proof['newTowerFlag'],[roofmat],'Pennant cap for crenellated tower variant.')
gate=prototype('VRV15_Prototype_GateRoof','volcano-fidelity-v15-gate-roof',proof['newGateRoofModel'],[roofmat],'Shared red tile canopy over the unchanged stone gateway; ghost scenery.')
# Removed original decorative towers retain every collision triangle in separate hidden map-only proxies.
main=parse(w/'candidate/volcano_track.spm');oldmain=parse(r/'fidelity-v14/candidate/volcano_track.spm')
for key in proof['mainRemovalTriangleIdsByBuffer']:
 i=int(key);old=oldmain['buffers'][i];texture_name=oldmain['materials'][old['material']][0];users=[o for o in bpy.data.objects if o.type=='MESH'and Path(o.get('source_model','')).name=='volcano_track.spm'and len(o.data.polygons)==len(old['indices'])//3 and any(m and (texture_name in m.name or texture_name=='castelwall.jpg'and m.name.startswith('VRV15_BrickAlias_'))for m in o.data.materials)];meshes={o.data for o in users};assert len(meshes)==1,(i,texture_name,[o.name for o in users]);mesh=next(iter(meshes));replacement=native_mesh('VRV15_Main_'+str(i),main['buffers'][i],list(mesh.materials))
 for o in users:o.data=replacement;newnativechanged.append(o.name)
# Replace three smoke prototypes and their linked in-map users; transforms unchanged.
retired=[]
for q in proof['smoke']:
 name=Path(q['model']).stem;oldrow=next(z for z in a['objects']if z['name']=='VRV7B_Cloud_'+name);oldproto=bpy.data.objects[oldrow['name']];proto=prototype('VRV15_Cloud_'+name,'volcano-fidelity-v15-cloud-'+name.lower(),w/'candidate'/q['model'],list(oldproto.data.materials),'Dense overlapping irregular puffs; source local bounds, origin, axes and palette pixels retained.');users=[o for o in bpy.data.objects if o.type=='MESH'and o!=oldproto and o.data==oldproto.data]
 for o in users:o.data=proto.data;newnativechanged.append(o.name)
 retired.append(oldrow['name']);bpy.data.objects.remove(oldproto,do_unlink=True)
scene=E.parse(w/'candidate/scene.xml').getroot()
def addpart(name,proto,xml,matrix):
 o=bpy.data.objects.new(name,proto.data);inst_col.objects.link(o);o.matrix_world=matrix;o['shared_runtime_library']=xml.get('name');o['source_prototype']=proto.name;o['asset_id']=proto['asset_id'];o['source_xml']=E.tostring(xml,encoding='unicode');row={'name':name,'prototype':proto.name,'library':xml.get('name'),'matrix':[list(v)for v in matrix],'sourcePlacementId':xml.get('id')};a['nativeSharedInstances'].append(row);return o
for xml in scene.findall('library'):
 ident=xml.get('id');isold=ident in ['VRV8_PooledTower_0','VRV8_PooledTower_1'];isnew=ident.startswith('VRV15_PooledTower_')
 if not(isold or isnew):continue
 role='battlement'if'battlement'in xml.get('name')else'roof';xyz=list(map(float,xml.get('xyz').split()));sc=list(map(float,xml.get('scale').split()));parent=Matrix.Translation((xyz[0],xyz[2],xyz[1]))@Matrix.Diagonal((sc[0],sc[2],sc[1],1));bm=parent@Matrix.Diagonal((1,1,1.2 if role=='battlement'else 1,1))
 if isold:
  o=bpy.data.objects[ident];o.data=body.data;o.matrix_world=bm;o['source_prototype']=body.name;o['shared_runtime_library']=xml.get('name');o['source_xml']=E.tostring(xml,encoding='unicode');o['asset_id']=body['asset_id'];entry=next(q for q in a['nativeSharedInstances']if q['name']==ident);entry.update({'prototype':body.name,'library':xml.get('name'),'matrix':[list(v)for v in bm],'sourcePlacementId':ident})
 else:addpart(ident,body,xml,bm)
 addpart(ident+'_Cap',roof if role=='roof'else flag,xml,parent)
xml=scene.find('library[@id="VRV15_GateRoof"]');xyz=list(map(float,xml.get('xyz').split()));addpart(xml.get('id'),gate,xml,Matrix.Translation((xyz[0],xyz[2],xyz[1])))
for q in proof['additionalTowerPlacements']:
 xml=scene.find(f"object[@model='{q['collider']}']");name=xml.get('id');mesh=native_mesh(name,parse(w/'candidate'/q['collider'])['buffers'][0],[]);o=bpy.data.objects.new(name,mesh);protected_col.objects.link(o);o.hide_set(True);o.hide_render=True;o['source_model']=str(w/'candidate'/q['collider']);o['source_xml']=E.tostring(xml,encoding='unicode');a['nativeOriginalObjects'].append({'name':name,'model':q['collider'],'matrix':[list(v)for v in o.matrix_world],'sourceXml':o['source_xml']})
retired.append('VRV9_Prototype_CastleTower');bpy.data.objects.remove(bpy.data.objects['VRV9_Prototype_CastleTower'],do_unlink=True);a['objects']=[q for q in a['objects']if q['name']not in retired]+newrows
for o in bpy.data.objects:
 if o.get('source_model')and 'fidelity-v14/candidate'in o['source_model']:o['source_model']=o['source_model'].replace('fidelity-v14/candidate','fidelity-v15/candidate')
 if o.get('source_xml'):o['source_xml']=o['source_xml'].replace('castelwall.jpg',texture.name)
for row in a['nativeOriginalObjects']:
 if 'sourceXml'in row:row['sourceXml']=row['sourceXml'].replace('castelwall.jpg',texture.name)
for filename in ['scene.xml','materials.xml']:
 bpy.data.texts[filename].clear();bpy.data.texts[filename].write((w/'candidate'/filename).read_text())
for key in ['roofedLibrary','battlementLibrary','sharedBodyLibrary','newGateRoofLibrary']:
 lib=Path(proof[key]);a['runtimeLibrarySources'][lib.name]=str(lib)
 for filename in ['node.xml','materials.xml']:bpy.data.texts.new(lib.name+'/'+filename).write((lib/filename).read_text())
a['runtimeLibrarySources'].pop('fluxara_driftlib_volcano_castle_tower_v9',None);a['newPrototypes']=newrows;a['newMaterialVariants']=newmats;a['retiredPrototypeNames']=retired;a['castleSmokeChangedNativeObjectNames']=newnativechanged;a['visualLibrary']=str(mod/'Volcano Remake Castle and Smoke Library.blend');bpy.data.libraries.write(a['visualLibrary'],{bpy.data.objects[q['name']]for q in newrows}|{bpy.data.materials[q['name']]for q in newmats},fake_user=True,compress=True)
for path in newlibrarymodels:shipped=mod/path.name;shipped.write_bytes(path.read_bytes())
a.update({'finalBlend':str(native/'Volcano Remake.blend'),'status':'V15 reusable gray brick castles, red roofs, pennants and dense smoke. Original road and exact source collisions preserved. Stone textures retained. Isolated candidate.'});bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=a['finalBlend']);(w/'asset-registration.json').write_text(json.dumps(a,indent=2));print('V15_NATIVE_CASTLE_SMOKE_SAVED',len(a['objects']),len(a['materials']),len(a['nativeSharedInstances']),flush=True)
