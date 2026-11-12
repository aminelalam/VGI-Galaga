"""Original industrial spacecraft, solid components and orbital environment.

X is lateral, +Y points forward, Z is up. Every exported piece is closed.
The builders use bevelled sections, inset glazing and integrated propulsion.
"""
import math
import random

import bpy
import bmesh
from mathutils import Matrix, Vector


def root_object(collection, name):
    root = bpy.data.objects.new(name, None)
    collection.objects.link(root)
    root["export_obj"] = name + ".obj"
    root["forward_axis"] = "+Y"
    return root


def piece(collection, root, name, vertices, faces, material, smooth=False):
    mesh = bpy.data.meshes.new(root.name + "_" + name)
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(material)
    mesh.update()
    topology = bmesh.new()
    topology.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(topology, faces=list(topology.faces))
    if topology.calc_volume(signed=True) < 0:
        bmesh.ops.reverse_faces(topology, faces=list(topology.faces))
    topology.to_mesh(mesh)
    topology.free()
    for polygon in mesh.polygons:
        polygon.use_smooth = smooth
    mesh.update()
    obj = bpy.data.objects.new(mesh.name, mesh)
    collection.objects.link(obj)
    obj.parent = root
    return obj


def skin(collection, root, name, rings, material, smooth=False):
    """Join equal-size closed cross sections, including solid end caps."""
    count = len(rings[0])
    vertices = [point for ring in rings for point in ring]
    faces = [tuple(reversed(range(count)))]
    for section in range(len(rings)-1):
        for index in range(count):
            nxt = (index+1) % count
            faces.append((section*count+index, section*count+nxt,
                          (section+1)*count+nxt, (section+1)*count+index))
    faces.append(tuple((len(rings)-1)*count+i for i in range(count)))
    return piece(collection,root,name,vertices,faces,material,smooth)


def hull(collection, root, name, sections, material, x=0, smooth=False):
    """Y, half width, half height, centre Z: eight bevelled armour facets."""
    profile = [(.67,1),(-.67,1),(-1,.55),(-1,-.55),
               (-.67,-1),(.67,-1),(1,-.55),(1,.55)]
    rings = [[(x+rx*px,y,z+rz*pz) for px,pz in profile] for y,rx,rz,z in sections]
    return skin(collection,root,name,rings,material,smooth)


def cylinder(collection, root, name, sections, material, x=0, segments=16, smooth=True):
    rings = [[(x+rx*math.cos(i*math.tau/segments),y,z+rz*math.sin(i*math.tau/segments))
              for i in range(segments)] for y,rx,rz,z in sections]
    return skin(collection,root,name,rings,material,smooth)


def box(collection, root, name, center, size, material, bevel=.12):
    x,y,z=center
    sx,sy,sz=(value*.5 for value in size)
    if min(size)<.025:
        return prism(collection,root,name,[(x-sx,y-sy),(x+sx,y-sy),(x+sx,y+sy),(x-sx,y+sy)],
                     z-sz,z+sz,material)
    cut=min(sx,sy,sz)*bevel
    obj=hull(collection,root,name,
             [(y-sy,max(.0001,sx-cut),max(.0001,sz-cut),z),
              (y-sy+cut,sx,sz,z),(y+sy-cut,sx,sz,z),
              (y+sy,max(.0001,sx-cut),max(.0001,sz-cut),z)],material,x)
    return obj


def prism(collection,root,name,outline,bottom,top,material):
    count=len(outline)
    vertices=[(x,y,bottom) for x,y in outline]+[(x,y,top) for x,y in outline]
    faces=[tuple(reversed(range(count))),tuple(range(count,2*count))]
    for index in range(count):
        nxt=(index+1)%count
        faces.append((index,nxt,nxt+count,index+count))
    return piece(collection,root,name,vertices,faces,material)


def beam(collection,root,name,start,end,width,depth,material):
    start,end=Vector(start),Vector(end)
    direction=end-start
    obj=box(collection,root,name,(0,0,0),(width,direction.length,depth),material,.18)
    rotation=direction.to_track_quat("Y","Z").to_matrix().to_4x4()
    transform=Matrix.Translation((start+end)*.5)@rotation
    obj.data.transform(transform)
    return obj


def wing(collection,root,name,sections,material,side=1):
    # Span, leading edge Y, trailing edge Y, centre Z, half thickness.
    rings=[]
    for x,front,rear,z,t in sections:
        chord=front-rear
        rings.append([(side*x,front-.07*chord,z+t*.48),
                      (side*x,front-.24*chord,z+t),
                      (side*x,rear+.20*chord,z+t*.72),
                      (side*x,rear,z+t*.20),(side*x,rear,z-t*.20),
                      (side*x,rear+.20*chord,z-t*.65),
                      (side*x,front-.20*chord,z-t*.70),
                      (side*x,front,z-t*.18)])
    return skin(collection,root,name,rings,material)


def paint_faces(obj,material,predicate):
    slot=len(obj.data.materials)
    obj.data.materials.append(material)
    for polygon in obj.data.polygons:
        if predicate(polygon.center,polygon.normal):
            polygon.material_index=slot


def fin(collection,root,name,x,profile,thickness,material,cant=0):
    count=len(profile)
    vertices=[(x+sign*thickness+cant*z,y,z) for sign in (-1,1) for y,z in profile]
    faces=[tuple(reversed(range(count))),tuple(range(count,2*count))]
    for i in range(count):
        j=(i+1)%count
        faces.append((i,j,j+count,i+count))
    return piece(collection,root,name,vertices,faces,material)


def nozzle(collection,root,name,x,y,z,radius,materials,hot=False,segments=20):
    """A deep six-ring exhaust with a physical lip, dark throat and hot core."""
    profile=[(y+.21,radius*.88),(y+.11,radius),
             (y,radius*.92),(y,radius*.72),
             (y+.14,radius*.51),(y+.21,radius*.54)]
    vertices=[]
    for depth,r in profile:
        for i in range(segments):
            angle=i*math.tau/segments
            vertices.append((x+r*math.cos(angle),depth,z+r*math.sin(angle)))
    faces=[]
    for ring in range(len(profile)):
        nxt=(ring+1)%len(profile)
        for index in range(segments):
            following=(index+1)%segments
            faces.append((ring*segments+index,ring*segments+following,
                          nxt*segments+following,nxt*segments+index))
    shell=piece(collection,root,name+"_Tobera",vertices,faces,materials["metal"],True)
    paint_faces(shell,materials["dark"],lambda p,n:p.y>y+.08 and abs(p.x-x)<radius*.60)
    cylinder(collection,root,name+"_Nucleo",[(y+.155,radius*.51,radius*.51,z),
             (y+.175,radius*.51,radius*.51,z)],materials["engine_hot" if hot else "engine_cold"],
             x,segments)
    # The back lip has a second narrow, heat-resistant band.
    collar=cylinder(collection,root,name+"_Collar",[(y+.195,radius*.91,radius*.91,z),
             (y+.235,radius*.88,radius*.88,z)],materials["dark"],x,segments)
    return shell


def gun(collection,root,name,x,y,z,materials,length=.31,radius=.021):
    box(collection,root,name+"_Cuna",(x,y-.025,z),(radius*3,.16,radius*2.6),materials["dark"])
    cylinder(collection,root,name+"_Canon",[(y-.06,radius*1.45,radius*1.45,z),
             (y+.04,radius*1.35,radius*1.35,z),
             (y+length-.035,radius,radius,z),(y+length,radius*1.13,radius*1.13,z)],
             materials["metal"],x,12,False)
    cylinder(collection,root,name+"_Boca",[(y+length+.001,radius*.7,radius*.7,z),
             (y+length+.006,radius*.7,radius*.7,z)],materials["dark"],x,12,False)


def canopy(collection,root,name,x,y,z,width,length,height,materials):
    # The glazing is itself a closed faceted volume inset into an armour coaming.
    hull(collection,root,name+"_Borde",[(y-length*.5,width*.77,height*.20,z),
         (y-length*.29,width,height*.39,z+height*.14),
         (y+length*.34,width*.70,height*.23,z+height*.10),
         (y+length*.5,width*.36,height*.10,z)],materials["dark"],x)
    hull(collection,root,name+"_Cristal",[(y-length*.43,width*.70,height*.12,z+height*.22),
         (y-length*.15,width*.80,height*.43,z+height*.40),
         (y+length*.21,width*.59,height*.32,z+height*.34),
         (y+length*.44,width*.28,height*.08,z+height*.14)],materials["cockpit"],x)
    beam(collection,root,name+"_Arco",(x-width*.78,y-length*.16,z+height*.28),
         (x+width*.78,y-length*.16,z+height*.28),.012,.014,materials["metal"])


def vents(collection,root,name,x,y,z,width,length,materials,count=3):
    box(collection,root,name+"_Hueco",(x,y,z),(width,length,.018),materials["dark"],.05)
    for index in range(count):
        yy=y-length*.36+index*length*.72/max(1,count-1)
        box(collection,root,name+f"_Lama{index}",(x,yy,z+.012),(width*.85,.012,.012),
            materials["metal"],.08)


def aft_bulkhead(collection,root,y,z,width,height,materials):
    hull(collection,root,"Registro_popa",[(y-.010,width*.82,height*.78,z),
         (y+.008,width*.82,height*.78,z)],materials["dark"])
    for index,offset in enumerate((-.035,0,.035)):
        box(collection,root,f"Lama_popa_{index}",(0,y-.017,z+offset),
             (width*1.25,.008,.010),materials["metal"])


def transform_root(root,matrix):
    for part in root.children:
        part.data.transform(matrix@part.matrix_basis)
        part.matrix_basis=Matrix.Identity(4)
        part.data.update()


def face_enemies(root):
    transform_root(root,Matrix.Rotation(math.pi,4,"Z"))
    root["forward_axis"]="-Y"
    return root


def build_ship(collection,name,variant,materials):
    root=root_object(collection,name)
    hull_color=materials["white" if variant!=1 else "armor"]
    mark=materials[("blue","red","green")[variant]]
    if variant==0:
        body=hull(collection,root,"Fuselaje",[(-.56,.13,.105,-.025),(-.32,.205,.14,0),
             (.02,.18,.14,.025),(.29,.12,.10,.025),(.62,.065,.06,.005),
             (.88,.012,.016,-.005)],hull_color)
        paint_faces(body,materials["dark"],lambda p,n:n.z<-.45)
        for side in (-1,1):
            panel=wing(collection,root,f"Ala_{side}",[(.12,.24,-.39,0,.047),
                 (.37,.13,-.45,-.02,.04),(.64,-.06,-.43,.005,.027),
                 (.78,-.22,-.37,.052,.018)],hull_color,side)
            paint_faces(panel,mark,lambda p,n:.43<abs(p.x)<.69 and n.z>.4)
            nacelle=cylinder(collection,root,f"Gondola_{side}",
                [(-.57,.082,.082,-.055),(-.38,.105,.102,-.035),
                 (-.13,.088,.077,-.025),(.04,.035,.040,-.02)],materials["armor"],side*.28,20,False)
            paint_faces(nacelle,mark,lambda p,n:n.z>.6)
            nozzle(collection,root,f"Reactor_{side}",side*.28,-.78,-.055,.09,materials)
            gun(collection,root,f"Arma_{side}",side*.56,-.18,.033,materials,.36,.020)
            fin(collection,root,f"Deriva_{side}",side*.17,
                [(-.51,.055),(-.40,.29),(-.25,.31),(-.15,.10)],.014,mark,side*.20)
            vents(collection,root,f"Radiador_{side}",side*.125,-.30,.135,.07,.16,materials)
        canopy(collection,root,"Cabina",0,.105,.14,.105,.43,.17,materials)
        paint_faces(body,mark,lambda p,n:.35<p.y<.65 and n.z>.75)
    elif variant==1:
        body=hull(collection,root,"Fuselaje",[(-.55,.20,.12,-.02),(-.24,.28,.16,.015),
            (.12,.24,.14,.025),(.43,.17,.105,.005),(.77,.045,.035,-.015)],hull_color)
        paint_faces(body,materials["dark"],lambda p,n:n.z<-.3)
        for side in (-1,1):
            panel=wing(collection,root,f"Ala_delta_{side}",[(.17,.40,-.50,-.015,.07),
                (.46,.19,-.54,-.025,.055),(.75,-.12,-.48,.025,.028),
                (.79,-.28,-.44,.07,.018)],materials["white"],side)
            paint_faces(panel,mark,lambda p,n:abs(p.x)>.51 and n.z>.3)
            hull(collection,root,f"Lomo_motor_{side}",[(-.57,.12,.10,-.045),
                 (-.25,.135,.13,-.025),(.08,.10,.10,-.025),(.22,.04,.045,-.035)],
                 materials["armor"],side*.31)
            nozzle(collection,root,f"Reactor_{side}",side*.31,-.78,-.065,.115,materials)
            fin(collection,root,f"Deriva_{side}",side*.35,
                [(-.50,.075),(-.41,.29),(-.26,.27),(-.15,.08)],.016,materials["dark"],side*.25)
            gun(collection,root,f"Arma_{side}",side*.56,-.18,.04,materials,.33,.024)
            vents(collection,root,f"Radiador_{side}",side*.32,-.18,.115,.10,.20,materials,4)
        canopy(collection,root,"Cabina",0,.12,.16,.13,.46,.16,materials)
        paint_faces(body,mark,lambda p,n:p.y>.3 and n.z>.75)
    else:
        body=hull(collection,root,"Habitaculo",[(-.45,.14,.13,-.01),(-.15,.19,.16,.01),
            (.21,.18,.14,.02),(.45,.125,.11,.005),(.68,.045,.04,-.01)],hull_color)
        paint_faces(body,materials["dark"],lambda p,n:n.z<-.4)
        bridge=wing(collection,root,"Puente_transversal",[(-.53,.05,-.33,-.04,.063),
                    (.53,.05,-.33,-.04,.063)],materials["metal"])
        for side in (-1,1):
            pod=hull(collection,root,f"Gondola_{side}",[(-.58,.13,.12,-.025),
                (-.28,.145,.145,0),(.16,.13,.13,.005),(.43,.095,.095,-.005),
                (.57,.03,.045,-.015)],materials["armor"],side*.49)
            paint_faces(pod,mark,lambda p,n:n.z>.65)
            nozzle(collection,root,f"Reactor_{side}",side*.49,-.79,-.025,.125,materials)
            gun(collection,root,f"Arma_{side}",side*.49,.25,.08,materials,.42,.024)
            fin(collection,root,f"Estabilizador_{side}",side*.56,
                [(-.47,.09),(-.33,.31),(-.13,.28),(-.07,.11)],.016,materials["white"],side*.24)
            vents(collection,root,f"Radiador_{side}",side*.49,-.18,.147,.13,.23,materials,4)
            box(collection,root,f"Collarin_{side}",(side*.49,-.45,.115),(.20,.055,.035),materials["metal"])
        canopy(collection,root,"Cabina",0,.18,.15,.13,.48,.17,materials)
    paint_faces(body,materials["armor" if variant!=1 else "white"],
                lambda p,n:-.35<p.y<-.05 and n.z>.75)
    aft_bulkhead(collection,root,(-.56,-.55,-.45)[variant],(-.025,-.02,-.01)[variant],
                 (.13,.20,.14)[variant],(.105,.12,.13)[variant],materials)
    # Navigation marks have meaning and stay tiny against the painted armour.
    for side in (-1,1):
        x=side*(.72 if variant<2 else .60)
        box(collection,root,f"Navegacion_{side}",(x,-.31,.085),(.025,.035,.015),
            materials["nav_red" if side<0 else "nav_green"],.12)
    return root


def build_enemy(collection,name,variant,materials):
    root=root_object(collection,name)
    if variant==0:
        body=hull(collection,root,"Fuselaje",[(-.31,.10,.095,-.005),(-.07,.145,.12,.005),
            (.17,.105,.10,.01),(.35,.06,.055,-.005),(.48,.012,.018,-.015)],materials["armor"])
        paint_faces(body,materials["dark"],lambda p,n:n.z<-.4)
        for side in (-1,1):
            blade=wing(collection,root,f"Ala_{side}",[(.09,.22,-.25,0,.042),
                (.28,.19,-.20,.012,.039),(.50,.13,-.035,.075,.024)],materials["white"],side)
            paint_faces(blade,materials["red"],lambda p,n:abs(p.x)>.26 and n.z>.35)
            hull(collection,root,f"Refuerzo_{side}",[(-.24,.054,.055,.008),
                (-.02,.065,.063,.02),(.18,.025,.033,.014)],materials["metal"],side*.21)
            gun(collection,root,f"Arma_{side}",side*.30,.09,.042,materials,.30,.019)
            fin(collection,root,f"Aleta_{side}",side*.16,
                [(-.28,.055),(-.17,.21),(-.03,.20),(.05,.07)],.012,materials["dark"],side*.25)
            vents(collection,root,f"Rejilla_{side}",side*.115,-.085,.123,.045,.13,materials,2)
        canopy(collection,root,"Sensor",0,.17,.096,.062,.20,.09,materials)
        nozzle(collection,root,"Reactor",0,-.47,-.015,.105,materials,True,24)
    else:
        hull(collection,root,"Habitaculo",[(-.27,.135,.12,.005),(-.02,.16,.15,.015),
             (.25,.12,.11,.02),(.43,.055,.035,-.005)],materials["white"])
        wing(collection,root,"Travesano",[(-.50,.04,-.15,-.015,.042),
             (.50,.04,-.15,-.015,.042)],materials["metal"])
        for side in (-1,1):
            pod=cylinder(collection,root,f"Gondola_{side}",[(-.30,.098,.12,-.025),
                (-.11,.115,.145,-.005),(.16,.10,.12,-.005),(.29,.055,.075,-.015)],
                materials["armor"],side*.255,24,False)
            paint_faces(pod,materials["red"],lambda p,n:p.y>.05 and n.z>.5)
            nozzle(collection,root,f"Reactor_{side}",side*.255,-.475,-.035,.097,materials,True,24)
            weapon=hull(collection,root,f"Contenedor_{side}",[(-.06,.045,.045,-.155),
                 (.18,.045,.045,-.155),(.31,.018,.025,-.145)],materials["dark"],side*.15)
            wing(collection,root,f"Ala_{side}",[(.34,.08,-.13,-.02,.04),
                 (.51,.055,-.07,.02,.023)],materials["white"],side)
            vents(collection,root,f"Radiador_{side}",side*.255,-.06,.145,.12,.18,materials,3)
            gun(collection,root,f"Arma_{side}",side*.16,.14,.09,materials,.25,.020)
        canopy(collection,root,"Cabina",0,.18,.13,.085,.26,.11,materials)
    return face_enemies(root)


def build_boss(collection,name,materials):
    root=root_object(collection,name)
    central=hull(collection,root,"Quilla",[(-.72,.24,.17,-.035),(-.44,.42,.23,0),
        (.12,.43,.23,.015),(.57,.28,.15,.015),(.94,.07,.045,-.04)],materials["armor"])
    paint_faces(central,materials["dark"],lambda p,n:n.z<-.4)
    for side in (-1,1):
        bridge=wing(collection,root,f"Estructura_{side}",[(.27,.28,-.46,-.015,.11),
           (.70,.41,-.55,.03,.12),(1.23,.12,-.34,.08,.07)],materials["metal"],side)
        pod=hull(collection,root,f"Casco_lateral_{side}",[(-.62,.22,.19,0),
             (-.22,.30,.245,.035),(.22,.25,.21,.04),(.63,.12,.10,-.005)],
             materials["white"],side*.80)
        paint_faces(pod,materials["red"],lambda p,n:p.y>.2 and n.z>.45)
        nozzle(collection,root,f"Reactor_{side}",side*.80,-.84,-.015,.21,materials,True,24)
        cylinder(collection,root,f"Torreta_{side}",[(-.01,.095,.095,.25),
                 (.11,.095,.095,.25)],materials["metal"],side*.52,16,False)
        gun(collection,root,f"Bateria_{side}",side*.52,.12,.28,materials,.61,.045)
        vents(collection,root,f"Radiadores_{side}",side*.80,-.12,.272,.28,.38,materials,4)
        fin(collection,root,f"Aleta_reactor_{side}",side*.91,
             [(-.57,.15),(-.43,.40),(-.18,.38),(-.09,.18)],.022,materials["dark"],side*.15)
    nozzle(collection,root,"Reactor_central",0,-.92,-.055,.18,materials,True,24)
    hull(collection,root,"Puente",[(-.19,.17,.075,.30),(.08,.20,.10,.325),
         (.35,.135,.065,.30)],materials["white"])
    box(collection,root,"Ventanal_puente",(0,.353,.327),(.21,.018,.057),materials["cockpit"])
    box(collection,root,"Luz_puente",(0,.367,.300),(.17,.010,.012),materials["window"])
    beam(collection,root,"Mastil",(0,-.10,.37),(0,-.16,.49),.026,.026,materials["metal"])
    box(collection,root,"Sensor",(0,-.16,.49),(.13,.07,.03),materials["dark"])
    return face_enemies(root)


def color_variant(base,name,color,emission=(0,0,0)):
    mat=base.copy()
    mat.name=name
    mat.diffuse_color=(*color,1)
    shader=mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value=(*color,1)
    shader.inputs["Emission Color"].default_value=(*emission,1)
    shader.inputs["Emission Strength"].default_value=1
    mat["emission_color"]=list(emission)
    return mat


def asteroid(collection,root,name,center,scale,material,seed,detail=2):
    randomizer=random.Random(seed)
    topology=bmesh.new()
    bmesh.ops.create_icosphere(topology,subdivisions=detail,radius=1)
    topology.verts.index_update()
    dents=[(Vector((randomizer.uniform(-1,1),randomizer.uniform(-1,1),randomizer.uniform(-1,1))).normalized(),
            randomizer.uniform(.10,.17)) for unused in range(3)]
    vertices=[]
    for vertex in topology.verts:
        direction=vertex.co.normalized()
        dent=sum(depth*max(0,(direction.dot(axis)-.83)/.17)**2 for axis,depth in dents)
        factor=randomizer.uniform(.86,1.06)-dent
        vertices.append(tuple(center[k]+direction[k]*scale[k]*factor for k in range(3)))
    faces=[tuple(vertex.index for vertex in face.verts) for face in topology.faces]
    topology.free()
    return piece(collection,root,name,vertices,faces,material)


def planet_patch(collection,root,name,center,radius,longitude,latitude,rx,rz,material,seed,steps=48,rings=5):
    """A closed curved continent: continuous coastline instead of face colours."""
    outline=[]
    for index in range(steps):
        angle=index*math.tau/steps
        variation=1+.19*math.sin(3*angle+seed)+.11*math.cos(5*angle-seed)
        outline.append((rx*math.cos(angle)*variation,rz*math.sin(angle)*variation))
    def spherical(lon,lat,r):
        return Vector((math.cos(lat)*math.sin(lon),-math.cos(lat)*math.cos(lon),math.sin(lat)))*r+center
    positions=[spherical(longitude,latitude,radius)]
    for ring in range(1,rings+1):
        factor=ring/rings
        positions += [spherical(longitude+dx*factor,latitude+dz*factor,radius) for dx,dz in outline]
    count=len(positions)
    vertices=[tuple(point) for point in positions]
    vertices += [tuple(center+(point-center).normalized()*(radius-.22)) for point in positions]
    top=[]
    for index in range(steps):
        nxt=(index+1)%steps
        top.append((0,1+index,1+nxt))
    for ring in range(rings-1):
        first=1+ring*steps
        following=first+steps
        for index in range(steps):
            nxt=(index+1)%steps
            top.append((first+index,following+index,following+nxt,first+nxt))
    faces=list(top)+[tuple(count+index for index in reversed(face)) for face in top]
    edge=1+(rings-1)*steps
    for index in range(steps):
        nxt=(index+1)%steps
        faces.append((edge+index,edge+nxt,count+edge+nxt,count+edge+index))
    obj=piece(collection,root,name,vertices,faces,material,True)
    # The two spherical surfaces use radial normals; the thin coastline keeps
    # its own side normals, preventing dark seams from smooth wall averaging.
    normals=[(0,0,0)]*len(obj.data.loops)
    for face in obj.data.polygons:
        upper=all(index<count for index in face.vertices)
        lower=all(index>=count for index in face.vertices)
        for loop_index in face.loop_indices:
            vertex=obj.data.vertices[obj.data.loops[loop_index].vertex_index]
            normal=(vertex.co-center).normalized()
            normals[loop_index]=tuple(normal if upper else -normal if lower else face.normal)
    obj.data.normals_split_custom_set(normals)
    return obj


def planet(collection,root,materials):
    center=Vector((-35,92,20))
    radius=22.5
    topology=bmesh.new()
    bmesh.ops.create_uvsphere(topology,u_segments=64,v_segments=32,radius=radius)
    topology.verts.index_update()
    vertices=[tuple(vertex.co+center) for vertex in topology.verts]
    faces=[tuple(vertex.index for vertex in face.verts) for face in topology.faces]
    topology.free()
    ocean=color_variant(materials["planet"],"Mundo_oceano",(.035,.095,.13))
    land=color_variant(materials["planet"],"Mundo_tierra",(.135,.17,.125))
    obj=piece(collection,root,"Planeta",vertices,faces,ocean,True)
    for index,(lon,lat,rx,rz,seed) in enumerate(((.35,.20,.43,.62,.5),
             (-.64,-.30,.34,.48,2.0),(1.20,-.34,.27,.37,4.4))):
        # Extra clearance keeps the chords of the curved triangles outside
        # the ocean. The bottom stays embedded in the underlying sphere.
        planet_patch(collection,root,f"Continente_{index}",center,radius+.15,
                     lon,lat,rx,rz,land,seed)
    return obj

def shipyard_background_materials(objects,factor=.60):
    """Separate background paint/specular from materials shared with spacecraft."""
    copies={}
    for obj in objects:
        if obj.type!="MESH":
            continue
        obj["role"]="astillero"
        for index,base in enumerate(obj.data.materials):
            if base.name.startswith("Astillero_"):
                continue
            if base.name not in copies:
                mat=base.copy()
                mat.name="Astillero_"+base.name
                color=tuple(value*factor for value in base.diffuse_color[:3])
                mat.diffuse_color=(*color,1)
                mat["phong_specular"]=float(base.get("phong_specular",.35))*factor
                shader=mat.node_tree.nodes.get("Principled BSDF")
                shader.inputs["Base Color"].default_value=(*color,1)
                specular=shader.inputs.get("Specular IOR Level")
                if specular:
                    specular.default_value*=factor
                copies[base.name]=mat
            obj.data.materials[index]=copies[base.name]


def build_space(collection,materials):
    root=root_object(collection,"escenario_orbital")
    root["role"]="Astillero industrial y planeta fuera del corredor de combate"
    planet(collection,root,materials)
    previous=set(root.children)
    # Two main docks and a service spine establish a large, purposeful silhouette.
    for index,x in enumerate((20.5,29.0)):
        hull(collection,root,f"Viga_dique_{index}",[(25,.55,.65,-1.5),(29,.90,.80,-1.5),
            (62,.90,.80,-1.5),(73,.48,.55,-1.5)],materials["station"],x)
        for number,y in enumerate((31,57)):
            beam(collection,root,f"Pilar_{index}_{number}",(x,y,-3),(x+.5,y+1,9.8),
                 1.05,1.10,materials["armor"])
            box(collection,root,f"Base_{index}_{number}",(x,y,-3),(2.3,3.8,2),materials["station"])
    beam(collection,root,"Puente_superior",(20.5,59,10.5),(30,59,10.5),1.30,1.45,materials["white"])
    beam(collection,root,"Espina_servicio",(29.5,27,9.8),(29.5,70,9.8),1.55,1.65,materials["station"])
    beam(collection,root,"Grúa_brazo",(29,44,10),(23.5,43,17),.60,.65,materials["metal"])
    beam(collection,root,"Grúa_pluma",(23.5,43,17),(15.5,42,16.1),.55,.65,materials["armor"])
    beam(collection,root,"Grúa_cable",(17.5,42,16.1),(17.5,42,9.6),.075,.075,materials["dark"])
    box(collection,root,"Grúa_pinza",(17.5,42,9.4),(1.0,.8,.6),materials["red"])
    for number,y in enumerate((35,53,67)):
        box(collection,root,f"Modulo_taller_{number}",(31.5,y,4.4),(5.5,7.5,5.4),materials["station"])
        box(collection,root,f"Blindaje_taller_{number}",(31.5,y,7.2),(5.0,7.0,.45),materials["armor"])
        # The dark inset is physically backed by a solid bulkhead.
        box(collection,root,f"Compuerta_{number}",(28.70,y,4.2),(.20,5.4,3.1),materials["dark"])
        box(collection,root,f"Luz_compuerta_{number}",(28.56,y,5.65),(.06,4.4,.10),materials["window"])
    beam(collection,root,"Conducto_oblicuo",(21,31,8.0),(29,57,10),.36,.42,materials["metal"])
    shipyard_background_materials([obj for obj in root.children if obj not in previous])
    # A derelict transport below-left supplies a separate distant scale reference.
    hull(collection,root,"Carguero_quilla",[(78,1.4,1.2,-12),(82,2.2,1.7,-12),
         (98,2.2,1.7,-12),(106,.9,.8,-12)],materials["station"],-24)
    for index,y in enumerate((83,91,99)):
        box(collection,root,f"Contenedor_carguero_{index}",(-24,y,-11),(6.1,6.2,3.7),
             materials["armor" if index!=1 else "red"])
        box(collection,root,f"Refuerzo_carga_{index}",(-24,y,-8.95),(6.3,.5,.30),materials["metal"])
    hull(collection,root,"Carguero_puente",[(77,.8,.5,-8.9),(80,1.6,1.0,-8.4),
         (83,1.5,.8,-8.6)],materials["white"],-24)
    box(collection,root,"Carguero_ventana",(-24,76.95,-8.65),(1.2,.12,.25),materials["window"])
    beam(collection,root,"Restos_aleta",(-29,96,-12),(-32,104,-15),.48,1.4,materials["metal"])
    locations=[(-18,11,-7),(17,21,-9),(-25,34,12),(19,53,-6),
               (-19,66,1),(34,71,17),(-31,51,-9),(16,65,17)]
    for index,position in enumerate(locations):
        asteroid(collection,root,f"Roca_{index}",position,
                 (1.0+index%2*.6,1.3+index%3*.25,.9+index%3*.3),materials["rock"],70+index)
    return root


def build_obstacle(collection,materials):
    root=root_object(collection,"obstaculo_asteroide")
    rock=asteroid(collection,root,"Fragmento",(0,0,0),(.94,.97,.90),materials["obstacle"],185,3)
    pale=color_variant(materials["obstacle"],"Mineral_claro",(.38,.35,.29))
    dark=color_variant(materials["obstacle"],"Mineral_oscuro",(.26,.255,.235))
    paint_faces(rock,pale,lambda p,n:math.sin(p.x*4+p.z*3)>.65)
    paint_faces(rock,dark,lambda p,n:p.z<-.22 and p.y>.1)
    return root


def build_cockpit(collection,materials):
    root=root_object(collection,"cockpit_marco")
    root["role"]="Cabina fisica de marcos biselados, visión frontal despejada"
    # Console top is inclined towards the seated pilot, below the threat area.
    outline=[(-.82,1.02),(.82,1.02),(.69,1.65),(-.69,1.65)]
    vertices=[(x,y,z) for z in (-.69,-.41) for x,y in outline]
    for index in (4,5):
        vertices[index]=(vertices[index][0],vertices[index][1],-.58)
    piece(collection,root,"Consola",vertices,
          [(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],materials["dark"])
    for side in (-1,1):
        points=[(side*.86,.60,-.65),(side*.97,1.15,.22),(side*.92,1.65,.85)]
        for index in range(2):
            beam(collection,root,f"Marco_{side}_{index}",points[index],points[index+1],
                 .038,.050,materials["metal"])
        box(collection,root,f"Union_{side}",points[1],(.055,.06,.065),materials["dark"])
        # Glazed display faces and machined bezels are real solids, not an overlay.
        x=side*.35
        box(collection,root,f"Bisel_{side}",(x,1.50,-.415),(.42,.11,.18),materials["metal"])
        box(collection,root,f"Instrumento_{side}",(x,1.438,-.405),(.365,.014,.128),materials["cockpit"])
        box(collection,root,f"Mando_base_{side}",(side*.59,1.25,-.50),(.12,.11,.04),materials["armor"])
        beam(collection,root,f"Mando_{side}",(side*.59,1.25,-.49),(side*.59,1.28,-.425),
             .032,.034,materials["metal"])
    box(collection,root,"Bisel_central",(0,1.50,-.43),(.17,.12,.13),materials["dark"])
    box(collection,root,"Indicador_central",(0,1.432,-.425),(.095,.009,.065),materials["cockpit"])
    return root
