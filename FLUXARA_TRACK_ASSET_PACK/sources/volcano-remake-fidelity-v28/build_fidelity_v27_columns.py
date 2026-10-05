from pathlib import Path
import copy,hashlib,json,math,shutil,struct,sys,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;w=r/'fidelity-v27';w.mkdir(exist_ok=True);c=w/'candidate';assert not c.exists();shutil.copytree(r/'fidelity-v26/candidate',c)
resources=Path('/Users/motoricallc/Downloads/fluxara-drift/iosApp/FluxaraResources');sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
from terrain_triangle_distance import triangle_distance
ns={'math':math,'struct':struct};s=(r/'fidelity_v2.py').read_text();exec(s[s.index('def encode_buffer'):s.index('new_vertices, new_indices')],ns)
source=resources/'library/fluxara_driftlib_volcano_organic_cliff_v22/vr_v22_organic_grass_stone_cliff.spm';data=parse(source)
def bounds(pp):return [min(p[k]for p in pp)for k in range(3)]+[max(p[k]for p in pp)for k in range(3)]
def boxdistance(a,b):return math.sqrt(sum(max(a[k]-b[k+3],b[k]-a[k+3],0)**2 for k in range(3)))
parts=[]
for part,buf in zip(['grass_cap','stone_column'],data['buffers']):
    b=copy.deepcopy(buf);mat=data['materials'][b['material']];b['material']=0;box=bounds([b['vertices'][i]['position']for i in b['indices']])
    raw=bytearray(b'SP'+bytes([10,3])+struct.pack('<6f',*box)+struct.pack('<H',1))
    for name in mat:v=name.encode();raw+=bytes([len(v)])+v
    raw+=struct.pack('<HH',1,1)+ns['encode_buffer'](b,[mat])
    lib=resources/f'library/fluxara_driftlib_volcano_{part}_v27';assert not lib.exists();lib.mkdir()
    model=lib/f'vr_v27_{part}.spm';model.write_bytes(raw)
    (lib/'node.xml').write_text(f'<scene><object id="{part}" type="animation" model="{model.name}" xyz="0 0 0" hpr="0 0 0" scale="1 1 1" interaction="ghost" skeletal-animation="false" /></scene>')
    shutil.copy2(source.parent/'materials.xml',lib/'materials.xml')
    parts.append({'part':part,'library':str(lib),'model':str(model),'sourceBuffer':buf['material'],'localBounds':box,'triangles':len(b['indices'])//3,'nativePrototype':'VRV22_Prototype_GrassLip'if part=='grass_cap'else'VRV22_Prototype_StoneBody'})
scene=E.parse(c/'scene.xml');root=scene.getroot();old=[e for e in root.findall('library')if e.get('id','').startswith('VRV16_RoundedTerrain_')];assert len(old)==58
poses=[];stone=parts[1];top=stone['localBounds'][4]
for e in old:
    xyz=list(map(float,e.get('xyz').split()));scale=list(map(float,e.get('scale').split()));hpr=list(map(float,e.get('hpr').split()));assert hpr[0]==hpr[2]==0
    root.remove(e)
    grass=E.SubElement(root,'library',**dict(e.attrib,id=e.get('id')+'_Grass',name=Path(parts[0]['library']).name))
    sx,sy,sz=scale;factor=2.8;newscale=[sx*.9,sy*factor,sz*.9];newxyz=[xyz[0],xyz[1]+top*(sy-newscale[1]),xyz[2]]
    column=E.SubElement(root,'library',**dict(e.attrib,id=e.get('id')+'_Stone',name=Path(parts[1]['library']).name,xyz=' '.join(f'{v:.8f}'for v in newxyz),scale=' '.join(f'{v:.8f}'for v in newscale)))
    poses.append({'source':dict(e.attrib),'grass':dict(grass.attrib),'stone':dict(column.attrib),'stoneHeightFactor':factor,'stoneWidthFactor':.9,'sourceStoneTopWorldY':xyz[1]+top*sy})
scene.write(c/'scene.xml',encoding='unicode')
main=parse(c/'volcano_track.spm');triangles=lambda b:[[b['vertices'][i]['position']for i in b['indices'][j:j+3]]for j in range(0,len(b['indices']),3)]
road=[t for b in main['buffers']if main['materials'][b['material']][0]in ['track01.png','stktex_generic_WoodA.png','stkflag_blackBooster_a.png','stkflag_blackBooster_b.png','stk_generic_gridA.png','stk_generic_gravalSnow_a.png']for t in triangles(b)]
for e in root.findall('object'):
    if e.get('driveable')=='true'and e.get('model'):
        assert e.get('hpr')=='0.0 -0.0 0.0';pos=list(map(float,e.get('xyz').split()));size=list(map(float,e.get('scale').split()))
        road += [[tuple(p[k]*size[k]+pos[k]for k in range(3))for p in t]for b in parse(c/e.get('model'))['buffers']for t in triangles(b)]
assert len(road)==2032;boxes=[bounds(t)for t in road];minimum=1e9
for q in poses:
    e=q['stone'];pos=list(map(float,e['xyz'].split()));size=list(map(float,e['scale'].split()));yaw=math.radians(float(e['hpr'].split()[1]));co,si=math.cos(yaw),math.sin(yaw)
    def world(p):return (pos[0]+co*p[0]*size[0]+si*p[2]*size[2],pos[1]+p[1]*size[1],pos[2]-si*p[0]*size[0]+co*p[2]*size[2])
    best=1e9
    for t in triangles(data['buffers'][1]):
        tt=[world(p)for p in t];box=bounds(tt)
        for rb,rt in zip(boxes,road):
            if boxdistance(box,rb)<best:best=min(best,triangle_distance(tt,rt))
    q['exactStoneTriangleRoadMarginMeters']=best;minimum=min(minimum,best)
    assert best>.5,(e['id'],best)
    print('COLUMN_CLEAR',e['id'],best,flush=True)
p={'baseCandidate':'V26','sourceModel':str(source),'sourceModelSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'parts':parts,'placements':poses,
   'originalAddedCombinedPlacements':58,'replacementPartPlacements':116,'sourceComponentGeometryUVsNormalsColorsAndLocalBoundsRetained':True,
   'grassWorldMatricesRetained':True,'stoneInstanceDimensionsIntentionallyChanged':True,'stoneWorldTopPlaneRetained':True,
   'minimumExactStoneTriangleRoadMarginMeters':minimum,'protectedDrivingTriangles':2032,'newMaterials':0,'newTextureFiles':0,'newImagePixels':False,
   'productionIntegrated':False,'referenceAcceptance':False}
(w/'column-changes.json').write_text(json.dumps(p,indent=2));print('V27_TALL_STONE_COLUMN_PLACEMENTS_READY',minimum,flush=True)
