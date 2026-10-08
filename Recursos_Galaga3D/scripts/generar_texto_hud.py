"""Sprites numéricos y preview HUD de producto, sin modificar preview_hud.png.

Renderiza las fuentes locales libres Bitstream Vera incluidas en fonts/.
Dependencia: Pillow. Ejecutar después de generar_hud.py.
"""
from __future__ import annotations

import hashlib
import json
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "hud"
FONT = ROOT / "fonts" / "Vera.ttf"
FONT_BOLD = ROOT / "fonts" / "VeraBd.ttf"
ICE=(216,237,243,255)
CYAN=(54,230,237,255)
RED=(250,82,105,255)
NAVY=(16,26,44,255)
SLOT=(24,40)
BASELINE=30
ADVANCE=24
NUM_SIZE=28


def font(size,bold=False):
    path=FONT_BOLD if bold else FONT
    if not path.exists():
        raise FileNotFoundError(f"Falta la fuente incluida en el pack: {path}")
    return ImageFont.truetype(str(path),size)


def export_digits():
    f=font(NUM_SIZE)
    atlas=Image.new("RGBA",(512,64))
    digits={}
    meta={"image":"atlas_digitos.png","size_px":[512,64],"format":"RGBA8",
          "alpha":"straight (no premultiplicado)","pixel_origin":"top_left",
          "rect_order":"[x,y,width,height]","uv_order":"[u_min,v_min,u_max,v_max]",
          "font_source":"Bitstream Vera Sans (fuente libre incluida en el pack)",
          "font_file":"../fonts/Vera.ttf","font_license":"../fonts/bitstream-vera-license.txt",
          "font_paths_relative_to":"atlas_digitos.json parent directory",
          "font_size_px":NUM_SIZE,"baseline_px_from_top":BASELINE,"line_height_px":40,
          "advance_px":ADVANCE,"layout":"monospaced/tabular sprite slots",
          "gutter_px":8,"extrusion_px":2,
          "position_from_baseline":"El quad de un glifo empieza en (pen_x, baseline_y - 30); después pen_x += 24.",
          "uv_top_left_usage":"Filas PNG sin invertir: asociar v mínima al vértice superior.",
          "uv_bottom_left_usage":"Invertir filas PNG al cargar: asociar v máxima al vértice superior.",
          "glyphs":{}}
    for i in range(10):
        s=str(i)
        im=Image.new("RGBA",SLOT)
        ImageDraw.Draw(im).text((4,BASELINE),s,font=f,fill=ICE,anchor="ls")
        im.save(OUT/f"digito_{s}.png")
        digits[s]=im
        x,y=4+i*32,4
        atlas.paste(im,(x,y))
        # Las celdas ya tienen padding transparente; duplicar bordes 2 px.
        for off in (1,2):
            atlas.paste(im.crop((0,0,SLOT[0],1)),(x,y-off))
            atlas.paste(im.crop((0,SLOT[1]-1,SLOT[0],SLOT[1])),(x,y+SLOT[1]+off-1))
            atlas.paste(im.crop((0,0,1,SLOT[1])),(x-off,y))
            atlas.paste(im.crop((SLOT[0]-1,0,SLOT[0],SLOT[1])),(x+SLOT[0]+off-1,y))
        b=im.getchannel("A").getbbox()
        w,h=SLOT
        meta["glyphs"][s]={"codepoint":ord(s),"rect_px":[x,y,w,h],
            "uv_top_left":[x/512,y/64,(x+w)/512,(y+h)/64],
            "uv_bottom_left":[x/512,1-(y+h)/64,(x+w)/512,1-y/64],
            "advance_px":ADVANCE,"baseline_px_from_top":BASELINE,
            "quad_offset_from_pen_baseline_px":[0,-BASELINE],
            "ink_bbox_px":list(b),"source_font_advance_px":f.getlength(s)}
    atlas.save(OUT/"atlas_digitos.png")
    (OUT/"atlas_digitos.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return digits,meta


def compose(value,digits):
    if not value or not value.isascii() or not value.isdecimal():
        raise ValueError("El contador acepta únicamente cifras ASCII 0..9")
    im=Image.new("RGBA",(len(value)*ADVANCE,SLOT[1]))
    for i,char in enumerate(value):
        im.alpha_composite(digits[char],(i*ADVANCE,0))
    return im


def export_labels():
    f=font(14,True)
    labels={"puntos":"PUNTOS","record":"RECORD","oleada":"OLEADA","vidas":"VIDAS",
            "jefe":"JEFE","plano_a":"PLANO A","plano_b":"PLANO B","cerca":"CERCA",
            "lejos":"LEJOS","pausa":"PAUSA","control_mover":"A / D  MOVER",
            "control_disparar":"ESPACIO  DISPARAR","control_plano":"E  CAMBIAR PLANO",
            "control_pausa":"P  PAUSA"}
    images={}
    meta={"font_source":"Bitstream Vera Sans Bold (fuente libre incluida en el pack)",
          "font_file":"../fonts/VeraBd.ttf","font_license":"../fonts/bitstream-vera-license.txt",
          "font_paths_relative_to":"etiquetas_hud.json parent directory",
          "font_size_px":14,"baseline_px_from_top":18,"alpha":"straight",
          "labels":{}}
    for name,text in labels.items():
        width=math.ceil(f.getlength(text))+4
        im=Image.new("RGBA",(width,24))
        ImageDraw.Draw(im).text((2,18),text,font=f,fill=ICE,anchor="ls")
        filename=f"etiqueta_{name}.png"
        im.save(OUT/filename)
        images[name]=im
        meta["labels"][name]={"text":text,"image":filename,"size_px":[width,24],
            "baseline_px_from_top":18,"advance_px":width,"ink_bbox_px":list(im.getchannel("A").getbbox())}
    (OUT/"etiquetas_hud.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return images


def tinted(im,color):
    result=Image.new("RGBA",im.size,color)
    result.putalpha(im.getchannel("A"))
    return result


def preview(digits,labels):
    im=Image.new("RGBA",(1280,720),NAVY)
    background=Image.new("RGBA",im.size)
    d=ImageDraw.Draw(background)
    random.seed(721)
    for i in range(115):
        x,y=random.randint(20,1260),random.randint(190,590)
        d.ellipse((x,y,x+1,y+1),fill=ICE[:3]+(random.randint(30,85),))
    d.line([(24,108),(1256,108)],fill=ICE[:3]+(42,))
    d.line([(24,600),(1256,600)],fill=ICE[:3]+(70,))
    im.alpha_composite(background)

    def label(name,pos,color=None):
        im.alpha_composite(tinted(labels[name],color) if color else labels[name],pos)

    def sprite(name,pos):
        with Image.open(OUT/f"{name}.png") as asset:
            im.alpha_composite(asset.convert("RGBA"),pos)

    # Todos los números principales se ensamblan desde las cifras a 1:1.
    for name,value,x in (("puntos","012500",28),("record","024000",230),("oleada","03",432)):
        label(name,(x,20))
        im.alpha_composite(compose(value,digits),(x,44))
    sprite("pausa",(1188,26))
    label("control_pausa",(1188,89))

    label("jefe",(320,115),RED)
    for layer in ("fondo","relleno","marco"):
        sprite(f"vida_jefe_{layer}",(320,142))
    # HP auxiliar; tamaño reducido del mismo atlas para no competir con puntos.
    hp=compose("24",digits).resize((24,20),Image.Resampling.LANCZOS)
    im.alpha_composite(hp,(877,117))
    ImageDraw.Draw(im).text((902,118),"/",font=font(14),fill=ICE)
    im.alpha_composite(hp,(916,117))

    label("vidas",(28,613))
    for layer in ("fondo","relleno","marco"):
        sprite(f"vida_jugador_{layer}",(24,641))
    for x in (381,429,477):
        with Image.open(OUT/"vida_nave.png") as asset:
            im.alpha_composite(asset.resize((42,42),Image.Resampling.LANCZOS),(x,643))

    sprite("plano_A",(929,628))
    label("plano_a",(1007,636),CYAN)
    label("cerca",(1007,663))
    # Controles de producto: sin notas sobre el proceso ni componentes opcionales.
    for name,x in (("control_mover",28),("control_disparar",230),("control_plano",500),("control_pausa",773)):
        label(name,(x,693))
    im.convert("RGB").save(OUT/"preview_hud_limpio.png")
    sample=compose("012500",digits)
    sample.save(OUT/"ejemplo_puntos_012500.png")
    contact=Image.new("RGBA",(440,140),NAVY)
    contact.alpha_composite(compose("0123456789",digits),(20,16))
    contact.alpha_composite(sample,(20,75))
    ImageDraw.Draw(contact).text((190,90),"012500 / 1:1",font=font(14),fill=CYAN)
    contact.convert("RGB").save(OUT/"preview_digitos_1a1.png")


def validate(digits,meta,preserved_hash):
    issues=[]
    with Image.open(OUT/"atlas_digitos.png") as atlas:
        for name,im in digits.items():
            x,y,w,h=meta["glyphs"][name]["rect_px"]
            if im.mode!="RGBA" or im.getextrema()[3][0]!=0:
                issues.append(f"{name}: modo/transparencia incorrectos")
            if atlas.crop((x,y,x+w,y+h)).tobytes()!=im.tobytes():
                issues.append(f"{name}: atlas diferente del PNG")
            if not all(0<=n<=1 for n in meta["glyphs"][name]["uv_top_left"]+meta["glyphs"][name]["uv_bottom_left"]):
                issues.append(f"{name}: UV fuera de rango")
    with Image.open(OUT/"ejemplo_puntos_012500.png") as sample:
        if sample.size!=(144,40):
            issues.append("Ancho del ejemplo no corresponde a 6 avances")
        for i,char in enumerate("012500"):
            if sample.crop((i*24,0,(i+1)*24,40)).tobytes()!=digits[char].tobytes():
                issues.append(f"Ejemplo: glifo {i} no coincide a 1:1")
    current_hash=hashlib.sha256((OUT/"preview_hud.png").read_bytes()).hexdigest()
    if preserved_hash!=current_hash:
        issues.append("preview_hud.png ha cambiado")
    report={"ascii_digits":"0123456789","digit_count":10,"slot_px":[24,40],
            "baseline_px_from_top":30,"advance_px":24,"example":"012500",
            "example_size_px":[144,40],"example_glyphs_1_to_1":not issues,
            "preview_original_unchanged":preserved_hash==current_hash,"issues":issues}
    (OUT/"validacion_texto_hud.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    if issues:
        raise AssertionError("; ".join(issues))
    print(json.dumps(report,ensure_ascii=False))


def main():
    if not (OUT/"vida_jugador_marco.png").exists():
        raise FileNotFoundError("Ejecuta primero generar_hud.py")
    preserved_hash=hashlib.sha256((OUT/"preview_hud.png").read_bytes()).hexdigest()
    digits,meta=export_digits()
    labels=export_labels()
    preview(digits,labels)
    validate(digits,meta,preserved_hash)
    (OUT/"README_texto.md").write_text("""# Texto HUD y composición limpia

`preview_hud_limpio.png` es una composición de producto a 1280 × 720 con puntos, récord, oleada, tres vidas, jefe 24/24, plano A cercano, pausa y controles. No contiene notas editoriales, mira ni modelos 3D. Conserva la preview previa y el resto de componentes.

`atlas_digitos.png` y `atlas_digitos.json` contienen las diez cifras ASCII **0..9**, también exportadas como `digito_0.png` … `digito_9.png`. Se renderiza **Bitstream Vera Sans**, tamaño 28 px, desde `fonts/Vera.ttf`, incluida en el pack. La fuente libre se distribuye junto con `fonts/bitstream-vera-license.txt`. Cada glifo ocupa una celda RGBA transparente de **24 × 40 px**, con avance fijo **24 px** y baseline **30 px desde arriba**. El quad empieza en `(pen_x, baseline_y - 30)`; incrementar `pen_x` en 24. El ejemplo **012500** usa las seis celdas a 1:1, tamaño **144 × 40**, sin reescalar. `preview_digitos_1a1.png` permite comprobar su lectura.

La metadata incluye avance original de la fuente, bounding box visible, offset respecto a la baseline, rectángulo en píxeles y UV superiores e inferiores explícitas. PNG conserva filas con origen arriba a la izquierda. UV `uv_top_left`: cargar filas sin invertir y usar v mínima arriba. UV `uv_bottom_left`: invertir filas al cargar y usar v máxima arriba. El atlas de cifras mide 512 × 64; los rectángulos excluyen márgenes de 8 px y extrusión de 2 px. Usar alpha recto, filtrado lineal y evitar mipmaps del atlas sin ampliar márgenes.

`etiqueta_*.png` aporta etiquetas de puntos, récord, oleada, vidas, jefe, planos, pausa y controles, en **Bitstream Vera Sans Bold** 14 px, desde `fonts/VeraBd.ttf`. `etiquetas_hud.json` recoge tamaños, baseline, archivo de fuente y licencia. Solo contienen texto estático; puntos y vidas provienen del estado de la partida.

Regenerar con `scripts/generar_texto_hud.py`, tras generar_hud.py. Requiere Python, Pillow y las dos fuentes locales Bitstream Vera incluidas en `fonts/`; no usa fuentes del sistema ni rutas absolutas. Las rutas de fuentes y licencia en la metadata son relativas a la carpeta del JSON. `validacion_texto_hud.json` comprueba transparencia, atlas, UV, montaje del ejemplo a 1:1 y conservación de preview_hud.png. No implementa la lógica del juego ni modifica las reglas.
""",encoding="utf-8")


if __name__=="__main__":
    main()
