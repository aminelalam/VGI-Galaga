"""Build editable game models and export triangulated OBJ/MTL for EntornVGI.

blender --background --factory-startup --python this_file
blender --background Mallas_Galaga3D.blend --python this_file -- --export-only
blender --background Mallas_Galaga3D.blend --python this_file -- --lod-only
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
from mallas_volumetricas import build_ship, build_enemy, build_boss, build_space, build_obstacle, build_cockpit


def material(name, color, roughness=.48, metallic=.35, specular=.35, emission=(0,0,0)):
    result = bpy.data.materials.new(name)
    result.diffuse_color = (*color, 1)
    result.use_nodes = True
    result["phong_specular"] = specular
    result["phong_shininess"] = max(8, min(128, 2 / max(.12, roughness)**2 - 2))
    result["emission_color"] = list(emission)
    shader = result.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Emission Color"].default_value = (*emission,1)
    shader.inputs["Emission Strength"].default_value = 1
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
        "white": (.66,.65,.60), "armor": (.33,.36,.36),
        "blue": (.15,.22,.25), "red": (.35,.105,.075), "green": (.22,.26,.21),
        "dark": (.025,.030,.033), "cockpit": (.018,.041,.050),
        "metal": (.28,.31,.33), "engine_cold": (.12,.22,.26),
        "engine_hot": (.24,.105,.038), "planet": (.07,.13,.16),
        "station": (.17,.19,.20), "window": (.24,.22,.17),
        "screen": (.018,.028,.031), "instrument": (.20,.16,.085),
        "nav_red": (.22,.045,.028), "nav_green": (.035,.16,.09),
        "rock": (.085,.085,.08), "obstacle": (.34,.32,.285),
    }
    materials = {name: material(name, color) for name, color in colors.items()}
    for name in ("cockpit", "metal"):
        mat = materials[name]
        mat["phong_specular"] = .80 if name == "cockpit" else .55
        mat["phong_shininess"] = 96 if name == "cockpit" else 48
        mat.node_tree.nodes.get("Principled BSDF").inputs["Roughness"].default_value = .22
    for name in ("planet", "rock", "obstacle"):
        materials[name]["phong_specular"] = .08
        materials[name]["phong_shininess"] = 12
        materials[name].node_tree.nodes.get("Principled BSDF").inputs["Roughness"].default_value = .85
    for name,emission in {"engine_cold":(.30,.56,.72),"engine_hot":(.72,.30,.085),
             "instrument":(.24,.17,.065),"window":(.25,.22,.16),
             "nav_red":(.32,.045,.025),"nav_green":(.04,.25,.12)}.items():
        materials[name]["emission_color"]=list(emission)
        materials[name].node_tree.nodes.get("Principled BSDF").inputs["Emission Color"].default_value=(*emission,1)
    roots = []
    for index, name in enumerate(("nave_flecha", "nave_delta", "nave_doble_motor")):
        roots.append(build_ship(catalog.collection, name, index, materials))
    roots.append(build_enemy(catalog.collection, "enemigo_abeja", 0, materials))
    roots.append(build_enemy(catalog.collection, "enemigo_escarabajo", 1, materials))
    roots.append(build_boss(catalog.collection, "jefe_acorazado", materials))
    for index, root in enumerate(roots):
        root.location = ((index % 3 - 1) * 2.4, 1.8 if index < 3 else -1.2, 0)
        root["export_obj"] = root.name + ".obj"
        root["forward_axis"] = "+Y" if index < 3 else "-Y"
    setup_scene(catalog, (4, -7, 10), (0, .3, 0), True)

    arena = bpy.data.scenes.new("02_Sector_espacial")
    build_space(arena.collection, materials)
    extra = bpy.data.scenes.new("03_Cabina_y_obstaculos")
    obstacle = build_obstacle(extra.collection, materials)
    obstacle.location = (-1.8, 0, 0)
    cockpit = build_cockpit(extra.collection, materials)
    cockpit.location = (1.8, 0, 0)
    setup_scene(extra, (3, -5, 4), (0, 0, 0), True)
    game_copy(roots[0], arena.collection, "Jugador", (0, -4, 0))
    for row in range(3):
        for column in range(6):
            enemy = roots[4 if row == 2 else 3]
            game_copy(enemy, arena.collection, f"Enemigo_{row}_{column}",
                      ((column - 2.5) * 2.6, 14 + 4 * row, -2.5 + 2.5 * row), 1.45, 35)
    setup_scene(arena, (0, -12.5, 2.3), (0, 18, .6))
    arena.camera.data.sensor_fit = "VERTICAL"
    arena.camera.data.sensor_width = 36
    arena.camera.data.sensor_height = 36
    arena.camera.data.lens = 36 / (2 * math.tan(math.radians(20)))
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


def build_enemy_lods():
    """Decimate detached copies; the editable original meshes remain untouched."""
    temporary_scene = bpy.data.scenes.new("LOD_exportacion_temporal")
    bpy.context.window.scene = temporary_scene
    roots = []
    for name in ("enemigo_abeja", "enemigo_escarabajo"):
        source = bpy.data.objects[name]
        source_counts={}
        for part in source.children:
            if part.type=="MESH":
                part.data.calc_loop_triangles()
                source_counts[part.name]=len(part.data.loop_triangles)
        preserved=sum(count for label,count in source_counts.items() if count<=32 or "_Ala_" in label)
        reduced=sum(source_counts.values())-preserved
        ratio=max(.15,min(.92,(1000-preserved)/max(1,reduced)))
        root = bpy.data.objects.new(name + "_lod", None)
        temporary_scene.collection.objects.link(root)
        root["export_obj"] = name + "_lod.obj"
        root["forward_axis"] = "-Y"
        for part in source.children:
            if part.type != "MESH":
                continue
            duplicate = part.copy()
            duplicate.data = part.data.copy()
            duplicate.name = part.name + "_LOD"
            temporary_scene.collection.objects.link(duplicate)
            duplicate.parent = root
            duplicate.matrix_parent_inverse = part.matrix_parent_inverse.copy()
            duplicate.matrix_basis = part.matrix_basis.copy()
            original_min = [min(vertex.co[axis] for vertex in part.data.vertices) for axis in range(3)]
            original_max = [max(vertex.co[axis] for vertex in part.data.vertices) for axis in range(3)]
            part.data.calc_loop_triangles()
            # Keep the silhouettes of thin wings and the small armour plates.
            # Engine housings, glazing and mechanical fittings supply the saving.
            if len(part.data.loop_triangles) <= 32 or "_Ala_" in part.name:
                continue
            modifier = duplicate.modifiers.new("LOD_estatico", "DECIMATE")
            modifier.decimate_type = "COLLAPSE"
            modifier.ratio = ratio
            modifier.use_collapse_triangulate = True
            bpy.context.view_layer.objects.active = duplicate
            duplicate.select_set(True)
            bpy.ops.object.modifier_apply(modifier=modifier.name)
            duplicate.select_set(False)
            mesh = duplicate.data
            reduced_min = [min(vertex.co[axis] for vertex in mesh.vertices) for axis in range(3)]
            reduced_max = [max(vertex.co[axis] for vertex in mesh.vertices) for axis in range(3)]
            # A positive affine rescale restores each piece's original extrema.
            # The global silhouette bounds therefore match the detailed model.
            for vertex in mesh.vertices:
                for axis in range(3):
                    size = reduced_max[axis] - reduced_min[axis]
                    if size <= 1e-8:
                        raise ValueError("El LOD ha perdido volumen en " + part.name)
                    factor = (vertex.co[axis] - reduced_min[axis]) / size
                    vertex.co[axis] = original_min[axis] + factor*(original_max[axis]-original_min[axis])
            mesh.update()
        roots.append(root)
    return roots


def export_root(root):
    """Write closed triangles with smooth curved surfaces and hard armour edges."""
    path = OUTPUT / root["export_obj"]
    lines = ["# Galaga3D - local XYZ coordinates, Z up", f"mtllib {path.stem}.mtl"]
    materials = {}
    vertex_offset = 0
    normal_index = 0
    triangle_count = 0
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
        normal_matrix = matrix.to_3x3().inverted().transposed()
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
            face = []
            for corner, index in enumerate(triangle.vertices):
                if mesh.polygons[triangle.polygon_index].use_smooth:
                    vertex_normal = normal_matrix @ mesh.corner_normals[triangle.loops[corner]].vector
                    vertex_normal.normalize()
                else:
                    vertex_normal = normal
                lines.append("vn " + " ".join(f"{v:.7f}" for v in vertex_normal))
                normal_index += 1
                vertex = vertex_offset + index + 1
                face.append(f"{vertex}/{vertex}/{normal_index}")
            lines.append("f " + " ".join(face))
            triangle_count += 1
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
                    "Ka 0.37 0.37 0.37",
                    "Ks " + " ".join([f"{float(mat.get('phong_specular', .4)):.4f}"] * 3),
                    "Ke " + " ".join(f"{float(value):.5f}" for value in mat.get('emission_color',(0,0,0))),
                    f"Ns {float(mat.get('phong_shininess', 32)):.2f}", "illum 2", ""])
    path.with_suffix(".mtl").write_text("\n".join(mtl), encoding="utf-8")
    return {"file": path.name, "triangles": triangle_count, "closed_parts": pieces,
            "min": list(minimum), "max": list(maximum)}


if __name__ == "__main__":
    OUTPUT.mkdir(parents=True, exist_ok=True)
    if "--lod-only" in sys.argv:
        # Reading the .blend and exporting copies never rewrites the nine sources.
        if "enemigo_abeja" not in bpy.data.objects:
            bpy.ops.wm.open_mainfile(filepath=str(BLEND))
        manifest = json.loads((OUTPUT / "catalogo.json").read_text(encoding="utf-8"))
        manifest = [entry for entry in manifest if not entry["file"].endswith("_lod.obj")]
    else:
        if "--export-only" not in sys.argv:
            build_library()
        assets = [root for root in bpy.data.objects if "export_obj" in root]
        if len(assets) != 9:
            raise ValueError("Se necesitan seis naves/enemigos, sector, asteroide y cabina")
        manifest = [export_root(root) for root in sorted(assets, key=lambda item: item.name)]
    for root in build_enemy_lods():
        entry = export_root(root)
        if not 800 <= entry["triangles"] <= 1100:
            raise ValueError("El LOD debe contener entre 800 y 1100 triangulos: " + entry["file"])
        entry["lod_of"] = entry["file"].replace("_lod.obj", ".obj")
        manifest.append(entry)
    manifest.sort(key=lambda entry: entry["file"])
    (OUTPUT / "catalogo.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))
