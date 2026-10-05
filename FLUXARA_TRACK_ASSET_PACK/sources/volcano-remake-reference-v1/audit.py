from pathlib import Path
import json,hashlib,sys,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;repo=Path('/Users/motoricallc/Downloads/fluxara-drift');f=r/'candidate';before=r/'before';sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();tri=lambda p:sum(len(b['indices'])//3 for b in parse(p)['buffers'])
smoke_tex={'smoke_huricane.png','smoke_huricane_transp.png','gfx_snowStormAnimated_a.png'}
smoke_models={q['model'] for q in json.load(open(r/'smoke-volume-proof.json'))}
changed=smoke_models|{'volcano_track.spm','vulcan_01.spm','vulcan_02.spm','vulcan_03.spm'};proof=[]
for p in before.glob('*.spm'):
    a,b=parse(p),parse(f/p.name);expected_materials=[[('vr_arch_stone.png' if n=='Lava_004_COLOR.jpg' and p.name=='volcano_track.spm' else n) for n in row] for row in a['materials']]
    if p.name in smoke_models:
        assert max(abs(u-v) for u,v in zip(a['bounds'],b['bounds']))<.001,p.name
        assert .8*tri(p)<=tri(f/p.name)<=1.2*tri(p),p.name
        proof.append({'model':p.name,'decorativeSmokeRemade':True,'boundsCentersOriginsPreserved':True,'triangleBudgetPassed':True});continue
    assert a['bounds']==b['bounds'] and expected_materials==b['materials'] and a['flags']==b['flags']
    assert len(a['buffers'])==len(b['buffers'])
    for x,y in zip(a['buffers'],b['buffers']):
        assert x['material']==y['material'] and x['indices']==y['indices'] and len(x['vertices'])==len(y['vertices'])
        for v,w in zip(x['vertices'],y['vertices']):
            assert v['position']==w['position'] and v.get('normal')==w.get('normal')
            if a['materials'][x['material']][0] in smoke_tex:assert v.get('color')==w.get('color')
            if p.name not in changed or a['materials'][x['material']][0] not in {'Rock13_col.jpg'}|smoke_tex:assert v.get('uv')==w.get('uv') and v.get('color')==w.get('color')
    if p.name not in changed:assert sha(p)==sha(f/p.name)
    proof.append({'model':p.name,'positionsNormalsIndicesBoundsExact':True,'byteExact':sha(p)==sha(f/p.name)})
for name in ['track.xml','quads.xml','graph.xml','scripting.as','easter_eggs.xml','magma.music','fortmagma5.ogg']:assert sha(before/name)==sha(f/name),name
def sig(e):return [e.tag,sorted(e.attrib.items()),(e.text or '').strip(),[sig(q) for q in e]]

visual_keys={'shader','normal-map','gloss-map'}
visual_materials={'blackrock.jpg','blackrock_lava.jpg','castelwall.jpg','lava.png','Lava_004_COLOR.jpg','lava_2k_diffuse.jpg','Rock13_col.jpg','fluxara_drifttex_generic_lavaA.png','smoke_huricane.png','smoke_huricane_transp.png','gfx_snowStormAnimated_a.png'}
ma=E.parse(before/'materials.xml').getroot();mb=E.parse(f/'materials.xml').getroot();assert len(mb)==len(ma)+1;assert mb[-1].attrib=={'name':'vr_arch_stone.png'}
for x,y in zip(ma,mb):
 if x.get('name') in visual_materials:
  assert {k:v for k,v in x.attrib.items() if k not in visual_keys}=={k:v for k,v in y.attrib.items() if k not in visual_keys}
  assert [sig(q) for q in x]==[sig(q) for q in y]
 else:assert sig(x)==sig(y)
old=E.parse(before/'scene.xml').getroot();new=E.parse(f/'scene.xml').getroot();rows=json.load(open(r/'placements.json'));ids={q['name'] for q in rows}
smoke_ids={q['id'] for q in json.load(open(r/'smoke-scale-proof.json'))}
def scene_sig(e):
 e=E.fromstring(E.tostring(e))
 if e.get('id') in smoke_ids:
  assert e.get('interaction')=='ghost';e.attrib.pop('scale',None)
 return sig(e)
assert [scene_sig(q) for q in old if q.tag not in ['sun','sky-box']]==[scene_sig(q) for q in new if q.tag not in ['sun','sky-box'] and q.get('id') not in ids]
def library_triangles(name,depth=0):
    assert depth<8;folder=repo/'iosApp/FluxaraResources/library'/name;node=E.parse(folder/'node.xml').getroot()
    models=[q.get('model') for q in node.findall('object') if q.get('model') and q.get('interaction') not in ['physicsonly','physics-only']]
    models += [list(g)[0].get('model') for g in node.findall('./lod/group') if len(g)]
    return sum(tri(folder/n) for n in models)+sum(library_triangles(q.get('name'),depth+1) for q in node.findall('library'))
ot=tri(before/'volcano_track.spm')+sum(tri(before/q.get('model')) for q in old.findall('./track/static-object')+old.findall('object') if q.get('model'))+sum(library_triangles(q.get('name')) for q in old.findall('library'))
names={q['library'] for q in rows};libraries=[{'library':n,'folder':str(repo/'iosApp/FluxaraResources/library'/n),'triangles':library_triangles(n)} for n in sorted(names)]
nt=tri(f/'volcano_track.spm')+sum(tri(f/q.get('model')) for q in old.findall('./track/static-object')+old.findall('object') if q.get('model'))+sum(library_triangles(q.get('name')) for q in old.findall('library'))+sum(library_triangles(q['library']) for q in rows)
assert all(q.get('interaction')=='ghost' for q in old.findall('object') if q.get('model') in smoke_models);shared=json.load(open(r/'new-shared-runtime.json'));sb=sum(q['bytes'] for q in shared['libraries']);size=lambda folder:sum(p.stat().st_size for p in folder.iterdir() if p.is_file());total=size(f)+sb
a={'originalBytes':size(before),'trackFolderBytes':size(f),'newSharedBytes':sb,'trackAndNewSharedBytes':total,'byteChangePercent':100*(total/size(before)-1),'originalTriangles':ot,'newTriangles':nt,'triangleChangePercent':100*(nt/ot-1),'newSharedPlacementCount':len(rows),'allOriginalNonSmokeMeshPositionsNormalsIndicesBoundsExact':True,'cloudModelDimensionsCentersOriginsPreserved':True,'originalPhysicalMaterialDefinitionsExact':True,'smokeVolumeModels':json.load(open(r/'smoke-volume-proof.json')),'archMaterial':json.load(open(r/'arch-material-proof.json')),'materialVisualChanges':['Three smoke materials use solid shaded geometry; old photographic normal/gloss maps removed from eight scenery materials; physical definitions unchanged'],'allOriginalSceneNodesExceptSunSkyAndGhostSmokeScaleExact':True,'decorativeSmokeScaleChanges':json.load(open(r/'smoke-scale-proof.json')),'protectedXmlMusicScriptByteExact':True,'meshProof':proof,'weightNotIncreased':total<=size(before),'triangleBudgetPassed':.8*ot<=nt<=1.2*ot,'triangleScope':'Highest visual LOD plus all original conditional objects, a conservative logical count; not GPU performance'}
(r/'preservation-audit.json').write_text(json.dumps(a,indent=2));(r/'shared-runtime.json').write_text(json.dumps({'libraries':libraries,'newExports':shared['libraries'],'placements':rows,'instances':len(rows),'newLibraryBytes':sb},indent=2));print(json.dumps(a));assert a['weightNotIncreased'] and a['triangleBudgetPassed']
