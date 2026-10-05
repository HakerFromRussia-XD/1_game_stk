from pathlib import Path
from PIL import Image
import shutil
r=Path(__file__).resolve().parent;src=Path('/Users/motoricallc/.codex/generated_images/01a0ed9b-a75e-74c3-a40c-1713421a0a70/exec-b5bc21f4-f08c-40af-8457-df89750d763a.png');shutil.copy2(src,r/'references/grass-generated.png');im=Image.open(src).convert('RGB').resize((256,256),Image.Resampling.LANCZOS)
for p in (r/'candidate').glob('*.jpg'):
 if 'grass' in p.name.lower() or p.name=='kusaiwa.jpg':im.save(p,quality=90,optimize=True)
repeat=Image.new('RGB',(768,768))
for x in range(3):
 for y in range(3):repeat.paste(im,(x*256,y*256))
repeat.save(r/'grass-repeat.jpg')
