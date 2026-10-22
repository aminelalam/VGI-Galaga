"""Package Blender's rendered frames as a compact animation and contact sheet."""
from pathlib import Path
from PIL import Image, ImageDraw
import json

OUT=Path(__file__).resolve().parents[1]/'previews'/'Retro'
files=sorted((OUT/'frames').glob('*.png'))
assert len(files)==90, f'Expected 90 Blender frames, found {len(files)}'
frames=[Image.open(path).convert('RGB') for path in files]
assert all(im.size==(640,360) for im in frames)
sample=Image.new('RGB',(640,360*5))
for i,index in enumerate([0,15,30,60,80]):sample.paste(frames[index],(0,360*i))
palette=sample.quantize(colors=256)
gif=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in frames]
gif[0].save(OUT/'Galaga_Retro_Demo.gif',save_all=True,append_images=gif[1:],
            duration=200,loop=0,optimize=False,disposal=2)
names=['01_INICIO','02_ELEGIR_NAVE','03_PARTIDA','04_PAUSA','05_JEFE','06_VICTORIA','07_DERROTA']
sheet=Image.new('RGB',(1200,765),'#151820')
for index,name in enumerate(names):
    with Image.open(OUT/(name+'.png')) as source:im=source.convert('RGB').resize((400,225))
    x,y=(index%3)*400,(index//3)*255
    sheet.paste(im,(x,y+30));ImageDraw.Draw(sheet).text((x+10,y+9),name[3:].replace('_',' '),fill='white')
sheet.save(OUT/'Todas_las_pantallas.png')
with Image.open(OUT/'Galaga_Retro_Demo.gif') as check:
    assert check.n_frames==90 and check.size==(640,360)
    durations=[]
    for index in range(check.n_frames):check.seek(index);durations.append(check.info.get('duration'))
    assert sum(durations)==18000
(OUT/'validacion_preview.json').write_text(json.dumps({'status':'PASS','frames':90,'fps':5,
    'duration_seconds':18,'size':[640,360],'source':'Render nativo Blender de 08_DEMO_COMPLETA',
    'original_blend_fps':30,'original_blend_frame_range':[1,540]},indent=2)+'\n',encoding='utf-8')
print('PREVIEW_PASS: 90 frames, 18 seconds, 640x360 GIF.')
