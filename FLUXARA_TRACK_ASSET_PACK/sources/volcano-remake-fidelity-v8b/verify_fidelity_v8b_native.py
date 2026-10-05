from pathlib import Path
import bpy,json,sys,hashlib,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;w=r/'fidelity-v8b';code=(r/'verify_blend.py').read_text().replace("r/'asset-registration.json'","r/'fidelity-v8b/asset-registration.json'").replace("r/'candidate'","r/'fidelity-v8b/candidate'").replace("r/'final-blend-verification.json'","r/'fidelity-v8b/final-blend-verification.json'");exec(compile(code,str(r/'verify_blend.py'),'exec'))
sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
a=json.loads((w/'asset-registration.json').read_text());checks=[]
def verify(obj,buffer,uv=True):
    assert len(obj.data.vertices)==len(buffer['vertices']);assert max(abs(x-y)for v,s in zip(obj.data.vertices,buffer['vertices'])for x,y in zip(v.co,(s['position'][0],s['position'][2],s['position'][1])))<.00002
    assert [tuple(p.vertices)for p in obj.data.polygons]==[tuple(reversed(buffer['indices'][t:t+3]))for t in range(0,len(buffer['indices']),3)]
    if uv:
        assert all(max(abs(x-y)for x,y in zip(obj.data.uv_layers['UVMap'].data[l].uv,(buffer['vertices'][obj.data.loops[l].vertex_index]['uv'][0],1-buffer['vertices'][obj.data.loops[l].vertex_index]['uv'][1])))<1e-7 for l in range(len(obj.data.loops)))
    checks.append({'object':obj.name,'positionsAndIndicesMatchSpm':True,'uvConvention':'Blender u,1-SPM-v'if uv else'No texture','triangles':len(buffer['indices'])//3})
main=parse(w/'candidate/volcano_track.spm')
for q in a['mainBufferUpdates']:verify(bpy.data.objects[q['object']],main['buffers'][q['buffer']])
proto=bpy.data.objects[a['newPrototypes'][0]['name']];verify(proto,parse(a['newPrototypes'][0]['sourceModel'])['buffers'][0]);assert proto.location.length<1e-7
skin=json.loads((w/'skin-changes.json').read_text());nodes=[n for n in proto.data.materials[0].node_tree.nodes if n.type=='TEX_IMAGE'];assert nodes
for n in nodes:assert n.image.packed_file and hashlib.sha256(n.image.packed_file.data).hexdigest()==skin['palettePixelsUnchangedSha256']
for change in json.loads((w/'castle-changes.json').read_text()):
    row=next(q for q in a['nativeOriginalObjects']if q['model']==change['collider']);obj=bpy.data.objects[row['name']];verify(obj,parse(w/'candidate'/change['collider'])['buffers'][0],False);assert obj.hide_render;assert E.fromstring(row['sourceXml']).get('interaction')=='physicsonly'
    obj=bpy.data.objects[change['id']];points=[obj.matrix_world@v.co for v in obj.data.vertices];actual=[[min(p[k]for p in points)for k in [0,2,1]],[max(p[k]for p in points)for k in [0,2,1]]];assert max(abs(x-y)for v,u in zip(actual,change['originalVisualBounds'])for x,y in zip(v,u))<.00002
p=w/'final-blend-verification.json';data=json.loads(p.read_text());data.update({'updatedMeshes':checks,'newPalettePixelsExactSource':True,'towerWorldBoundsFitOriginalDecorativeBounds':True,'originalCollidersHiddenAndExact':True});p.write_text(json.dumps(data,indent=2));print('V8B_NATIVE_AND_UV_VERIFIED',flush=True)
