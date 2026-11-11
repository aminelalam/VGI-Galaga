"""Closed polygon models for Galaga's three-dimensional flight scene.

The mesh pieces share positions along their edges. Curved bodies use smooth
normals, while armour plates and wing edges retain flat polygon normals.
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


def loft(collection, root, name, sections, material, segments=24):
    """Elliptic cross-sections described by Y, X radius, Z radius, centre Z."""
    vertices = []
    for y, radius_x, radius_z, z in sections:
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            vertices.append((radius_x * math.cos(angle), y, z + radius_z * math.sin(angle)))
    faces = [tuple(reversed(range(segments)))]
    for ring in range(len(sections) - 1):
        for i in range(segments):
            j = (i + 1) % segments
            faces.append((ring * segments + i, ring * segments + j,
                          (ring + 1) * segments + j, (ring + 1) * segments + i))
    faces.append(tuple((len(sections) - 1) * segments + i for i in range(segments)))
    return piece(collection, root, name, vertices, faces, material, True)


def ellipsoid(collection, root, name, center, radii, material, segments=24, rings=12):
    topology = bmesh.new()
    bmesh.ops.create_uvsphere(topology, u_segments=segments, v_segments=rings, radius=1)
    vertices = [tuple(center[k] + radii[k] * vertex.co[k] for k in range(3)) for vertex in topology.verts]
    topology.verts.index_update()
    faces = [tuple(vertex.index for vertex in face.verts) for face in topology.faces]
    topology.free()
    return piece(collection, root, name, vertices, faces, material, True)


def plate(collection, root, name, outline, bottom, top, material):
    count = len(outline)
    vertices = [(x, y, bottom) for x, y in outline] + [(x, y, top) for x, y in outline]
    faces = [tuple(reversed(range(count))), tuple(range(count, 2 * count))]
    for i in range(count):
        j = (i + 1) % count
        faces.append((i, j, j + count, i + count))
    return piece(collection, root, name, vertices, faces, material)


def wing(collection, root, name, sections, material, side=1):
    """Airfoil rings along the span give wings a rounded leading edge and depth."""
    vertices = []
    segments = 12
    for x, leading, trailing, z, thickness in sections:
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            y = (leading + trailing) * .5 + (leading - trailing) * .5 * math.cos(angle)
            vertices.append((side * x, y, z + thickness * math.sin(angle)))
    faces = [tuple(reversed(range(segments)))]
    for section in range(len(sections) - 1):
        for i in range(segments):
            j = (i + 1) % segments
            faces.append((section * segments + i, section * segments + j,
                          (section + 1) * segments + j, (section + 1) * segments + i))
    faces.append(tuple((len(sections) - 1) * segments + i for i in range(segments)))
    return piece(collection, root, name, vertices, faces, material)


def wing_panel(collection, root, name, outline, sections, material):
    """A small closed armour patch follows the wing profile instead of floating."""
    def surface(x, y):
        x = abs(x)
        for first, second in zip(sections, sections[1:]):
            if x <= second[0]:
                factor = max(0, min(1, (x - first[0]) / (second[0] - first[0])))
                leading, trailing, z, thickness = [first[k] + factor*(second[k]-first[k]) for k in range(1,5)]
                normalized = max(-1, min(1, (2*y-leading-trailing) / (leading-trailing)))
                return z + thickness*math.sqrt(1-normalized*normalized)
        return sections[-1][3]
    points = list(outline)
    points.append((sum(point[0] for point in outline)/len(outline),
                   sum(point[1] for point in outline)/len(outline)))
    count = len(outline)
    layer = count+1
    vertices = [(x,y,surface(x,y)+offset) for offset in (.002,.013) for x,y in points]
    faces=[]
    for index in range(count):
        following=(index+1)%count
        faces.extend([(count,following,index),(layer+count,layer+index,layer+following),
                      (index,following,layer+following,layer+index)])
    return piece(collection,root,name,vertices,faces,material)


def fin(collection, root, name, x, profile, thickness, material):
    count = len(profile)
    vertices = [(x - thickness, y, z) for y, z in profile]
    vertices += [(x + thickness, y, z) for y, z in profile]
    faces = [tuple(reversed(range(count))), tuple(range(count, 2 * count))]
    for i in range(count):
        j = (i + 1) % count
        faces.append((i, j, j + count, i + count))
    return piece(collection, root, name, vertices, faces, material)


def nozzle(collection, root, name, x, y, z, radius, materials):
    segments = 24
    profile = [(y + .20, radius * .76), (y, radius),
               (y, radius * .68), (y + .16, radius * .48)]
    vertices = []
    for depth, r in profile:
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            vertices.append((x + r * math.cos(angle), depth, z + r * math.sin(angle)))
    faces = []
    for ring in range(4):
        following = (ring + 1) % 4
        for i in range(segments):
            j = (i + 1) % segments
            faces.append((ring * segments + i, ring * segments + j,
                          following * segments + j, following * segments + i))
    piece(collection, root, name + "_tobera", vertices, faces, materials["metal"], True)
    core = loft(collection, root, name + "_nucleo",
                [(y + .15, radius * .46, radius * .46, z),
                 (y + .17, radius * .46, radius * .46, z)], materials["engine"], 24)
    core.location.x = x
    for side in (-1, 1):
        rib = plate(collection, root, name + f"_aleta_{side}",
                    [(x + side * radius * .76, y + .08), (x + side * radius * 1.09, y + .03),
                     (x + side * radius * .96, y + .16)], z - .012, z + .012, materials["dark"])


def tube(collection, root, name, points, radius, material, segments=12, transport_frame=False):
    vertices = []
    direction = (Vector(points[-1])-Vector(points[0])).normalized()
    axes = (Vector((1,0,0)), Vector((0,1,0)), Vector((0,0,1)))
    reference = min(axes, key=lambda axis: abs(direction.dot(axis)))
    previous_u = None
    for index, point in enumerate(points):
        previous = Vector(points[max(0, index - 1)])
        following = Vector(points[min(len(points) - 1, index + 1)])
        tangent = (following - previous).normalized()
        if transport_frame:
            # Keep cockpit rings continuous even when the tangent crosses Z.
            u = tangent.cross(reference) if previous_u is None else previous_u-tangent*previous_u.dot(tangent)
            if u.length < 1e-6:
                reference = min(axes, key=lambda axis: abs(tangent.dot(axis)))
                u = tangent.cross(reference)
            u.normalize()
            if previous_u is not None and u.dot(previous_u) < 0:
                u.negate()
        else:
            reference = Vector((0,0,1)) if abs(tangent.z)<.9 else Vector((0,1,0))
            u = tangent.cross(reference).normalized()
        v = tangent.cross(u).normalized()
        previous_u = u.copy()
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            vertices.append(tuple(Vector(point) + radius * (math.cos(angle) * u + math.sin(angle) * v)))
    faces = [tuple(reversed(range(segments)))]
    for ring in range(len(points) - 1):
        for i in range(segments):
            j = (i + 1) % segments
            faces.append((ring * segments + i, ring * segments + j,
                          (ring + 1) * segments + j, (ring + 1) * segments + i))
    faces.append(tuple((len(points) - 1) * segments + i for i in range(segments)))
    return piece(collection, root, name, vertices, faces, material, True)


def canopy(collection, root, center, radii, materials):
    frame_center = (center[0], center[1], center[2] - .015)
    ellipsoid(collection, root, "Marco_cabina", frame_center,
              (radii[0] * 1.13, radii[1] * 1.04, radii[2]), materials["dark"])
    ellipsoid(collection, root, "Cristal_cabina", center, radii, materials["cockpit"])
    tube(collection, root, "Arco_cabina", [
        (center[0] - radii[0], center[1] - .07, center[2]),
        (center[0] - radii[0] * .7, center[1] - .07, center[2] + radii[2] * .72),
        (center[0], center[1] - .07, center[2] + radii[2] * 1.02),
        (center[0] + radii[0] * .7, center[1] - .07, center[2] + radii[2] * .72),
        (center[0] + radii[0], center[1] - .07, center[2])], .009, materials["metal"], 8)


def build_ship(collection, name, variant, materials):
    root = root_object(collection, name)
    primary = materials[("blue", "red", "green")[variant]]
    if variant == 0:
        loft(collection, root, "Fuselaje", [
            (-.52, .11, .10, -.01), (-.35, .17, .13, .01), (-.10, .18, .14, .03),
            (.14, .14, .13, .04), (.39, .095, .09, .025), (.64, .043, .045, .015),
            (.79, .006, .008, .01)], primary)
        for side in (-1, 1):
            sections = [(.11, .29, -.40, -.01, .058),
                 (.30, .11, -.43, -.025, .041), (.48, -.08, -.43, -.005, .03),
                 (.64, -.24, -.38, .055, .018)]
            wing(collection, root, f"Ala_{side}", sections, materials["white"], side)
            wing_panel(collection, root, f"Panel_rojo_{side}",
                  [(side * .32, -.03), (side * .51, -.22), (side * .53, -.30),
                   (side * .34, -.17)], sections, materials["red"])
            housing = loft(collection, root, f"Carena_motor_{side}", [
                (-.51, .069, .068, -.045), (-.35, .088, .082, -.035),
                (-.17, .066, .063, -.025), (-.09, .018, .025, -.015)], primary)
            housing.location.x = side * .28
            nozzle(collection, root, f"Motor_{side}", side * .28, -.68, -.045, .084, materials)
            tube(collection, root, f"Canon_{side}", [(side * .52, -.29, .06),
                 (side * .52, .02, .06)], .021, materials["metal"])
            fin(collection, root, f"Estabilizador_{side}", side * .53,
                [(-.37, .055), (-.24, .23), (-.12, .22), (-.21, .055)], .014, primary)
        canopy(collection, root, (0, .03, .185), (.097, .245, .115), materials)
        fin(collection, root, "Timon", 0, [(-.45, .07), (-.38, .38),
            (-.24, .40), (-.10, .12)], .021, materials["white"])
    elif variant == 1:
        loft(collection, root, "Fuselaje", [(-.50, .15, .12, -.015), (-.30, .21, .14, .015),
             (0, .19, .15, .04), (.31, .12, .11, .04), (.57, .063, .06, .02),
             (.74, .009, .01, .005)], primary)
        for side in (-1, 1):
            sections = [(.13, .48, -.48, -.015, .065),
                 (.31, .22, -.52, -.035, .052), (.49, -.10, -.52, -.01, .037),
                 (.64, -.35, -.48, .055, .02)]
            wing(collection, root, f"Ala_delta_{side}", sections, primary, side)
            wing_panel(collection, root, f"Panel_blanco_{side}",
                  [(side * .23, .13), (side * .48, -.30), (side * .54, -.42),
                   (side * .30, -.33)], sections, materials["white"])
            nozzle(collection, root, f"Motor_{side}", side * .235, -.68, -.07, .095, materials)
            fin(collection, root, f"Timon_{side}", side * .15,
                [(-.46, .09), (-.37, .36), (-.23, .35), (-.09, .12)], .014, materials["dark"])
            tube(collection, root, f"Canon_{side}", [(side * .44, -.31, .065),
                 (side * .44, .04, .065)], .022, materials["metal"])
        canopy(collection, root, (0, .075, .195), (.10, .23, .11), materials)
    else:
        loft(collection, root, "Cabina_central", [(-.46, .13, .11, 0), (-.20, .16, .14, .02),
             (.11, .16, .14, .025), (.38, .13, .115, .015), (.59, .065, .075, .01),
             (.66, .015, .02, 0)], materials["white"])
        plate(collection, root, "Travesano", [(-.51, -.30), (.51, -.30),
              (.51, .01), (-.51, .01)], -.13, -.035, materials["metal"])
        for side in (-1, 1):
            pod = loft(collection, root, f"Barquilla_{side}", [(-.48, .105, .12, -.025),
                 (-.28, .125, .14, 0), (.10, .12, .14, .01), (.37, .10, .115, .015),
                 (.54, .065, .07, .015), (.60, .018, .025, .01)], primary)
            pod.location.x = side * .40
            pod.data.materials.append(materials["white"])
            for face in pod.data.polygons:
                if abs(face.center.x) < .035 and face.normal.z > .80:
                    face.material_index = 1
            nozzle(collection, root, f"Motor_{side}", side * .40, -.69, -.025, .11, materials)
            for rib, y in enumerate((-.27, -.16, -.05)):
                tube(collection, root, f"Refrigerador_{side}_{rib}",
                     [(side * .50, y, -.065), (side * .50, y, .075)], .014, materials["dark"], 8)
            fin(collection, root, f"Aleta_{side}", side * .46,
                [(-.37, .10), (-.31, .29), (-.10, .28), (-.12, .12)], .018, primary)
        canopy(collection, root, (0, .13, .19), (.105, .22, .115), materials)
    return root


def build_enemy(collection, name, variant, materials):
    root = root_object(collection, name)
    body = materials["yellow" if variant == 0 else "green"]
    wings = materials["red" if variant == 0 else "purple"]
    sections = [(-.39, .04, .07, -.01), (-.29, .15, .13, 0),
                (-.06, .21, .18, .02), (.15, .19, .17, .02), (.29, .11, .12, .015)]
    for y in (-.24, -.19, -.09, -.03):
        for first,second in zip(sections,sections[1:]):
            if first[0] < y < second[0]:
                factor = (y-first[0])/(second[0]-first[0])
                sections.append(tuple([y]+[first[k]+factor*(second[k]-first[k]) for k in range(1,4)]))
                sections.sort(key=lambda section: section[0])
                break
    abdomen = loft(collection, root, "Abdomen", sections, body)
    abdomen.data.materials.append(materials["dark"])
    for face in abdomen.data.polygons:
        if -.24 < face.center.y < -.19 or -.09 < face.center.y < -.03:
            face.material_index = 1
    ellipsoid(collection, root, "Cabeza", (0, .27, .035), (.18, .17, .16), body)
    for side in (-1, 1):
        ellipsoid(collection, root, f"Ojo_{side}", (side * .102, .389, .10),
                  (.067, .033, .065), materials["dark"], 16, 8)
        ellipsoid(collection, root, f"Pupila_{side}", (side * .102, .418, .10),
                  (.048, .014, .025), materials["engine"], 16, 8)
        ellipsoid(collection, root, f"Articulacion_{side}", (side * .23, .01, -.01),
                  (.09, .10, .085), materials["metal"], 16, 8)
        sections = [(.20, .15, -.24, .0, .06),
             (.37, .20, -.34, .065, .065), (.58, .06, -.28, .10, .03)]
        wing(collection, root, f"Ala_{side}", sections, wings, side)
        if variant == 0:
            wing_panel(collection, root, f"Armadura_{side}", [(side * .28, .08), (side * .48, .03),
                  (side * .48, -.12), (side * .32, -.08)], sections, body)
            tube(collection, root, f"Mandibula_{side}", [(side * .16, .25, -.05),
                 (side * .24, .41, -.045), (side * .18, .52, -.01)], .035, materials["metal"])
        else:
            tube(collection, root, f"Cuerno_{side}", [(side * .27, .02, .04),
                 (side * .40, .22, .13), (side * .34, .46, .13),
                 (side * .24, .54, .055)], .049, wings)
        nozzle(collection, root, f"Propulsor_{side}", side * .11, -.48, -.045, .056, materials)
    rotation = Matrix.Rotation(math.pi, 4, "Z")
    for part in root.children:
        part.data.transform(rotation @ part.matrix_basis)
        part.matrix_basis = Matrix.Identity(4)
        part.data.update()
    root["forward_axis"] = "-Y"
    return root


def build_boss(collection, name, materials):
    root = root_object(collection, name)
    loft(collection, root, "Torax", [(-.62, .17, .17, -.02), (-.39, .39, .28, 0),
         (.0, .46, .34, .03), (.35, .37, .29, .04), (.63, .18, .17, .01)], materials["dark"], 32)
    ellipsoid(collection, root, "Caparazon", (0, -.02, .13), (.40, .52, .28), materials["purple"], 32, 14)
    ellipsoid(collection, root, "Cabeza", (0, .48, .04), (.29, .26, .24), materials["metal"], 24, 12)
    for side in (-1, 1):
        ellipsoid(collection, root, f"Hombro_{side}", (side * .51, -.04, 0),
                  (.23, .26, .21), materials["metal"], 20, 10)
        sections = [(.39, .32, -.46, .045, .11),
             (.76, .48, -.55, .11, .13), (1.12, .35, -.44, .18, .11),
             (1.34, .11, -.29, .22, .045)]
        wing(collection, root, f"Acorazado_{side}", sections, materials["red"], side)
        wing_panel(collection, root, f"Placa_superior_{side}", [(side*.58,.19),(side*1.04,.25),
              (side*1.14,-.16),(side*.70,-.25)], sections, materials["metal"])
        tube(collection, root, f"Pinza_{side}", [(side*.37,.27,-.09),(side*.68,.53,-.08),
             (side*.65,.79,.01),(side*.47,.91,.11)], .075, materials["yellow"])
        tube(collection, root, f"Canon_{side}", [(side*.77,-.1,.10),(side*.77,.47,.10)],
             .095, materials["dark"], 20)
        ellipsoid(collection, root, f"Ojo_{side}", (side*.16,.69,.16),
                  (.09,.035,.08), materials["engine"], 20, 10)
        nozzle(collection, root, f"Motor_{side}", side * .58, -.73, -.04, .18, materials)
    nozzle(collection, root, "Motor_central", 0, -.75, -.08, .16, materials)
    rotation = Matrix.Rotation(math.pi, 4, "Z")
    for part in root.children:
        part.data.transform(rotation @ part.matrix_basis)
        part.matrix_basis = Matrix.Identity(4)
        part.data.update()
    root["forward_axis"] = "-Y"
    return root


def asteroid(collection, root, name, center, scale, material, seed):
    randomizer = random.Random(seed)
    topology = bmesh.new()
    bmesh.ops.create_icosphere(topology, subdivisions=2, radius=1)
    topology.verts.index_update()
    vertices = []
    for vertex in topology.verts:
        factor = randomizer.uniform(.80, 1.17)
        vertices.append(tuple(center[k] + vertex.co[k] * scale[k] * factor for k in range(3)))
    faces = [tuple(vertex.index for vertex in face.verts) for face in topology.faces]
    topology.free()
    return piece(collection, root, name, vertices, faces, material)


def torus(collection, root, name, center, major, minor, material, tilt=0, segments=64):
    vertices = []
    small_segments = 8
    rotation = Matrix.Rotation(tilt, 4, "Z")
    for ring in range(segments):
        a = math.tau * ring / segments
        for side in range(small_segments):
            b = math.tau * side / small_segments
            point = Vector(((major + minor * math.cos(b)) * math.cos(a),
                            minor * math.sin(b), (major + minor * math.cos(b)) * math.sin(a)))
            vertices.append(tuple(Vector(center) + rotation @ point))
    faces = []
    for ring in range(segments):
        next_ring = (ring + 1) % segments
        for side in range(small_segments):
            next_side = (side + 1) % small_segments
            faces.append((ring * small_segments + side, next_ring * small_segments + side,
                          next_ring * small_segments + next_side, ring * small_segments + next_side))
    return piece(collection, root, name, vertices, faces, material, True)


def build_space(collection, materials):
    root = root_object(collection, "escenario_orbital")
    root["role"] = "Sector espacial exterior al corredor de combate"
    planet = ellipsoid(collection, root, "Planeta", (-29, 78, 21), (18,18,18),
                       materials["planet"], 64, 32)
    # Close colour values make gradual gas bands instead of a coarse chequered map.
    for index in range(16):
        tone = index / 15
        band_material = materials["planet"].copy()
        band_material.name = f"planeta_banda_{index:02}"
        color = (.020+.045*tone, .08+.07*tone, .16+.08*tone, 1)
        band_material.diffuse_color = color
        band_material.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value = color
        planet.data.materials.append(band_material)
    for face in planet.data.polygons:
        center = face.center - Vector((-29,78,21))
        latitude = math.asin(max(-1,min(1,center.z/18)))
        band = .5 + .5*math.sin(latitude*7 + .35*math.sin(center.x*.15) + .15*math.sin(center.y*.1))
        face.material_index = 1+round(band*15)
    torus(collection, root, "Anillo_estacion", (23, 62, 6), 8.0, .34, materials["station"], .35)
    torus(collection, root, "Luz_anillo", (23, 61.84, 6), 7.66, .055, materials["signal"], .35)
    for index in range(8):
        angle = math.tau * index / 8
        center = Vector((23,62,6)) + Matrix.Rotation(.35, 4, "Z") @ Vector((7.8*math.cos(angle), 0, 7.8*math.sin(angle)))
        ellipsoid(collection, root, f"Modulo_estacion_{index}", center, (.7,1.2,.7),
                  materials["station"], 12, 6)
    placements = [(-16,4,-4), (18,12,7), (-22,25,11), (16,33,-5),
                  (-15,49,0), (25,53,13), (-31,62,-7), (19,72,-4),
                  (-18,18,-10), (30,40,2), (-25,40,17), (15,60,19)]
    for index, location in enumerate(placements):
        asteroid(collection, root, f"Asteroide_{index}", location,
                 (1.3+(index%3)*.5, 1.6+(index%2)*.6, 1.2+(index%4)*.3), materials["rock"], index+40)
    return root


def build_obstacle(collection, materials):
    root = root_object(collection, "obstaculo_asteroide")
    asteroid(collection, root, "Roca", (0,0,0), (.85, .88, .82), materials["obstacle"], 185)
    return root


def build_cockpit(collection, materials):
    root = root_object(collection, "cockpit_marco")
    root["role"] = "Cabina fisica con centro libre, orientada a +Y"
    plate(collection, root, "Consola", [(-.80,1.0),(.80,1.0),(.70,1.65),(-.70,1.65)],
          -.70, -.37, materials["dark"])
    plate(collection, root, "Tablero", [(-.73,1.12),(.73,1.12),(.64,1.56),(-.64,1.56)],
          -.37, -.355, materials["metal"])
    for side in (-1,1):
        tube(collection, root, f"Montante_{side}", [(side*.82,.48,-.65),
             (side*.96,.90,-.22),(side*.98,1.15,.35),(side*.90,1.40,.82)],
             .055, materials["metal"], 12, True)
        tube(collection, root, f"Guia_{side}", [(side*.82,.52,-.60),
             (side*.92,.91,-.22),(side*.94,1.15,.35)], .013, materials["signal"], 8, True)
        plate(collection, root, f"Panel_{side}", [(side*.13,1.24),(side*.55,1.24),
              (side*.48,1.50),(side*.13,1.50)], -.354, -.34, materials["cockpit"])
    plate(collection, root, "Panel_central", [(-.07,1.24),(.07,1.24),(.07,1.48),(-.07,1.48)],
          -.354, -.335, materials["engine"])
    return root
