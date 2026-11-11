"""Build editable game models and export triangulated OBJ/MTL for EntornVGI.

blender --background --factory-startup --python this_file
blender --background Mallas_Galaga3D.blend --python this_file -- --export-only
"""
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

SCRIPTS = Path(__file__).resolve().parent
BASE = SCRIPTS.parent
OUTPUT = BASE / "modelos"
BLEND = BASE / "blender" / "Mallas_Galaga3D.blend"
sys.path.insert(0, str(SCRIPTS))
from retro_modelos import build_ship, build_enemy, build_boss
from retro_base import box


def material(name, color):
    result = bpy.data.materials.new(name)
    result.diffuse_color = (*color, 1)
    result.use_nodes = True
    shader = result.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Roughness"].default_value = .65
    return result


def setup_scene(scene, eye, target, orthographic=False):
    scene.world = bpy.data.worlds.new(scene.name + "_Fondo")
    scene.world.color = (.015, .015, .015)
    camera_data = bpy.data.cameras.new(scene.name + "_Camara")
    camera = bpy.data.objects.new(camera_data.name, camera_data)
    scene.collection.objects.link(camera)
    camera.location = eye
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera_data.angle = math.radians(62)
    if orthographic:
        camera_data.type = "ORTHO"
        camera_data.ortho_scale = 8.5
    scene.camera = camera
    light_data = bpy.data.lights.new(scene.name + "_Luz", "SUN")
    light_data.energy = 2
    light = bpy.data.objects.new(light_data.name, light_data)
    scene.collection.objects.link(light)
    light.rotation_euler = (math.radians(25), math.radians(-20), math.radians(-25))
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 24


def game_copy(root, collection, name, position, scale=1, pitch=0):
    instance = bpy.data.objects.new(name, None)
    collection.objects.link(instance)
    instance.location = position
    instance.scale = (scale,) * 3
    instance.rotation_euler.x = math.radians(pitch)
    for part in root.children:
        duplicate = part.copy()
        duplicate.data = part.data
        collection.objects.link(duplicate)
        duplicate.parent = instance
        duplicate.matrix_parent_inverse = Matrix.Identity(4)
        duplicate.matrix_basis = part.matrix_basis.copy()
    return instance


def build_library():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.filepaths.save_version = 0
    catalog = bpy.context.scene
    catalog.name = "01_Modelos"
    colors = {
        "white": (.94, .96, 1), "blue": (.13, .37, .96),
        "red": (.96, .12, .18), "yellow": (1, .79, .12),
        "green": (.26, .86, .37), "purple": (.64, .24, .89),
        "dark": (.025, .045, .09), "cockpit": (.24, .88, 1),
        "engine": (1, .46, .12), "metal": (.22, .28, .40),
    }
    materials = {name: material(name, color) for name, color in colors.items()}
    roots = []
    for index, name in enumerate(("nave_flecha", "nave_delta", "nave_doble_motor")):
        roots.append(build_ship(catalog.collection, name, index, materials))
    roots.append(build_enemy(catalog.collection, "enemigo_abeja", 0, materials))
    roots.append(build_enemy(catalog.collection, "enemigo_escarabajo", 1, materials))
    roots.append(build_boss(catalog.collection, "jefe_acorazado", materials))
    for index, root in enumerate(roots):
        factor = .275 if index == 5 else .70
        rotation = Matrix.Rotation(math.pi if index >= 3 else 0, 4, "Z")
        conversion = rotation @ Matrix.Scale(factor, 4)
        for part in root.children:
            part.data.transform(conversion)
            part.data.update()
        root.location = ((index % 3 - 1) * 2.4, 1.8 if index < 3 else -1.2, 0)
        root["export_obj"] = root.name + ".obj"
        root["forward_axis"] = "+Y" if index < 3 else "-Y"
    setup_scene(catalog, (4, -7, 10), (0, .3, 0), True)

    arena = bpy.data.scenes.new("02_Escenario")
    stage = bpy.data.objects.new("escenario_orbital", None)
    arena.collection.objects.link(stage)
    stage["export_obj"] = "escenario_orbital.obj"
    stage["role"] = "Decoracion fuera del espacio de vuelo"
    deck = material("cubierta", (.045, .05, .06))
    edge = material("borde", (.10, .115, .13))
    seam = material("junta", (.022, .026, .032))
    signal = material("baliza", (.32, .23, .10))
    box(arena.collection, "Plataforma", (0, 16, -5.9), (23, 42, .5), deck, stage)
    for side in (-1, 1):
        box(arena.collection, f"Borde_{side}", (side * 11.3, 16, -5.45), (.4, 42, .4), edge, stage)
        for row, y in enumerate((1, 11, 21, 31)):
            box(arena.collection, f"Pilar_{side}_{row}", (side * 10.7, y, -4.1), (.65, .85, 3.1), edge, stage)
            box(arena.collection, f"Baliza_{side}_{row}", (side * 10.7, y, -2.51), (.5, .65, .08), signal, stage)
            box(arena.collection, f"Marca_{side}_{row}", (side * 8.9, y, -5.635), (.1, 2.2, .025), signal, stage)
    for row, y in enumerate((1, 7, 13, 19, 25, 31)):
        box(arena.collection, f"Junta_{row}", (0, y, -5.635), (21, .08, .025), seam, stage)
    game_copy(roots[0], arena.collection, "Jugador", (0, -4, 0))
    for row in range(3):
        for column in range(6):
            enemy = roots[4 if row == 2 else 3]
            game_copy(enemy, arena.collection, f"Enemigo_{row}_{column}",
                      ((column - 2.5) * 2.6, 14 + 4 * row, -2.5 + 2.5 * row), 1.45, 35)
    setup_scene(arena, (0, -16, 6), (0, 8, 0))
    arena.camera.data.sensor_fit = "VERTICAL"
    arena.camera.data.sensor_width = 36
    arena.camera.data.sensor_height = 36
    arena.camera.data.lens = 36 / (2 * math.tan(math.radians(19)))
    bpy.context.window.scene = arena
    bpy.context.view_layer.update()
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == "VIEW_3D":
                area.spaces.active.region_3d.view_perspective = "CAMERA"
                area.spaces.active.shading.color_type = "MATERIAL"
                area.spaces.active.overlay.show_floor = False
    BLEND.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))


def export_root(root):
    """Write one closed, triangulated asset in local coordinates with flat normals."""
    path = OUTPUT / root["export_obj"]
    lines = ["# Galaga3D - local XYZ coordinates, Z up", f"mtllib {path.stem}.mtl"]
    materials = {}
    vertex_offset = 0
    normal_index = 0
    minimum = Vector((math.inf,) * 3)
    maximum = Vector((-math.inf,) * 3)
    pieces = 0
    for part in sorted(root.children, key=lambda item: item.name):
        if part.type != "MESH":
            continue
        if part.modifiers:
            raise ValueError("Aplica los modificadores antes de exportar " + part.name)
        mesh = part.data
        mesh.calc_loop_triangles()
        matrix = part.matrix_parent_inverse @ part.matrix_basis
        edge_counts = {}
        signed_volume = 0
        lines.append("o " + part.name)
        positions = [matrix @ vertex.co for vertex in mesh.vertices]
        for point in positions:
            if not all(math.isfinite(value) for value in point):
                raise ValueError("Coordenada no finita en " + part.name)
            lines.append("v " + " ".join(f"{v:.7f}" for v in point))
            lines.append(f"vt {point.x + .5:.7f} {point.y + .5:.7f}")
        for triangle in mesh.loop_triangles:
            points = [positions[index] for index in triangle.vertices]
            normal = (points[1] - points[0]).cross(points[2] - points[0])
            if normal.length < 1e-8:
                raise ValueError("Triangulo degenerado en " + part.name)
            normal.normalize()
            signed_volume += points[0].dot(points[1].cross(points[2])) / 6
            indices = list(triangle.vertices)
            for start, end in zip(indices, indices[1:] + indices[:1]):
                edge = tuple(sorted((start, end)))
                count, orientation = edge_counts.get(edge, (0, 0))
                edge_counts[edge] = (count + 1, orientation + (1 if start < end else -1))
            mat = mesh.materials[triangle.material_index]
            materials[mat.name] = mat
            lines.append("usemtl " + mat.name)
            for point in points:
                minimum = Vector(tuple(min(minimum[k], point[k]) for k in range(3)))
                maximum = Vector(tuple(max(maximum[k], point[k]) for k in range(3)))
            lines.append("vn " + " ".join(f"{v:.7f}" for v in normal))
            normal_index += 1
            face = [vertex_offset + index + 1 for index in triangle.vertices]
            lines.append("f " + " ".join(f"{i}/{i}/{normal_index}" for i in face))
        if not edge_counts or any(value != (2, 0) for value in edge_counts.values()) or signed_volume <= 1e-9:
            raise ValueError("La pieza debe ser cerrada y orientada hacia fuera: " + part.name)
        pieces += 1
        vertex_offset += len(positions)
    if not pieces:
        raise ValueError("El modelo no tiene piezas " + root.name)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    mtl = []
    for name, mat in sorted(materials.items()):
        mtl.extend(["newmtl " + name,
                    "Kd " + " ".join(f"{value:.6f}" for value in mat.diffuse_color[:3]),
                    "Ka 0.37 0.37 0.37", "Ks 0.16 0.16 0.16", "Ns 32", "illum 2", ""])
    path.with_suffix(".mtl").write_text("\n".join(mtl), encoding="utf-8")
    return {"file": path.name, "triangles": normal_index, "closed_parts": pieces,
            "min": list(minimum), "max": list(maximum)}


if __name__ == "__main__":
    if "--export-only" not in sys.argv:
        build_library()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    assets = [root for root in bpy.data.objects if "export_obj" in root]
    if len(assets) != 7:
        raise ValueError("Se necesitan seis modelos de naves/enemigos y un escenario")
    manifest = [export_root(root) for root in sorted(assets, key=lambda item: item.name)]
    (OUTPUT / "catalogo.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))
