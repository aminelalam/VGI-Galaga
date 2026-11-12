"""Exporta las tres naves de la prueba 2D como solidos OBJ del juego anterior.

blender --background --factory-startup --python-exit-code 1 --python
Recursos_Galaga3D/scripts/exportar_naves_2d.py

La primera ejecucion admite -- --source-original ruta/Galaga2D_Entidades.blend.
Guarda una copia dedicada con las tres escenas; nunca guarda la fuente original.
"""
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

BASE = Path(__file__).resolve().parents[1]
OUTPUT = BASE / 'modelos'
SOURCE = BASE / 'blender' / 'Naves_2D_fuente.blend'
REPORT = OUTPUT / 'procedencia_naves_2d.json'
SCALE = .75
NAMES = ('nave_flecha', 'nave_delta', 'nave_doble_motor')
EXPECTED_PARTS = (6, 7, 7)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def srgb(value):
    return 12.92 * value if value <= .0031308 else 1.055 * value ** (1 / 2.4) - .055


def verify_saved_obj(path):
    positions, normals, groups = [], [], {}
    group = None
    for line in path.read_text(encoding='utf-8').splitlines():
        words = line.split()
        if not words:
            continue
        if words[0] == 'o':
            group = groups.setdefault(words[1], [])
        elif words[0] == 'v':
            positions.append(Vector(tuple(map(float, words[1:]))))
        elif words[0] == 'vn':
            normals.append(Vector(tuple(map(float, words[1:]))))
        elif words[0] == 'f':
            if len(words) != 4 or group is None:
                raise ValueError('Cara no triangular o sin pieza: ' + path.name)
            group.append([tuple(int(value) - 1 for value in corner.split('/')) for corner in words[1:]])
    reports = []
    for name, faces in groups.items():
        edges, volume = {}, 0
        normal_error = 0
        for face in faces:
            indices = [corner[0] for corner in face]
            a, b, c = [positions[index] for index in indices]
            normal = (b - a).cross(c - a)
            if normal.length <= 1e-8:
                raise ValueError('Triangulo degenerado al releer: ' + name)
            normal.normalize()
            for corner in face:
                normal_error = max(normal_error, (normal - normals[corner[2]]).length)
            volume += a.dot(b.cross(c)) / 6
            for start, end in zip(indices, indices[1:] + indices[:1]):
                edge = tuple(sorted((start, end)))
                count, direction = edges.get(edge, (0, 0))
                edges[edge] = (count + 1, direction + (1 if start < end else -1))
        if any(value != (2, 0) for value in edges.values()) or volume <= 1e-9 or normal_error >= 1e-5:
            raise ValueError('Topologia o normales incorrectas al releer: ' + name)
        reports.append({'pieza': name, 'volumen_firmado_obj': volume,
                        'max_error_normal_obj': normal_error, 'estado': 'PASS'})
    if not reports:
        raise ValueError('OBJ sin piezas: ' + path.name)
    return reports


def export_root(root):
    name = root.name
    path = OUTPUT / (name + '.obj')
    lines = ['# Naves originales de la prueba 2D; X lateral, +Y proa, +Z altura',
             '# Escala uniforme 0.75; centrado y transformacion de la fuente conservados',
             'mtllib ' + name + '.mtl']
    materials = {}
    vertex_offset = normal_index = triangle_count = 0
    source_positions = []
    part_reports = []
    for part in sorted(root.children, key=lambda item: item.name):
        if part.type != 'MESH':
            continue
        if part.modifiers:
            raise ValueError('La fuente tiene modificadores pendientes: ' + part.name)
        mesh = part.data
        mesh.calc_loop_triangles()
        # El objeto raiz conserva el centrado exacto usado al renderizar el sprite.
        matrix = Matrix.Scale(SCALE, 4) @ root.matrix_world @ part.matrix_parent_inverse @ part.matrix_basis
        positions = [matrix @ vertex.co for vertex in mesh.vertices]
        lines.append('o ' + part.name)
        for point in positions:
            if not all(math.isfinite(value) for value in point):
                raise ValueError('Coordenada no finita: ' + part.name)
            source_positions.append(tuple(point))
            lines.append('v ' + ' '.join(f'{value:.7f}' for value in point))
            lines.append(f'vt {point.x + .5:.7f} {point.y + .5:.7f}')
        edges = {}
        signed_volume = 0
        part_triangles = 0
        for triangle in mesh.loop_triangles:
            a, b, c = [positions[index] for index in triangle.vertices]
            normal = (b - a).cross(c - a)
            if normal.length <= 1e-8:
                raise ValueError('Triangulo degenerado: ' + part.name)
            normal.normalize()
            signed_volume += a.dot(b.cross(c)) / 6
            indices = list(triangle.vertices)
            for start, end in zip(indices, indices[1:] + indices[:1]):
                edge = tuple(sorted((start, end)))
                count, direction = edges.get(edge, (0, 0))
                edges[edge] = (count + 1, direction + (1 if start < end else -1))
            material = mesh.materials[triangle.material_index]
            materials[material.name] = material
            lines.append('usemtl ' + material.name)
            face = []
            for index in triangle.vertices:
                normal_index += 1
                lines.append('vn ' + ' '.join(f'{value:.7f}' for value in normal))
                vertex = vertex_offset + index + 1
                face.append(f'{vertex}/{vertex}/{normal_index}')
            lines.append('f ' + ' '.join(face))
            triangle_count += 1
            part_triangles += 1
        if not edges or any(value != (2, 0) for value in edges.values()) or signed_volume <= 1e-9:
            raise ValueError('La pieza debe ser cerrada y orientada hacia fuera: ' + part.name)
        part_reports.append({'pieza': part.name, 'triangulos': part_triangles,
                             'volumen_firmado': signed_volume, 'aristas_compartidas_dos_veces': True})
        vertex_offset += len(positions)
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    material_lines = []
    material_report = []
    for name, material in sorted(materials.items()):
        linear_color = tuple(material.diffuse_color[:3])
        display_color = tuple(srgb(value) for value in linear_color)
        material_lines.extend(['newmtl ' + name,
            'Kd ' + ' '.join(f'{value:.6f}' for value in display_color),
            'Ka 0.37 0.37 0.37', 'Ks 0.16 0.16 0.16', 'Ns 8.00', 'illum 2', ''])
        material_report.append({'nombre': name, 'color_lineal_blender': linear_color,
            'color_srgb_mtl': display_color, 'roughness_blender': material.roughness})
    path.with_suffix('.mtl').write_text('\n'.join(material_lines), encoding='utf-8')

    # Se relee lo escrito para comprobar geometria y precision del archivo real.
    saved = [Vector(tuple(float(value) for value in line.split()[1:]))
             for line in path.read_text(encoding='utf-8').splitlines() if line.startswith('v ')]
    maximum_error = max((Vector(reference) - actual).length for reference, actual in zip(source_positions, saved))
    if len(saved) != len(source_positions) or maximum_error > 1e-6:
        raise ValueError('El OBJ no reproduce las coordenadas de la fuente: ' + root.name)
    minimum = [min(point[axis] for point in saved) for axis in range(3)]
    maximum = [max(point[axis] for point in saved) for axis in range(3)]
    if any(maximum[axis] - minimum[axis] <= .05 for axis in range(3)):
        raise ValueError('El modelo ha perdido volumen: ' + root.name)
    if abs(minimum[0] + maximum[0]) > 1e-6 or abs(minimum[1] + maximum[1]) > 1e-6:
        raise ValueError('El modelo no conserva el pivot centrado del sprite: ' + root.name)
    return {'archivo': path.name, 'sha256_obj': sha256(path), 'sha256_mtl': sha256(path.with_suffix('.mtl')),
        'vertices': len(saved), 'triangulos': triangle_count, 'piezas_cerradas': len(part_reports),
        'min': minimum, 'max': maximum, 'escala_uniforme': SCALE,
        'max_error_coordenada_fuente_escalada': maximum_error,
        'orientacion': '+Y proa, +Z altura', 'partes': part_reports, 'materiales': material_report,
        'validacion_obj_serializado': verify_saved_obj(path)}


def main():
    previous = json.loads(REPORT.read_text(encoding='utf-8')) if REPORT.exists() else {}
    arguments = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    original = Path(arguments[arguments.index('--source-original') + 1]).resolve() if '--source-original' in arguments else None
    source = original or SOURCE
    if not source.is_file():
        raise FileNotFoundError('Falta el Blender fuente: ' + str(source))
    origin = previous.get('fuente_2d_original', {})
    if original:
        origin = {'archivo': original.name, 'sha256': sha256(original)}
        catalog = original.parents[1] / 'datos' / 'modelos.json'
        origin['sha256_modelos_json'] = sha256(catalog)
        sprite_records = json.loads(catalog.read_text(encoding='utf-8'))['sprites']
        origin['sprites'] = [entry for entry in sprite_records if entry['id'] in NAMES]
        for entry in origin['sprites']:
            sprite = original.parents[1] / entry['archivo']
            if sha256(sprite) != entry['sha256']:
                raise ValueError('El sprite no coincide con su procedencia: ' + entry['id'])

    bpy.ops.wm.open_mainfile(filepath=str(source))
    bpy.context.preferences.filepaths.save_version = 0
    for name in NAMES:
        if name not in bpy.data.scenes or name not in bpy.data.objects:
            raise ValueError('Falta la escena/nave original: ' + name)
    bpy.context.window.scene = bpy.data.scenes[NAMES[0]]
    for scene in list(bpy.data.scenes):
        if scene.name not in NAMES:
            bpy.data.scenes.remove(scene)
    keep = {obj for scene in bpy.data.scenes for obj in scene.objects}
    for obj in list(bpy.data.objects):
        if obj not in keep:
            bpy.data.objects.remove(obj, do_unlink=True)
    bpy.context.view_layer.update()
    SOURCE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    if original:
        bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE))
    manifest = []
    for name, expected in zip(NAMES, EXPECTED_PARTS):
        bpy.context.window.scene = bpy.data.scenes[name]
        bpy.context.view_layer.update()
        entry = export_root(bpy.data.objects[name])
        if entry['piezas_cerradas'] != expected:
            raise ValueError('Ha cambiado el numero de piezas de la nave original: ' + name)
        manifest.append(entry)
        print('NAVE_2D_EXPORTADA', name, entry['vertices'], entry['triangulos'], entry['min'], entry['max'], flush=True)
    catalog_path = OUTPUT / 'catalogo.json'
    catalog = json.loads(catalog_path.read_text(encoding='utf-8'))
    for entry in catalog:
        exported = next((item for item in manifest if item['archivo'] == entry['file']), None)
        if exported is not None:
            entry.update({'triangles': exported['triangulos'], 'closed_parts': exported['piezas_cerradas'],
                'min': exported['min'], 'max': exported['max'],
                'source_blend': '../blender/Naves_2D_fuente.blend', 'source_scene': Path(entry['file']).stem,
                'uniform_scale': SCALE, 'export_script': '../scripts/exportar_naves_2d.py',
                'provenance': 'procedencia_naves_2d.json'})
    catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    report = {'version': 1, 'estado': 'PASS', 'fuente_2d_original': origin,
        'fuente_blender_dedicada': {'archivo': str(SOURCE.relative_to(BASE)), 'sha256': sha256(SOURCE)},
        'script': {'archivo': str(Path(__file__).relative_to(BASE)), 'sha256': sha256(Path(__file__))},
        'base_juego': 'cc3ced6', 'mapeo': 'OBJ = escala uniforme 0.75 * root.matrix_world * parte.local * vertice',
        'color': 'La paleta lineal de Blender se convierte a sRGB para el shader antiguo sin conversion gamma; no se altera la fuente.',
        'alcance': 'Solo las tres naves; enemigos, jefe, escenario y reglas del juego anterior se conservan.',
        'pruebas': ['Coincidencia con hashes de sprites originales', 'Solo tres escenas de naves en copia Blender',
            'Coincidencia de coordenadas de la fuente a escala uniforme', 'Pivot XY centrado igual que sprite',
            'Piezas cerradas y volumen firmado positivo', 'Triangulos sin degeneraciones y normales exteriores',
            'Profundidad real en XYZ y materiales originales'],
        'naves': manifest}
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('NAVE_2D_VALIDACION_PASS', REPORT, flush=True)


if __name__ == '__main__':
    main()
