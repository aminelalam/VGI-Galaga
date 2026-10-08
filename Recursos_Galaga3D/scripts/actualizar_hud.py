import bpy, json
ctrl=bpy.data.objects['CONTROL_HUD']
def clamp(v,a,b): return max(a,min(b,v))
def hide(ob,value): ob.hide_render=value; ob.hide_viewport=value
def clip(ob,right):
    original=json.loads(ob['clip_original']);vv=[];ff=[]
    for face in original['f']:
        points=[original['v'][i] for i in face];out=[]
        for a,b in zip(points,points[1:]+points[:1]):
            ia=a[0]<=right;ib=b[0]<=right
            if ia: out.append(a)
            if ia!=ib:
                t=(right-a[0])/(b[0]-a[0]);out.append([a[j]+t*(b[j]-a[j]) for j in range(3)])
        # Remove coincident intersections and zero-area faces at HP=0 / boundaries.
        clean=[]
        for p in out:
            if not clean or sum((p[j]-clean[-1][j])**2 for j in range(3))>1e-14: clean.append(p)
        if len(clean)>1 and sum((clean[0][j]-clean[-1][j])**2 for j in range(3))<1e-14: clean.pop()
        out=clean
        area=abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(out,out[1:]+out[:1]))) if len(out)>=3 else 0
        if len(out)>=3 and area>1e-12:
            start=len(vv);vv+=out;ff.append(tuple(range(start,start+len(out))))
    ob.data.clear_geometry();ob.data.from_pydata(vv,[],ff);ob.data.update()
p=int(clamp(ctrl['puntos'],0,999999));r=int(clamp(ctrl['record'],0,999999))
v=int(clamp(ctrl['vidas'],0,3));hp=int(clamp(ctrl['vida_jefe'],0,24));w=int(clamp(ctrl['oleada'],1,3))
bpy.data.objects['TXT_Puntos'].data.body=f'{p:06d}'
bpy.data.objects['TXT_Record'].data.body=f'{r:06d}'
bpy.data.objects['TXT_Oleada'].data.body=f'{w:02d} / 03'
bpy.data.objects['TXT_Vidas'].data.body=f'{v} / 3'
bpy.data.objects['TXT_VidaJefe'].data.body=f'{hp} / 24'
b=bool(ctrl['plano_B'])
bpy.data.objects['TXT_Plano'].data.body='PLANO B' if b else 'PLANO A'
bpy.data.objects['TXT_Plano'].data.materials[0]=bpy.data.materials['#ffba52_1000' if b else '#36e6ed_1000']
bpy.data.objects['TXT_Distancia'].data.body='LEJOS' if b else 'CERCA'
seconds=clamp(float(ctrl['recarga_plano']),0,1.2)
bpy.data.objects['TXT_Recarga'].data.body=f'{seconds:.1f} s' if seconds else 'LISTO'
hide(bpy.data.objects['TXT_Invulnerable'],not ctrl['invulnerable'])
hide(bpy.data.objects['TXT_Doble'],not ctrl['doble_disparo'])
for ob in bpy.data.objects:
    group=ob.get('grupo_hud','')
    if group=='Icono_plano_A': hide(ob,b)
    if group=='Icono_plano_B': hide(ob,not b)
    if 'indice_vida' in ob: hide(ob,v<ob['indice_vida'])
    if ob.name.startswith('JEFE_') or ob.name in ('TXT_JEFE','TXT_VidaJefe'): hide(ob,not ctrl['mostrar_jefe'])
    if 'clip_original' in ob:
        if group=='JEFE_Relleno': right=(320+28+584*hp/24-640)/100
        elif group=='VIDAS_Relleno': right=(24+28+280*v/3-640)/100
        else: right=(548+272*(1-seconds/1.2)-640)/100
        clip(ob,right)
print('HUD actualizado: puntos',p,'vidas',v,'jefe',hp,'plano','B' if b else 'A')

