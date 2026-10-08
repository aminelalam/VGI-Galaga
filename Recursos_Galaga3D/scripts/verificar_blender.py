"""Audita el .blend abierto sin guardar cambios; ejecutar con Blender en background."""
import bpy
import json
import math
from pathlib import Path

BASE=Path(__file__).resolve().parents[1]
errors=[]
def check(condition,message):
    if not condition: errors.append(message)
def area(ob):
    return sum(abs(sum(ob.data.vertices[a].co.x*ob.data.vertices[b].co.y-ob.data.vertices[b].co.x*ob.data.vertices[a].co.y for a,b in zip(list(p.vertices),list(p.vertices)[1:]+list(p.vertices)[:1])))/2 for p in ob.data.polygons)
def group(name): return [o for o in bpy.data.objects if o.get('grupo_hud')==name]
def update():
    exec(bpy.data.texts['ACTUALIZAR_HUD.py'].as_string(),{})
    bpy.context.view_layer.update()

scene_names=['01_HUD_TRANSPARENTE','02_PREVIEW_INTERFAZ','03_PANTALLA_PAUSA']
for name in scene_names:
    check(name in bpy.data.scenes,'Falta escena '+name)
    sc=bpy.data.scenes[name]
    check((sc.render.resolution_x,sc.render.resolution_y,sc.render.resolution_percentage)==(1280,720,100),'Resolucion incorrecta '+name)
    check(sc.camera is not None and sc.camera.data.type=='ORTHO','Camara incorrecta '+name)
    check(sc.render.filepath.replace('\\','/').startswith('//../previews/'),'Ruta render no portable '+name)
fonts=[f for f in bpy.data.fonts if f.filepath!='<builtin>']
check(len(fonts)==2,'Se esperan exactamente las dos fuentes Vera')
for f in fonts:
    check(bool(f.packed_file),'Fuente no empaquetada '+f.name)
    check(f.filepath.replace('\\','/') in ('//../fonts/Vera.ttf','//../fonts/VeraBd.ttf'),'Fuente externa '+f.name)
check((BASE/'fonts/bitstream-vera-license.txt').is_file(),'Falta licencia de fuentes')
check(not list(bpy.data.images),'La interfaz vectorial no debe depender de imagenes externas')
check(bpy.data.texts['ACTUALIZAR_HUD.py'].as_string().strip()==(BASE/'scripts/actualizar_hud.py').read_text(encoding='utf-8').strip(),'Script interno no coincide con externo')
pause_bars=[o for o in group('Boton_pausa') if o.name in ('Boton_pausa_relleno_02','Boton_pausa_relleno_03')]
check(len(pause_bars)==2 and all(area(o)>0 for o in pause_bars),'Faltan las dos barras del boton de pausa')

c=bpy.data.objects['CONTROL_HUD']
keys=['puntos','record','oleada','vidas','vida_jefe','mostrar_jefe','plano_B','recarga_plano','invulnerable','doble_disparo']
original={k:c[k] for k in keys}
results={}
try:
    for value,expected in [(-5,'000000'),(0,'000000'),(123,'000123'),(999999,'999999'),(1000000,'999999')]:
        c['puntos']=value;c['record']=value;update()
        check(bpy.data.objects['TXT_Puntos'].data.body==expected,'Puntos incorrectos '+str(value))
        check(bpy.data.objects['TXT_Record'].data.body==expected,'Record incorrecto '+str(value))
    results['puntos_y_record']={'casos':5,'limites':[0,999999],'cifras':6}
    for field,gname,maxvalue,left,width in [('vidas','VIDAS_Relleno',3,24+28,280),('vida_jefe','JEFE_Relleno',24,320+28,584)]:
        samples=[]
        for value in range(maxvalue+1):
            c[field]=value;update();obs=group(gname)
            total=sum(area(o) for o in obs)
            right=(left+width*value/maxvalue-640)/100
            check(all(v.co.x<=right+1e-6 for o in obs for v in o.data.vertices),f'Recorte excedido {field}={value}')
            check(all(area(o)>=0 for o in obs),f'Area negativa {field}={value}')
            check(all(math.isfinite(component) for o in obs for v in o.data.vertices for component in v.co),f'Vertice no finito {field}={value}')
            check(all(p.area>1e-12 for o in obs for p in o.data.polygons),f'Cara degenerada {field}={value}')
            if value==0: check(total<1e-10,'Relleno visible con '+field+'=0')
            if samples: check(total>=samples[-1]['area']-1e-9,'Relleno no monotono '+field)
            if field=='vidas':
                visible={o['indice_vida'] for o in bpy.data.objects if 'indice_vida' in o and not o.hide_render}
                check(len(visible)==value,'Iconos vidas incorrectos '+str(value))
            samples.append({'valor':value,'area':round(total,9)})
        results[field]={'casos':len(samples),'relleno_monotono':True,'cero_sin_relleno':True,'muestras':samples}
    for b in (False,True):
        c['plano_B']=b;update()
        check(all(o.hide_render==b for o in group('Icono_plano_A')),'Icono A incorrecto')
        check(all(o.hide_render==(not b) for o in group('Icono_plano_B')),'Icono B incorrecto')
        check(bpy.data.objects['TXT_Plano'].data.body==('PLANO B' if b else 'PLANO A'),'Texto plano incorrecto')
        check(bpy.data.objects['TXT_Distancia'].data.body==('LEJOS' if b else 'CERCA'),'Texto distancia incorrecto')
    results['planos']=['A/CERCA/circulo/cian','B/LEJOS/rombo/ambar']
    for show in (False,True):
        c['mostrar_jefe']=show;update()
        boss=[o for o in bpy.data.objects if o.name.startswith('JEFE_') or o.name in ('TXT_JEFE','TXT_VidaJefe')]
        check(all(o.hide_render==(not show) for o in boss),'Visibilidad jefe incorrecta')
    for field,name in [('invulnerable','TXT_Invulnerable'),('doble_disparo','TXT_Doble')]:
        for state in (False,True):
            c[field]=state;update();check(bpy.data.objects[name].hide_render==(not state),'Estado incorrecto '+field)
    cooldown=[]
    for seconds in (0,.6,1.2):
        c['recarga_plano']=seconds;update();cooldown.append(area(bpy.data.objects['Recarga_Relleno']))
    check(cooldown[0]>cooldown[1]>cooldown[2] and cooldown[2]<1e-10,'Recarga incorrecta')
    results['recarga']={'segundos':[0,.6,1.2],'areas':cooldown}
    # Evidence of actual opened file with changed values, no modification to .blend.
    for k,v in original.items(): c[k]=v
    c['vidas']=2;c['vida_jefe']=12;c['plano_B']=True;c['recarga_plano']=.6;update()
    sc=bpy.data.scenes['02_PREVIEW_INTERFAZ'];bpy.context.window.scene=sc
    previous=sc.render.filepath;sc.render.filepath='//../previews/verificacion_estado.png'
    bpy.ops.render.render(write_still=True,scene=sc.name)
    sc.render.filepath=previous
finally:
    for k,v in original.items(): c[k]=v
    update()

report={'status':'PASS' if not errors else 'FAIL','blender_version':bpy.app.version_string,'archivo':'blender/Galaga3D_Interfaz.blend','escenas':scene_names,'fuentes_locales_y_empaquetadas':True,'rutas_render_relativas':True,'boton_pausa_barras':len(pause_bars),'script_interno_coincide':True,'pruebas':results,'errors':errors,'blend_modificado':False}
(BASE/'validacion_blender_final.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('BLENDER_AUDIT',report['status'],'errors',errors)
if errors: raise RuntimeError('Validacion Blender no superada')
