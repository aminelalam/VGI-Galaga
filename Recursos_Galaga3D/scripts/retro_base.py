"""Small editable Blender primitives and a 5x7 arcade alphabet."""
import bpy
import math
import random
from mathutils import Vector

GLYPHS = {
'A':['01110','10001','10001','11111','10001','10001','10001'],
'B':['11110','10001','10001','11110','10001','10001','11110'],
'C':['01111','10000','10000','10000','10000','10000','01111'],
'D':['11110','10001','10001','10001','10001','10001','11110'],
'E':['11111','10000','10000','11110','10000','10000','11111'],
'F':['11111','10000','10000','11110','10000','10000','10000'],
'G':['01111','10000','10000','10111','10001','10001','01111'],
'H':['10001','10001','10001','11111','10001','10001','10001'],
'I':['11111','00100','00100','00100','00100','00100','11111'],
'J':['00111','00010','00010','00010','10010','10010','01100'],
'K':['10001','10010','10100','11000','10100','10010','10001'],
'L':['10000','10000','10000','10000','10000','10000','11111'],
'M':['10001','11011','10101','10101','10001','10001','10001'],
'N':['10001','11001','10101','10011','10001','10001','10001'],
'O':['01110','10001','10001','10001','10001','10001','01110'],
'P':['11110','10001','10001','11110','10000','10000','10000'],
'Q':['01110','10001','10001','10001','10101','10010','01101'],
'R':['11110','10001','10001','11110','10100','10010','10001'],
'S':['01111','10000','10000','01110','00001','00001','11110'],
'T':['11111','00100','00100','00100','00100','00100','00100'],
'U':['10001','10001','10001','10001','10001','10001','01110'],
'V':['10001','10001','10001','10001','10001','01010','00100'],
'W':['10001','10001','10001','10101','10101','10101','01010'],
'X':['10001','10001','01010','00100','01010','10001','10001'],
'Y':['10001','10001','01010','00100','00100','00100','00100'],
'Z':['11111','00001','00010','00100','01000','10000','11111'],
'0':['01110','10001','10011','10101','11001','10001','01110'],
'1':['00100','01100','00100','00100','00100','00100','01110'],
'2':['01110','10001','00001','00010','00100','01000','11111'],
'3':['11110','00001','00001','01110','00001','00001','11110'],
'4':['00010','00110','01010','10010','11111','00010','00010'],
'5':['11111','10000','10000','11110','00001','00001','11110'],
'6':['01110','10000','10000','11110','10001','10001','01110'],
'7':['11111','00001','00010','00100','01000','01000','01000'],
'8':['01110','10001','10001','01110','10001','10001','01110'],
'9':['01110','10001','10001','01111','00001','00001','01110'],
':':['00000','00100','00100','00000','00100','00100','00000'],
'/':['00001','00010','00010','00100','01000','01000','10000'],
'-':['00000','00000','00000','11111','00000','00000','00000'],
'>':['10000','01000','00100','00010','00100','01000','10000'],
'.':['00000','00000','00000','00000','00000','00110','00110'],
'%':['11001','11010','00100','01000','10110','00110','00000'],
'+':['00000','00100','00100','11111','00100','00100','00000'],
}

def linear(v):
    return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4

def palette():
    colors={'white':'F3EEDB','blue':'3B7DDD','red':'D94C48','yellow':'EAC64B',
            'green':'63AF70','purple':'9870B3','dark':'10131C','cockpit':'90D0DD',
            'engine':'E98B3E','metal':'747E89','muted':'9EA8B4','panel':'1C2330',
            'black':'05070C'}
    materials={}
    for name,h in colors.items():
        color=tuple(linear(int(h[i:i+2],16)/255) for i in (0,2,4))
        mat=bpy.data.materials.new('Retro_'+name)
        mat.diffuse_color=(*color,1);mat.use_nodes=True
        bs=mat.node_tree.nodes.get('Principled BSDF')
        bs.inputs['Base Color'].default_value=(*color,1)
        bs.inputs['Roughness'].default_value=.82
        if name in ('white','yellow','blue','red','green','muted','cockpit'):
            bs.inputs['Emission Color'].default_value=(*color,1)
            bs.inputs['Emission Strength'].default_value=.35
        materials[name]=mat
    return materials

CUBE_FACES=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
def cube_vertices(x,y,z,w,h,d):
    return [(x+a*w/2,y+b*h/2,z+c*d/2) for a,b,c in
            [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),
             (-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]

def mesh_object(col,name,verts,faces,mat,parent=None):
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
    ob=bpy.data.objects.new(name,mesh);col.objects.link(ob)
    mesh.materials.append(mat);ob.parent=parent
    return ob

def box(col,name,location,size,mat,parent=None):
    ob=mesh_object(col,name,cube_vertices(0,0,0,*size),CUBE_FACES,mat,parent)
    ob.location=location;return ob

def pixel_text(col,name,body,x,y,height,mat,align='CENTER',z=8.5,action=None,parent=None):
    body=body.upper();step=height/7
    advances=[3 if c==' ' else 6 for c in body]
    width=max(0,(sum(advances)-1))*step
    start=x-(width/2 if align=='CENTER' else width if align=='RIGHT' else 0)
    verts=[];faces=[];pen=start
    for ch,advance in zip(body,advances):
        if ch!=' ':
            glyph=GLYPHS.get(ch,GLYPHS['-'])
            for row,data in enumerate(glyph):
                for column,bit in enumerate(data):
                    if bit=='1':
                        start_index=len(verts)
                        verts.extend(cube_vertices(pen+column*step+step*.5,
                                                  y+(3-row)*step,z,step*.89,step*.89,.055))
                        faces.extend(tuple(start_index+i for i in face) for face in CUBE_FACES)
        pen+=advance*step
    ob=mesh_object(col,name,verts,faces,mat,parent)
    ob['texto']=body
    if action:ob['retro_action']=action
    return ob

def border(col,name,cx,cy,width,height,mat,z=8.0,thickness=.05,parent=None):
    parts=[]
    for suffix,loc,size in [
      ('arriba',(cx,cy+height/2,z),(width,thickness,.07)),
      ('abajo',(cx,cy-height/2,z),(width,thickness,.07)),
      ('izq',(cx-width/2,cy,z),(thickness,height,.07)),
      ('der',(cx+width/2,cy,z),(thickness,height,.07))]:
        parts.append(box(col,name+'_'+suffix,loc,size,mat,parent))
    return parts

def button(col,name,label,x,y,width,action,mats,height=.78):
    body=box(col,name,(x,y,8.03),(width,height,.18),mats['panel'])
    body['retro_action']=action
    for edge in border(col,name+'_borde',x,y,width,height,mats['metal'],z=8.18,thickness=.045):
        edge['retro_action']=action
    pixel_text(col,name+'_texto',label,x,y,.32,mats['white'],z=8.24,action=action)
    return body

def plane_badge(col,name,x,y,plane,mats,scale=.28,z=1):
    # Geometry preserves shape and letter when colour is removed.
    mat=mats['blue' if plane=='A' else 'yellow']
    n=12 if plane=='A' else 4
    angle=0 if plane=='A' else math.pi/2
    r=scale
    for i in range(n):
        a=i*math.tau/n+angle;b=(i+1)*math.tau/n+angle
        ax,ay=x+r*math.cos(a),y+r*math.sin(a)
        bx,by=x+r*math.cos(b),y+r*math.sin(b)
        part=box(col,name+f'_{i}',((ax+bx)/2,(ay+by)/2,z),
                 (math.hypot(bx-ax,by-ay),.025,.05),mat)
        part.rotation_euler.z=math.atan2(by-ay,bx-ax)
    pixel_text(col,name+'_letra',plane,x,y,scale*.90,mat,z=z+.07)

def stars(col,mats,seed=3):
    rng=random.Random(seed)
    for i in range(55):
        x,y=rng.uniform(-10.4,10.4),rng.uniform(-5.65,5.65)
        sz=rng.choice([.025,.04,.055])
        box(col,f'Estrella_{seed}_{i:02}',(x,y,-2.65),(sz,sz,.04),mats['metal'])

def make_scene(name,mats):
    scene=bpy.data.scenes.new(name)
    col=bpy.data.collections.new(name+'_Objetos');scene.collection.children.link(col)
    world=bpy.data.worlds.new(name+'_Espacio');world.use_nodes=True
    world.node_tree.nodes['Background'].inputs['Color'].default_value=(.07,.085,.12,1)
    world.node_tree.nodes['Background'].inputs['Strength'].default_value=.45;scene.world=world
    scene.render.engine='BLENDER_EEVEE';scene.eevee.taa_render_samples=24
    scene.render.resolution_x=1280;scene.render.resolution_y=720;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
    scene.render.fps=30;scene.frame_start=1;scene.frame_end=240
    scene.view_settings.view_transform='Standard';scene.view_settings.look='None'
    scene['nave_elegida']=0
    cam_data=bpy.data.cameras.new(name+'_Camara');cam=bpy.data.objects.new(name+'_Camara',cam_data)
    col.objects.link(cam);cam.location=(0,0,32);cam_data.type='ORTHO';cam_data.ortho_scale=22
    scene.camera=cam
    for suffix,pos,energy,size in [('Principal',(-6,5,15),1700,7),('Relleno',(7,-3,10),650,6)]:
        light_data=bpy.data.lights.new(name+'_'+suffix,'AREA');light_data.energy=energy;light_data.shape='DISK';light_data.size=size
        light=bpy.data.objects.new(name+'_'+suffix,light_data);col.objects.link(light);light.location=pos
        light.rotation_euler=(Vector((0,0,0))-light.location).to_track_quat('-Z','Y').to_euler()
    box(col,name+'_Fondo',(0,0,-3),(21.8,12.2,.3),mats['black'])
    border(col,name+'_Marco',0,0,21.6,12.0,mats['metal'],z=-2.75,thickness=.035)
    stars(col,mats)
    return scene,col

def loop_keyframes(ob,path,values,linear=False,cycles=True):
    for frame,value in values:
        setattr(ob,path,value);ob.keyframe_insert(data_path=path,frame=frame)
    action=ob.animation_data.action
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for curve in bag.fcurves:
                    for key in curve.keyframe_points:
                        key.interpolation='LINEAR' if linear else 'BEZIER'
                    if cycles:curve.modifiers.new('CYCLES')
