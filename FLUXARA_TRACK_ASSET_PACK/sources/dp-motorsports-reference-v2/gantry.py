from pathlib import Path
r=Path(__file__).resolve().parent
base=(r/'dp_palette.svg').read_text().replace('width="256" height="256"','width="512" height="256"',1).replace('</svg>','')
b='<rect x="256" width="256" height="256" fill="#93cbe5"/><path d="M256 15H512M256 240H512" stroke="#264e67" stroke-width="15"/>'
for i,c in enumerate(['#f46b54','#f6c946','#3386cf','#fff0dc','#f46b54','#f6c946']):
 x=259+i*42;b+=f'<path d="M{x} 38L{x+39} 38L{x+19} 204Z" fill="{c}"/>'
(r/'dp_gantry.png.svg').write_text(base+b+'</svg>')
