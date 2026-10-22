"""Check button hit geometry in the saved .blend, without desktop automation."""
import bpy
import json
from pathlib import Path
from mathutils import Vector

OUT=Path(__file__).resolve().parents[1]/'previews'/'Retro'
cases=[];errors=[]
for scene in bpy.data.scenes:
    if scene.name=='08_DEMO_COMPLETA':continue
    bpy.context.window.scene=scene
    scene.frame_set(1);bpy.context.view_layer.update()
    depsgraph=bpy.context.evaluated_depsgraph_get()
    for button in scene.objects:
        action=button.get('retro_action')
        if not action or button.get('texto') or button.type!='MESH':continue
        center=button.matrix_world.translation
        # Test the centre and clear space near both ends of the button.
        for fraction in [0.0,-.35,.35]:
            x=center.x+button.dimensions.x*fraction
            ray=Vector((x,center.y,32))
            hit,point,normal,index,obj,matrix=scene.ray_cast(depsgraph,ray,Vector((0,0,-1)))
            actual=obj.get('retro_action') if hit and obj else None
            passed=actual==action
            cases.append({'scene':scene.name,'button':button.name,'offset':fraction,
                          'expected':action,'actual':actual,'hit_object':obj.name if obj else None,'pass':passed})
            if not passed:errors.append(f'{scene.name}/{button.name}: {fraction} hit {obj.name if obj else None}')
report={'scope':'Rayos contra la geometria guardada; no prueba de eventos de escritorio',
        'status':'PASS' if not errors else 'FAIL','cases':cases,'errors':errors}
(OUT/'validacion_botones_3d.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('RETRO_BUTTON_GEOMETRY',report['status'],len(cases),'rays',errors)
if errors:raise RuntimeError('Button surfaces are occluded')
