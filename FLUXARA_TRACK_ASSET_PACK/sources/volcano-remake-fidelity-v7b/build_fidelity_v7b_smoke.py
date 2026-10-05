from pathlib import Path
import bpy,sys,math,json,random,shutil,xml.etree.ElementTree as E
from mathutils import Vector
r=Path(__file__).resolve().parent;w=r/'fidelity-v7b';w.mkdir(exist_ok=True);c=w/'candidate'
shutil.copytree(r/'fidelity-v5-alpha/candidate',c,dirs_exist_ok=True)
sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
bpy.ops.wm.read_factory_settings(use_empty=True)
sys.path.insert(0,'/Users/motoricallc/Library/Application Support/Blender/4.5/scripts/addons');import io_scene_spm;io_scene_spm.register()
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.preferences.filepaths.save_version=0
targets={'AshCloud.spm':((-260,80,-160),(-155,155,-50)),
         'AshColumn.spm':((-95,75,-70),(5,175,25)),
         'PyroclasticFlow.spm':((145,90,-135),(245,160,-25))}
proof=[]
for name,(worldlo,worldhi)in targets.items():
    source=parse(r/'before'/name);lo=Vector((source['bounds'][0],source['bounds'][2],source['bounds'][1]));hi=Vector((source['bounds'][3],source['bounds'][5],source['bounds'][4]));ext=hi-lo
    dimensions=Vector((worldhi[0]-worldlo[0],worldhi[2]-worldlo[2],worldhi[1]-worldlo[1]));scale=Vector(tuple(dimensions[k]/ext[k]for k in range(3)));count=round(sum(len(b['indices'])//3 for b in source['buffers'])/80);radius=min(dimensions)*.19;rng=random.Random(7718+count);parts=[]
    for j in range(count):
        t=j/(count-1);rad=radius if j in [0,count-1]else radius*rng.uniform(.72,1.)
        centre=Vector((dimensions.x-radius,dimensions.y-radius,radius)).lerp(Vector((radius,radius,dimensions.z-radius)),t)
        if j not in [0,count-1]:
            for k in range(3):centre[k]=max(rad,min(dimensions[k]-rad,centre[k]+math.sin(t*math.pi)*rng.uniform(-radius*.65,radius*.65)))
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1);obj=bpy.context.object;obj.name='VRV7B_'+Path(name).stem+'_Puff_'+str(j)
        ul=[min(v.co[k]for v in obj.data.vertices)for k in range(3)];uh=[max(v.co[k]for v in obj.data.vertices)for k in range(3)]
        for v in obj.data.vertices:
            spherical=Vector(tuple(centre[k]+((v.co[k]-ul[k])/(uh[k]-ul[k])*2-1)*rad for k in range(3)))
            v.co=Vector(tuple(lo[k]+spherical[k]/scale[k]for k in range(3)))
        parts.append(obj)
    bpy.ops.object.select_all(action='DESELECT')
    for obj in parts:obj.select_set(True)
    bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();obj=bpy.context.object;obj.location=(0,0,0);obj.name='VRV7B_'+Path(name).stem
    texture=source['materials'][0][0];material=bpy.data.materials.get('VRV7B_'+texture)or bpy.data.materials.new('VRV7B_'+texture);material.use_nodes=True
    if not any(n.type=='TEX_IMAGE'for n in material.node_tree.nodes):
        node=material.node_tree.nodes.new('ShaderNodeTexImage');node.image=bpy.data.images.load(str(c/texture));material.node_tree.links.new(node.outputs['Color'],material.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
    obj.data.materials.append(material);obj.data.uv_layers.new(name='UVMap')
    for polygon in obj.data.polygons:
        polygon.use_smooth=True
        face_height=sum(obj.data.vertices[i].co.z for i in polygon.vertices)/len(polygon.vertices)
        for loop in polygon.loop_indices:
            obj.data.uv_layers['UVMap'].data[loop].uv=(.75 if face_height<lo.z+ext.z*.25 else .25,.5)
    bpy.ops.screen.spm_export(filepath=str(c/name),selection_type='selected',localsp=False,applymodifiers=True,export_normal=True,export_vcolor=False,export_tangent=False)
    d=parse(c/name);error=max(abs(a-b)for a,b in zip(source['bounds'],d['bounds']));assert error<.0001
    xyz=(worldlo[0]-source['bounds'][0]*scale.x,worldlo[1]-source['bounds'][1]*scale.z,worldlo[2]-source['bounds'][2]*scale.y)
    proof.append({'model':name,'billows':count,'originalTriangles':sum(len(b['indices'])//3 for b in source['buffers']),'triangles':sum(len(b['indices'])//3 for b in d['buffers']),'localBoundsMaxError':error,'sourceSpm':str(r/'before'/name),'paletteReused':texture,'worldBoundsTarget':[worldlo,worldhi],'instanceScaleGame':[scale.x,scale.z,scale.y],'instanceXyz':xyz,'instanceHpr':[0,0,0],'construction':'Near-spherical puffs in world space; inverse per-map scaling stored in local mesh, local bounds/origin/axes retained.'})
    obj.hide_set(True);obj.hide_render=True;bpy.ops.object.select_all(action='DESELECT')
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(w/'Smoke Billow Sources.blend'))
scene=E.parse(c/'scene.xml');changes=[];removed=[];sprite_names={'AshCloud2.spm','AshCloudEffect.spm','AshColumnEffect.spm','EruptionAsh.spm','PyroclasticFlowAsh.spm'}
for obj in list(scene.getroot().findall('object')):
    if obj.get('model')in sprite_names:
        assert obj.get('interaction')=='ghost';removed.append(E.tostring(obj,encoding='unicode'));scene.getroot().remove(obj)
    elif obj.get('model')in targets:
        assert obj.get('interaction')=='ghost';old=E.tostring(obj,encoding='unicode');row=next(q for q in proof if q['model']==obj.get('model'))
        for key,values in [('xyz',row['instanceXyz']),('hpr',row['instanceHpr']),('scale',row['instanceScaleGame'])]:obj.set(key,' '.join(f'{v:.9f}'for v in values))
        for child in list(obj):obj.remove(child)
        changes.append({'id':obj.get('id'),'model':obj.get('model'),'originalXml':old,'candidateXml':E.tostring(obj,encoding='unicode'),'scope':'Decorative ghost atmosphere only; obsolete cards and their motion consolidated into three static volumetric plumes.'})
scene.write(c/'scene.xml',encoding='unicode');(w/'smoke-changes.json').write_text(json.dumps(proof,indent=2));(w/'layout-changes.json').write_text(json.dumps({'modified':changes,'consolidatedSpriteInstances':removed,'removedCount':len(removed)},indent=2));print('V7B_SPHERICAL_WORLD_SMOKE_READY',len(proof),len(removed),flush=True)
