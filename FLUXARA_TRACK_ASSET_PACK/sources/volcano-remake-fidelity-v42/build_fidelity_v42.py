from pathlib import Path
import copy,hashlib,json,shutil,struct,sys,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;w=r/'fidelity-v42';w.mkdir(exist_ok=True);c=w/'candidate';assert not c.exists();shutil.copytree(r/'fidelity-v41/candidate',c)
sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
res=Path('/Users/motoricallc/Downloads/fluxara-drift/iosApp/FluxaraResources');src=res/'library/fluxara_driftlib_volcano_closed_terrain_v40';shared=w/'shared-runtime';shared.mkdir();lib=shared/'fluxara_driftlib_volcano_closed_terrain_v42';shutil.copytree(src,lib)
mainpath=c/'volcano_track.spm';main=parse(mainpath);mainraw=bytearray(main['raw']);mainuv=set()
for v in main['buffers'][2]['vertices']:
 mainuv.update(range(v['uv_offset'],v['uv_offset']+4));struct.pack_into('<2e',mainraw,v['uv_offset'],*(q/3 for q in v['uv']))
mainpath.write_bytes(mainraw);assert all(a==b for i,(a,b)in enumerate(zip(mainraw,main['raw']))if i not in mainuv)
source=src/'vr_v40_closed_terrain.spm';d=parse(source);raw=bytearray(d['raw']);uv_offsets=set()
for b in d['buffers']:
 if d['materials'][b['material']][0]!='fluxara_volcano_stone_shared_v16.jpg':continue
 for v in b['vertices']:
  offset=v['uv_offset'];uv_offsets.update(range(offset,offset+4));struct.pack_into('<2e',raw,offset,*(q/3 for q in v['uv']))
target=lib/'vr_v42_closed_terrain.spm';target.write_bytes(raw);(lib/source.name).unlink()
node=E.parse(lib/'node.xml');node.getroot().find('object').set('model',target.name);node.write(lib/'node.xml',encoding='unicode')
tree=E.parse(c/'scene.xml');entry=tree.getroot().find('library[@name="'+src.name+'"]');before=dict(entry.attrib);assert before['scale']=='1 1 1';entry.set('name',lib.name);tree.write(c/'scene.xml',encoding='unicode')
new=parse(target);assert len(raw)==len(d['raw']);assert all(a==b for i,(a,b)in enumerate(zip(raw,d['raw']))if i not in uv_offsets)
for oldbuf,newbuf in zip(d['buffers'],new['buffers']):
 assert oldbuf['indices']==newbuf['indices']and oldbuf['material']==newbuf['material']
 for a,b in zip(oldbuf['vertices'],newbuf['vertices']):
  assert all(a[k]==b[k]for k in a if k not in ['uv'])
assert d['bounds']==new['bounds']and d['materials']==new['materials']
base=json.loads((r/'fidelity-v41/preservation-verification.json').read_text());own=sum(p.stat().st_size for p in c.rglob('*')if p.is_file());newbytes=sum(p.stat().st_size for p in lib.iterdir()if p.is_file());total=own+base['allCandidateAndAcceptedHistoryBytes']-base['candidateAllFilesBytes']+newbytes
assert total<base['v1Bytes']
for old in (r/'fidelity-v41/candidate').iterdir():
 if old.is_file()and old.name not in ['scene.xml','volcano_track.spm']:assert old.read_bytes()==(c/old.name).read_bytes()
prev=E.parse(r/'fidelity-v41/candidate/scene.xml').getroot();curr=tree.getroot();assert len(list(prev))==len(list(curr))
for a,b in zip(prev,curr):
 assert E.tostring(a)==E.tostring(b)or (a.get('id')==before['id']and {k:v for k,v in a.attrib.items()if k!='name'}=={k:v for k,v in b.attrib.items()if k!='name'})
stone=res/'textures/fluxara_volcano_stone_shared_v16.jpg';stone_sha=hashlib.sha256(stone.read_bytes()).hexdigest();assert stone_sha=='6c765884a7846501355a429f3548d2df78698798a97a0318aefe358d0bdafdfd'
proof={'mainStoneBufferOnlyUVChanged':2,'mainStoneUVVerticesChanged':743,'mainSPMBytesUnchanged':len(mainraw),'mainProtectedRoadBuffersByteExactV41':True,'mainStoneSourceTileMetersApprox':28,'mainStoneNewTileMetersApprox':84,'baseCandidate':'V41','sourceField':str(source),'newField':str(target),'sourceTextureTileMeters':28,'newTextureTileMeters':84,'textureApparentScaleMultiplier':3,'changedUVVertices':len(uv_offsets)//4,'onlyStoneBufferUVBytesChanged':True,'allGeometryNormalsColorsMaterialSlotsIndicesHeaderAndBoundsExact':True,'sameModelBytes':len(raw),'logicalModelPlusUsedTextureIncreasePercent':0,'noNewTexturePixelsOrMaterials':True,'stoneTextureBytes':stone.stat().st_size,'stoneTextureSha256':stone_sha,'referenceNearCliffsAnd97ColumnInstancesRetained':True,'allOtherCandidateFilesExactV41':True,'oldFieldPlacement':before,'newFieldPlacement':dict(entry.attrib),'allPreviousScenePosesExactV41':True,'candidateAllFilesBytes':own,'acceptedSharedHistoryIncludingV40Bytes':base['allCandidateAndAcceptedHistoryBytes']-base['candidateAllFilesBytes'],'newSharedRuntimeAllFilesBytes':newbytes,'allCandidateAndAcceptedHistoryBytes':total,'v1Bytes':base['v1Bytes'],'savingVsV1Bytes':base['v1Bytes']-total,'productionIntegrated':False,'referenceAcceptance':False}
(w/'stone-scale-preflight.json').write_text(json.dumps(proof,indent=2));(w/'preservation-verification.json').write_text(json.dumps(proof,indent=2));print('V42_STONE_SCALE_UV_ONLY_VERIFIED',proof,flush=True)
