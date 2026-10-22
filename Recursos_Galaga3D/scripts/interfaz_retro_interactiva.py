"""Interfaz retro dentro de Blender; no implementa la lógica de una partida.

Uso: abrir este texto en el Editor de texto y pulsar Alt+P. Se registra el panel
Vista 3D > N > Galaga y se activa la navegación. También se puede usar F3 y buscar
«Activar interfaz retro». Abrir el .blend por sí solo NO ejecuta este script.

En la vista 3D: clic en los botones, 1/2/3 para elegir nave, Enter para avanzar,
P para pausa/continuar y Espacio para reproducir/detener la animación de la escena.
Esc desactiva los clics y atajos del script; no cierra Blender. Los atajos se
aplican solo bajo el cursor en la vista 3D para poder seguir editando este texto.

Contrato para el generador: escenas SCREENS; botones de malla con propiedad
«retro_action»; raíces de naves con «retro_player_variant» = 0, 1 o 2; marcos de
selección con «retro_selection_frame» = 0, 1 o 2. La visibilidad de las dos últimas
familias se aplica recursivamente. Todas las escenas guardan «nave_elegida».

Para comprobaciones sin interfaz: register(); galaga_retro_action("start");
galaga_retro_action("select_2"); galaga_retro_action("confirm"). Importar/ejecutar
en modo background registra las clases, pero no lanza un operador modal.
"""

import bpy
from bpy.props import BoolProperty, StringProperty
from bpy_extras import view3d_utils


SCREENS = (
    "01_INICIO", "02_ELEGIR_NAVE", "03_PARTIDA", "04_PAUSA", "05_JEFE",
    "06_VICTORIA", "07_DERROTA", "08_DEMO_COMPLETA",
)
_RUNTIME_KEY = "galaga_retro_interactive_runtime"
_RUNNING_KEY = "galaga_retro_activo"
_CLASSES = (
    "GALAGA_RETRO_OT_accion", "GALAGA_RETRO_OT_activar",
    "GALAGA_RETRO_OT_desactivar", "GALAGA_RETRO_PT_panel",
)


def _window(context=None):
    context = context or bpy.context
    window = getattr(context, "window", None)
    if window is not None:
        return window
    manager = getattr(context, "window_manager", None)
    return next(iter(manager.windows), None) if manager is not None else None


def _runtime():
    return bpy.app.driver_namespace.get(_RUNTIME_KEY)


def _redraw(window=None):
    windows = (window,) if window is not None else bpy.context.window_manager.windows
    for item in windows:
        screen = getattr(item, "screen", None)
        if screen is not None:
            for area in screen.areas:
                area.tag_redraw()


def _prepare_views(window):
    if window is None or window.screen is None:
        return
    for area in window.screen.areas:
        if area.type != "VIEW_3D":
            continue
        space = area.spaces.active
        space.use_local_camera = False
        if window.scene.camera is not None:
            space.camera = window.scene.camera
        if space.region_3d is not None:
            space.region_3d.view_perspective = "CAMERA"
        for region_view in space.region_quadviews:
            region_view.view_perspective = "CAMERA"
        space.shading.type = "MATERIAL"
        space.shading.use_scene_world = True
        space.shading.use_scene_lights = True
        space.overlay.show_overlays = False
        space.show_gizmo = False
        area.tag_redraw()


def _animation(window, play=None):
    """Use an explicit window/area override, including calls from the text editor."""
    if window is None or window.screen is None or bpy.app.background:
        return False
    running = bool(window.screen.is_animation_playing)
    desired = not running if play is None else bool(play)
    if running == desired:
        return running
    area = next((area for area in window.screen.areas if area.type == "VIEW_3D"), None)
    if area is None:
        area = next(iter(window.screen.areas), None)
    if area is None:
        return running
    region = next((region for region in area.regions if region.type == "WINDOW"), None)
    if region is None:
        return running
    with bpy.context.temp_override(window=window, area=area, region=region):
        if desired:
            bpy.ops.screen.animation_play()
        else:
            # Explicit cancellation avoids accidentally starting playback during
            # navigation if another operator has just stopped the timeline.
            bpy.ops.screen.animation_cancel(restore_frame=False)
    return bool(window.screen.is_animation_playing)


def _selected_ship(context=None):
    context = context or bpy.context
    scene = getattr(_window(context), "scene", None) or getattr(context, "scene", None)
    try:
        return max(0, min(2, int(scene.get("nave_elegida", 0)))) if scene else 0
    except (TypeError, ValueError, OverflowError):
        return 0


def _hide_tree(root, hidden):
    """An Empty's viewport/render flags do not hide its children by themselves."""
    pending = [root]
    while pending:
        obj = pending.pop()
        obj.hide_viewport = bool(hidden)
        obj.hide_render = bool(hidden)
        # Clear/restore the per-view-layer eye switch as well. This matters when
        # selecting a variant previously hidden with hide_set in the UI.
        for scene in bpy.data.scenes:
            for layer in scene.view_layers:
                if layer.objects.get(obj.name) is not None:
                    obj.hide_set(bool(hidden), view_layer=layer)
        pending.extend(obj.children)


def elegir_nave(index, context=None):
    """Select 0..2 in every scene and show only the corresponding player/frame."""
    index = max(0, min(2, int(index)))
    for scene in bpy.data.scenes:
        scene["nave_elegida"] = index
    for obj in bpy.data.objects:
        for key in ("retro_player_variant", "retro_selection_frame"):
            if key in obj:
                try:
                    variant = int(obj[key])
                except (TypeError, ValueError, OverflowError):
                    continue
                _hide_tree(obj, variant != index)
                break
    window = _window(context)
    if window is not None:
        for layer in window.scene.view_layers:
            layer.update()
    _redraw(window)
    return index


def cambiar_pantalla(name, context=None):
    """Stop playback and display an existing scene through its own camera."""
    context = context or bpy.context
    scene = bpy.data.scenes.get(name)
    if name not in SCREENS or scene is None:
        raise ValueError("No existe la pantalla retro: " + str(name))
    window = _window(context)
    if window is None:
        raise RuntimeError("Hace falta una ventana de Blender para cambiar de escena.")
    selected = _selected_ship(context)
    _animation(window, False)
    window.scene = scene
    elegir_nave(selected, context)
    _prepare_views(window)
    if name != "04_PAUSA":
        _animation(window, True)
    _redraw(window)
    return scene


def galaga_retro_action(action, context=None):
    """Public action API shared by ray-cast buttons, keyboard, sidebar and QA."""
    context = context or bpy.context
    action = str(action)
    if action in ("select_0", "select_1", "select_2"):
        elegir_nave(int(action[-1]), context)
        window = _window(context)
        return window.scene if window else getattr(context, "scene", None)
    if action == "pause":
        window = _window(context)
        if window and window.scene.name in ("03_PARTIDA", "05_JEFE"):
            context.window_manager["galaga_retro_antes_pausa"] = window.scene.name
    if action == "resume":
        previous = context.window_manager.get("galaga_retro_antes_pausa", "03_PARTIDA")
        if previous not in ("03_PARTIDA", "05_JEFE"):
            previous = "03_PARTIDA"
        return cambiar_pantalla(previous, context)
    destinations = {
        "start": "02_ELEGIR_NAVE", "confirm": "03_PARTIDA", "back": "01_INICIO",
        "pause": "04_PAUSA", "resume": "03_PARTIDA", "boss": "05_JEFE",
        "victory": "06_VICTORIA", "defeat": "07_DERROTA", "demo": "08_DEMO_COMPLETA",
    }
    if action in destinations:
        return cambiar_pantalla(destinations[action], context)
    if action == "play_pause":
        window = _window(context)
        if window and window.scene.name == "04_PAUSA":
            _animation(window, False)
            return window.scene
        _animation(window)
        _redraw(window)
        return window.scene if window else getattr(context, "scene", None)
    raise ValueError("Acción retro desconocida: " + action)


def _view_under_mouse(window, event):
    """Modal context can still be a text editor; use absolute window coordinates."""
    if window is None or window.screen is None:
        return None
    for area in window.screen.areas:
        if area.type != "VIEW_3D":
            continue
        # With region overlap enabled, WINDOW also extends behind the N panel,
        # toolbar and headers. Native UI must receive those clicks first.
        for ui_region in area.regions:
            if ui_region.type == "WINDOW" or ui_region.width <= 1 or ui_region.height <= 1:
                continue
            if ui_region.x <= event.mouse_x < ui_region.x + ui_region.width and ui_region.y <= event.mouse_y < ui_region.y + ui_region.height:
                return None
        regions = [region for region in area.regions if region.type == "WINDOW"]
        for index, region in enumerate(regions):
            if region.x <= event.mouse_x < region.x + region.width and region.y <= event.mouse_y < region.y + region.height:
                space = area.spaces.active
                views = space.region_quadviews
                region_view = views[index] if views and len(views) == len(regions) else space.region_3d
                if region_view is not None:
                    return area, region, region_view
    return None


def _clicked_action(window, event, view):
    area, region, region_view = view
    position = (event.mouse_x - region.x, event.mouse_y - region.y)
    origin = view3d_utils.region_2d_to_origin_3d(region, region_view, position)
    direction = view3d_utils.region_2d_to_vector_3d(region, region_view, position)
    camera = window.scene.camera
    if region_view.view_perspective == "CAMERA" and camera is not None and camera.data.type == "ORTHO":
        # Blender's utility places an orthographic CAMERA origin halfway
        # between near/far clipping planes. That can be BEHIND the buttons.
        # Slide the same ray back to the camera plane, retaining its lateral
        # screen position and direction (also valid for a rotated camera).
        origin += direction * (camera.matrix_world.translation - origin).dot(direction)
    with bpy.context.temp_override(window=window, area=area, region=region):
        depsgraph = bpy.context.evaluated_depsgraph_get()
        hit, _point, _normal, _face, obj, _matrix = window.scene.ray_cast(depsgraph, origin, direction, distance=1000000.0)
    if not hit or obj is None:
        return None
    obj = getattr(obj, "original", obj)
    # A button can consist of several mesh glyphs parented to one labelled root.
    while obj is not None:
        action = obj.get("retro_action")
        if action:
            return str(action)
        obj = obj.parent
    return None


def _stop_runtime(context=None):
    runtime = _runtime()
    if runtime is not None:
        operator = runtime.get("operator")
        if operator is not None:
            try:
                operator.finish(context or bpy.context)
            except (ReferenceError, RuntimeError):
                pass
    bpy.app.driver_namespace.pop(_RUNTIME_KEY, None)
    manager = getattr(context or bpy.context, "window_manager", None)
    if manager is not None:
        manager[_RUNNING_KEY] = False


def _retro_on_load_pre(_unused):
    # Runtime only: this handler is installed by manual registration, never
    # embedded as an automatic execution requirement in the saved .blend.
    _stop_runtime()


class GALAGA_RETRO_OT_accion(bpy.types.Operator):
    bl_idname = "galaga_retro.accion"
    bl_label = "Acción de la interfaz retro"
    bl_description = "Navegar por la presentación retro o elegir la nave"
    accion: StringProperty(name="Acción", default="start")

    def execute(self, context):
        try:
            galaga_retro_action(self.accion, context)
        except (ValueError, RuntimeError) as error:
            self.report({"WARNING"}, str(error))
            return {"CANCELLED"}
        return {"FINISHED"}


class GALAGA_RETRO_OT_activar(bpy.types.Operator):
    bl_idname = "galaga_retro.activar"
    bl_label = "Activar interfaz retro"
    bl_description = "Activar clics en la vista 3D; Esc los desactiva sin cerrar Blender"
    reiniciar: BoolProperty(name="Mostrar inicio", default=True)
    reproducir: BoolProperty(name="Reproducir animación al activar", default=True)

    _active = False
    _timer = None
    _manager = None
    _window = None

    def invoke(self, context, _event):
        return self.execute(context)

    def execute(self, context):
        if bpy.app.background:
            self.report({"WARNING"}, "Los clics necesitan la ventana de Blender; usa galaga_retro_action para comprobar acciones.")
            return {"CANCELLED"}
        current = _runtime()
        if current is not None and getattr(current.get("operator"), "_active", False):
            self.report({"INFO"}, "La interfaz retro ya está activa. Esc la desactiva.")
            return {"FINISHED"}
        window = _window(context)
        if window is None:
            return {"CANCELLED"}
        try:
            if self.reiniciar:
                cambiar_pantalla("01_INICIO", context)
            else:
                elegir_nave(_selected_ship(context), context)
                _prepare_views(window)
        except (ValueError, RuntimeError) as error:
            self.report({"WARNING"}, str(error))
            return {"CANCELLED"}
        self._window = window
        self._manager = context.window_manager
        self._active = True
        self._timer = self._manager.event_timer_add(0.15, window=window)
        self._manager[_RUNNING_KEY] = True
        bpy.app.driver_namespace[_RUNTIME_KEY] = {"operator": self, "window": window}
        self._manager.modal_handler_add(self)
        if self.reproducir:
            _animation(window, True)
        self.report({"INFO"}, "Clics activos: 1/2/3 nave, Enter avanzar, P pausa, Espacio animación, Esc desactivar.")
        return {"RUNNING_MODAL"}

    def finish(self, _context=None):
        self._active = False
        if self._timer is not None and self._manager is not None:
            try:
                self._manager.event_timer_remove(self._timer)
            except (ReferenceError, RuntimeError):
                pass
            self._timer = None
        runtime = _runtime()
        if runtime is not None and runtime.get("operator") is self:
            bpy.app.driver_namespace.pop(_RUNTIME_KEY, None)
            if self._manager is not None:
                self._manager[_RUNNING_KEY] = False
        try:
            _redraw(self._window)
        except (ReferenceError, RuntimeError):
            pass

    def cancel(self, context):
        self.finish(context)

    def modal(self, context, event):
        if not self._active:
            return {"FINISHED"}
        if event.type == "ESC" and event.value == "PRESS":
            self.finish(context)
            self.report({"INFO"}, "Interfaz retro desactivada. Blender sigue abierto.")
            return {"FINISHED"}
        if event.type == "TIMER":
            _redraw(self._window)
            return {"PASS_THROUGH"}
        view = _view_under_mouse(self._window, event)
        if view is None:
            return {"PASS_THROUGH"}
        action = None
        # Consume the press before Blender's selection/box-select operator can
        # capture its release. Otherwise a button click merely selects its mesh.
        if event.type == "LEFTMOUSE" and event.value == "PRESS":
            action = _clicked_action(self._window, event, view)
        elif event.value == "PRESS":
            if event.type in {"ONE", "TWO", "THREE", "NUMPAD_1", "NUMPAD_2", "NUMPAD_3"}:
                action = "select_" + str({"ONE": 0, "TWO": 1, "THREE": 2, "NUMPAD_1": 0, "NUMPAD_2": 1, "NUMPAD_3": 2}[event.type])
            elif event.type in {"RET", "NUMPAD_ENTER"}:
                action = {
                    "01_INICIO": "start", "02_ELEGIR_NAVE": "confirm", "04_PAUSA": "resume",
                    "06_VICTORIA": "start", "07_DERROTA": "start", "08_DEMO_COMPLETA": "start",
                }.get(self._window.scene.name)
            elif event.type == "P":
                action = "resume" if self._window.scene.name == "04_PAUSA" else "pause" if self._window.scene.name in {"03_PARTIDA", "05_JEFE"} else None
            elif event.type == "SPACE":
                action = "play_pause"
        if action is None:
            return {"PASS_THROUGH"}
        try:
            galaga_retro_action(action, context)
        except (ValueError, RuntimeError) as error:
            self.report({"WARNING"}, str(error))
        return {"RUNNING_MODAL"}


class GALAGA_RETRO_OT_desactivar(bpy.types.Operator):
    bl_idname = "galaga_retro.desactivar"
    bl_label = "Desactivar clics"
    bl_description = "Dejar de capturar clics y atajos; mantener Blender abierto"

    def execute(self, context):
        _stop_runtime(context)
        return {"FINISHED"}


class GALAGA_RETRO_PT_panel(bpy.types.Panel):
    bl_idname = "GALAGA_RETRO_PT_panel"
    bl_label = "Interfaz retro"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Galaga"

    def draw(self, context):
        layout = self.layout
        runtime = _runtime()
        active = runtime is not None and getattr(runtime.get("operator"), "_active", False)
        layout.label(text="Presentación dentro de Blender")
        layout.label(text="Alt+P registra este panel.")
        layout.label(text="F3: Activar interfaz retro")
        layout.operator("galaga_retro.desactivar" if active else "galaga_retro.activar", text="Desactivar clics (Esc)" if active else "Activar clics")
        layout.separator()
        layout.label(text="Nave elegida: " + str(_selected_ship(context) + 1))
        row = layout.row(align=True)
        for index in range(3):
            row.operator("galaga_retro.accion", text="Nave " + str(index + 1), depress=index == _selected_ship(context)).accion = "select_" + str(index)
        for caption, action in (
            ("Inicio", "back"), ("Elegir nave", "start"), ("Confirmar / Partida", "confirm"),
            ("Pausa", "pause"), ("Continuar", "resume"), ("Jefe", "boss"),
            ("Victoria", "victory"), ("Derrota", "defeat"), ("Demo completa", "demo"),
            ("Reproducir / Detener", "play_pause"),
        ):
            layout.operator("galaga_retro.accion", text=caption).accion = action
        layout.separator()
        layout.label(text="Clic: botones en la vista 3D")
        layout.label(text="1/2/3: nave · Enter: avanzar")
        layout.label(text="P: pausa · Espacio: animar")
        layout.label(text="Esc: desactivar, sin salir")


def unregister():
    """Safe for another Alt+P, including an already-running modal instance."""
    _stop_runtime()
    for handler in tuple(bpy.app.handlers.load_pre):
        if getattr(handler, "__name__", "") == "_retro_on_load_pre":
            bpy.app.handlers.load_pre.remove(handler)
    for name in reversed(_CLASSES):
        old_class = getattr(bpy.types, name, None)
        if old_class is not None:
            try:
                bpy.utils.unregister_class(old_class)
            except RuntimeError:
                pass


def register():
    unregister()
    for name in _CLASSES:
        bpy.utils.register_class(globals()[name])
    bpy.app.handlers.load_pre.append(_retro_on_load_pre)
    for scene in bpy.data.scenes:
        if "nave_elegida" not in scene:
            scene["nave_elegida"] = 0
    elegir_nave(_selected_ship())


if __name__ == "__main__":
    register()
    if not bpy.app.background:
        bpy.ops.galaga_retro.activar("INVOKE_DEFAULT")
