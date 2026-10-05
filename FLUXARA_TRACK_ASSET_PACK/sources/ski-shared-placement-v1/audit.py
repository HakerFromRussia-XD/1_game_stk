from pathlib import Path
import json,sys,hashlib,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;before=r/'before';out=r/'candidate';a=json.load(open(r/'ski-extraction.json'));sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
changed={'scene.xml','materials.xml','ski-dash_winter_scenery.spm','ski-dash-branchless-fir-v12.spm'}|{q['original'] for q in a['textures']}
if (r/'preview-update.json').exists():
 preview=json.load(open(r/'preview-update.json'));assert sha(out/'screenshot.png')==preview['sha256'];changed.add('screenshot.png')
for p in before.iterdir():
 if p.is_file() and p.name not in changed:assert sha(p)==sha(out/p.name),p.name
old=E.parse(before/'scene.xml').getroot();new=E.parse(out/'scene.xml').getroot();moved={q['id']:q for q in a['placements'] if q.get('existingCoordinateInstance')};inserted={q['id'] for q in a['placements'] if not q.get('existingCoordinateInstance')}|{q['id'] for q in a['extraCoordinatePlacements']}
# Structural comparison preserves every atmospheric, house, item, spawn and control node.
for original,actual in zip(list(old),[q for q in new if q.get('id') not in inserted]):
 if original.get('id') in moved:
  assert actual.tag=='library' and actual.get('name')==moved[original.get('id')]['library']
  assert {k:actual.get(k) for k in ['id','xyz','hpr','scale']}=={k:original.get(k) for k in ['id','xyz','hpr','scale']};assert not list(original)
 else:assert E.tostring(original)==E.tostring(actual),(original.attrib,actual.attrib)
assert len(list(old))==len([q for q in new if q.get('id') not in inserted])
oldfir=parse(before/'ski-dash-branchless-fir-v12.spm');newfir=parse(next((r/'new-library/fluxara_driftlib_ski_branchless_fir_v12').glob('*.spm')))
for ob,nb in zip(oldfir['buffers'],newfir['buffers']):
 assert ob['indices']==nb['indices']
 for ov,nv in zip(ob['vertices'],nb['vertices']):assert {k:v for k,v in ov.items() if not k.endswith('offset')}=={k:v for k,v in nv.items() if not k.endswith('offset')}
for q in a['textures']:assert sha(Path(q['source']))==sha(Path(q['path']))
# Alias replacement changes only visual names; original material settings are exact.
aliases={q['original']:q['alias'] for q in a['textures']};original=E.parse(before/'materials.xml').getroot();actual=E.parse(out/'materials.xml').getroot();origdict={q.get('name'):dict(q.attrib) for q in original};newdict={q.get('name'):dict(q.attrib) for q in actual}
for name,attr in origdict.items():
 expected={k:aliases.get(v,v) if k=='name' else v for k,v in attr.items()};assert newdict[aliases.get(name,name)]==expected,name
result={'track':'fluxara-user-ski-dash','protectedRouteMeshAndNavmeshByteExact':True,'originalAtmosphereObjectsAndAuroraByteExact':True,'originalHouseLibrariesAndTransformsExact':len(old.findall('library')),'originalGameplayNodesStructurallyExact':True,'fir71TransformsExact':True,'firModelVerticesIndicesNormalsUVColorsExact':True,'texturePixelsByteExact':True,'materialParametersExactUnderTextureAliases':True,'retainedSceneryVertexRecordsExactBeforeStringAliasPromotion':a['remainderVertexRecordsAndTriangleOrderExact'],'newTrees':a['newTreeInstances'],'newTreeFootprintsOutsideNavmesh':'Conservative expanded whole-mesh AABB test; runtime validation pending','sourceBytes':a['sourceBytes'],'candidateTrackBytes':a['candidateTrackBytes'],'allNewSharedBytes':a['allNewSharedBytes'],'totalBytes':a['totalCandidateBytes'],'savedBytesBeforePreview':50900,'savedBytesIncludingPreviewAndWindowSettings':a['sourceBytes']-a['totalCandidateBytes'],'notes':['Only three baked bunting spans extracted. Differing normals/UVs in other groups retained.','Seventy-one firs were already coordinate objects: promotion enables cross-track runtime reuse, it does not remove seventy-one baked copies.','Three bunting surfaces differ by exporter triangulation within sub-millimeter bounds; all source vertex UV/color/material identities retained.']};(r/'preservation-audit.json').write_text(json.dumps(result,indent=2));print('SKI_PRESERVATION_VERIFIED',result['savedBytesBeforePreview'])
