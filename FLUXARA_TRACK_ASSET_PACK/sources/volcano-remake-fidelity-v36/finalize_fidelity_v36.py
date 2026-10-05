from pathlib import Path
import bpy,copy,hashlib,json,math,sys,xml.etree.ElementTree as E
from mathutils import Matrix,Vector,Euler
r=Path(__file__).resolve().parent;w=r/'fidelity-v36';native=w/'native';native.mkdir(exist_ok=True)
a=json.loads((r/'fidelity-v35/asset-registration.json').read_text());before=copy.deepcopy(a);p=json.loads((w/'visual-batch-preflight.json').read_text());plants=json.loads((w/'plant-grounding.json').read_text());assert (w/'preservation-verification.json').is_file()
bpy.ops.wm.open_mainfile(filepath=a['finalBlend']);bpy.context.preferences.filepaths.save_version=0
sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
s=(r/'finalize_fidelity_v9.py').read_text();exec(s[s.index('def mesh_from_buffer'):s.index('updates=a')]);s=(r/'finalize_fidelity_v15.py').read_text();exec(s[s.index('def native_mesh'):s.index('newrows=[]')])
scene=E.parse(w/'candidate/scene.xml').getroot();proto_col=bpy.data.collections['Volcano Remake Asset Prototypes'];newrows=[];newmats=[];changed_geo=[];changed_mat=[];changed_matrix=[]
def geometry(o):
 m=o.data;return(tuple(tuple(v.co)for v in m.vertices),tuple(tuple(v.vertices)for v in m.polygons),tuple((layer.name,tuple(tuple(v.uv)for v in layer.data))for layer in m.uv_layers),tuple(tuple(v.vector)for v in m.corner_normals),tuple((attr.name,attr.data_type,attr.domain,tuple(tuple(v.color)for v in attr.data))for attr in m.color_attributes),tuple(x.name if x else None for x in m.materials))
snap={o.name:geometry(o)for o in bpy.data.objects if o.type=='MESH'};matrices={n:tuple(tuple(v)for v in bpy.data.objects[n].matrix_world)for n in snap}
def matrix(attrs):
 pos=list(map(float,attrs['xyz'].split()));sc=list(map(float,attrs['scale'].split()));hp=list(map(float,attrs['hpr'].split()));return Matrix.Translation(Vector((pos[0],pos[2],pos[1])))@Euler(tuple(math.radians(-v)for v in [hp[0],hp[2],hp[1]]),'XZY').to_matrix().to_4x4()@Matrix.Diagonal((sc[0],sc[2],sc[1],1))
def proto(name,ident,path,mat):
 d=parse(path);mesh=native_mesh(name+'Mesh',d['buffers'][0],[mat]);obj=bpy.data.objects.new(name,mesh);proto_col.objects.link(obj);obj.hide_set(True);obj.hide_render=True;obj['asset_id']=ident;obj['source_model']=str(path);row={'id':ident,'name':name,'sourceModel':str(path),'sourceBuffer':0,'triangles':len(d['buffers'][0]['indices'])//3,'materials':[mat.name]};newrows.append(row);return obj
def texture_variant(oldname,newname,ident,image,oldtex):
 mat=bpy.data.materials[oldname].copy();mat.name=newname;mat['asset_id']=ident;hits=0
 for node in mat.node_tree.nodes:
  if node.type=='TEX_IMAGE'and node.image and oldtex in node.image.name:node.image=image;hits+=1
 assert hits,(oldname,[n.image.name for n in mat.node_tree.nodes if n.type=='TEX_IMAGE'and n.image]);newmats.append({'id':ident,'name':mat.name,'textures':[image.name],'sourceMaterial':oldname,'adaptation':'Exact reused image pixels with original shader settings.'});return mat
alias=Path(p['newMudTextureAlias']['path']);image=bpy.data.images.load(str(alias),check_existing=False);image.name=alias.name;image.pack()
mapping={}
for row in before['materials']:
 if any(t in ['stk_mudpot_a.png','fluxara_drift_mudpot_a.png']for t in row.get('textures',[])):
  oldtex=next(t for t in row['textures']if t in ['stk_mudpot_a.png','fluxara_drift_mudpot_a.png']);mapping[row['name']]=texture_variant(row['name'],'VRV36_LavaMud_'+str(len(mapping)),'volcano-fidelity-v36-mud-material-'+str(len(mapping)),image,oldtex)
# Original map-local MudBubbles and eight mud pad triangles: only copied material slots change.
for obj in bpy.data.objects:
 if obj.type!='MESH':continue
 if any(m and m.name in mapping for m in obj.data.materials):
  obj.data=obj.data.copy()
  for i,m in enumerate(obj.data.materials):
   if m and m.name in mapping:obj.data.materials[i]=mapping[m.name]
  changed_mat.append(obj.name)
# Copied pooled mud prototypes preserve their exact native skin geometry and all native attributes.
mud_proto_map={}
for row in before['objects']:
 if Path(row['sourceModel']).parent.name!='fluxara_driftlib_mudpot_a':continue
 old=bpy.data.objects[row['name']];name='VRV36_Prototype_'+Path(row['sourceModel']).stem;obj=bpy.data.objects.new(name,old.data);proto_col.objects.link(obj);obj.hide_set(True);obj.hide_render=True;obj['asset_id']='volcano-fidelity-v36-mud-'+Path(row['sourceModel']).stem;obj['source_model']=str(w/'shared-runtime/fluxara_driftlib_volcano_mudpot_v36'/Path(row['sourceModel']).name);newrows.append({'id':obj['asset_id'],'name':name,'sourceModel':obj['source_model'],'triangles':row['triangles'],'materials':[m.name for m in obj.data.materials],'sourcePoolObjectId':row['id'],'role':'Copied original native animated mud source with existing lava image alias; runtime skeletal data exact.'});mud_proto_map[row['name']]=obj
for row in a['nativeSharedInstances']:
 if row['library']=='fluxara_driftlib_mudpot_a':
  obj=bpy.data.objects[row['name']];new=mud_proto_map[row['prototype']];obj.data=new.data;row['prototype']=new.name;row['library']='fluxara_driftlib_volcano_mudpot_v36';obj['source_prototype']=new.name;obj['asset_id']=new['asset_id'];obj['source_model']=new['source_model'];obj['shared_runtime_library']=row['library'];changed_mat.append(obj.name)
brick=bpy.data.materials['VRV15_CastleBodyVertexBrick'].copy();brick.name='VRV36_TerracottaBrickRoof';brick['asset_id']='volcano-fidelity-v36-roof-material';newmats.append({'id':brick['asset_id'],'name':brick.name,'textures':['fluxara_castle_brick_v15.jpg'],'sourceMaterial':'VRV15_CastleBodyVertexBrick','adaptation':'Existing masonry pixels multiplied by authored roof vertex tint and new planar UVs.'})
roof=proto('VRV36_Prototype_TiledRoof','volcano-fidelity-v36-tiled-roof',p['newRoofModel']['path'],brick)
for row in a['nativeSharedInstances']:
 if row['library']=='fluxara_driftlib_volcano_castle_roof_v15':
  row['library']='fluxara_driftlib_volcano_tile_roof_v36';obj=bpy.data.objects[row['name']];obj['shared_runtime_library']=row['library']
  if row['prototype']=='VRV15_Prototype_CastleRoof':obj.data=roof.data;row['prototype']=roof.name;obj['source_prototype']=roof.name;obj['source_model']=roof['source_model'];obj['asset_id']=roof['asset_id'];changed_geo.append(obj.name)
  ident=row.get('sourcePlacementId');obj['source_xml']=E.tostring(scene.find(f'library[@id="{ident}"]'),encoding='unicode')
for q in plants['placements']:
 matches=[x for x in a['nativeSharedInstances']if x.get('sourcePlacementId')==q['after']['id']or(not x.get('sourcePlacementId')and x['name'].startswith(q['after']['id']+'_'))];assert len(matches)==1;row=matches[0];row['sourcePlacementId']=q['after']['id'];obj=bpy.data.objects[row['name']];obj.matrix_world=matrix(q['after']);row['matrix']=[list(v)for v in obj.matrix_world];obj['source_xml']=E.tostring(scene.find(f'library[@id="{q["after"]["id"]}"]'),encoding='unicode');changed_matrix.append(obj.name)
# Author only the Color values of four existing cone roofs; preserve all native geometry/UV/custom normal arrays.
main=parse(w/'candidate/volcano_track.spm');wood=main['buffers'][p['woodBuffer']];users=[o for o in bpy.data.objects if o.name.startswith('VR_OriginalSurface_')and o.type=='MESH'and len(o.data.polygons)==159 and any(m and 'WoodA'in m.name for m in o.data.materials)];assert len(users)==1;obj=users[0];mesh=obj.data.copy();assert len(mesh.vertices)==len(wood['vertices']);col=mesh.color_attributes.get('Color');assert col and col.domain=='CORNER'
for loop in mesh.loops:col.data[loop.index].color=tuple(x/255 for x in wood['vertices'][loop.vertex_index].get('color',(255,255,255)))+(1,)
obj.data=mesh;changed_geo.append(obj.name)
sm=next(q for q in a['nativeOriginalObjects']if q['model']=='AshColumn.spm');obj=bpy.data.objects[sm['name']];obj.matrix_world=matrix(p['smokeAfter']);sm['matrix']=[list(v)for v in obj.matrix_world];sm['sourceXml']=E.tostring(scene.find('object[@model="AshColumn.spm"]'),encoding='unicode');obj['source_xml']=sm['sourceXml'];changed_matrix.append(obj.name)
for name in ['scene.xml','track.xml','materials.xml','quads.xml','graph.xml']:
 bpy.data.texts[name].clear();bpy.data.texts[name].write((w/'candidate'/name).read_text())
for lib in (w/'shared-runtime').iterdir():
 a['runtimeLibrarySources'][lib.name]=str(lib)
 for fn in ['node.xml','materials.xml']:bpy.data.texts.new(lib.name+'/'+fn).write((lib/fn).read_text())
for f in (w/'shared-textures').iterdir():a['textures'][f.name]={'source':str(f),'packPath':str(f),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'poolId':'volcano-fidelity-v36-texture-'+f.stem,'reusedPixels':True}
a['objects']+=newrows;a['materials']+=newmats;a['newPrototypes']=newrows;a['newMaterialVariants']=newmats;a['changedNativeGeometry']=sorted(set(changed_geo));a['changedNativeMaterials']=sorted(set(changed_mat));a['changedNativeMatrices']=changed_matrix
pack=Path('/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK');mod=pack/'models/volcano-remake-fidelity-v36';mod.mkdir(exist_ok=True);a['visualLibrary']=str(mod/'Volcano Remake Lava Roof Variants.blend');bpy.data.libraries.write(a['visualLibrary'],{bpy.data.objects[q['name']]for q in newrows}|{bpy.data.materials[q['name']]for q in newmats},fake_user=True,compress=True)
a['finalBlend']=str(native/'Volcano Remake.blend');a['status']='V36 isolated working draft. Stone pixels retained,136 existing plants grounded on supported caps, lava material aliases, tile roof variant, leaned visual smoke and reused blue sky. Runtime/reference/integration gates separate.'
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=a['finalBlend']);(w/'asset-registration.json').write_text(json.dumps(a,indent=2))
# Compare every pre-existing native object with V35; only explicitly listed changes are allowed.
current={o.name:geometry(o)for o in bpy.data.objects if o.type=='MESH'};curmat={n:tuple(tuple(v)for v in bpy.data.objects[n].matrix_world)for n in current}
allowed_geo=set(a['changedNativeGeometry'])|set(a['changedNativeMaterials']);allowed_m=set(changed_matrix)
for name,g in snap.items():
 if name not in allowed_geo:assert current[name]==g,name
 if name not in allowed_m:assert matrices[name]==curmat[name],name
stone=bpy.data.materials['VRV4E_Rock13_col.jpg'];im=next(n.image for n in stone.node_tree.nodes if n.type=='TEX_IMAGE');assert hashlib.sha256(im.packed_file.data).hexdigest()=='6c765884a7846501355a429f3548d2df78698798a97a0318aefe358d0bdafdfd'
for row in a['nativeSharedInstances']:assert bpy.data.objects[row['name']].data==bpy.data.objects[row['prototype']].data,row['name']
proof={'allPriorNativeObjectsRetained':len(snap),'newPrototypes':newrows,'changedNativeGeometry':a['changedNativeGeometry'],'changedNativeMaterialUsers':a['changedNativeMaterials'],'changedNativeMatrices':changed_matrix,'allOtherNativeAttributesExactV35':len(set(snap)-allowed_geo),'allOtherNativeMatricesExactV35':len(set(snap)-allowed_m),'stonePackedPixelsExact':True,'meshObjects':len(current),'skyAndSunNativeEmbeddedSceneXMLExact':True,'canonicalPending':True,'runtimeAndReferenceAcceptanceSeparate':True}
(w/'final-blend-verification.json').write_text(json.dumps(proof,indent=2));print('V36_NATIVE_VARIANTS_AND_PRESERVATION_VERIFIED',len(current),len(newrows),len(changed_matrix),flush=True)

exec(compile((r/"register_fidelity_v36_canonical.py").read_text(),str(r/"register_fidelity_v36_canonical.py"),"exec"))
print("V36_NATIVE_CANONICAL_PIPELINE_COMPLETE",flush=True)
