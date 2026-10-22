"""Comprueba el .blend retro abierto, sin renderizar ni guardar el archivo.

Uso: blender --background archivo.blend --python-exit-code 1 --python este_script.py
Escribe solo previews/Retro/validacion_estatica.json o validacion_animada.json.
Las acciones se prueban mediante su funcion Python, sin simular la interfaz GUI.
"""

import json
import math
from pathlib import Path

import bpy


BASE = Path(__file__).resolve().parents[1]
SOURCE_NAME = "Galaga3D_Interfaz.blend"
SCENES = (
    "01_INICIO", "02_ELEGIR_NAVE", "03_PARTIDA", "04_PAUSA",
    "05_JEFE", "06_VICTORIA", "07_DERROTA",
)
ANIMATED = "animada" in Path(bpy.data.filepath).stem.lower() or "08_DEMO_COMPLETA" in bpy.data.scenes
REPORT = BASE / "previews" / "Retro" / ("validacion_animada.json" if ANIMATED else "validacion_estatica.json")
checks = {}
errors = []
namespace = None


def require(condition, code, detail):
    if not condition:
        errors.append({"code": code, "detail": detail})


def section(name, function):
    """Un fallo no impide recoger los resultados de las otras comprobaciones."""
    try:
        checks[name] = function()
    except Exception as exc:
        errors.append({"code": "SECTION_EXCEPTION", "detail": name + ": " + type(exc).__name__ + ": " + str(exc)})
        checks[name] = {"completed": False}


def descendants(root):
    return [root] + list(root.children_recursive)


def material_meshes(root):
    return [obj for obj in descendants(root) if obj.type == "MESH"]


def audit_structure():
    required = SCENES + (("08_DEMO_COMPLETA",) if ANIMATED else ())
    require(bool(bpy.data.filepath), "OPEN_FILE", "No hay un .blend guardado abierto.")
    require(all(name in bpy.data.scenes for name in required), "SCENES", "Faltan escenas: " + ", ".join(name for name in required if name not in bpy.data.scenes))
    result = {}
    for scene in bpy.data.scenes:
        size = (scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage)
        require(size == (1280, 720, 100), "RESOLUTION", scene.name + ": " + str(size))
        require(scene.camera is not None and scene.camera.name in scene.objects, "CAMERA", scene.name + ": falta camara vinculada a la escena.")
        if ANIMATED:
            expected_end = 540 if scene.name == "08_DEMO_COMPLETA" else 240
            require(scene.frame_start == 1 and scene.frame_end == expected_end, "FRAME_RANGE", scene.name + ": se esperaba 1.." + str(expected_end))
        result[scene.name] = {"resolution": list(size), "camera": scene.camera.name if scene.camera else None,
                              "frames": [scene.frame_start, scene.frame_end], "source_blend": scene.get("source_blend")}
    reused = [obj for obj in bpy.data.objects if "reused_from_blend" in obj]
    require(bool(reused), "SOURCE_ICONS", "No hay objetos identificados como reutilizados del .blend original.")
    require(any(SOURCE_NAME in str(obj["reused_from_blend"]) for obj in reused), "SOURCE_NAME", "No se identifica " + SOURCE_NAME + " en los iconos reutilizados.")
    return {"scenes": result, "source_icon_objects": len(reused)}


def audit_models():
    roots = [obj for obj in bpy.data.objects if obj.get("model_type") in ("player", "enemy", "boss")]
    variants = sorted({int(obj.get("variant", -1)) for obj in roots if obj.get("model_type") == "player"})
    require(all(index in variants for index in range(3)), "SHIP_VARIANTS", "Se requieren variantes de nave 0, 1 y 2; encontradas " + str(variants))
    require(any(obj.get("model_type") == "boss" for obj in roots), "BOSS_MODEL", "Falta un modelo volumetrico de jefe.")
    require(any(obj.get("model_type") == "enemy" for obj in roots), "ENEMY_MODEL", "Falta un modelo volumetrico de enemigo.")
    inventory = []
    for root in roots:
        meshes = material_meshes(root)
        require(bool(meshes), "MODEL_MESHES", root.name + ": no contiene mallas.")
        volumetric = 0
        for obj in meshes:
            vertices = [tuple(vertex.co) for vertex in obj.data.vertices]
            require(bool(vertices) and bool(obj.data.polygons), "MESH_CONTENT", obj.name + ": malla vacia.")
            require(all(math.isfinite(value) for point in vertices for value in point), "MESH_FINITE", obj.name + ": coordenadas no finitas.")
            require(len(obj.data.materials) > 0 and all(material is not None for material in obj.data.materials), "MESH_MATERIAL", obj.name + ": falta material.")
            if vertices and all(max(point[axis] for point in vertices) - min(point[axis] for point in vertices) > 1e-6 for axis in range(3)):
                volumetric += 1
        require(volumetric > 0, "MODEL_VOLUME", root.name + ": todas las piezas son planas.")
        inventory.append({"name": root.name, "type": root["model_type"], "variant": root.get("variant"),
                          "mesh_parts": len(meshes), "volumetric_parts": volumetric})
    return {"player_variants": variants, "models": inventory}


def audit_buttons():
    expected = {"start", "select_0", "select_1", "select_2", "confirm", "back",
                "pause", "resume", "boss", "victory", "defeat"}
    if ANIMATED:
        expected.add("demo")
    buttons = {obj.name: str(obj["retro_action"]) for obj in bpy.data.objects if "retro_action" in obj}
    found = set(buttons.values())
    require(expected <= found, "BUTTON_ACTIONS", "Faltan acciones: " + ", ".join(sorted(expected - found)))
    return {"buttons": buttons, "expected_actions": sorted(expected)}


def animatable_ids():
    """Incluye datos de objetos, escenas y los arboles de nodos internos."""
    seen = set()
    for prop in bpy.data.bl_rna.properties:
        if prop.type != "COLLECTION":
            continue
        for value in getattr(bpy.data, prop.identifier, ()):
            for data in (value, getattr(value, "node_tree", None)):
                if data is None or not hasattr(data, "animation_data"):
                    continue
                pointer = data.as_pointer()
                if pointer not in seen:
                    seen.add(pointer)
                    yield data


def action_fcurves(action):
    # Blender 5 usa channelbags dentro de strips de acciones por capas.
    # https://developer.blender.org/docs/release_notes/4.4/upgrading/slotted_actions/
    for layer in getattr(action, "layers", ()):
        for strip in layer.strips:
            for bag in getattr(strip, "channelbags", ()):
                yield from bag.fcurves


def audit_animation():
    animated_ids = []
    for data in animatable_ids():
        animation = data.animation_data
        if animation is not None:
            animated_ids.append({"name": data.name, "rna_type": data.bl_rna.identifier,
                                 "action": animation.action.name if animation.action else None,
                                 "drivers": len(animation.drivers), "nla_tracks": len(animation.nla_tracks)})
    actions = []
    for action in bpy.data.actions:
        curves = list(action_fcurves(action))
        actions.append({"name": action.name, "fcurves": len(curves),
                        "keyframes": sum(len(curve.keyframe_points) for curve in curves)})
    if not ANIMATED:
        require(not animated_ids, "STATIC_ANIMATION_DATA", "La version estatica contiene datos de animacion: " + str(animated_ids))
        require(not actions, "STATIC_ACTIONS", "La version estatica contiene acciones.")
        return {"animation_data": animated_ids, "actions": actions}
    require(any(action["fcurves"] > 0 and action["keyframes"] > 0 for action in actions), "NATIVE_KEYFRAMES", "No se encontraron F-curves nativas con keyframes.")
    motion = {}
    for scene in bpy.data.scenes:
        bpy.context.window.scene = scene
        candidates = [obj for obj in scene.objects if obj.animation_data and obj.animation_data.action]
        matrices = []
        for frame in (1, 60):
            scene.frame_set(frame)
            bpy.context.view_layer.update()
            depsgraph = bpy.context.evaluated_depsgraph_get()
            matrices.append({obj.name: tuple(value for row in obj.evaluated_get(depsgraph).matrix_world for value in row) for obj in candidates})
        moved = [name for name, before in matrices[0].items()
                 if any(abs(a - b) > 1e-5 for a, b in zip(before, matrices[1][name]))]
        motion[scene.name] = moved
    require(any(motion.values()), "ANIMATION_MOTION", "Ningun objeto con accion cambia su transformacion evaluada entre frames 1 y 60.")
    return {"animation_data": animated_ids, "actions": actions, "moved_between_1_and_60": motion}


def audit_embedded_script():
    global namespace
    text = bpy.data.texts.get("INICIAR_INTERFAZ.py")
    external = BASE / "scripts" / "interfaz_retro_interactiva.py"
    if not ANIMATED and text is None:
        return {"required": False, "present": False, "mode": "Version estatica visual; sin codigo de interaccion embebido."}
    require(text is not None, "EMBEDDED_SCRIPT", "Falta INICIAR_INTERFAZ.py en el .blend.")
    require(external.is_file(), "EXTERNAL_SCRIPT", "Falta scripts/interfaz_retro_interactiva.py.")
    if text is None or not external.is_file():
        return {"completed": False}
    source = text.as_string()
    matches = source.strip() == external.read_text(encoding="utf-8").strip()
    require(matches, "SCRIPT_MATCH", "El script embebido difiere del script externo.")
    namespace = {"__name__": "__main__", "__file__": str(external)}
    exec(compile(source, "INICIAR_INTERFAZ.py", "exec"), namespace)
    callback = namespace.get("galaga_retro_action")
    require(callable(callback), "ACTION_FUNCTION", "Falta la funcion galaga_retro_action.")
    return {"embedded_equals_external": matches, "action_function": callable(callback),
            "execution": "background; sin eventos de raton ni teclado GUI"}


def player_visibility(scene):
    roots = [obj for obj in scene.objects if "retro_player_variant" in obj]
    variants = {}
    for root in roots:
        variant = int(root["retro_player_variant"])
        meshes = [obj for obj in material_meshes(root) if obj.name in scene.objects]
        visible = [obj.name for obj in meshes if not obj.hide_render and not obj.hide_viewport
                   and not obj.hide_get(view_layer=bpy.context.view_layer)]
        variants.setdefault(str(variant), []).extend(visible)
    require(all(str(index) in variants for index in range(3)), "PLAYER_VARIANT_TAGS", "Faltan raices retro_player_variant 0/1/2 en " + scene.name + ".")
    require(bool(variants.get("2")) and not variants.get("0") and not variants.get("1"), "SELECTED_PLAYER_VISIBILITY", scene.name + ": seleccion 2; debe verse solo esa nave; visibles " + str(variants))
    return variants


def audit_actions():
    callback = namespace.get("galaga_retro_action") if namespace else None
    if not ANIMATED and not callable(callback):
        return {"required": False, "executed": False,
                "mode": "Version estatica visual; se comprobaron los metadatos de botones, sin ejecutar acciones."}
    require(callable(callback), "ACTION_TEST_AVAILABLE", "No se pueden probar las acciones sin la funcion de interfaz.")
    if not callable(callback):
        return {"completed": False}
    results = []
    sequence = [("start", "02_ELEGIR_NAVE"), ("select_2", "02_ELEGIR_NAVE"),
                ("confirm", "03_PARTIDA"), ("pause", "04_PAUSA"),
                ("resume", "03_PARTIDA"), ("boss", "05_JEFE"),
                ("pause", "04_PAUSA"), ("resume", "05_JEFE"),
                ("victory", "06_VICTORIA"), ("defeat", "07_DERROTA"), ("back", "01_INICIO")]
    if ANIMATED:
        sequence.append(("demo", "08_DEMO_COMPLETA"))
    if "01_INICIO" in bpy.data.scenes:
        bpy.context.window.scene = bpy.data.scenes["01_INICIO"]
    for action, expected_scene in sequence:
        try:
            callback(action, context=bpy.context)
            actual = bpy.context.scene.name
            require(actual == expected_scene, "ACTION_SCENE", action + ": esperado " + expected_scene + ", obtenido " + actual)
            result = {"action": action, "expected_scene": expected_scene, "actual_scene": actual}
            if action == "select_2":
                selections = {scene.name: scene.get("nave_elegida") for scene in bpy.data.scenes}
                require(all(value == 2 for value in selections.values()), "SELECTION_PROPAGATION", "La nave elegida no es 2 en todas las escenas: " + str(selections))
                result["nave_elegida"] = selections
            if action in ("confirm", "boss", "victory", "defeat") and actual == expected_scene:
                result["visible_meshes_by_variant"] = player_visibility(bpy.context.scene)
            results.append(result)
        except Exception as exc:
            errors.append({"code": "ACTION_EXCEPTION", "detail": action + ": " + type(exc).__name__ + ": " + str(exc)})
            results.append({"action": action, "completed": False})
    return {"mode": "llamadas Python; GUI pendiente de comprobacion manual", "sequence": results}


original_scene = bpy.context.window.scene
original_frames = [(scene, scene.frame_current, scene.frame_subframe) for scene in bpy.data.scenes]
original_selections = [(scene, "nave_elegida" in scene, scene.get("nave_elegida")) for scene in bpy.data.scenes]
original_visibility = [(obj, obj.hide_render, obj.hide_viewport) for obj in bpy.data.objects]
original_layer_visibility = [(layer, [(obj, obj.hide_get(view_layer=layer)) for obj in layer.objects])
                             for scene in bpy.data.scenes for layer in scene.view_layers]
try:
    section("structure", audit_structure)
    section("models", audit_models)
    section("buttons", audit_buttons)
    section("animation", audit_animation)
    section("embedded_script", audit_embedded_script)
    section("actions", audit_actions)
finally:
    restore_errors_before = len(errors)
    try:
        if namespace and callable(namespace.get("galaga_retro_action")):
            namespace["galaga_retro_action"]("select_0", context=bpy.context)
    except Exception as exc:
        errors.append({"code": "RESTORE_ACTION_EXCEPTION", "detail": type(exc).__name__ + ": " + str(exc)})
    try:
        for scene, existed, value in original_selections:
            if existed:
                scene["nave_elegida"] = value
            elif "nave_elegida" in scene:
                del scene["nave_elegida"]
        for scene, frame, subframe in original_frames:
            scene.frame_set(frame, subframe=subframe)
        for obj, hidden_render, hidden_viewport in original_visibility:
            obj.hide_render = hidden_render
            obj.hide_viewport = hidden_viewport
        for layer, states in original_layer_visibility:
            for obj, hidden in states:
                obj.hide_set(hidden, view_layer=layer)
        bpy.context.window.scene = original_scene
        bpy.context.view_layer.update()
        checks["restored"] = {"original_scene": original_scene.name,
                              "frames_selection_and_visibility": len(errors) == restore_errors_before}
    except Exception as exc:
        errors.append({"code": "RESTORE_EXCEPTION", "detail": type(exc).__name__ + ": " + str(exc)})

report = {"status": "PASS" if not errors else "FAIL", "blender_version": bpy.app.version_string,
          "file": bpy.data.filepath, "version": "animada" if ANIMATED else "estatica",
          "scope": "Estructura, materiales, keyframes y funciones de interfaz en background; sin render ni prueba manual de GUI.",
          "blend_saved_by_verifier": False, "checks": checks, "errors": errors}
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("RETRO_AUDIT", report["status"], "errors", len(errors), "report", str(REPORT))
if errors:
    raise RuntimeError("La auditoria retro ha encontrado " + str(len(errors)) + " incidencias; consultar " + str(REPORT))
