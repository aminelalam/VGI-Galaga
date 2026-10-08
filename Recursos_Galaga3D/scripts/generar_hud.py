"""Genera los recursos HUD originales de Galaga 3D con Pillow, sin Blender.

Ejecutar desde cualquier directorio: python generar_hud.py
Los SVG usan primitivas vectoriales; los PNG son RGBA y alpha no premultiplicado.
"""
from __future__ import annotations

import json
import math
import random
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "hud"
SCALE = 4
PAL = {"navy": "#101a2c", "ice": "#d8edf3", "cyan": "#36e6ed",
       "amber": "#ffba52", "red": "#fa5269", "purple": "#9478ff"}


def rgba(color, alpha=255):
    h = PAL.get(color, color).lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4)) + (alpha,)


class Vector:
    """Una fuente de primitivas compartida por SVG y PNG."""
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.im = Image.new("RGBA", (w*SCALE, h*SCALE))
        self.draw = ImageDraw.Draw(self.im)
        self.elements = []

    def attrs(self, fill=None, stroke=None, width=1, alpha=255):
        result = f'fill="{PAL.get(fill, fill) if fill else "none"}"'
        if stroke:
            result += f' stroke="{PAL.get(stroke, stroke)}" stroke-width="{width}" stroke-linejoin="round" stroke-linecap="round"'
        if alpha != 255:
            result += f' opacity="{alpha/255:.6f}"'
        return result

    def poly(self, pts, fill=None, stroke=None, width=1, alpha=255):
        self.elements.append(f'<polygon points="{" ".join(f"{x},{y}" for x,y in pts)}" {self.attrs(fill, stroke, width, alpha)}/>')
        p = [(round(x*SCALE), round(y*SCALE)) for x,y in pts]
        if fill:
            self.draw.polygon(p, fill=rgba(fill, alpha))
        if stroke:
            self.draw.line(p + [p[0]], fill=rgba(stroke, alpha), width=round(width*SCALE), joint="curve")

    def line(self, pts, stroke="ice", width=1, alpha=255):
        self.elements.append(f'<polyline points="{" ".join(f"{x},{y}" for x,y in pts)}" {self.attrs(None, stroke, width, alpha)}/>')
        p = [(round(x*SCALE), round(y*SCALE)) for x,y in pts]
        self.draw.line(p, fill=rgba(stroke, alpha), width=max(1, round(width*SCALE)), joint="curve")
        r = width*SCALE/2
        for x,y in (p[0], p[-1]):
            self.draw.ellipse((x-r,y-r,x+r,y+r), fill=rgba(stroke, alpha))

    def ellipse(self, box, fill=None, stroke=None, width=1, alpha=255):
        x0,y0,x1,y1 = box
        self.elements.append(f'<ellipse cx="{(x0+x1)/2}" cy="{(y0+y1)/2}" rx="{(x1-x0)/2}" ry="{(y1-y0)/2}" {self.attrs(fill,stroke,width,alpha)}/>')
        self.draw.ellipse(tuple(round(v*SCALE) for v in box), fill=rgba(fill,alpha) if fill else None,
                          outline=rgba(stroke,alpha) if stroke else None, width=max(1,round(width*SCALE)))

    def rect(self, box, fill, alpha=255):
        x0,y0,x1,y1 = box
        self.elements.append(f'<rect x="{x0}" y="{y0}" width="{x1-x0}" height="{y1-y0}" {self.attrs(fill, alpha=alpha)}/>')
        self.draw.rectangle(tuple(round(v*SCALE) for v in box), fill=rgba(fill,alpha))

    def save(self, name):
        im = self.im.resize((self.w,self.h), Image.Resampling.LANCZOS)
        im.save(OUT / f"{name}.png")
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}">\n<title>{escape(name)} — Galaga 3D</title>\n' + "\n".join(self.elements) + "\n</svg>\n"
        (OUT / f"{name}.svg").write_text(svg, encoding="utf-8")
        return im


assets = {}
guides = {}


def save(name, v, meaning):
    assets[name] = v.save(name)
    guides[name] = {"meaning": meaning, "size": [v.w,v.h], "anchor_px": [v.w/2,v.h/2]}


def bar(kind, w, color, segments):
    h = 48
    outer = [(6,16),(17,5),(w-20,5),(w-6,19),(w-6,32),(w-17,43),(20,43),(6,29)]
    inner = [(25,14),(w-32,14),(w-24,22),(w-24,32),(32,32),(24,24)]
    bg = Vector(w,h)
    bg.poly(outer, "navy", alpha=236)
    bg.poly(inner, "ice", alpha=18)
    save(f"vida_{kind}_fondo", bg, "Fondo oscuro del canal, detrás del relleno.")
    frame = Vector(w,h)
    frame.poly(outer, stroke="ice",width=1,alpha=135)
    frame.line([(6,19),(6,16),(17,5),(83,5)],color,2.5)
    frame.line([(w-83,43),(w-17,43),(w-6,32),(w-6,26)],color,2.5)
    frame.line([(25,11),(w-33,11)],"ice",1,alpha=80)
    frame.poly([(14,20),(21,20),(21,28),(14,28)],color)
    frame.poly([(w-22,20),(w-15,20),(w-15,28),(w-22,28)],color,alpha=90)
    left,right,top,bottom = 28, w-28, 17,31
    for i in range(1,segments):
        x = left+(right-left)*i/segments
        frame.line([(x,15),(x,18)], "ice",1,alpha=170)
        frame.line([(x,31),(x,34)], "ice",1,alpha=100)
        if segments > 3:
            frame.line([(x,18),(x,30)], "navy",1.4,alpha=210)
    save(f"vida_{kind}_marco", frame, "Contorno y marcas; dibujar sobre el relleno.")
    fill = Vector(w,h)
    if segments == 3:
        for i in range(segments):
            x0 = left+(right-left)*i/segments+2
            x1 = left+(right-left)*(i+1)/segments-2
            fill.poly([(x0+5,top),(x1,top),(x1-5,bottom),(x0,bottom)],color)
            fill.line([(x0+8,top+2),(x1-4,top+2)],"ice",1,alpha=155)
    else:
        fill.poly([(left+7,top),(right,top),(right-7,bottom),(left,bottom)],color)
        fill.poly([(left+7,top),(right,top),(right-2,top+4),(left+5,top+4)], "ice",alpha=96)
        fill.line([(left+2,bottom),(right-8,bottom)],"purple",1,alpha=190)
    save(f"vida_{kind}_relleno", fill, "Relleno a máximo. Recortar horizontalmente, conservando ancho del quad y UV.")
    for layer in ("fondo","marco","relleno"):
        guides[f"vida_{kind}_{layer}"].update({"fill_rect_px": [left,top,right-left,bottom-top],
            "max_value": segments, "value_kind": "vidas_discretas" if segments==3 else "HP"})


def fighter(v, faded=False):
    color = "navy" if faded else "ice"
    edge = "ice" if faded else "cyan"
    a = 85 if faded else 255
    v.poly([(32,5),(38,23),(48,30),(55,47),(40,42),(37,55),(27,55),(24,42),(9,47),(16,30),(26,23)], color,edge,1.7,a)
    v.poly([(32,17),(36,29),(32,37),(28,29)], "purple",alpha=a)
    v.line([(19,34),(16,41)],edge,2,a)
    v.line([(45,34),(48,41)],edge,2,a)
    v.line([(28,56),(28,59)],edge,3,a)
    v.line([(36,56),(36,59)],edge,3,a)


def icons():
    v = Vector(64,64); fighter(v); save("vida_nave",v,"Una vida del jugador. Repetir hasta un máximo de 3.")
    v = Vector(64,64); fighter(v,True); save("vida_nave_inactiva",v,"Ranura de vida perdida; decorar, sin alterar el número de vidas.")
    v = Vector(64,64)
    v.ellipse((5,5,59,59),"navy","cyan",2.5)
    v.ellipse((10,10,54,54),stroke="ice",width=.6,alpha=85)
    v.line([(22,44),(32,20),(42,44)],"ice",3)
    v.line([(27,34),(37,34)],"ice",3)
    v.ellipse((29,54,35,60),"cyan")
    save("plano_A",v,"Plano A: círculo cian + A. Acompañar con PLANO A · CERCA.")
    v = Vector(64,64)
    v.poly([(32,3),(61,32),(32,61),(3,32)],"navy","amber",2.5)
    v.poly([(32,9),(55,32),(32,55),(9,32)],stroke="ice",width=.6,alpha=85)
    v.line([(25,20),(25,44),(36,44),(42,39),(42,35),(36,32),(25,32),(36,32),(40,28),(40,24),(36,20),(25,20)],"ice",2.7)
    save("plano_B",v,"Plano B: rombo ámbar + B. Acompañar con PLANO B · LEJOS.")
    v = Vector(64,64)
    v.poly([(14,6),(50,6),(58,14),(58,50),(50,58),(14,58),(6,50),(6,14)],"navy","ice",1.2)
    v.rect((22,19,28,45),"ice");v.rect((36,19,42,45),"ice")
    v.line([(6,21),(6,14),(14,6),(25,6)],"cyan",2.2)
    save("pausa",v,"Pausa. El icono no pausa la simulación por sí mismo.")
    v = Vector(64,64)
    v.poly([(32,5),(54,14),(50,38),(42,49),(32,57),(22,49),(14,38),(10,14)],"navy","cyan",2.5)
    v.poly([(32,12),(46,18),(43,37),(32,48),(21,37),(18,18)],stroke="ice",width=1.4)
    v.line([(32,15),(32,44)],"cyan",2)
    v.line([(23,25),(41,25)],"cyan",2)
    save("escudo",v,"Señal visual de invulnerabilidad; no añade una mecánica de escudo a P0.")
    v = Vector(64,64)
    v.poly([(10,59),(10,20),(20,5),(30,20),(30,59),(24,59),(24,23),(20,16),(16,23),(16,59)],"cyan")
    v.poly([(34,59),(34,20),(44,5),(54,20),(54,59),(48,59),(48,23),(44,16),(40,23),(40,59)],"purple")
    v.line([(20,27),(20,41)],"ice",2)
    v.line([(44,27),(44,41)],"ice",2)
    save("doble_disparo",v,"Dos proyectiles paralelos; ampliación opcional P2.")
    v = Vector(96,96)
    for pts in ([(32,8),(14,8),(8,14),(8,32)],[(64,8),(82,8),(88,14),(88,32)],
                [(8,64),(8,82),(14,88),(32,88)],[(64,88),(82,88),(88,82),(88,64)]):
        v.line(pts,"cyan",2)
    v.ellipse((31,31,65,65),stroke="ice",width=1,alpha=190)
    for a,b in (((48,19),(48,34)),((48,62),(48,77)),((19,48),(34,48)),((62,48),(77,48))):
        v.line([a,b],"cyan",1.8)
    v.ellipse((45.5,45.5,50.5,50.5),"cyan")
    save("mira",v,"Mira decorativa opcional. No modifica la puntería ni las colisiones del diseño.")
    v = Vector(64,64)
    v.poly([(32,6),(59,53),(56,58),(8,58),(5,53)],"navy","amber",2.7)
    v.line([(32,23),(32,38)],"ice",4)
    v.ellipse((29.5,45,34.5,50),"ice")
    save("aviso",v,"Alerta de ataque. Acompañar con letra del plano y texto.")
    v = Vector(64,64)
    v.poly([(8,14),(24,14),(48,32),(24,50),(8,50),(32,32)],"cyan")
    v.line([(33,13),(57,32),(33,51)],"ice",1.5)
    save("flecha",v,"Flecha hacia la derecha. Rotar para otras direcciones.")


def atlas():
    width, height = 1024,512
    canvas = Image.new("RGBA",(width,height))
    x,y,row_h = 4,4,0
    meta = {"image":"atlas_hud.png", "size_px":[width,height], "format":"RGBA8",
            "alpha":"straight (no premultiplicado)", "pixel_origin":"top_left",
            "rect_order":"[x, y, width, height]", "gutter_px":4, "extrusion_px":2,
            "uv_order":"[u_min, v_min, u_max, v_max]",
            "uv_top_left_usage":"Textura con las filas PNG sin invertir; v=0 corresponde a la fila superior del PNG.",
            "uv_bottom_left_usage":"Invertir filas al cargar el PNG. v=0 corresponde a la parte inferior de la imagen.",
            "sprites":{}}
    for name,im in assets.items():
        w,h=im.size
        if x+w+4 > width:
            x,y,row_h = 4,y+row_h+8,0
        if y+h+4 > height:
            raise ValueError("El atlas requiere mayor altura")
        # Extrusión de bordes para filtrado lineal; rect excluye los dos píxeles.
        for d in (1,2):
            canvas.paste(im.crop((0,0,w,1)),(x,y-d))
            canvas.paste(im.crop((0,h-1,w,h)),(x,y+h+d-1))
            canvas.paste(im.crop((0,0,1,h)),(x-d,y))
            canvas.paste(im.crop((w-1,0,w,h)),(x+w+d-1,y))
        for dx in (-2,-1,w,w+1):
            for dy in (-2,-1,h,h+1):
                canvas.putpixel((x+dx,y+dy),im.getpixel((0 if dx<0 else w-1,0 if dy<0 else h-1)))
        canvas.paste(im,(x,y))
        meta["sprites"][name] = {"rect_px":[x,y,w,h],
            "uv_top_left":[x/width,y/height,(x+w)/width,(y+h)/height],
            "uv_bottom_left":[x/width,1-(y+h)/height,(x+w)/width,1-y/height],
            **guides[name]}
        x += w+8
        row_h=max(row_h,h)
    canvas.save(OUT / "atlas_hud.png")
    (OUT / "atlas_hud.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return meta


def font(size,bold=False):
    path=ROOT/"fonts"/("VeraBd.ttf" if bold else "Vera.ttf")
    if not path.exists():
        raise FileNotFoundError(f"Falta la fuente incluida en el pack: {path}")
    return ImageFont.truetype(str(path),size)


def preview():
    im=Image.new("RGBA",(1280,720),rgba("navy"))
    d=ImageDraw.Draw(im)
    random.seed(721)
    for i in range(115):
        x,y=random.randint(20,1260),random.randint(130,590)
        a=random.randint(35,105)
        d.ellipse((x,y,x+1,y+1),fill=rgba("ice",a))
    # Campo esquemático neutro: deja libres las áreas del HUD.
    d.line([(260,601),(440,231),(840,231),(1020,601)],fill=rgba("cyan",38),width=1)
    for yy in (285,345,420,513,601):
        frac=(yy-231)/(601-231)
        d.line([(440-180*frac,yy),(840+180*frac,yy)],fill=rgba("cyan",30),width=1)
    d.line([(24,112),(1256,112)],fill=rgba("ice",40))
    d.text((28,24),"GALAGA 3D",font=font(26,True),fill=rgba("ice"))
    d.text((28,58),"HUD / RECURSOS ORIGINALES",font=font(11),fill=rgba("cyan"))
    d.text((28,82),"PUNTOS 012500    OLEADA 03",font=font(15),fill=rgba("ice"))
    d.text((320,23),"JEFE / 24 HP",font=font(13),fill=rgba("red"))
    for layer in ("fondo","relleno","marco"):
        im.alpha_composite(assets[f"vida_jefe_{layer}"],(320,44))
    d.text((908,91),"24 / 24",font=font(12),fill=rgba("ice"))
    im.alpha_composite(assets["pausa"],(1188,27))
    d.text((1205,94),"P",font=font(11),fill=rgba("ice"))
    # Aviso de un ataque del plano B con señal redundante.
    im.alpha_composite(assets["aviso"],(497,153))
    im.alpha_composite(assets["plano_B"],(568,153))
    d.text((646,163),"ATAQUE / PLANO B",font=font(16),fill=rgba("amber"))
    d.text((646,189),"LEJOS",font=font(12),fill=rgba("ice"))
    im.alpha_composite(assets["mira"],(592,312))
    d.text((546,425),"MIRA OPCIONAL",font=font(12),fill=rgba("ice",170))
    # Banda inferior, con reservas de espacio a 24 px del borde.
    d.rectangle((0,596,1280,720),fill=rgba("navy",245))
    d.line([(24,600),(1256,600)],fill=rgba("ice",70))
    d.text((28,614),"VIDAS / 3 DE 3",font=font(13),fill=rgba("ice"))
    for layer in ("fondo","relleno","marco"):
        im.alpha_composite(assets[f"vida_jugador_{layer}"],(24,634))
    for x in (380,426,472):
        ship=assets["vida_nave"].resize((42,42),Image.Resampling.LANCZOS)
        im.alpha_composite(ship,(x,638))
    im.alpha_composite(assets["escudo"],(590,628))
    d.text((578,697),"INVULNERABLE",font=font(10),fill=rgba("cyan"))
    im.alpha_composite(assets["doble_disparo"],(697,628))
    d.text((693,697),"DOBLE / P2",font=font(10),fill=rgba("purple"))
    im.alpha_composite(assets["plano_A"],(929,628))
    d.text((1007,636),"PLANO A",font=font(19),fill=rgba("cyan"))
    d.text((1007,666),"CERCA / E PARA CAMBIAR",font=font(12),fill=rgba("ice"))
    d.text((28,697),"Representación de muestra: escudo = invulnerabilidad; doble disparo = opción P2.",font=font(10),fill=rgba("ice",150))
    # ImageDraw escribe alpha en lugar de mezclarlo; aplanar contra navy.
    flat=Image.new("RGBA",im.size,rgba("navy"))
    flat.alpha_composite(im)
    flat.convert("RGB").save(OUT/"preview_hud.png")
    # Carta de componentes, a escala 1:1 para comprobar transparencia y lectura.
    sheet=Image.new("RGBA",(1280,720),rgba("navy"))
    dd=ImageDraw.Draw(sheet)
    dd.text((32,24),"GALAGA 3D / COMPONENTES HUD",font=font(23),fill=rgba("ice"))
    dd.text((32,62),"PNG RGBA + SVG EDITABLE / CAPAS INDEPENDIENTES / ATLAS 1024 x 512",font=font(12),fill=rgba("cyan"))
    for kind,x,y in (("jugador",32,112),("jefe",520,112)):
        dd.text((x,y),f"VIDA {kind.upper()}",font=font(17),fill=rgba("ice"))
        for j,layer in enumerate(("fondo","relleno","marco")):
            name=f"vida_{kind}_{layer}"
            sheet.alpha_composite(assets[name],(x,y+34+j*69))
            dd.text((x,y+81+j*69),layer.upper(),font=font(10),fill=rgba("ice",150))
        for layer in ("fondo","relleno","marco"):
            sheet.alpha_composite(assets[f"vida_{kind}_{layer}"],(x,y+251))
        dd.text((x,y+300),"COMPOSICIÓN A MÁXIMO",font=font(10),fill=rgba("cyan"))
    names=[n for n in assets if not n.startswith("vida_jugador") and not n.startswith("vida_jefe")]
    for i,name in enumerate(names):
        x=32+(i%5)*248;y=470+(i//5)*112
        sheet.alpha_composite(assets[name],(x,y))
        dd.text((x+106,y+25),name.replace("_"," ").upper(),font=font(10),fill=rgba("ice"))
    flat=Image.new("RGBA",sheet.size,rgba("navy"))
    flat.alpha_composite(sheet)
    flat.convert("RGB").save(OUT/"componentes_hud.png")


def readme():
    content = """# HUD original · Galaga 3D

16 sprites originales: PNG **RGBA8** transparentes con alpha recto y SVG editables. `atlas_hud.png` agrupa los mismos sprites a 1024 × 512. No usa recursos gráficos de Namco. `preview_hud.png` muestra composición a 1280 × 720; `componentes_hud.png` muestra cada capa por separado. Los PNG de las vistas previas tienen fondo opaco y no son sprites.

## Barras por capas

Dibujar en este orden, **con la misma posición y dimensiones**: `vida_*_fondo`, `vida_*_relleno`, `vida_*_marco`. Jugador: 336 × 48; jefe: 640 × 48. El marco tiene centro transparente, por lo que no tapa el relleno. El fondo garantiza contraste. Labels y contadores se dibujan como texto de la aplicación y pueden traducirse.

El jugador conserva **3 vidas**: las tres celdas representan 3/3, 2/3, 1/3 o 0/3. No se introduce vida continua ni una regla adicional. El jefe conserva **24 HP**, con una marca por HP. `vida_nave.png` se puede repetir tres veces como alternativa a la barra; `vida_nave_inactiva.png` decora las reservas perdidas.

Para actualizar una barra: `r = clamp(valor / maximo, 0, 1)`. Conserva el quad completo y recorta **solo el relleno** mediante scissor/máscara en su rectángulo interno. Los límites internos son x=28..308 para jugador y x=28..612 para jefe; y=17..31. Limita la derecha a `28 + ancho_interno * r`. A 0 no dibujes el relleno. No escales horizontalmente la textura: deformaría las celdas. La ficha de cada sprite del atlas incorpora `fill_rect_px` y `max_value`.

## Iconos y reglas

`plano_A`: círculo + cian + letra A; usar texto **PLANO A · CERCA**. `plano_B`: rombo + ámbar + letra B; texto **PLANO B · LEJOS**. No depender solo del color. Iconos de plano, nave, pausa, escudo, doble disparo, aviso y flecha: 64 × 64. Mira: 96 × 96. Son adecuados a 48–64 px en un HUD de 1280 × 720; se recomienda mantener 24 px de margen al borde.

`escudo` es un indicador visual de **invulnerabilidad** ya prevista; no añade un power-up de escudo a P0. `doble_disparo` pertenece a P2 opcional. La mira es una ayuda visual opcional y no cambia la puntería. `aviso` acompaña la señal del plano de ataque del jefe. La flecha apunta a la derecha; girarla por transformaciones para otros sentidos. El prototipo no cambia reglas por cargar estos archivos.

## Atlas y OpenGL

`atlas_hud.json` contiene `rect_px: [x,y,ancho,alto]` con origen **arriba a la izquierda**, y dos UV explícitas `[u_min,v_min,u_max,v_max]`:

- `uv_top_left`: filas PNG sin invertir; v=0 corresponde a la fila superior del PNG. Asociar v mínima al vértice superior del quad para verlo derecho.
- `uv_bottom_left`: invertir filas al cargar; v=0 corresponde a la parte inferior. Asociar v máxima al vértice superior del quad.

Cada sprite tiene 4 px de separación y 2 px de extrusión fuera de su rectángulo. Los rects excluyen la extrusión. Para este HUD, usar `GL_LINEAR`, `GL_CLAMP_TO_EDGE` y no generar mipmaps del atlas sin ampliar márgenes. Texturas con alpha **no premultiplicado**: `glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)`. Desactivar escritura de profundidad para el HUD y dibujarlo después de la escena 3D. El RGB de píxeles transparentes no contiene un fondo blanco.

## Regenerar y editar

`scripts/generar_hud.py` requiere Python y Pillow; no requiere Blender. Todas las formas usan una fuente compartida para SVG y rasterizado a 4× con reducción antialias. Los SVG no dependen de fuentes instaladas: las letras A/B están dibujadas con líneas. Las vistas previas usan exclusivamente las fuentes libres locales `fonts/Vera.ttf` y `fonts/VeraBd.ttf`; su licencia se incluye en `fonts/bitstream-vera-license.txt`. No hay rutas a fuentes del sistema. Los SVG son masters editables; si se editan manualmente, no ejecutar el generador sin guardar una copia, porque regenera el pack desde el script.

Paleta: navy `#101a2c`, hielo `#d8edf3`, cian `#36e6ed`, ámbar `#ffba52`, rojo `#fa5269`, morado `#9478ff`. Diseño geométrico original para este proyecto. No hay dependencias de red.
"""
    (OUT/"README.md").write_text(content,encoding="utf-8")


def validate(meta):
    packed=Image.open(OUT/"atlas_hud.png")
    issues=[]
    rects=[]
    for name,im in assets.items():
        x,y,w,h=meta["sprites"][name]["rect_px"]
        rects.append((name,x,y,x+w,y+h))
        if im.mode!="RGBA" or im.getextrema()[3][0]!=0:
            issues.append(f"{name}: falta transparencia RGBA")
        if packed.crop((x,y,x+w,y+h)).tobytes()!=im.tobytes():
            issues.append(f"{name}: atlas difiere del PNG")
        if not all(0<=n<=1 for n in meta["sprites"][name]["uv_top_left"]+meta["sprites"][name]["uv_bottom_left"]):
            issues.append(f"{name}: UV fuera de 0..1")
    for i,a in enumerate(rects):
        for b in rects[i+1:]:
            if max(a[1],b[1])<min(a[3],b[3]) and max(a[2],b[2])<min(a[4],b[4]):
                issues.append(f"Rectángulos solapados: {a[0]}, {b[0]}")
    report={"sprite_count":len(assets),"rgba_with_transparency":True,"atlas_exact_pixels":True,
            "uv_valid_range":True,"atlas_nonoverlap":True,"preview_size":[1280,720],
            "max_values":{"jugador":3,"jefe":24},"issues":issues}
    (OUT/"validacion_hud.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    if issues:
        raise AssertionError("; ".join(issues))
    print(json.dumps(report,ensure_ascii=False))


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    bar("jugador",336,"cyan",3)
    bar("jefe",640,"red",24)
    icons()
    meta=atlas()
    preview()
    readme()
    validate(meta)


if __name__ == "__main__":
    main()
