"""Render native Blender evidence. The opened .blend is never saved.

Arguments after --: ``animacion`` renders 90 preview frames; ``cpu`` uses
Cycles on the CPU instead of the scene's saved Eevee engine; ``validar``
checks every PNG after saving it and fails if it is black or almost uniform.
These overrides exist only in this background process and are never saved.
"""
import bpy
import sys
import os
import time
from array import array
from pathlib import Path

BASE=Path(__file__).resolve().parents[1]
OUT=BASE/'previews'/'Retro'
OUT.mkdir(exist_ok=True,parents=True)
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
cpu='cpu' in args
validate_png='validar' in args


def configure(scene):
    if cpu:
        scene.render.engine='CYCLES'
        scene.cycles.device='CPU'
        scene.cycles.samples=16
        scene.cycles.use_adaptive_sampling=True
        scene.cycles.adaptive_threshold=.12
        scene.cycles.use_denoising=True
        scene.cycles.denoiser='OPENIMAGEDENOISE'
        if hasattr(scene.cycles,'denoising_use_gpu'):
            scene.cycles.denoising_use_gpu=False
        scene.cycles.max_bounces=2
        scene.cycles.diffuse_bounces=1
        scene.cycles.glossy_bounces=1
        scene.cycles.transmission_bounces=0
        scene.cycles.transparent_max_bounces=1
        scene.render.threads_mode='FIXED'
        scene.render.threads=min(8,os.cpu_count() or 1)
    scene.render.image_settings.file_format='PNG'
    scene.render.image_settings.color_mode='RGB'
    scene.render.resolution_percentage=100


def check_png(path):
    """Check the saved file itself, independently of Render Result caching."""
    if not path.is_file() or path.stat().st_size<1024:
        raise RuntimeError('PNG missing or unexpectedly small: '+str(path))
    image=bpy.data.images.load(str(path),check_existing=False)
    try:
        pixels=array('f',[0.0])*len(image.pixels)
        image.pixels.foreach_get(pixels)
        channels=image.channels
        if channels<3 or not pixels:
            raise RuntimeError('PNG has no RGB pixels: '+str(path))
        pixel_count=len(pixels)//channels
        stride=max(1,pixel_count//60000)*channels
        low=1.0;high=0.0;total=0.0;count=0;bright=0
        for index in range(0,len(pixels)-channels+1,stride):
            value=.2126*pixels[index]+.7152*pixels[index+1]+.0722*pixels[index+2]
            low=min(low,value);high=max(high,value)
            total+=value;count+=1
            if value>.10:bright+=1
        if count==0 or high<.10 or high-low<.08 or bright/count<.005:
            raise RuntimeError('Black/almost uniform PNG: '+str(path))
        print('RETRO_PNG_PASS',path.name,'mean',round(total/count,4),
              'range',round(low,4),round(high,4),'bright_fraction',round(bright/count,4),flush=True)
    finally:
        bpy.data.images.remove(image)


def render(scene,path):
    start=time.monotonic()
    scene.render.filepath=str(path)
    bpy.ops.render.render(write_still=True,scene=scene.name)
    if validate_png:check_png(path)
    print('RETRO_RENDER_SECONDS',path.name,round(time.monotonic()-start,2),flush=True)


print('RETRO_RENDER_MODE','CYCLES_CPU_16' if cpu else 'SAVED_ENGINE',
      'validate_png',validate_png,flush=True)
if 'animacion' in args:
    scene=bpy.data.scenes['08_DEMO_COMPLETA']
    bpy.context.window.scene=scene
    scene.render.resolution_x=640;scene.render.resolution_y=360
    scene.eevee.taa_render_samples=12
    configure(scene)
    folder=OUT/'frames';folder.mkdir(exist_ok=True)
    # 5fps preview of an 18 second native 30fps animation.
    for frame in range(1,541,6):
        scene.frame_set(frame)
        render(scene,folder/f'{frame:04}.png')
        print('RETRO_ANIMATION_FRAME',frame,flush=True)
else:
    for name in ['01_INICIO','02_ELEGIR_NAVE','03_PARTIDA','04_PAUSA','05_JEFE','06_VICTORIA','07_DERROTA']:
        scene=bpy.data.scenes[name];bpy.context.window.scene=scene
        configure(scene)
        scene.frame_set(1)
        render(scene,OUT/(name+'.png'))
        print('RETRO_PREVIEW',name,flush=True)
    scene=bpy.data.scenes['03_PARTIDA']
    scene.render.resolution_x=1024;scene.render.resolution_y=768
    bpy.context.window.scene=scene
    render(scene,OUT/'03_PARTIDA_1024x768.png')
