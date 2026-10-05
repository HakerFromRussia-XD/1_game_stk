from pathlib import Path
import json,shutil,xml.etree.ElementTree as E,sys,hashlib
r=Path(__file__).resolve().parent;repo=Path('/Users/motoricallc/Downloads/fluxara-drift');pack=repo/'FLUXARA_TRACK_ASSET_PACK';src=pack/'models/shared/fluxara_reused_winter_fir_b_v1/library/fluxara_driftlib_pinetree_b';name='fluxara_driftlib_summit_snow_fir_v1';out=pack/'models/summit-run-reference-v1/runtime-library'/name;out.mkdir(parents=True,exist_ok=True)
for n in ['fluxara_driftlib_pinetree_b_high.spm','fluxara_driftlib_pinetree_b_low.spm','fir_reuse_b_foliage.png','fir_reuse_b_snow.png','fir_reuse_bark_224.png','fir_reuse_b_far.png']:shutil.copy2(src/n,out/n)
# The approved donor stores wind strength in vertex RGB. The solid compatibility
# material interpreted that strength as black paint in the first runtime draft.
# Strip only the wind channel on this copy; retain all shape/normal/UV/index data.
sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
model=out/'fluxara_driftlib_pinetree_b_high.spm';d=parse(model);raw=d['raw'];raw[3]&=~2
for v in sorted([v for b in d['buffers'] for v in b['vertices']],key=lambda v:v['color_offset'],reverse=True):
 at=v['color_offset'];del raw[at:at+(1 if raw[at]==128 else 4)]
model.write_bytes(raw);a=parse(model)
for x,y in zip(a['buffers'],d['buffers']):assert x['indices']==y['indices'] and all(v['position']==w['position'] and v['normal']==w['normal'] and v['uv']==w['uv'] for v,w in zip(x['vertices'],y['vertices']))
(r/'fir-compatibility.json').write_text(json.dumps({'source':str(src/model.name),'sourceSha256':hashlib.sha256((src/model.name).read_bytes()).hexdigest(),'variantSha256':hashlib.sha256(model.read_bytes()).hexdigest(),'shapeNormalsUvIndicesExact':True,'removedChannel':'Vertex RGB wind strengths, incompatible with solid shader fallback','approvedSourceUnchanged':True},indent=2))
root=E.Element('scene');g=E.SubElement(E.SubElement(root,'lod'),'group',name=name)
for distance,model in [(160,'fluxara_driftlib_pinetree_b_high.spm'),(2000,'fluxara_driftlib_pinetree_b_low.spm')]:
 E.SubElement(g,'static-object',lod_distance=str(distance),lod_group=name,model=model,xyz='-0.331 0.558 0.03',hpr='0 0 0',scale='1.64 0.904 1.75',interaction='ghost',**{'skeletal-animation':'false'})
E.SubElement(root,'object',id=name+'_visual',type='animation',xyz='0 0 0',hpr='0 0 0',scale='1 1 1',interaction='ghost',lod_instance='true',lod_group=name,**{'skeletal-animation':'false'})
E.ElementTree(root).write(out/'node.xml',encoding='unicode');mat=E.Element('materials')
for n in ['fir_reuse_b_foliage.png','fir_reuse_b_snow.png','fir_reuse_bark_224.png']:E.SubElement(mat,'material',name=n)
E.SubElement(mat,'material',name='fir_reuse_b_far.png',shader='alphatest');E.ElementTree(mat).write(out/'materials.xml',encoding='unicode');shutil.copytree(out,repo/'iosApp/FluxaraResources/library'/name,dirs_exist_ok=True)
scene=E.parse(r/'candidate/scene.xml');rows=[]
for q in list(scene.getroot()):
 if q.tag=='library' and q.get('id','').startswith('SR_OriginalFir_'):scene.getroot().remove(q)
for i,o in enumerate(scene.getroot().find('track').findall('static-object')):
 e=E.SubElement(scene.getroot(),'library',id='SR_OriginalFir_'+str(i).zfill(3),name=name,xyz=o.get('xyz'),hpr=o.get('hpr'),scale=o.get('scale'));rows.append({'name':e.get('id'),'library':name,'role':'original-fir','xyz':list(map(float,e.get('xyz').split())),'hpr':list(map(float,e.get('hpr').split())),'scale':list(map(float,e.get('scale').split())),'originalStaticObjectIndex':i})
scene.write(r/'candidate/scene.xml',encoding='unicode');(r/'placements.json').write_text(json.dumps(rows,indent=2));(r/'new-shared-runtime.json').write_text(json.dumps({'libraries':[{'library':name,'path':str(out),'bytes':sum(p.stat().st_size for p in out.iterdir() if p.is_file()),'source':str(src),'reuseTier':'adapt','adaptation':'Unchanged approved winter fir geometry/textures, wrapper aligns original tree envelope; original tree collider remains separately'}]},indent=2));print('FIR_REUSED',len(rows))
