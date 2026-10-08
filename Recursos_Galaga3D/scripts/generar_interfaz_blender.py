"""Construye solo la interfaz Galaga 3D, con graficos vectoriales editables.
Ejecutar: blender --background --factory-startup --python este_archivo.py
"""
import bpy
import math
import json
import random
import xml.etree.ElementTree as ET
from pathlib import Path
from mathutils import Vector
from mathutils.geometry import tessellate_polygon

BASE=Path(__file__).resolve().parents[1]
HUD=BASE/'hud'
OUT=BASE/'blender'
PRE=BASE/'previews'
OUT.mkdir(exist_ok=True);PRE.mkdir(exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.preferences.filepaths.save_version=0
main=bpy.context.scene
main.name='01_HUD_TRANSPARENTE'
main.world=bpy.data.worlds.new('Fondo_espacio')
main.world.color=(.004,.007,.013)

def lin(x): return x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4
def px(x,y): return ((x-640)/100,(360-y)/100)
palette={'hielo':'#d8edf3','cian':'#36e6ed','ambar':'#ffba52','rojo':'#fa5269','morado':'#9478ff','navy':'#101a2c','muted':'#8096ac','panel':'#111e32'}
materials={}
def material(color,alpha=1):
    color=palette.get(color,color)
    key=color+'_%04d'%round(alpha*1000)
    if key in materials: return materials[key]
    rgb=tuple(int(color[i:i+2],16)/255 for i in (1,3,5))
    m=bpy.data.materials.new(key);m.use_nodes=True;m.diffuse_color=(*rgb,alpha)
    nd=m.node_tree.nodes;nd.clear()
    output=nd.new('ShaderNodeOutputMaterial')
    em=nd.new('ShaderNodeEmission');em.inputs['Color'].default_value=(*map(lin,rgb),1);em.inputs['Strength'].default_value=1
    if alpha<1:
        transparent=nd.new('ShaderNodeBsdfTransparent')
        mix=nd.new('ShaderNodeMixShader');mix.inputs[0].default_value=alpha
        m.node_tree.links.new(transparent.outputs[0],mix.inputs[1]);m.node_tree.links.new(em.outputs[0],mix.inputs[2]);m.node_tree.links.new(mix.outputs[0],output.inputs['Surface'])
        m.surface_render_method='BLENDED'
    else: m.node_tree.links.new(em.outputs[0],output.inputs['Surface'])
    materials[key]=m
    return m

def collection(name,scene=main):
    c=bpy.data.collections.new(name);scene.collection.children.link(c);return c

col_points=collection('01_PUNTOS_Y_OLEADA')
col_boss=collection('02_VIDA_JEFE')
col_lives=collection('03_VIDAS_JUGADOR')
col_plane=collection('04_PLANO_Y_RECARGA')
col_pause=collection('05_PAUSA_Y_CONTROLES')
col_decor=collection('06_PANELES_HUD')
col_extra=collection('07_INDICADORES_ESTADO')
col_control=collection('00_CONTROL_HUD')
root=bpy.data.objects.new('CONTROL_HUD',None);col_control.objects.link(root)
root.empty_display_size=.05
props={'puntos':12500,'record':34800,'oleada':3,'vidas':3,'vida_jefe':24,'mostrar_jefe':True,'plano_B':False,'recarga_plano':0.0,'invulnerable':False,'doble_disparo':False}
for k,v in props.items(): root[k]=v
for k,mx in [('puntos',999999),('record',999999),('oleada',3),('vidas',3),('vida_jefe',24)]: root.id_properties_ui(k).update(min=0,max=mx)
root.id_properties_ui('recarga_plano').update(min=0,max=1.2)
root['instrucciones']='Editar propiedades y ejecutar texto ACTUALIZAR_HUD.py. Textos y geometria tambien editables directamente.'

def polygon(name,points,col,color,z=.1,alpha=1,parent=None):
    points=[tuple(p) for p in points]
    if len(points)<3: return None
    vv=[Vector((*p,0)) for p in points]
    tris=tessellate_polygon([vv])
    ids={tuple(v):i for i,v in enumerate(vv)}
    faces=[tuple(int(v) if isinstance(v,int) else ids[tuple(v)] for v in t) for t in tris]
    mesh=bpy.data.meshes.new(name);mesh.from_pydata([(x,y,0) for x,y in points],[],faces);mesh.update()
    ob=bpy.data.objects.new(name,mesh);col.objects.link(ob);mesh.materials.append(material(color,alpha));ob.parent=parent;ob.location.z=z
    return ob

def poly_px(name,points,col,color,z=.1,alpha=1): return polygon(name,[px(x,y) for x,y in points],col,color,z,alpha)

def stroke(name,points,col,color,width=1,z=.1,alpha=1,closed=False):
    objects=[]
    if closed: points=points+[points[0]]
    for i,(a,b) in enumerate(zip(points[:-1],points[1:])):
        dx=b[0]-a[0];dy=b[1]-a[1];length=math.hypot(dx,dy)
        if length<1e-7: continue
        ox=-dy/length*width/2;oy=dx/length*width/2
        objs=poly_px(name+'_%02d'%i,[(a[0]+ox,a[1]+oy),(b[0]+ox,b[1]+oy),(b[0]-ox,b[1]-oy),(a[0]-ox,a[1]-oy)],col,color,z,alpha)
        if objs: objects.append(objs)
    return objects

def sprite(sprite_id,name,x,y,col,size=None,z=.15):
    svg=ET.parse(HUD/(sprite_id+'.svg')).getroot()
    w=float(svg.attrib['width']);s=1 if size is None else size/w
    made=[]
    for i,e in enumerate(svg):
        tag=e.tag.rsplit('}',1)[-1]
        if tag in ('polygon','polyline'):
            pts=[tuple(map(float,p.split(','))) for p in e.attrib['points'].split()]
        elif tag=='ellipse':
            cx,cy,rx,ry=[float(e.attrib[k]) for k in ('cx','cy','rx','ry')]
            pts=[(cx+rx*math.cos(j*math.tau/64),cy+ry*math.sin(j*math.tau/64)) for j in range(64)]
        elif tag=='rect':
            rx,ry,rw,rh=[float(e.attrib[k]) for k in ('x','y','width','height')]
            pts=[(rx,ry),(rx+rw,ry),(rx+rw,ry+rh),(rx,ry+rh)]
        elif tag=='title': continue
        else: raise ValueError(f'Primitiva SVG no soportada: {sprite_id}: {tag}')
        pts=[(x+p[0]*s,y+p[1]*s) for p in pts]
        closed=tag!='polyline'
        fill=e.attrib.get('fill','none');alpha=float(e.attrib.get('opacity',1));layer=z+i*.0002
        if fill!='none':
            ob=poly_px(name+'_relleno_%02d'%i,pts,col,fill,layer,alpha)
            if ob: made.append(ob)
        if e.attrib.get('stroke','none')!='none':
            made+=stroke(name+'_trazo_%02d'%i,pts,col,e.attrib['stroke'],float(e.attrib.get('stroke-width',1))*s,layer+.0001,alpha,closed)
    for ob in made:
        ob['sprite_fuente']=sprite_id
        ob['grupo_hud']=name
    return made

# Font is packed into the .blend; raster exports remain independent of it.
fontpath=BASE/'fonts'/'Vera.ttf'
boldpath=BASE/'fonts'/'VeraBd.ttf'
regular=bpy.data.fonts.load(str(fontpath))
bold=bpy.data.fonts.load(str(boldpath))
def text(name,body,x,y,size,col,color='hielo',boldface=False,align='LEFT',z=.3):
    cu=bpy.data.curves.new(name,'FONT');cu.body=body;cu.size=size/100*.648;cu.font=bold if boldface else regular;cu.align_x=align
    ob=bpy.data.objects.new(name,cu);col.objects.link(ob);ob.location=(*px(x,y),z);cu.materials.append(material(color));return ob

# Minimal translucent edge panels: the centre stays clear for the game.
poly_px('Panel_superior',[(0,0),(1280,0),(1280,103),(0,103)],col_decor,'navy',.025,.95)
stroke('Linea_superior',[(24,103),(1256,103)],col_decor,'hielo',1,.06,.22)
poly_px('Panel_inferior',[(0,604),(1280,604),(1280,720),(0,720)],col_decor,'navy',.025,.95)
stroke('Linea_inferior',[(24,604),(1256,604)],col_decor,'hielo',1,.06,.3)
stroke('Acento_superior',[(28,27),(54,27)],col_decor,'cian',2,.1)
text('TXT_EtiquetaPuntos','PUNTOS',28,45,12,col_points,'cian',True)
text('TXT_Puntos','012500',28,82,35,col_points,'hielo',True)
text('TXT_EtiquetaRecord','RÉCORD',210,44,11,col_points,'muted')
text('TXT_Record','034800',210,73,20,col_points)
stroke('Separador_1',[(324,32),(324,81)],col_decor,'hielo',1,.08,.17)
text('TXT_EtiquetaOleada','OLEADA',350,44,11,col_points,'muted')
text('TXT_Oleada','03 / 03',350,73,20,col_points,'hielo',True)
text('TXT_Titulo','GALAGA // 3D',640,59,24,col_points,'hielo',True,'CENTER')
text('TXT_Subtitulo','SUPERA LAS TRES OLEADAS',640,81,10,col_points,'muted',False,'CENTER')
text('TXT_TeclaPausa','P  PAUSA',1155,74,11,col_pause,'muted',False,'RIGHT')
sprite('pausa','Boton_pausa',1193,28,col_pause,size=52)

text('TXT_JEFE','JEFE FINAL',322,129,12,col_boss,'rojo',True)
text('TXT_VidaJefe','24 / 24',957,129,12,col_boss,'hielo',False,'RIGHT')
sprite('vida_jefe_fondo','JEFE_Fondo',320,140,col_boss,z=.15)
bossfill=sprite('vida_jefe_relleno','JEFE_Relleno',320,140,col_boss,z=.17)
sprite('vida_jefe_marco','JEFE_Marco',320,140,col_boss,z=.21)

text('TXT_EtiquetaVidas','VIDAS',28,632,12,col_lives,'cian',True)
text('TXT_Vidas','3 / 3',353,632,12,col_lives,'hielo',False,'RIGHT')
sprite('vida_jugador_fondo','VIDAS_Fondo',24,645,col_lives,z=.15)
lifefill=sprite('vida_jugador_relleno','VIDAS_Relleno',24,645,col_lives,z=.17)
sprite('vida_jugador_marco','VIDAS_Marco',24,645,col_lives,z=.21)
for j,x in enumerate((382,420,458)):
    objects=sprite('vida_nave','Vida_icono_%d'%(j+1),x,649,col_lives,size=32,z=.2)
    for ob in objects: ob['indice_vida']=j+1

# Plane and cooldown use color, shape and words simultaneously.
sprite('plano_A','Icono_plano_A',936,626,col_plane,z=.2)
sprite('plano_B','Icono_plano_B',936,626,col_plane,z=.2)
text('TXT_Plano','PLANO A',1016,649,21,col_plane,'cian',True)
text('TXT_Distancia','CERCA',1017,673,12,col_plane,'hielo')
text('TXT_Cambiar','E  CAMBIAR DE PLANO',1017,694,10,col_plane,'muted')
text('TXT_RecargaLabel','CAMBIO DE PLANO',548,632,11,col_plane,'muted')
text('TXT_Recarga','LISTO',822,632,11,col_plane,'cian',True,'RIGHT')
poly_px('Recarga_Fondo',[(548,644),(820,644),(820,650),(548,650)],col_plane,'muted',.14,.2)
cool=poly_px('Recarga_Relleno',[(548,644),(820,644),(820,650),(548,650)],col_plane,'cian',.16)
stroke('Control_Linea',[(548,661),(820,661)],col_pause,'hielo',1,.1,.1)
text('TXT_Controles','A / D   MOVER     ESPACIO   DISPARAR',548,684,12,col_pause,'hielo')
text('TXT_Controles2','E   PLANO              P   PAUSA',548,704,10,col_pause,'muted')
text('TXT_Invulnerable','INVULNERABLE',30,582,12,col_extra,'cian',True)
text('TXT_Doble','DOBLE DISPARO',1250,582,12,col_extra,'morado',True,'RIGHT')

# Keep original meshes for mathematically correct clipping, instead of stretching.
for ob in bossfill+lifefill+[cool]:
    ob['clip_original']=json.dumps({'v':[list(v.co) for v in ob.data.vertices],'f':[list(p.vertices) for p in ob.data.polygons]})

UPDATER=r'''import bpy, json
ctrl=bpy.data.objects['CONTROL_HUD']
def clamp(v,a,b): return max(a,min(b,v))
def hide(ob,value): ob.hide_render=value; ob.hide_viewport=value
def clip(ob,right):
    original=json.loads(ob['clip_original']);vv=[];ff=[]
    for face in original['f']:
        points=[original['v'][i] for i in face];out=[]
        for a,b in zip(points,points[1:]+points[:1]):
            ia=a[0]<=right;ib=b[0]<=right
            if ia: out.append(a)
            if ia!=ib:
                t=(right-a[0])/(b[0]-a[0]);out.append([a[j]+t*(b[j]-a[j]) for j in range(3)])
        # Remove coincident intersections and zero-area faces at HP=0 / boundaries.
        clean=[]
        for p in out:
            if not clean or sum((p[j]-clean[-1][j])**2 for j in range(3))>1e-14: clean.append(p)
        if len(clean)>1 and sum((clean[0][j]-clean[-1][j])**2 for j in range(3))<1e-14: clean.pop()
        out=clean
        area=abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(out,out[1:]+out[:1]))) if len(out)>=3 else 0
        if len(out)>=3 and area>1e-12:
            start=len(vv);vv+=out;ff.append(tuple(range(start,start+len(out))))
    ob.data.clear_geometry();ob.data.from_pydata(vv,[],ff);ob.data.update()
p=int(clamp(ctrl['puntos'],0,999999));r=int(clamp(ctrl['record'],0,999999))
v=int(clamp(ctrl['vidas'],0,3));hp=int(clamp(ctrl['vida_jefe'],0,24));w=int(clamp(ctrl['oleada'],1,3))
bpy.data.objects['TXT_Puntos'].data.body=f'{p:06d}'
bpy.data.objects['TXT_Record'].data.body=f'{r:06d}'
bpy.data.objects['TXT_Oleada'].data.body=f'{w:02d} / 03'
bpy.data.objects['TXT_Vidas'].data.body=f'{v} / 3'
bpy.data.objects['TXT_VidaJefe'].data.body=f'{hp} / 24'
b=bool(ctrl['plano_B'])
bpy.data.objects['TXT_Plano'].data.body='PLANO B' if b else 'PLANO A'
bpy.data.objects['TXT_Plano'].data.materials[0]=bpy.data.materials['#ffba52_1000' if b else '#36e6ed_1000']
bpy.data.objects['TXT_Distancia'].data.body='LEJOS' if b else 'CERCA'
seconds=clamp(float(ctrl['recarga_plano']),0,1.2)
bpy.data.objects['TXT_Recarga'].data.body=f'{seconds:.1f} s' if seconds else 'LISTO'
hide(bpy.data.objects['TXT_Invulnerable'],not ctrl['invulnerable'])
hide(bpy.data.objects['TXT_Doble'],not ctrl['doble_disparo'])
for ob in bpy.data.objects:
    group=ob.get('grupo_hud','')
    if group=='Icono_plano_A': hide(ob,b)
    if group=='Icono_plano_B': hide(ob,not b)
    if 'indice_vida' in ob: hide(ob,v<ob['indice_vida'])
    if ob.name.startswith('JEFE_') or ob.name in ('TXT_JEFE','TXT_VidaJefe'): hide(ob,not ctrl['mostrar_jefe'])
    if 'clip_original' in ob:
        if group=='JEFE_Relleno': right=(320+28+584*hp/24-640)/100
        elif group=='VIDAS_Relleno': right=(24+28+280*v/3-640)/100
        else: right=(548+272*(1-seconds/1.2)-640)/100
        clip(ob,right)
print('HUD actualizado: puntos',p,'vidas',v,'jefe',hp,'plano','B' if b else 'A')
'''
txt=bpy.data.texts.new('ACTUALIZAR_HUD.py');txt.write(UPDATER)
(BASE/'scripts'/'actualizar_hud.py').write_text(UPDATER+'\n',encoding='utf-8')
exec(UPDATER)

def setup(sc):
    sc.render.engine='BLENDER_EEVEE';sc.render.resolution_x=1280;sc.render.resolution_y=720;sc.render.resolution_percentage=100
    sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.film_transparent=True
    sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0;sc.view_settings.gamma=1
    sc.world=main.world
    cam=bpy.data.cameras.new('Camara_HUD_'+sc.name);ob=bpy.data.objects.new(cam.name,cam);sc.collection.objects.link(ob)
    cam.type='ORTHO';cam.ortho_scale=12.8;ob.location=(0,0,10);ob.rotation_euler=(0,0,0);sc.camera=ob
    sc.render.fps=60

setup(main)
preview=bpy.data.scenes.new('02_PREVIEW_INTERFAZ')
setup(preview)
for c in main.collection.children: preview.collection.children.link(c)
back=collection('FONDO_PREVIEW_solo_presentacion',preview)
poly_px('Espacio',[(0,0),(1280,0),(1280,720),(0,720)],back,'navy',-.1)
random.seed(42)
for j in range(90):
    x=random.uniform(25,1255);y=random.uniform(200,592);r=random.choice([.6,.8,1.0]);a=random.uniform(.15,.45)
    poly_px('Estrella_%03d'%j,[(x-r,y-r),(x+r,y-r),(x+r,y+r),(x-r,y+r)],back,'hielo',-.05,a)
# Subtle angular background, placed only in the presentation scene.
stroke('Sector_izq',[(66,535),(182,418),(182,287)],back,'cian',1,-.03,.055)
stroke('Sector_der',[(1214,535),(1098,418),(1098,287)],back,'cian',1,-.03,.055)

pause=bpy.data.scenes.new('03_PANTALLA_PAUSA')
setup(pause)
for c in preview.collection.children: pause.collection.children.link(c)
pa=collection('PAUSA_Overlay',pause)
poly_px('Oscurecer_campo',[(0,191),(1280,191),(1280,602),(0,602)],pa,'navy',.38,.8)
poly_px('PAUSA_Panel',[(454,291),(477,268),(803,268),(826,291),(826,453),(803,476),(477,476),(454,453)],pa,'panel',.4)
stroke('PAUSA_Marco',[(454,326),(454,291),(477,268),(539,268)],pa,'cian',2,.42)
stroke('PAUSA_Marco2',[(741,476),(803,476),(826,453),(826,418)],pa,'cian',2,.42)
text('TXT_PausaTitulo','PAUSA',640,365,46,pa,'hielo',True,'CENTER',.5)
text('TXT_PausaContinuar','P  PARA CONTINUAR',640,408,15,pa,'cian',False,'CENTER',.5)
text('TXT_PausaMensaje','LA PARTIDA SE REANUDARÁ DESDE AQUÍ',640,443,10,pa,'muted',False,'CENTER',.5)

# Manual in the file, accessible from Blender's Text Editor.
manual=bpy.data.texts.new('LEEME_INTERFAZ.txt')
manual.write('GALAGA 3D / INTERFAZ EDITABLE\n\n01_HUD_TRANSPARENTE: HUD aislado, PNG alpha.\n02_PREVIEW_INTERFAZ: fondo de presentacion.\n03_PANTALLA_PAUSA: pausa.\n\nTodas las lineas y formas son mallas vectoriales. Los textos siguen editables.\nCONTROL_HUD contiene puntos, record, vidas (0..3), jefe (0..24), plano B y recarga.\nCambiar propiedades y ejecutar ACTUALIZAR_HUD.py en el editor de textos con Alt+P.\nNo hay scripts automaticos al abrir.\nFuentes empaquetadas. Resolucion 1280x720. Camara ortografica.\n\nEsto es un recurso visual; conectar valores/eventos a C++ sera la integracion posterior.\n')

bpy.context.window.scene=preview
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective='CAMERA'
            area.spaces.active.region_3d.view_camera_zoom=5
            area.spaces.active.shading.type='MATERIAL'
            area.spaces.active.overlay.show_overlays=False
            area.spaces.active.shading.use_scene_world=True
            area.spaces.active.shading.use_scene_lights=True
bpy.ops.file.pack_all()
regular.filepath='//../fonts/Vera.ttf'
bold.filepath='//../fonts/VeraBd.ttf'
main.render.filepath='//../previews/hud_transparente.png'
preview.render.filepath='//../previews/interfaz_galaga.png'
pause.render.filepath='//../previews/interfaz_pausa.png'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Galaga3D_Interfaz.blend'))
for sc in (main,preview,pause):
    bpy.context.window.scene=sc
    bpy.context.view_layer.update()
    bpy.ops.render.render(write_still=True,scene=sc.name)
bpy.context.window.scene=preview
report={'resolucion':[1280,720],'escenas':[main.name,preview.name,pause.name],'mallas_vectoriales':len([o for o in bpy.data.objects if o.type=='MESH']),'textos_editables':len([o for o in bpy.data.objects if o.type=='FONT']),'valores_iniciales':props,'fuentes_empaquetadas':True,'hud_transparente':True,'modelos_juego_generados':False}
(BASE/'validacion_interfaz_blender.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('INTERFAZ_OK',json.dumps(report,ensure_ascii=False))
