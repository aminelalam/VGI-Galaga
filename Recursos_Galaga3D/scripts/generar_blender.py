"""Recursos originales Galaga 3D. Ejecutar con Blender --background --python.

Modelos en X/Y, profundidad Z, frontal +Y; export OBJ para objLoader de VGI.
Solo reconstruye la carpeta de recursos; nunca abre ni altera una sesion existente.
"""
import bpy
import math
import json
import random
from pathlib import Path
from mathutils import Vector, Matrix, Quaternion

BASE = Path(__file__).resolve().parents[1]
for folder in ('blender', 'modelos/obj', 'modelos/glb', 'previews'):
    (BASE / folder).mkdir(parents=True, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.name = '01_CATALOGO'
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1800
scene.render.resolution_y = 1400
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.film_transparent = False
scene.world = bpy.data.worlds.new('Espacio')
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.015, .023, .045, 1)
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = .45
scene.view_settings.view_transform = 'AgX'

def linear(v):
    return v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4

MATS = {}
def mat(name, color, metal=.0, rough=.45, emit=0):
    rgb = tuple(int(color[i:i+2], 16)/255 for i in (0,2,4))
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*map(linear, rgb), 1)
    p.inputs['Metallic'].default_value = metal
    p.inputs['Roughness'].default_value = rough
    p.inputs['Emission Color'].default_value = (*map(linear, rgb), 1)
    p.inputs['Emission Strength'].default_value = emit
    m.diffuse_color = (*rgb, 1)
    m['srgb'] = rgb
    m['emission_strength'] = emit
    MATS[name] = m
    return m

mat('Casco_hielo', 'd8edf3', .5, .32)
mat('Titanio', '536b86', .55, .42)
mat('Carbono', '172339', .25, .5)
mat('Cian', '36e6ed', .3, .3, .55)
mat('Cabina', '147996', .55, .22)
mat('Rojo', 'fa5269', .25, .38)
mat('Coral_oscuro', '80394e', .35, .4)
mat('Ambar', 'ffba52', .35, .35, .4)
mat('Morado', '9478ff', .4, .35)
mat('Violeta_oscuro', '493964', .35, .4)
mat('Nucleo', 'f2e6ff', .2, .25, .6)
mat('Piedra', '677b91', .1, .75)

assets = []
CURRENT = None
def begin(name, label, role, radius=None, hp=None):
    global CURRENT
    col = bpy.data.collections.new(name)
    scene.collection.children.link(col)
    root = bpy.data.objects.new(name, None)
    col.objects.link(root)
    root.empty_display_type = 'PLAIN_AXES'
    root.empty_display_size = .12
    root['descripcion'] = label
    root['frontal'] = '+Y'
    root['rol'] = role
    root['export_id'] = name
    if radius is not None: root['radio_colision'] = radius
    if hp is not None: root['hp_referencia'] = hp
    CURRENT = dict(id=name, label=label, role=role, radius=radius, hp=hp, root=root, col=col, parts=[])
    assets.append(CURRENT)
    return root

def register(o, name, material, bevel=0):
    o.name = name
    for c in list(o.users_collection): c.objects.unlink(o)
    CURRENT['col'].objects.link(o)
    o.parent = CURRENT['root']
    o.data.materials.append(MATS[material])
    if bevel:
        b = o.modifiers.new('Bordes_mecanizados', 'BEVEL')
        b.width = bevel
        b.segments = 1
    CURRENT['parts'].append(o)
    return o

def outline(name, pts, z, depth, material, bevel=.015):
    # Polygon caps stay ngons until Blender triangulates: safe for concave wings.
    if sum(pts[i][0]*pts[(i+1)%len(pts)][1]-pts[(i+1)%len(pts)][0]*pts[i][1] for i in range(len(pts))) < 0:
        pts = list(reversed(pts))
    n = len(pts)
    verts = [(x,y,z-depth/2) for x,y in pts] + [(x,y,z+depth/2) for x,y in pts]
    faces = [tuple(reversed(range(n))), tuple(range(n,2*n))]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    ob = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(ob)
    return register(ob,name,material,bevel)

def box(name, loc, scale, material, bevel=.02):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    ob = bpy.context.object
    ob.scale = scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return register(ob,name,material,bevel)

def ico(name, loc, scale, material, subdivisions=1):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdivisions, radius=1, location=loc)
    ob = bpy.context.object
    ob.scale = scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return register(ob,name,material)

def cylinder(name, loc, radius, length, material, axis='Y', vertices=8, tip=None):
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=radius, radius2=radius if tip is None else tip, depth=length, location=loc)
    ob = bpy.context.object
    if axis == 'Y': ob.rotation_euler.x = math.pi/2
    if axis == 'X': ob.rotation_euler.y = math.pi/2
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return register(ob,name,material,.005 if tip is None else 0)

def mirror(pts, sign):
    return [(x*sign,y) for x,y in pts]

def ring(name, loc, radius, tube, material, sides=12):
    bpy.ops.mesh.primitive_torus_add(major_segments=sides, minor_segments=4, location=loc, major_radius=radius, minor_radius=tube)
    return register(bpy.context.object,name,material)

def finalize(width):
    a = CURRENT
    # Bake modifiers and transforms before UV/export. Every part keeps its own name.
    bpy.ops.object.select_all(action='DESELECT')
    for o in a['parts']:
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.convert(target='MESH')
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        o.select_set(False)
    bounds = [o.matrix_local @ v.co for o in a['parts'] for v in o.data.vertices]
    scale = width / (max(v.x for v in bounds)-min(v.x for v in bounds))
    for o in a['parts']:
        o.location *= scale
        for v in o.data.vertices: v.co *= scale
        o.data.update()
        uv = o.data.uv_layers.new(name='UV_Planar')
        for p in o.data.polygons:
            for li in p.loop_indices:
                v = o.matrix_local @ o.data.vertices[o.data.loops[li].vertex_index].co
                uv.data[li].uv = (.5+v.x/width, .5+v.y/width)
    a['root'].asset_mark()
    a['root'].asset_data.description = a['label'] + ' | Frente +Y, pantalla XY, profundidad Z'
    a['root'].asset_data.tags.new('Galaga3D')
    a['root'].asset_data.tags.new('LowPoly')

# Jugador: interceptor de doble ala, carenado blanco y ventanas cian.
def player(name, ally=False):
    begin(name,'Nave aliada' if ally else 'Nave del jugador','aliada_opcional' if ally else 'jugador',.32,3)
    outline('Fuselaje',[(0,.83),(.19,.35),(.22,-.38),(.13,-.64),(-.13,-.64),(-.22,-.38),(-.19,.35)],.06,.20,'Casco_hielo')
    outline('Espina_carbono',[(0,.66),(.09,.33),(.10,-.4),(-.10,-.4),(-.09,.33)],.19,.10,'Carbono',.01)
    outline('Cabina_cristal',[(0,.48),(.11,.17),(.09,-.06),(-.09,-.06),(-.11,.17)],.25,.15,'Cian' if ally else 'Cabina')
    for s in (-1,1):
        outline('Ala_izq' if s<0 else 'Ala_der',mirror([(.13,.20),(.28,.17),(.88,-.33),(.92,-.6),(.43,-.48),(.16,-.27)],s),.015,.13,'Casco_hielo')
        outline('Franja_cian',mirror([(.39,-.02),(.77,-.35),(.76,-.44),(.37,-.23)],s),.089,.022,'Ambar' if ally else 'Cian',0)
        cylinder('Pod_motor',(s*.46,-.48,-.01),.105,.45,'Titanio')
        cylinder('Tobera',(s*.46,-.715,-.01),.085,.065,'Carbono')
        cylinder('Motor_luz',(s*.46,-.76,-.01),.065,.025,'Cian')
        cylinder('Canon',(s*.64,-.04,.08),.038,.36,'Titanio')
        box('Boca_canon',(s*.64,.15,.08),(.07,.07,.07),'Cian',.008)
    outline('Marca_nariz',[(-.03,.63),(.03,.63),(0,.75)],.17,.014,'Cian',0)
    finalize(.86)

player('nave_jugador')
player('nave_aliada',True)

# Enemigos: siluetas insectoides originales, sin copiar sprites de Galaga.
begin('enemigo_explorador','Explorador · aguijon','enemigo',.36,1)
ico('Cuerpo',(0,0,.04),(.25,.4,.19),'Ambar',2)
outline('Caparazon',[(-.16,-.13),(-.15,.22),(0,.48),(.15,.22),(.16,-.13),(0,-.31)],.19,.13,'Casco_hielo')
for s in (-1,1):
    outline('Aleta',mirror([(.18,.1),(.43,.37),(.69,.17),(.54,-.30),(.24,-.17)],s),.015,.10,'Ambar')
    outline('Veta_ala',mirror([(.29,.08),(.49,.22),(.58,.14),(.45,-.10)],s),.077,.025,'Carbono',.006)
    ico('Ojo',(s*.09,.23,.275),(.054,.074,.034),'Rojo')
cylinder('Aguijon',(0,.48,.035),.065,.20,'Titanio',tip=0)
cylinder('Motor',(0,-.36,.015),.09,.09,'Cian')
finalize(.9)

begin('enemigo_interceptor','Interceptor · alas de cuchilla','enemigo',.36,1)
outline('Fuselaje',[(0,.65),(.15,.23),(.19,-.36),(0,-.58),(-.19,-.36),(-.15,.23)],.07,.23,'Rojo')
outline('Dorso',[(0,.51),(.095,.14),(.085,-.34),(-.085,-.34),(-.095,.14)],.24,.10,'Carbono')
ico('Ojo_central',(0,.18,.30),(.065,.16,.055),'Ambar',1)
for s in (-1,1):
    outline('Cuchilla',mirror([(.12,.19),(.55,.53),(.86,.40),(.50,-.29),(.23,-.48)],s),.03,.13,'Rojo')
    outline('Panel_cuchilla',mirror([(.39,.20),(.66,.38),(.52,.03),(.30,-.23)],s),.115,.03,'Coral_oscuro',.008)
    outline('Borde_luz',mirror([(.55,.47),(.81,.38),(.77,.30),(.52,.38)],s),.127,.015,'Ambar',0)
    cylinder('Turbina',(s*.24,-.31,-.015),.09,.3,'Titanio')
    cylinder('Reactor',(s*.24,-.49,-.015),.06,.08,'Ambar')
finalize(1.02)

def guardian(damaged=False):
    begin('enemigo_guardian_danado' if damaged else 'enemigo_guardian','Guardian dañado' if damaged else 'Guardian · blindado','enemigo_danado' if damaged else 'enemigo',.48,1 if damaged else 2)
    ico('Abdomen',(0,-.13,0),(.34,.45,.22),'Violeta_oscuro',2)
    outline('Placa_central',[(-.26,-.25),(-.27,.22),(0,.53),(.27,.22),(.26,-.25),(0,-.43)],.19,.19,'Morado')
    ring('Aro_nucleo',(0,.1,.34),.135,.029,'Titanio',10)
    ico('Nucleo',(0,.1,.34),(.102,.12,.065),'Rojo' if damaged else 'Cian',2)
    for s in (-1,1):
        outline('Blindaje_lateral',mirror([(.24,.16),(.51,.4),(.77,.27),(.82,-.17),(.60,-.39),(.25,-.33)],s),.06,.23,'Violeta_oscuro')
        # Damage also removes the starboard armour, exposing two physical cracks.
        if not(damaged and s==1):
            outline('Placa_ala',mirror([(.32,.14),(.53,.29),(.67,.18),(.68,-.14),(.53,-.25),(.33,-.20)],s),.21,.10,'Morado')
        else:
            for yy in (-.12,.05): box('Brecha_blindaje',(.48,yy,.20),(.22,.037,.028),'Rojo',.005)
        outline('Mandibula',mirror([(.2,.21),(.29,.49),(.25,.74),(.16,.44)],s),.12,.10,'Casco_hielo')
        cylinder('Motor',(s*.40,-.40,0),.075,.12,'Ambar')
        box('Marca_vida',(s*.53,-.08,.285),(.05,.16,.022),'Rojo' if damaged else 'Cian',.004)
    finalize(1.12)

guardian(False)
guardian(True)

begin('jefe_final','Jefe · coronado','jefe',1.,24)
outline('Puente',[(-.5,-.32),(-.43,.46),(0,.86),(.43,.46),(.5,-.32),(0,-.66)],.08,.34,'Violeta_oscuro',.028)
outline('Cresta',[(-.26,-.37),(-.23,.46),(0,.68),(.23,.46),(.26,-.37)],.32,.24,'Morado',.025)
ring('Corona_nucleo',(0,.13,.50),.23,.056,'Ambar',12)
ico('Nucleo',(0,.13,.50),(.185,.22,.125),'Nucleo',2)
for s in (-1,1):
    outline('Ala_mayor',mirror([(.33,.32),(.8,.66),(1.56,.31),(1.85,-.29),(1.58,-.63),(.73,-.4),(.4,-.51)],s),.045,.25,'Violeta_oscuro',.025)
    outline('Blindaje',mirror([(.56,.21),(.84,.46),(1.42,.18),(1.59,-.27),(1.32,-.4),(.75,-.28)],s),.235,.16,'Morado',.018)
    outline('Franja_corona',mirror([(.9,.47),(1.48,.23),(1.51,.10),(.87,.33)],s),.335,.025,'Ambar',.003)
    for x,y in ((.70,-.20),(1.32,-.18)):
        cylinder('Canon_pesado',(s*x,y,.22),.11,.62,'Titanio')
        cylinder('Boca_canon',(s*x,y+.34,.22),.074,.055,'Rojo')
        cylinder('Turbina',(s*x,y-.41,.07),.11,.16,'Ambar')
    outline('Cuerno',mirror([(.30,.42),(.48,.74),(.43,1.13),(.23,.72)],s),.18,.16,'Casco_hielo',.01)
for yy in (-.35,-.47): box('Rejilla',(0,yy,.475),(.30,.035,.022),'Carbono',.003)
finalize(2.65)

begin('proyectil_jugador','Proyectil aliado','proyectil',.10)
ico('Punta',(0,.21,0),(.055,.115,.055),'Casco_hielo',1)
cylinder('Cuerpo',(0,0,0),.045,.36,'Cian')
ico('Cola',(0,-.24,0),(.03,.16,.03),'Cian')
finalize(.13)

begin('proyectil_enemigo','Proyectil hostil','proyectil',.10)
ico('Nucleo',(0,0,0),(.075,.11,.06),'Ambar',1)
ring('Corona',(0,0,0),.09,.022,'Rojo',8)
outline('Cola',[(-.033,-.04),(.033,-.04),(0,-.25)],0,.04,'Rojo',0)
finalize(.20)

for aid, label, accent in (('powerup_escudo','Escudo · recurso opcional','Cian'),('powerup_doble','Doble disparo · recurso opcional','Ambar')):
    begin(aid,label,'powerup_opcional')
    outline('Contenedor',[(-.23,-.25),(-.32,0),(-.23,.25),(.23,.25),(.32,0),(.23,-.25)],0,.16,'Titanio')
    outline('Panel',[(-.18,-.19),(-.24,0),(-.18,.19),(.18,.19),(.24,0),(.18,-.19)],.10,.055,'Carbono')
    if aid.endswith('escudo'):
        outline('Simbolo_escudo',[(-.135,.10),(0,.16),(.135,.10),(.105,-.05),(0,-.16),(-.105,-.05)],.15,.03,accent,.005)
    else:
        for s in (-1,1): outline('Simbolo_disparo',[(s*.08-.028,-.13),(s*.08+.028,-.13),(s*.08+.028,.055),(s*.08+.065,.055),(s*.08,.15),(s*.08-.065,.055),(s*.08-.028,.055)],.15,.03,accent,.003)
    finalize(.44)

begin('asteroide','Asteroide decorativo','escenario')
o=ico('Roca',(0,0,0),(.6,.5,.38),'Piedra',2)
rng=random.Random(43)
for v in o.data.vertices: v.co *= rng.uniform(.77,1.14)
for loc,sca in [((.24,.13,.31),(.12,.11,.035)),((-.21,-.1,.28),(.14,.09,.04))]: ico('Veta',loc,sca,'Titanio',1)
finalize(.95)

begin('barra_vida_3d','Barra de vida 3D · relleno separado','hud_3d')
box('Marco',(0,0,0),(2.0,.24,.10),'Titanio',.03)
box('Fondo',(0,0,.06),(1.83,.13,.035),'Carbono',.015)
fill=box('Relleno',(-.007,0,.085),(1.77,.09,.024),'Cian',.003)
# Rebase mesh origin to left end: fill.scale.x changes HP without drifting.
for v in fill.data.vertices: v.co.x += .885
fill.location.x -= .885
for s in (-1,1): box('Extremo',(s*.952,0,.045),(.036,.12,.04),'Cian',.002)
finalize(1.8)
CURRENT['root']['uso'] = 'Escalar Relleno en X: hp/maxHp, origen en extremo izquierdo.'

for idx,(r,spikes) in enumerate(((.16,6),(.30,8),(.43,10)),1):
    begin('explosion_%02d'%idx,'Explosion · fase %d'%idx,'efecto')
    ico('Flash',(0,0,0),(r*.6,r*.6,.08),'Ambar' if idx>1 else 'Casco_hielo',1)
    for j in range(spikes):
        a=j*math.tau/spikes+.15*idx
        length=r*(.45+.22*(j%3))
        center=(math.cos(a)*r,math.sin(a)*r,.01*(j%2))
        ob=ico('Fragmento',center,(length,.037,.03),'Rojo' if j%2 else 'Ambar',1)
        ob.rotation_euler.z=a
    finalize(r*2.8)

def meshes(a): return a['parts']

def export_obj(a):
    """No axis swap, positive indices, triangle-only, MTL order matches draw VGI."""
    verts,uvs,normals = [],[],[]
    groups = {}
    for o in meshes(a):
        mesh=o.data
        mesh.calc_loop_triangles()
        normal_matrix=o.matrix_local.to_3x3().inverted().transposed()
        for t in mesh.loop_triangles:
            m=mesh.materials[t.material_index]
            refs=[]
            normal=(normal_matrix @ t.normal).normalized()
            normals.append(tuple(normal))
            ni=len(normals)
            for vi,li in zip(t.vertices,t.loops):
                co=o.matrix_local @ mesh.vertices[vi].co
                verts.append(tuple(co))
                uvs.append(tuple(mesh.uv_layers.active.data[li].uv))
                i=len(verts)
                refs.append(f'{i}/{i}/{ni}')
            groups.setdefault(m.name,[]).append('f '+' '.join(refs))
    obj=['# Galaga3D original; X right Y forward Z depth; metres arbitrary',f'mtllib {a["id"]}.mtl']
    obj += ['v %.7f %.7f %.7f'%v for v in verts]
    obj += ['vt %.7f %.7f'%v for v in uvs]
    obj += ['vn %.7f %.7f %.7f'%v for v in normals]
    mtl=['# Legacy VGI: Ka Kd Ks Ns. No texture dependencies.']
    for name,faces in groups.items():
        m=MATS[name]; rgb=m['srgb']
        obj += [f'usemtl {name}']+faces
        mtl += [f'newmtl {name}','Ka %.5f %.5f %.5f'%tuple(c*.20 for c in rgb),'Kd %.5f %.5f %.5f'%tuple(rgb),'Ks 0.25000 0.25000 0.25000','Ns 32.00000','']
    (BASE/'modelos/obj'/f'{a["id"]}.obj').write_text('\n'.join(obj)+'\n',encoding='ascii')
    (BASE/'modelos/obj'/f'{a["id"]}.mtl').write_text('\n'.join(mtl)+'\n',encoding='ascii')
    bound=[Vector(v) for v in verts]
    a['stats']=dict(triangulos=len(normals),materiales=list(groups),piezas=len(a['parts']),bbox_min=[min(v[j] for v in bound) for j in range(3)],bbox_max=[max(v[j] for v in bound) for j in range(3)])

for a in assets:
    export_obj(a)
    bpy.ops.object.select_all(action='DESELECT')
    a['root'].select_set(True)
    for o in a['parts']: o.select_set(True)
    bpy.context.view_layer.objects.active=a['root']
    bpy.ops.export_scene.gltf(filepath=str(BASE/'modelos/glb'/f'{a["id"]}.glb'),use_selection=True,export_format='GLB',export_yup=False,export_materials='EXPORT',export_extras=True)

# Archive originals in a scene whose objects remain at local origin, hidden in gallery.
library=bpy.data.scenes.new('03_BIBLIOTECA_ORIGEN')
for a in assets:
    library.collection.children.link(a['col'])
    scene.collection.children.unlink(a['col'])

def collection(sc,name):
    col=bpy.data.collections.new(name)
    sc.collection.children.link(col)
    return col

def duplicate(a,col,position,scale=1,angle=0):
    root=a['root'].copy()
    col.objects.link(root)
    root.name=a['id']+'_vista'
    root.location=position
    root.scale=(scale,)*3
    root.rotation_euler.z=angle
    for source in a['parts']:
        ob=source.copy()
        ob.data=source.data
        col.objects.link(ob)
        ob.parent=root
    return root

def text(sc,col,body,loc,size=.19,color='Casco_hielo',align='LEFT'):
    cu=bpy.data.curves.new('Rotulo','FONT'); cu.body=body;cu.size=size;cu.align_x=align;cu.extrude=0
    ob=bpy.data.objects.new(body,cu);col.objects.link(ob);ob.location=loc;ob.data.materials.append(MATS[color])
    return ob

def plane(sc,col,loc,width,height,material):
    mesh=bpy.data.meshes.new('Panel')
    mesh.from_pydata([(-width/2,-height/2,0),(width/2,-height/2,0),(width/2,height/2,0),(-width/2,height/2,0)],[],[(0,1,2,3)])
    ob=bpy.data.objects.new('Panel',mesh);col.objects.link(ob);ob.location=loc;mesh.materials.append(MATS[material]);return ob

def setup(sc,target,ortho,resolution):
    sc.render.engine='BLENDER_EEVEE';sc.render.resolution_x=resolution[0];sc.render.resolution_y=resolution[1];sc.render.resolution_percentage=100
    sc.render.image_settings.file_format='PNG';sc.world=scene.world
    sc.view_settings.view_transform='AgX'
    col=collection(sc,'ESTUDIO_camara_luces')
    camd=bpy.data.cameras.new('Camara');cam=bpy.data.objects.new('Camara',camd);col.objects.link(cam)
    cam.location=(target[0],target[1],28);cam.rotation_euler=(0,0,0);camd.type='ORTHO';camd.ortho_scale=ortho;sc.camera=cam
    for name,loc,power,size,color in [('Principal',(-7,8,14),1800,10,(.72,.88,1)),('Relleno',(8,1,10),1200,9,(.55,.8,1)),('Calida',(0,-6,8),700,7,(1,.55,.32))]:
        data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size;data.color=color
        ob=bpy.data.objects.new(name,data);col.objects.link(ob);ob.location=loc;ob.rotation_euler=(Vector((target[0],target[1],0))-ob.location).to_track_quat('-Z','Y').to_euler()

setup(scene,(0,0),17.0,(1800,1400))
views=collection(scene,'CATALOGO_Modelos')
labels=collection(scene,'CATALOGO_Rotulos')
plane(scene,labels,(0,0,-.45),19,16,'Carbono')
text(scene,labels,'GALAGA / 3D',(-7.3,5.65,.1),.57,'Casco_hielo')
text(scene,labels,'RECURSOS ORIGINALES   /   LOW POLY   /   VGI',(-7.3,5.11,.1),.17,'Cian')
text(scene,labels,'01  NAVES & ENEMIGOS',(-7.3,4.63,.1),.18,'Titanio')
byid={a['id']:a for a in assets}
layout=[('nave_jugador',-5.9,3.20,2.75,'NAVE JUGADOR'),('enemigo_explorador',-2.15,3.2,2.7,'EXPLORADOR'),('enemigo_interceptor',1.65,3.2,2.6,'INTERCEPTOR'),('enemigo_guardian',5.4,3.2,2.5,'GUARDIAN'),('nave_aliada',-5.9,-.3,2.5,'ALIADA / P2'),('enemigo_guardian_danado',-2.15,-.3,2.3,'GUARDIAN DANADO'),('jefe_final',3.5,-.25,1.65,'JEFE FINAL / 24 HP')]
for aid,x,y,s,label in layout:
    duplicate(byid[aid],views,(x,y,0),s)
    text(scene,labels,label,(x,y-1.66,.1),.16,'Casco_hielo','CENTER')
text(scene,labels,'02  PROYECTILES / EFECTOS / UTILIDAD',(-7.3,-2.35,.1),.18,'Titanio')
small=[('proyectil_jugador',-6.3,2.5,'ALIADO'),('proyectil_enemigo',-4.55,2.5,'HOSTIL'),('powerup_escudo',-2.8,2.5,'ESCUDO'),('powerup_doble',-1.0,2.5,'DOBLE'),('asteroide',1.0,1.25,'ROCA'),('explosion_02',3.0,1.4,'EXPLOSION'),('barra_vida_3d',5.7,1.2,'VIDA 3D')]
for aid,x,s,label in small:
    duplicate(byid[aid],views,(x,-3.65,0),s)
    text(scene,labels,label,(x,-4.6,.1),.15,'Casco_hielo','CENTER')
text(scene,labels,'BLEND + GLB + OBJ / MTL     |     FRENTE +Y / PROFUNDIDAD Z',(-7.3,-5.45,.1),.16,'Cian')
text(scene,labels,'HUD 2D CON CAPAS Y ATLAS EN LA CARPETA hud/',(-7.3,-5.82,.1),.14,'Titanio')

# A second editable scene shows actual composition, keeping gallery scale separate.
game=bpy.data.scenes.new('02_DEMO_FORMACION')
setup(game,(0,1),14,(1600,1100))
gamecol=collection(game,'DEMOSTRACION_No_es_logica_juego')
gamehud=collection(game,'HUD_demo')
plane(game,gamecol,(0,1,-3.5),16,13,'Carbono')
random.seed(42)
for j in range(95):
    x=random.uniform(-7.5,7.5);y=random.uniform(-4.5,7)
    mesh=bpy.data.meshes.new('Estrella');r=random.uniform(.012,.026)
    mesh.from_pydata([(x-r,y-r,-3.3),(x+r,y-r,-3.3),(x+r,y+r,-3.3),(x-r,y+r,-3.3)],[],[(0,1,2,3)])
    ob=bpy.data.objects.new('Estrella',mesh);gamecol.objects.link(ob);mesh.materials.append(MATS['Titanio'])
for row,aid in enumerate(['enemigo_guardian','enemigo_interceptor','enemigo_explorador']):
    for n in range(6): duplicate(byid[aid],gamecol,(-3.25+n*1.3,4.1-row*1.32,0),.84,math.pi)
duplicate(byid['nave_jugador'],gamecol,(0,-3.4,0),1.18)
for x,y in ((0,-1.9),(0,-.15)):
    duplicate(byid['proyectil_jugador'],gamecol,(x,y,.06))
for x,y in ((-1.3,-.8),(2.3,.4)):
    duplicate(byid['proyectil_enemigo'],gamecol,(x,y,.06),1.,math.pi)
text(game,gamehud,'SCORE  001250',(-5.8,5.5,.5),.25,'Casco_hielo')
text(game,gamehud,'OLEADA 01',(0,5.5,.5),.25,'Casco_hielo','CENTER')
text(game,gamehud,'PLANO A',(5.8,5.5,.5),.25,'Cian','RIGHT')
for i in range(3): duplicate(byid['nave_jugador'],gamehud,(-5.4+i*.5,-4.3,.2),.4)
text(game,gamehud,'A / D  MOVER    ESPACIO  DISPARAR    E  PLANO    P  PAUSA',(-2.6,-4.4,.5),.14,'Titanio')

manifest={'version':1,'estilo':'Low poly futurista original','coordenadas':{'x':'derecha','y':'frontal +Y / arriba pantalla','z':'profundidad / camara en +Z'},'gltf_export_yup':False,'planos':{'A_z':0,'B_z':-3},'materiales_obj':'Ka/Kd/Ks/Ns opacos, colores sRGB, sin texturas requeridas','assets':[]}
for a in assets:
    entry={k:a[k] for k in ('id','label','role','radius','hp')}
    entry.update(a['stats'])
    entry['obj']='modelos/obj/'+a['id']+'.obj'
    entry['glb']='modelos/glb/'+a['id']+'.glb'
    manifest['assets'].append(entry)
(BASE/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

# Nice opening view: camera catalogue, materials shown in solid mode, overlays off.
bpy.context.window.scene=scene
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective='CAMERA'
            area.spaces.active.region_3d.view_camera_zoom=0
            area.spaces.active.shading.type='MATERIAL'
            area.spaces.active.overlay.show_overlays=False
            area.spaces.active.clip_end=1000
scene.render.filepath=str(BASE/'previews'/'catalogo_3d.png')
bpy.ops.wm.save_as_mainfile(filepath=str(BASE/'blender'/'Galaga3D_Recursos.blend'))
bpy.ops.render.render(write_still=True)
bpy.context.window.scene=game
game.render.filepath=str(BASE/'previews'/'demo_formacion.png')
bpy.ops.render.render(write_still=True)
bpy.context.window.scene=scene
print('GALAGA_PACK_OK',len(assets),'assets')
