from pathlib import Path
import sys, math, struct, json, copy, shutil, hashlib, xml.etree.ElementTree as E

r=Path(__file__).resolve().parent; w=r/'fidelity-v21'; w.mkdir(exist_ok=True)
old=r/'fidelity-v20/candidate'; c=w/'candidate'; assert not c.exists()
shutil.copytree(old,c)
sys.path.insert(0,str(r.parent/'shared-object-redesign')); from spm_io import parse
from terrain_triangle_distance import triangle_distance
ns={'math':math,'struct':struct}; helper=(r/'fidelity_v2.py').read_text(); exec(helper[helper.index('def encode_buffer'):helper.index('new_vertices, new_indices')],ns)
d=parse(old/'volcano_track.spm'); stone=d['buffers'][2]; green=d['buffers'][3]
assert len(stone['indices'])==192 and len(green['indices'])==24
names=[d['materials'][green['material']],d['materials'][stone['material']]]
center=green['vertices'][8]['position']; cx,peak,cz=center
rx,rz=1.,1.; lip_depth=.6; segments=32
old_ring=[v['position']for v in green['vertices'][:8]]
old_ring.sort(key=lambda p:math.atan2((p[2]-cz)/rz,(p[0]-cx)/rx))
old_ring.append(old_ring[0])
stone_uv={tuple(v['position']):v['uv']for v in stone['vertices']}

def boundary(theta):
    dx,dz=math.cos(theta)*rx,math.sin(theta)*rz
    for a,b in zip(old_ring,old_ring[1:]):
        ex,ez=b[0]-a[0],b[2]-a[2]; den=dx*ez-dz*ex
        if abs(den)<1e-8:continue
        ax,az=a[0]-cx,a[2]-cz
        rad=(ax*ez-az*ex)/den; t=(ax*dz-az*dx)/den
        if rad>0 and -1e-6<=t<=1.000001:
            uv=[stone_uv[tuple(a)][k]*(1-t)+stone_uv[tuple(b)][k]*t for k in range(2)]
            p=tuple(a[k]*(1-t)+b[k]*t for k in range(3))
            return p,tuple(uv)
    raise AssertionError(('No source boundary',theta))

def mesh_buffer(points,faces,uvs,colors,material):
    normals=[[0.,0.,0.]for _ in points]
    for t in faces:
        a,b,z=[points[i]for i in t]; u=[b[k]-a[k]for k in range(3)]; v=[z[k]-a[k]for k in range(3)]
        n=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
        assert sum(q*q for q in n)>1e-10
        for i in t:
            for k in range(3):normals[i][k]+=n[k]
    vertices=[]
    for p,uv,col,n in zip(points,uvs,colors,normals):
        length=math.sqrt(sum(q*q for q in n));assert length>1e-8
        vertices.append({'position':p,'uv':uv,'color':col,'normal':ns['packed_normal']([q/length for q in n])})
    return {'vertices':vertices,'indices':[i for t in faces for i in t],'material':material}

# Twice corner-cut the actual eight-point source rim; stay inside its footprint.
outline=old_ring[:-1]
for step in range(2):
    smoothed=[]
    for a,b in zip(outline,outline[1:]+outline[:1]):
        smoothed.extend([tuple(.75*a[k]+.25*b[k]for k in range(3)),tuple(.25*a[k]+.75*b[k]for k in range(3))])
    outline=smoothed
assert len(outline)==segments
points=[center]; faces=[]; colors=[(242,255,230)]
radii=[.15,.3,.5,.68,.82,.93,1.]
for ri,rad in enumerate(radii):
    for j in range(segments):
        edge=outline[j]; theta=math.atan2(edge[2]-cz,edge[0]-cx); edge_y=edge[1]+.15
        y=edge_y+(peak-edge_y)*math.sqrt(max(0,1-rad*rad))
        points.append((cx+(edge[0]-cx)*rad,y,cz+(edge[2]-cz)*rad))
        shade=.93+.055*(1-rad)+.015*math.sin(theta+.7)
        colors.append(tuple(round(q*shade)for q in (242,255,230)))
    start=1+ri*segments
    for j in range(segments):
        nxt=(j+1)%segments
        if ri==0:faces.append((0,start+nxt,start+j))
        else:
            prev=start-segments
            faces.extend([(prev+j,start+nxt,start+j),(prev+j,prev+nxt,start+nxt)])
top=1+(len(radii)-1)*segments; bottom=len(points)
for j in range(segments):
    p=points[top+j]; points.append((p[0],p[1]-lip_depth,p[2]));colors.append((192,220,177))
    nxt=(j+1)%segments;faces.extend([(top+j,top+nxt,bottom+j),(top+nxt,bottom+nxt,bottom+j)])
grass=mesh_buffer(points,faces,[(.75,.5)]*len(points),colors,0)
adapter_points=[];adapter_uv=[]
for j in range(segments):
    edge=outline[j];theta=math.atan2(edge[2]-cz,edge[0]-cx); p,uv=boundary(theta); adapter_points.extend([p,points[bottom+j]])
    adapter_uv.extend([uv,(uv[0]+.035*math.cos(theta),uv[1]+.035*math.sin(theta))])
adapter_faces=[]
for j in range(segments):
    nxt=(j+1)%segments; adapter_faces.extend([(2*j,2*nxt+1,2*j+1),(2*j,2*nxt,2*nxt+1)])
for i,t in enumerate(adapter_faces):
    a,b,z=[adapter_points[j]for j in t]
    if (b[2]-a[2])*(z[0]-a[0])-(b[0]-a[0])*(z[2]-a[2])<0:adapter_faces[i]=tuple(reversed(t))
adapter=mesh_buffer(adapter_points,adapter_faces,adapter_uv,[(225,230,228)]*len(adapter_points),1)

def bounds(pp):return [min(p[k]for p in pp)for k in range(3)]+[max(p[k]for p in pp)for k in range(3)]
def standalone(buffers,materials,bd):
    raw=bytearray(b'SP'+bytes([10,3])+struct.pack('<6f',*bd)+struct.pack('<H',len(materials)))
    for pair in materials:
        for name in pair:
            value=name.encode();raw+=bytes([len(value)])+value
    raw+=struct.pack('<HH',1,len(buffers))
    for buffer in buffers:raw+=ns['encode_buffer'](buffer,materials)
    return raw
resources=Path('/Users/motoricallc/Downloads/fluxara-drift/iosApp/FluxaraResources')
library=resources/'library/fluxara_driftlib_volcano_rounded_crest_v21';library.mkdir(exist_ok=True)
visual=library/'vr_v21_rounded_central_crest.spm';visual.write_bytes(standalone([grass,adapter],names,bounds(points+adapter_points)))
(library/'node.xml').write_text(f'<scene><object id="RoundedCrest" type="animation" model="{visual.name}" xyz="0 0 0" hpr="0 0 0" scale="1 1 1" interaction="ghost" skeletal-animation="false" /></scene>')
(library/'materials.xml').write_text('<materials>'+''.join(f'<material name="{pair[0]}" />'for pair in names)+'</materials>')
collision=copy.deepcopy(green);collision['material']=0
collider_name='vr_v21_original_central_crest_collision.spm'
(c/collider_name).write_bytes(standalone([collision],[names[0]],bounds([v['position']for v in green['vertices']])))
(c/'volcano_track.spm').write_bytes(ns['replace_buffers'](d,{3:[]}))
scene=E.parse(c/'scene.xml')
E.SubElement(scene.getroot(),'object',id='VRV21_OriginalCentralCrestCollision',type='animation',model=collider_name,xyz='0 0 0',hpr='0 0 0',scale='1 1 1',interaction='physicsonly',shape='exact',**{'skeletal-animation':'false'})
E.SubElement(scene.getroot(),'library',id='VRV21_RoundedCentralCrest_000',name=library.name,xyz='0 0 0',hpr='0 0 0',scale='1 1 1')
scene.write(c/'scene.xml',encoding='unicode')
old_box=bounds([v['position']for b in [stone,green]for v in b['vertices']]); new_box=bounds([v['position']for b in [stone,grass,adapter]for v in b['vertices']])
assert max(abs(x-y)for x,y in zip(old_box,new_box))<1e-5
proof={'baseCandidate':'V20','removedMainBuffer':3,'originalCentralCrestTriangles':8,'retainedCentralStoneTriangles':64,
       'visibleGrassTriangles':len(grass['indices'])//3,'stoneAdapterTriangles':len(adapter['indices'])//3,
       'visibleTriangles':sum(len(b['indices'])//3 for b in [grass,adapter]),'visibleVertices':sum(len(b['vertices'])for b in [grass,adapter]),
       'sourceAndTargetCompositeBounds':old_box,'newSharedCrestLibrary':str(library),'newSharedCrestModel':str(visual),
       'sourceColliderModel':collider_name,'originalStoneGeometryUVsAndPixelsRetained':True,'newTexturePixels':False,
       'existingRuntimeTextures':[str(resources/'textures'/pair[0])for pair in names],
       'sourcePoolObjectId':'volcano-fidelity-v17-centralgreencrest','productionIntegrated':False,'referenceAcceptance':False}
(w/'crest-changes.json').write_text(json.dumps(proof,indent=2)); print('V21_ROUNDED_CENTRAL_CREST_READY',proof['visibleTriangles'],proof['visibleVertices'],flush=True)
