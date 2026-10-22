"""Naves retro originales para las dos escenas de Galaga 3D.

Solo construye mallas: no cambia la escena activa, no usa operadores,
no incorpora animaciones y no guarda archivos. Cada modelo tiene un Empty
raiz; sus piezas conservan coordenadas locales y miran hacia +Y, con el
grosor en Z. Los tejados triangulados proporcionan volumen con shade flat.

Uso:
    nave = build_ship(coleccion, "Nave", 0, materiales, (0, -4, 0))
    enemigo = build_enemy(coleccion, "Abeja", 0, materiales)
    jefe = build_boss(coleccion, "Jefe", materiales)

Los materiales se suministran desde fuera. Claves utilizadas: white, blue,
red, yellow, green, purple, dark, cockpit, engine y metal.
"""

import math

import bpy


SHIP_NAMES = ("FLECHA", "DELTA", "DOBLEMOTOR")
ENEMY_NAMES = ("ABEJA", "ESCARABAJO")


def _check_materials(materials, names):
    missing = [name for name in names if name not in materials]
    if missing:
        raise KeyError("Faltan materiales del modelo: " + ", ".join(missing))


def _root(collection, name, model_type, variant, variant_name, location, scale):
    scale = float(scale)
    if not math.isfinite(scale) or scale <= 0:
        raise ValueError("La escala del modelo debe ser positiva y finita.")
    position = tuple(float(value) for value in location)
    if len(position) != 3 or not all(math.isfinite(value) for value in position):
        raise ValueError("La posicion del modelo debe tener tres valores finitos.")
    root = bpy.data.objects.new(name, None)
    collection.objects.link(root)
    root.empty_display_type = "PLAIN_AXES"
    root.empty_display_size = 0.25
    root.location = position
    root.scale = (scale, scale, scale)
    root["model_type"] = model_type
    root["variant"] = variant
    root["variant_name"] = variant_name
    root["forward_axis"] = "+Y"
    root["construction"] = "Mallas originales de pocas piezas; sombreado plano"
    return root


def _solid(collection, root, part, outline, bottom, eave, peak, material):
    """Prisma convexo cerrado, coronado por un tejado de caras inclinadas.

    outline contiene puntos XY. bottom es la base; eave el borde superior;
    peak la altura central del tejado. Las normales salen hacia fuera.
    No hay modificadores ni dependencias de seleccion o escena activa.
    """
    points = [(float(x), float(y)) for x, y in outline]
    if len(points) < 3 or not bottom < eave <= peak:
        raise ValueError("El solido necesita un contorno y alturas validos.")
    area = sum(
        points[i][0] * points[(i + 1) % len(points)][1]
        - points[(i + 1) % len(points)][0] * points[i][1]
        for i in range(len(points))
    )
    if abs(area) < 1e-8:
        raise ValueError("El contorno no puede tener area nula.")
    if area < 0:
        points.reverse()

    count = len(points)
    vertices = [(x, y, bottom) for x, y in points]
    vertices += [(x, y, eave) for x, y in points]
    vertices.append((sum(x for x, _ in points) / count,
                     sum(y for _, y in points) / count, peak))
    apex = 2 * count
    faces = [tuple(reversed(range(count)))]
    for index in range(count):
        following = (index + 1) % count
        faces.append((index, following, following + count, index + count))
        faces.append((index + count, following + count, apex))

    mesh = bpy.data.meshes.new(root.name + "__" + part + "_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(material)
    mesh.update()
    for polygon in mesh.polygons:
        polygon.use_smooth = False
    obj = bpy.data.objects.new(root.name + "__" + part, mesh)
    collection.objects.link(obj)
    obj.parent = root
    obj["part"] = part
    return obj


def _rectangle(xmin, xmax, ymin, ymax):
    return ((xmin, ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax))


def build_ship(collection, name, variant, materials, location=(0, 0, 0), scale=1.0):
    """Crea FLECHA=0, DELTA=1 o DOBLEMOTOR=2 y devuelve su Empty raiz.

    Limites locales de cualquier variante: x[-.85,.85], y[-.8,.9],
    z[-.25,.4]. El color y la silueta permiten distinguir las tres naves.
    """
    variant = int(variant)
    if variant not in range(3):
        raise ValueError("La variante de nave debe ser 0, 1 o 2.")
    hull_key = ("blue", "red", "green")[variant]
    _check_materials(materials, (hull_key, "white", "cockpit", "engine", "metal"))
    root = _root(collection, name, "player", variant, SHIP_NAMES[variant], location, scale)
    root["hull_material"] = hull_key
    hull = materials[hull_key]
    white, cockpit = materials["white"], materials["cockpit"]
    engine, metal = materials["engine"], materials["metal"]

    def part(label, points, bottom, eave, peak, material):
        return _solid(collection, root, label, points, bottom, eave, peak, material)

    if variant == 0:
        # Cuerpo largo, dos alas finas y dos pequenas salidas de motor.
        part("fuselaje", ((-.16, -.62), (.16, -.62), (.19, .16), (0, .90), (-.19, .16)),
             -.17, .12, .28, hull)
        part("ala_izquierda", ((-.13, .25), (-.85, -.48), (-.79, -.74), (-.13, -.42)),
             -.16, .015, .13, white)
        part("ala_derecha", ((.13, .25), (.85, -.48), (.79, -.74), (.13, -.42)),
             -.16, .015, .13, white)
        part("cabina", ((-.095, -.10), (.095, -.10), (.08, .28), (0, .53), (-.08, .28)),
             .17, .29, .37, cockpit)
        part("motor_izquierdo", _rectangle(-.56, -.37, -.78, -.52), -.14, .035, .075, engine)
        part("motor_derecho", _rectangle(.37, .56, -.78, -.52), -.14, .035, .075, engine)
    elif variant == 1:
        # Una ala delta ancha se reconoce incluso sin color o cabina.
        part("ala_delta", ((-.85, -.75), (.85, -.75), (0, .72)), -.20, .03, .15, hull)
        part("fuselaje", ((-.17, -.64), (.17, -.64), (.15, .34), (0, .88), (-.15, .34)),
             -.16, .16, .29, hull)
        part("cabina", ((-.105, -.12), (.105, -.12), (.09, .27), (0, .51), (-.09, .27)),
             .20, .31, .39, cockpit)
        part("panel_izquierdo", ((-.69, -.64), (-.35, -.64), (-.18, -.20)),
             .04, .08, .12, white)
        part("panel_derecho", ((.69, -.64), (.35, -.64), (.18, -.20)),
             .04, .08, .12, white)
        part("motor_izquierdo", _rectangle(-.37, -.18, -.80, -.65), -.15, .03, .07, engine)
        part("motor_derecho", _rectangle(.18, .37, -.80, -.65), -.15, .03, .07, engine)
    else:
        # Fuselaje rectangular y dos barquillas largas, sin alas en flecha.
        part("travesano", _rectangle(-.64, .64, -.26, .02), -.19, -.015, .055, metal)
        part("fuselaje", _rectangle(-.23, .23, -.61, .73), -.17, .15, .28, hull)
        part("barquilla_izquierda", ((-.76, -.76), (-.43, -.76), (-.43, .44), (-.52, .65), (-.67, .65), (-.76, .44)),
             -.23, .09, .24, hull)
        part("barquilla_derecha", ((.43, -.76), (.76, -.76), (.76, .44), (.67, .65), (.52, .65), (.43, .44)),
             -.23, .09, .24, hull)
        part("cabina", _rectangle(-.12, .12, -.03, .46), .19, .30, .39, cockpit)
        part("motor_izquierdo", _rectangle(-.70, -.49, -.80, -.66), -.15, .12, .16, engine)
        part("motor_derecho", _rectangle(.49, .70, -.80, -.66), -.15, .12, .16, engine)
    return root


def build_enemy(collection, name, kind, materials, location=(0, 0, 0), scale=1.0):
    """Crea ABEJA=0 (alas angulares) o ESCARABAJO=1 (dos cuernos)."""
    kind = int(kind)
    if kind not in range(2):
        raise ValueError("El tipo de enemigo debe ser 0 o 1.")
    _check_materials(materials, ("yellow", "red", "green", "purple", "dark"))
    root = _root(collection, name, "enemy", kind, ENEMY_NAMES[kind], location, scale)

    def part(label, points, bottom, eave, peak, key):
        return _solid(collection, root, label, points, bottom, eave, peak, materials[key])

    if kind == 0:
        part("cuerpo", ((-.23, -.45), (.23, -.45), (.27, .17), (0, .54), (-.27, .17)),
             -.18, .13, .28, "yellow")
        part("ala_izquierda", ((-.18, .35), (-.77, .53), (-.65, -.37), (-.26, -.23)),
             -.13, .035, .15, "red")
        part("ala_derecha", ((.18, .35), (.77, .53), (.65, -.37), (.26, -.23)),
             -.13, .035, .15, "red")
        part("visor", _rectangle(-.15, .15, .04, .24), .21, .30, .34, "dark")
    else:
        part("caparazon", ((-.30, -.48), (.30, -.48), (.40, -.10), (.28, .38), (-.28, .38), (-.40, -.10)),
             -.20, .13, .32, "green")
        part("cuerno_izquierdo", ((-.33, -.02), (-.77, .22), (-.55, .73), (-.38, .64)),
             -.13, .08, .23, "purple")
        part("cuerno_derecho", ((.33, -.02), (.77, .22), (.55, .73), (.38, .64)),
             -.13, .08, .23, "purple")
        part("visor", ((-.17, -.08), (.17, -.08), (.13, .15), (-.13, .15)),
             .27, .34, .38, "dark")
    return root


def build_boss(collection, name, materials, location=(0, 0, 0), scale=1.0):
    """Crea un jefe de cuatro unidades de ancho, con nucleo y alas macizas."""
    _check_materials(materials, ("purple", "red", "yellow", "dark", "engine"))
    root = _root(collection, name, "boss", 0, "ACORAZADO", location, scale)

    def part(label, points, bottom, eave, peak, key):
        return _solid(collection, root, label, points, bottom, eave, peak, materials[key])

    part("nucleo", ((-.67, -.57), (.67, -.57), (.78, .05), (.43, .70), (-.43, .70), (-.78, .05)),
         -.27, .24, .49, "purple")
    part("ala_izquierda", ((-.52, .25), (-1.73, .70), (-2.0, -.29), (-.88, -.58)),
         -.23, .08, .30, "red")
    part("ala_derecha", ((.52, .25), (1.73, .70), (2.0, -.29), (.88, -.58)),
         -.23, .08, .30, "red")
    part("visor", ((-.40, -.12), (.40, -.12), (.31, .20), (-.31, .20)),
         .31, .50, .57, "dark")
    part("proa", ((-.25, .29), (.25, .29), (0, .78)),
         .25, .39, .48, "yellow")
    part("motor_izquierdo", _rectangle(-1.46, -1.06, -.66, -.42), -.18, .04, .12, "engine")
    part("motor_derecho", _rectangle(1.06, 1.46, -.66, -.42), -.18, .04, .12, "engine")
    return root
