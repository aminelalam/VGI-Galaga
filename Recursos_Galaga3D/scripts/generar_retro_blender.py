"""Build two editable retro 3D Blender versions from the project's HUD resources.

Run with Blender --background --factory-startup --python-exit-code 1 --python this_file.
The original Galaga3D_Interfaz.blend is read only and never overwritten.
"""
import bpy
import sys
import math
import json
import hashlib
from pathlib import Path
from mathutils import Vector

SCRIPTS=Path(__file__).resolve().parent
BASE=SCRIPTS.parent
OUT=BASE/'blender'/'Retro'
PRE=BASE/'previews'/'Retro'
SOURCE=BASE/'blender'/'Galaga3D_Interfaz.blend'
OUT.mkdir(exist_ok=True,parents=True);PRE.mkdir(exist_ok=True,parents=True)
sys.path.insert(0,str(SCRIPTS))
from retro_base import palette,box,pixel_text,border,button,plane_badge,make_scene,loop_keyframes
from retro_modelos import build_ship,build_enemy,build_boss

source_hash=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.preferences.filepaths.save_version=0
materials=palette()
scenes={}
collections={}
animated_objects=[]

def scene(name):
    sc,col=make_scene(name,materials)
    sc['source_blend']='Galaga3D_Interfaz.blend'
    sc['estilo']='Arcade retro, mallas sencillas y letras de 5 por 7 bloques'
    scenes[name]=sc;collections[name]=col
    return sc,col

def text(col,name,body,x,y,height=.35,color='white',align='CENTER',z=8.5,action=None):
    return pixel_text(col,name,body,x,y,height,materials[color],align,z,action)

def control_button(col,name,label,x,y,width,action,height=.78):
    return button(col,name,label,x,y,width,action,materials,height)

def animate(ob,path,values,linear=False):
    loop_keyframes(ob,path,values,linear=linear)
    animated_objects.append(ob.name)

# Preserve and visibly reuse actual meshes from the original editable .blend.
with bpy.data.libraries.load(str(SOURCE),link=False) as (source,dest):
    dest.objects=[name for name in source.objects if name.startswith('Vida_icono_1')]
original_icons=[ob for ob in dest.objects if ob and ob.type=='MESH']
vertices=[ob.matrix_world @ v.co for ob in original_icons for v in ob.data.vertices]
lo=Vector(tuple(min(p[k] for p in vertices) for k in range(3)))
hi=Vector(tuple(max(p[k] for p in vertices) for k in range(3)))
icon_center=(lo+hi)/2
icon_factor=.43/max(hi.x-lo.x,hi.y-lo.y)

def life_icon(col,name,x,y):
    for i,master in enumerate(original_icons):
        ob=master.copy();ob.data=master.data.copy();ob.name=name+f'_{i:02}'
        col.objects.link(ob)
        world=master.matrix_world.copy()
        for v in ob.data.vertices:
            local=(world @ v.co-icon_center)*icon_factor
            v.co=(local.x,local.y,local.z)
        ob.location=(x,y,8.5);ob.rotation_euler=(0,0,0);ob.scale=(1,1,1)
        ob.data.materials.clear();ob.data.materials.append(materials['white' if 'relleno_02' in master.name else 'blue'])
        ob['reused_from_blend']=SOURCE.name
        solid=ob.modifiers.new('Grosor_icono_original','SOLIDIFY');solid.thickness=.025

def hud(col,boss=False,points='012500',lives=3,plane='A',charge_level=1.0):
    box(col,'HUD_Franja_superior',(0,5.26,8),(21.0,1.25,.15),materials['panel'])
    text(col,'HUD_Puntos_label','PUNTOS',-10.0,5.56,.26,'yellow','LEFT')
    text(col,'HUD_Puntos',points,-10.0,5.04,.43,'white','LEFT')
    text(col,'HUD_Record_label','RECORD',-5.9,5.56,.26,'muted','LEFT')
    text(col,'HUD_Record','038000',-5.9,5.04,.43,'white','LEFT')
    text(col,'HUD_Oleada','OLEADA 3/3',.8,5.26,.37)
    control_button(col,'Boton_pausa','PAUSA',8.4,5.25,3.15,'pause',.68)
    box(col,'HUD_Franja_inferior',(0,-5.15,8),(21.0,1.38,.15),materials['panel'])
    text(col,'HUD_Vidas','VIDAS',-10.0,-4.83,.27,'yellow','LEFT')
    for i in range(lives):life_icon(col,f'Vida_reutilizada_{i}',-9.65+i*.65,-5.38)
    text(col,'HUD_Controles','A/D MOVER  ESPACIO DISPARAR',-.5,-4.96,.26)
    text(col,'HUD_Ayuda','E PLANO    P PAUSA',-.5,-5.48,.26,'muted')
    plane_badge(col,'HUD_Plano',5.05,-5.15,plane,materials,scale=.32,z=8.3)
    text(col,'HUD_Plano_texto','PLANO '+plane,5.62,-4.96,.30,'blue' if plane=='A' else 'yellow','LEFT')
    text(col,'HUD_Distancia','CERCA' if plane=='A' else 'LEJOS',5.62,-5.47,.25,'white','LEFT')
    text(col,'HUD_Recarga_label','LISTO' if charge_level==1 else 'RECARGA',9.0,-4.88,.25,'white' if charge_level==1 else 'yellow')
    box(col,'HUD_Recarga_fondo',(9.0,-5.40,8.12),(1.70,.16,.07),materials['metal'])
    charge=box(col,'HUD_Recarga',(9.0,-5.40,8.20),(1.65,.13,.07),materials['green'])
    charge['indicador']='recarga_plano'
    charge['nivel_inicial']=charge_level
    charge.scale.x=charge_level
    charge.location.x=8.175+.825*charge_level
    if charge_level<1:
        animate(charge,'scale',[(1,(charge_level,1,1)),(160,(.98,1,1)),(240,(charge_level,1,1))],True)
        animate(charge,'location',[(1,(8.175+.825*charge_level,-5.40,8.20)),(160,(8.175+.825*.98,-5.40,8.20)),(240,(8.175+.825*charge_level,-5.40,8.20))],True)
    if boss:
        text(col,'HUD_Jefe','JEFE FINAL  18/24',0,4.29,.30,'red')
        box(col,'HUD_Jefe_fondo',(0,3.82,8.05),(8.0,.30,.08),materials['metal'])
        fill=box(col,'HUD_Jefe_relleno',(-1.0,3.82,8.13),(6.0,.26,.08),materials['red'])
        fill['hp_ejemplo']=18
    return col

def player_variants(col,y=-3.55):
    roots=[]
    for variant in range(3):
        root=build_ship(col,'Jugador_'+str(variant),variant,materials,(0,y,1.0),.82)
        root['retro_player_variant']=variant
        for child in [root,*root.children_recursive]:
            child.hide_render=variant!=0;child.hide_viewport=variant!=0
        animate(root,'location',[(1,(-2.6,y,1)),(60,(2.6,y,1)),(120,(0,y,1)),(180,(-2.0,y,1)),(240,(-2.6,y,1))])
        roots.append(root)
    return roots

def playfield(col,show_boss=False):
    for x in [-8.6,8.6]:box(col,'Limite_campo',(x,-.2,-1.5),(.025,7.5,.035),materials['metal'])
    if not show_boss:
        for row in range(2):
            for column in range(6):
                x=(column-2.5)*2.1;y=2.8-row*1.45
                root=build_enemy(col,f'Enemigo_{row}_{column}',(row+column)%2,materials,(x,y,-.25-row*.3),.65)
                plane='A' if (row+column)%2==0 else 'B'
                before=set(col.objects)
                plane_badge(col,f'Marca_{row}_{column}',x+.60,y+.40,plane,materials,.15,z=.45)
                for mark in set(col.objects)-before:
                    mark.parent=root;mark.matrix_parent_inverse=root.matrix_basis.inverted()
                if row==1 and column==4:
                    animate(root,'location',[(1,(x,y,-.55)),(70,(x,y,-.55)),(115,(5.8,-2.1,.4)),(160,(2,-2.8,.4)),(205,(-3,2,-.55)),(240,(x,y,-.55))])
                else:
                    animate(root,'location',[(1,(x,y,root.location.z)),(80,(x+.38,y,root.location.z)),(160,(x-.38,y,root.location.z)),(240,(x,y,root.location.z))])
    else:
        boss=build_boss(col,'Jefe_final',materials,(0,2.0,-.2),1.1)
        animate(boss,'location',[(1,(-2,2,-.2)),(120,(2,2,-.2)),(240,(-2,2,-.2))])
        plane_badge(col,'Aviso_B',0,1.05,'B',materials,.28,z=1.1)
        warning=text(col,'Aviso_ataque','ATAQUE PLANO B',0,.25,.30,'yellow',z=8.4)
        animate(warning,'scale',[(1,(1,1,1)),(30,(1.06,1.06,1)),(60,(1,1,1))])
    for i,x in enumerate([-2.4,.1,3.1]):
        bullet=box(col,f'Disparo_jugador_{i}',(x,-1+i*.9,.7),(.10,.40,.10),materials['yellow'])
        start=1+i*17
        animate(bullet,'location',[(start,(x,-3.2,.7)),(start+57,(x,3.4,.7)),(start+58,(x,-3.2,.7))],True)
    for i,x in enumerate([-4.5,1.8]):
        bullet=box(col,f'Disparo_enemigo_{i}',(x,1-i*.8,-.1),(.13,.30,.10),materials['red'])
        start=1+i*25
        animate(bullet,'location',[(start,(x,2.8,-.1)),(start+90,(x,-3.5,-.1)),(start+91,(x,2.8,-.1))],True)
    player_variants(col)

sc,col=scene('01_INICIO')
text(col,'Titulo_Galaga','GALAGA',0,3.85,1.52,'yellow')
text(col,'Titulo_3D','3D',0,2.30,.60,'blue')
intro_ship=build_ship(col,'Nave_portada',0,materials,(0,.45,2),1.35)
animate(intro_ship,'rotation_euler',[(1,(.25,.12,-.15)),(120,(.25,.12,.15)),(240,(.25,.12,-.15))])
control_button(col,'Iniciar','INICIAR PARTIDA',0,-1.72,7.6,'start')
control_button(col,'Elegir','ELEGIR NAVE',0,-2.86,7.6,'start')
control_button(col,'Demo','VER DEMO',7.65,5.18,4.1,'demo',.7)
text(col,'Inicio_controles','A/D MOVER  ESPACIO DISPARAR',0,-4.4,.29,'muted')
text(col,'Inicio_controles2','E PLANO  P PAUSA',0,-5.10,.29,'muted')

sc,col=scene('02_ELEGIR_NAVE')
text(col,'Seleccion_titulo','ELEGIR NAVE',0,4.72,.90,'yellow')
for variant,label in enumerate(['FLECHA','DELTA','DOBLE MOTOR']):
    x=(variant-1)*6.7
    box(col,'Tarjeta_'+label,(x,.6,-1.0),(5.6,5.4,.3),materials['panel'])
    border(col,'Marco_tarjeta_'+label,x,.6,5.6,5.4,materials['metal'],z=.5)
    root=bpy.data.objects.new('Seleccion_marco_'+str(variant),None);col.objects.link(root)
    root['retro_selection_frame']=variant
    selected=border(col,'Seleccion_'+label,x,.6,5.73,5.53,materials['yellow'],z=.7,thickness=.085,parent=root)
    for ob in [root,*root.children_recursive]:ob.hide_render=variant!=0;ob.hide_viewport=variant!=0
    ship=build_ship(col,'Vista_'+label,variant,materials,(x,1.15,1.9),1.40)
    animate(ship,'rotation_euler',[(1,(.35,.16,-.15)),(120,(.35,.16,.35)),(240,(.35,.16,-.15))])
    box(col,'Peana_'+label,(x,-.90,.0),(3.5,.35,.5),materials['metal'])
    control_button(col,'Elegir_'+label,str(variant+1)+' '+label,x,-1.62,5.15,'select_'+str(variant))
text(col,'Seleccion_cosmetica','MISMAS REGLAS / TRES MODELOS',0,-2.90,.30,'muted')
control_button(col,'Confirmar','CONFIRMAR',3.3,-4.18,5.8,'confirm')
control_button(col,'Volver','VOLVER',-3.3,-4.18,5.8,'back')
text(col,'Seleccion_atajos','1 2 3 ELEGIR  /  ENTER CONFIRMAR',0,-5.42,.27,'muted')

sc,col=scene('03_PARTIDA');hud(col);playfield(col)
control_button(col,'Ver_jefe','JEFE',8.8,4.1,2.7,'boss',.55)

sc,col=scene('04_PAUSA');hud(col);playfield(col)
box(col,'Pausa_fondo',(0,.15,7.80),(9.2,5.5,.12),materials['dark'])
border(col,'Pausa_marco',0,.15,9.2,5.5,materials['metal'],z=8.3)
text(col,'Pausa_titulo','PAUSA',0,1.90,.88,'yellow',z=8.55)
control_button(col,'Continuar','CONTINUAR',0,.35,6.8,'resume')
control_button(col,'Pausa_menu','MENU',0,-1.13,6.8,'back')
sc.frame_set(1)
for ob in sc.objects:
    ob.animation_data_clear()

sc,col=scene('05_JEFE');hud(col,boss=True,plane='B',charge_level=.40);playfield(col,True)
control_button(col,'Victoria','VICTORIA',-7.6,4.0,4.1,'victory',.6)
control_button(col,'Derrota','DERROTA',7.6,4.0,4.1,'defeat',.6)

for name,title,color,score in [('06_VICTORIA','VICTORIA','green','038000'),('07_DERROTA','FIN DE PARTIDA','red','012500')]:
    sc,col=scene(name)
    text(col,name+'_Titulo',title,0,3.80,.95,color)
    text(col,name+'_Puntos','PUNTOS '+score,0,2.30,.47)
    text(col,name+'_Mensaje','LAS TRES OLEADAS SUPERADAS' if 'VICTORIA' in name else 'NO QUEDAN VIDAS',0,1.22,.30,'muted')
    for variant in range(3):
        display=build_ship(col,name+'_Nave_'+str(variant),variant,materials,(0,-.10,2),1.10)
        display['retro_player_variant']=variant
        for child in [display,*display.children_recursive]:
            child.hide_render=variant!=0;child.hide_viewport=variant!=0
        if 'VICTORIA' in name:animate(display,'rotation_euler',[(1,(.25,.15,-.20)),(120,(.25,.15,.20)),(240,(.25,.15,-.20))])
    control_button(col,name+'_Reintentar','NUEVA PARTIDA' if 'VICTORIA' in name else 'REINTENTAR',0,-2.0,7.2,'start')
    control_button(col,name+'_Menu','MENU',0,-3.25,7.2,'back')

# A normal Blender camera animation makes the complete menu-to-result demo
# playable with the timeline, without installing or enabling any Python scripts.
demo=bpy.data.scenes.new('08_DEMO_COMPLETA');demo['nave_elegida']=0
demo.render.engine='BLENDER_EEVEE';demo.eevee.taa_render_samples=24
demo.render.resolution_x=1280;demo.render.resolution_y=720;demo.render.resolution_percentage=100
demo.render.image_settings.file_format='PNG';demo.render.image_settings.color_mode='RGB';demo.render.fps=30
demo.view_settings.view_transform='Standard';demo.view_settings.look='None';demo.frame_end=540
demo.world=scenes['01_INICIO'].world
camdata=bpy.data.cameras.new('Camara_demo');cam=bpy.data.objects.new('Camara_demo',camdata)
demo.collection.objects.link(cam);camdata.type='ORTHO';camdata.ortho_scale=22;demo.camera=cam
stages=[('01_INICIO',1),('02_ELEGIR_NAVE',91),('03_PARTIDA',181),('05_JEFE',361),('06_VICTORIA',481)]
for i,(name,frame) in enumerate(stages):
    inst=bpy.data.objects.new('Escenario_demo_'+name,None);demo.collection.objects.link(inst)
    inst.instance_type='COLLECTION';inst.instance_collection=collections[name];inst.location.x=40*i
    cam.location=(40*i,0,32);cam.keyframe_insert(data_path='location',frame=frame)
    marker=demo.timeline_markers.new(name,frame=frame)
for layer in cam.animation_data.action.layers:
    for strip in layer.strips:
        for bag in strip.channelbags:
            for curve in bag.fcurves:
                for point in curve.keyframe_points:point.interpolation='CONSTANT'

for sc in scenes.values():
    sc.timeline_markers.new('INICIO DEL BUCLE',frame=1)
    sc.timeline_markers.new('MITAD',frame=120)
    sc.timeline_markers.new('FIN DEL BUCLE',frame=240)
    sc.frame_set(1)
demo.frame_set(1)

interactive_source=(SCRIPTS/'interfaz_retro_interactiva.py').read_text(encoding='utf-8-sig')
embedded=bpy.data.texts.new('INICIAR_INTERFAZ.py');embedded.write(interactive_source)
readme=bpy.data.texts.new('LEEME_RETRO.txt')
readme.write('GALAGA 3D RETRO\n\nVersion animada. Escenas 01 inicio, 02 elegir nave, 03 partida, 04 pausa, 05 jefe, 06 victoria, 07 derrota.\n08_DEMO_COMPLETA: presentacion de 18 segundos; reproducir con Espacio sobre la vista 3D.\n\nPara botones reales dentro de Blender: abrir INICIAR_INTERFAZ.py en el editor de texto y Alt+P.\nTambien se puede ejecutar Abrir_animada.ps1. No se ejecutan scripts automaticamente al abrir el archivo.\nClic en botones, 1/2/3 elige nave, Enter avanza, P pausa. Esc desactiva los clics.\nLa barra lateral N > Galaga ofrece los mismos controles.\n\nNaves, enemigos, jefe, fondo, interfaz y letras son geometria 3D editable.\nLos iconos de vida vienen del Galaga3D_Interfaz.blend original, conservado sin sobrescribir.\nLa animacion ilustra la interfaz y las acciones del juego; no incluye simulacion de colisiones ni musica.\n')

for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            space=area.spaces.active
            space.region_3d.view_perspective='CAMERA';space.region_3d.view_camera_zoom=18
            space.overlay.show_overlays=False;space.shading.type='MATERIAL'
            space.shading.use_scene_world=True;space.shading.use_scene_lights=True
            space.show_region_ui=False
        elif area.type=='PROPERTIES':area.spaces.active.context='SCENE'
bpy.context.window.scene=scenes['01_INICIO']
for sc in list(scenes.values())+[demo]:sc.render.filepath='//../../previews/Retro/'+sc.name
if 'Scene' in bpy.data.scenes:
    bpy.data.scenes.remove(bpy.data.scenes['Scene'])
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Galaga3D_Retro_Animada.blend'))

# Freeze a separate copy: no actions, drivers, animated camera or runtime code.
bpy.data.scenes.remove(demo)
for datablocks in [bpy.data.objects,bpy.data.scenes,bpy.data.materials,bpy.data.lights,bpy.data.cameras,bpy.data.meshes]:
    for block in datablocks:
        if hasattr(block,'animation_data_clear'):block.animation_data_clear()
        if getattr(block,'node_tree',None):block.node_tree.animation_data_clear()
for action in list(bpy.data.actions):bpy.data.actions.remove(action)
for sc in scenes.values():sc.frame_set(1);sc.frame_end=1
bpy.data.texts.remove(embedded)
readme.clear();readme.write('GALAGA 3D RETRO / VERSION ESTATICA\n\nNo hay animaciones, drivers ni scripts de interaccion.\nElegir escena en el selector superior: inicio, naves, partida, pausa, jefe, victoria y derrota.\nNumpad 0 muestra la camara; F12 renderiza la escena.\nTodo es editable: seleccionar objetos y mover/escalar, materiales simples, mallas de pocos poligonos.\nLos iconos de vida proceden del archivo Blender original.\n')
bpy.context.window.scene=scenes['03_PARTIDA']
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Galaga3D_Retro_Estatica.blend'))
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==source_hash
report={'source':SOURCE.name,'original_preserved_sha256':source_hash,
        'static':'Galaga3D_Retro_Estatica.blend','animated':'Galaga3D_Retro_Animada.blend',
        'scenes_static':list(scenes),'scene_animated_extra':'08_DEMO_COMPLETA',
        'three_ship_variants':['FLECHA','DELTA','DOBLE MOTOR'],'source_icon_meshes':len(original_icons),
        'animation_objects':len(set(animated_objects)), 'render_size':[1280,720]}
(PRE/'construccion.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('RETRO_BUILT',json.dumps(report,ensure_ascii=False))
