from pathlib import Path
import bpy,hashlib,json
r=Path(__file__).resolve().parent;root=r.parents[2];file=root/'output/fluxara-summit-run-final/Summit Run.blend';texture=Path('/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK/textures/summit-run-reference-v1/wooden.png');bpy.ops.wm.open_mainfile(filepath=str(file));bpy.context.preferences.filepaths.save_version=0;updated=[]
for image in bpy.data.images:
 if Path(bpy.path.abspath(image.filepath)).name=='wooden.png':
  if image.packed_file:image.unpack(method='REMOVE')
  image.filepath=str(texture);image.reload();image.pack();updated.append({'name':image.name,'size':list(image.size),'source':str(texture)})
assert updated,'No native timber image found'
t=bpy.data.texts.get('TextureWeightFix.json')or bpy.data.texts.new('TextureWeightFix.json');t.clear();t.write((r/'integration.json').read_text());bpy.ops.wm.save_as_mainfile(filepath=str(file));q=json.loads((r/'integration.json').read_text());q['nativeUpdatedImages']=updated;q['finalNative']={'path':str(file),'bytes':file.stat().st_size,'sha256':hashlib.sha256(file.read_bytes()).hexdigest()};(r/'integration.json').write_text(json.dumps(q,indent=2)+'\n');p=root/'fluxara-summit-run.asset-ledger.json';j=json.loads(p.read_text());j['textureWeightFix']=q;p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n');print('SUMMIT_NATIVE_256_TIMBER_SAVED',updated,flush=True)
