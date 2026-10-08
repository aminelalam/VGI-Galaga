"""Auditoría del HUD existente: solo lee assets; escribe un informe JSON.

No ejecuta generadores, Blender ni scripts del proyecto. El algoritmo clip()
se aísla mediante AST y se verifica con una malla mínima sin bpy.
"""
from __future__ import annotations

import ast
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
import xml.etree.ElementTree as ET

from PIL import Image, ImageFont

BASE=Path(__file__).resolve().parents[1]
HUD=BASE/"hud"
REPORT=BASE/"validacion_hud_final.json"
errors=[]
warnings=[]
checks={}
SHAPES={"polygon","polyline","ellipse","rect","path","circle","line","text","image","use"}


def error(code,message,files=None):
    errors.append({"code":code,"message":message,"files":files or []})


def require(condition,code,message,files=None):
    if not condition:
        error(code,message,files)


def digest_assets():
    return {str(p.relative_to(BASE)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(HUD.iterdir()) if p.is_file()}


def tag(e): return e.tag.rsplit("}",1)[-1]


def audit_svg():
    result={}
    total=Counter()
    files=sorted(HUD.glob("*.svg"))
    require(len(files)==16,"SVG_COUNT","Se esperan los 16 SVG declarados en el pack")
    for p in files:
        root=ET.parse(p).getroot()
        counts=Counter(tag(e) for e in root if tag(e) in SHAPES)
        total.update(counts)
        size=[int(float(root.attrib[k])) for k in ("width","height")]
        with Image.open(p.with_suffix(".png")) as png:
            require(list(png.size)==size,"SVG_PNG_SIZE",f"Dimensiones distintas para {p.stem}",[p.name])
        require(root.attrib.get("viewBox")==f"0 0 {size[0]} {size[1]}","SVG_VIEWBOX",f"viewBox incorrecto: {p.name}")
        for e in root:
            if tag(e) in ("polygon","polyline"):
                pts=[tuple(map(float,v.split(","))) for v in e.attrib["points"].split()]
                minimum=3 if tag(e)=="polygon" else 2
                require(len(pts)>=minimum,"SVG_POINTS",f"{p.name}: puntos insuficientes")
                require(all(math.isfinite(x) and math.isfinite(y) for x,y in pts),"SVG_FINITE",f"{p.name}: coordenadas inválidas")
            elif tag(e)=="rect":
                require(float(e.attrib["width"])>0 and float(e.attrib["height"])>0,"SVG_RECT",f"{p.name}: rect degenerado")
            elif tag(e)=="ellipse":
                require(float(e.attrib["rx"])>0 and float(e.attrib["ry"])>0,"SVG_ELLIPSE",f"{p.name}: elipse degenerada")
            if tag(e) in SHAPES:
                require(not any(k in e.attrib for k in ("transform","style")),"SVG_IMPORT_ATTRIBUTES",f"{p.name}: atributos no interpretados por importer")
        result[p.stem]={"size_px":size,"shape_counts":dict(counts),"shape_total":sum(counts.values())}
    importer=BASE/"scripts/generar_interfaz_blender.py"
    tree=ast.parse(importer.read_text(encoding="utf-8"))
    fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="sprite")
    supported=set()
    for node in ast.walk(fn):
        if isinstance(node,ast.Compare) and isinstance(node.left,ast.Name) and node.left.id=="tag":
            for c in node.comparators:
                if isinstance(c,ast.Constant) and c.value in SHAPES:
                    supported.add(c.value)
                elif isinstance(c,(ast.Tuple,ast.List)):
                    supported.update(e.value for e in c.elts if isinstance(e,ast.Constant) and e.value in SHAPES)
    # closed=tag!='polyline' does not add a new capability; polyline is a supported branch.
    unsupported={name:{shape:n for shape,n in data["shape_counts"].items() if shape not in supported}
                 for name,data in result.items()}
    unsupported={name:data for name,data in unsupported.items() if data}
    for name,data in unsupported.items():
        error("BLENDER_SVG_PRIMITIVE_OMITTED",f"El importador omite {data} de {name}.svg",[f"hud/{name}.svg","scripts/generar_interfaz_blender.py"])
    checks["svg"]={"file_count":len(files),"total_shape_counts":dict(total),"files":result,
                   "blender_importer_supported_shapes":sorted(supported),"unsupported_shapes":unsupported}


def audit_png():
    files=sorted(HUD.glob("*.png"))
    result={}
    rgb_previews={"preview_hud.png","componentes_hud.png","preview_hud_limpio.png","preview_digitos_1a1.png"}
    for p in files:
        with Image.open(p) as im:
            im.load()
            info={"size_px":list(im.size),"mode":im.mode}
            if p.name not in rgb_previews:
                require(im.mode=="RGBA","PNG_RGBA",f"{p.name} no es RGBA")
                if im.mode=="RGBA":
                    amin,amax=im.getextrema()[3]
                    info["alpha_range"]=[amin,amax]
                    require(amin==0 and amax>0,"PNG_ALPHA",f"{p.name}: transparencia o contenido vacío")
            if p.name in ("preview_hud.png","componentes_hud.png","preview_hud_limpio.png"):
                require(im.size==(1280,720),"PREVIEW_SIZE",f"{p.name}: resolución inesperada")
            result[p.name]=info
    checks["png"]={"file_count":len(files),"files":result}


def audit_atlas(filename,table_key,png_name):
    path=HUD/filename
    meta=json.loads(path.read_text(encoding="utf-8"))
    entries=meta[table_key]
    with Image.open(HUD/png_name) as atlas:
        W,H=atlas.size
        require([W,H]==meta["size_px"],"ATLAS_SIZE",f"{filename}: dimensiones incorrectas")
        require(meta["pixel_origin"]=="top_left","ATLAS_ORIGIN",f"{filename}: origen de píxeles ambiguo")
        rects=[]
        for name,data in entries.items():
            x,y,w,h=data["rect_px"]
            rects.append((name,x,y,x+w,y+h))
            require(0<=x<x+w<=W and 0<=y<y+h<=H,"ATLAS_BOUNDS",f"{filename}: {name} fuera de atlas")
            source=HUD/(f"digito_{name}.png" if table_key=="glyphs" else f"{name}.png")
            with Image.open(source) as im:
                require(im.size==(w,h),"ATLAS_RECT_SIZE",f"{filename}: rect de {name} difiere del sprite")
                require(im.tobytes()==atlas.crop((x,y,x+w,y+h)).tobytes(),"ATLAS_PIXELS",f"{filename}: píxeles de {name} distintos")
            expected_top=[x/W,y/H,(x+w)/W,(y+h)/H]
            expected_bottom=[x/W,1-(y+h)/H,(x+w)/W,1-y/H]
            for uv_key,expected in (("uv_top_left",expected_top),("uv_bottom_left",expected_bottom)):
                require(len(data[uv_key])==4 and all(abs(a-b)<1e-12 for a,b in zip(data[uv_key],expected)),
                        "ATLAS_UV",f"{filename}: UV {uv_key} incorrectas para {name}")
        for i,a in enumerate(rects):
            for b in rects[i+1:]:
                require(not(max(a[1],b[1])<min(a[3],b[3]) and max(a[2],b[2])<min(a[4],b[4])),
                        "ATLAS_OVERLAP",f"{filename}: {a[0]} solapa {b[0]}")
    checks[filename]={"entry_count":len(entries),"size_px":[W,H],"pixels_exact":True,
                      "rectangles_nonoverlap":True,"uv_formulas_checked":True,"pixel_origin":meta["pixel_origin"]}
    return meta


def audit_digits(meta):
    require(set(meta["glyphs"])==set("0123456789"),"DIGIT_SET","Atlas debe contener exactamente ASCII 0..9")
    require(meta["baseline_px_from_top"]==30 and meta["advance_px"]==24,"DIGIT_METRICS","Baseline o avance global incorrectos")
    with Image.open(HUD/"ejemplo_puntos_012500.png") as sample:
        require(sample.size==(144,40),"DIGIT_EXAMPLE_SIZE","Ejemplo 012500 no ocupa 6 avances de 24")
        for i,char in enumerate("012500"):
            with Image.open(HUD/f"digito_{char}.png") as glyph:
                require(sample.crop((i*24,0,(i+1)*24,40)).tobytes()==glyph.tobytes(),"DIGIT_EXAMPLE_PIXELS",f"Glifo {i} en 012500 no está a 1:1")
    for char,data in meta["glyphs"].items():
        require(data["codepoint"]==ord(char),"DIGIT_CODEPOINT",f"Codepoint incorrecto para {char}")
        require(data["advance_px"]==24 and data["baseline_px_from_top"]==30,"DIGIT_GLYPH_METRICS",f"{char}: métricas inconsistente")
        require(data["quad_offset_from_pen_baseline_px"]==[0,-30],"DIGIT_OFFSET",f"{char}: offset incorrecto")
        with Image.open(HUD/f"digito_{char}.png") as im:
            require(im.size==(24,40),"DIGIT_SIZE",f"{char}: tamaño incorrecto")
            require(list(im.getchannel("A").getbbox())==data["ink_bbox_px"],"DIGIT_INK_BBOX",f"{char}: bbox visible diferente")
    labels=json.loads((HUD/"etiquetas_hud.json").read_text(encoding="utf-8"))
    require(len(labels["labels"])==14,"LABEL_COUNT","Se esperan 14 etiquetas estáticas")
    for name,data in labels["labels"].items():
        with Image.open(HUD/data["image"]) as im:
            require(list(im.size)==data["size_px"],"LABEL_SIZE",f"{name}: dimensiones incorrectas")
            require(list(im.getchannel("A").getbbox())==data["ink_bbox_px"],"LABEL_BBOX",f"{name}: bbox incorrecta")
    checks["digits"]={"ascii_set_exact":True,"example_012500_1_to_1":True,"advance_px":24,
                      "baseline_px_from_top":30,"label_count":len(labels["labels"])}


def count_runs(values):
    return sum(v and (i==0 or not values[i-1]) for i,v in enumerate(values))


class Mesh:
    def clear_geometry(self): self.v=[];self.f=[]
    def from_pydata(self,v,edges,f): self.v=v;self.f=f
    def update(self): pass


class Object(dict):
    def __init__(self,geometry):
        super().__init__(clip_original=json.dumps(geometry))
        self.data=Mesh()


def area(points):
    return abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(points,points[1:]+points[:1])))/2


def audit_life_clip(meta):
    updater=ast.parse((BASE/"scripts/actualizar_hud.py").read_text(encoding="utf-8"))
    clip_fn=next(n for n in updater.body if isinstance(n,ast.FunctionDef) and n.name=="clip")
    module=ast.Module(body=[clip_fn],type_ignores=[])
    namespace={"json":json}
    exec(compile(ast.fix_missing_locations(module),"isolated_clip","exec"),namespace)
    result={}
    for kind,maximum,offset in (("jugador",3,24),("jefe",24,320)):
        name=f"vida_{kind}_relleno"
        guide=meta["sprites"][name]
        require(guide["max_value"]==maximum,"LIFE_MAX",f"{kind}: máximo incorrecto")
        left,top,width,height=guide["fill_rect_px"]
        expected_width=280 if kind=="jugador" else 584
        require((left,top,width,height)==(28,17,expected_width,14),"LIFE_RECT",f"{kind}: zona de relleno incorrecta")
        # Analizar todos los polígonos de color; son convexos y pueden dividirse en abanico.
        vertices=[];faces=[]
        for shape in ET.parse(HUD/f"{name}.svg").getroot():
            if tag(shape)=="polygon" and shape.attrib.get("fill","none")!="none":
                pts=[tuple(map(float,v.split(","))) for v in shape.attrib["points"].split()]
                start=len(vertices)
                vertices.extend([[(offset+x-640)/100,(360-y)/100,.17] for x,y in pts])
                faces.extend([(start,start+j,start+j+1) for j in range(1,len(pts)-1)])
        original={"v":vertices,"f":faces}
        original_area=sum(area([vertices[i] for i in f]) for f in faces)
        samples=[]
        for value in range(maximum+1):
            right=(offset+left+width*value/maximum-640)/100
            ob=Object(original)
            namespace["clip"](ob,right)
            total=sum(area([ob.data.v[i] for i in f]) for f in ob.data.f)
            require(all(p[0]<=right+1e-10 for p in ob.data.v),"LIFE_CLIP_RIGHT",f"{kind}={value}: vértice rebasa recorte")
            if value==0:
                require(total<1e-10,"LIFE_ZERO",f"{kind}: vida 0 mantiene relleno visible")
            if value==maximum:
                require(abs(total-original_area)<1e-10,"LIFE_FULL",f"{kind}: recorte máximo pierde geometría")
            if samples:
                require(total>=samples[-1]["polygon_area"]-1e-10,"LIFE_MONOTONIC",f"{kind}: área de vida no monotónica")
            samples.append({"value":value,"clip_right_px":left+width*value/maximum,"polygon_area":total})
        if kind=="jugador":
            # Tres grupos legibles; alpha débil del antialias no se cuenta como vida.
            with Image.open(HUD/f"{name}.png") as im:
                for value in range(4):
                    right=left+width*value/3
                    runs=count_runs([im.getpixel((x,24))[3]>=128 and x<right and value>0 for x in range(im.width)])
                    require(runs==value,"LIFE_PIXEL_SEGMENTS",f"Jugador={value}: {runs} segmentos visibles")
                    samples[value]["visible_pixel_segments"]=runs
        result[kind]={"max_value":maximum,"tested_values":samples,"isolated_updater_clip":True,
                      "note":"Prueba de geometría sin bpy; no abre ni altera el archivo .blend."}
    checks["life_clipping"]=result


def audit_docs():
    base_doc=(HUD/"README.md").read_text(encoding="utf-8")
    text_doc=(HUD/"README_texto.md").read_text(encoding="utf-8")
    for snippet in ("16 sprites","3 vidas","24 HP","PLANO A · CERCA","PLANO B · LEJOS","no premultiplicado","uv_top_left","uv_bottom_left"):
        require(snippet in base_doc,"README_BASE",f"README falta información: {snippet}")
    for snippet in ("012500","24 × 40","30 px","24 px","1280 × 720","Bitstream Vera","fonts/Vera.ttf","fonts/VeraBd.ttf","bitstream-vera-license.txt"):
        require(snippet in text_doc,"README_TEXT",f"README_texto falta información: {snippet}")
    checks["documentation"]={"readme_rules_and_origins":True,"readme_digit_metrics":True}


def audit_local_fonts():
    for script in ("generar_hud.py","generar_texto_hud.py"):
        source=(BASE/"scripts"/script).read_text(encoding="utf-8")
        require("Windows/Fonts" not in source and "Segoe" not in source and "bahnschrift" not in source,
                "SYSTEM_FONT_DEPENDENCY",f"{script}: conserva una dependencia de fuentes del sistema")
        require('"Vera.ttf"' in source and '"VeraBd.ttf"' in source,"LOCAL_FONT_GENERATOR",f"{script}: faltan fuentes locales")
    for filename in ("atlas_digitos.json","etiquetas_hud.json"):
        meta=json.loads((HUD/filename).read_text(encoding="utf-8"))
        for field in ("font_file","font_license"):
            value=meta[field]
            require(not Path(value).is_absolute() and ":" not in value,"FONT_RELATIVE_PATH",f"{filename}: {field} no es relativo")
            require((HUD/value).is_file(),"FONT_FILE_EXISTS",f"{filename}: no existe {value}")
    license_text=(BASE/"fonts/bitstream-vera-license.txt").read_text(encoding="utf-8")
    require("Copyright" in license_text and "Bitstream" in license_text,"FONT_LICENSE","Falta texto de licencia Bitstream Vera")
    meta=json.loads((HUD/"atlas_digitos.json").read_text(encoding="utf-8"))
    f=ImageFont.truetype(str(BASE/"fonts/Vera.ttf"),meta["font_size_px"])
    for char,data in meta["glyphs"].items():
        require(abs(f.getlength(char)-data["source_font_advance_px"])<1e-9,"FONT_ADVANCE",f"{char}: avance original no corresponde a Vera")
    checks["fonts"]={"local_fonts_only":True,"relative_metadata_paths":True,"license_included":True,
                     "numeric_font_advances_match_vera":True}


def main():
    before=digest_assets()
    audit_svg()
    audit_png()
    atlas=audit_atlas("atlas_hud.json","sprites","atlas_hud.png")
    digits=audit_atlas("atlas_digitos.json","glyphs","atlas_digitos.png")
    audit_digits(digits)
    audit_life_clip(atlas)
    audit_docs()
    audit_local_fonts()
    after=digest_assets()
    require(before==after,"READ_ONLY","La auditoría ha modificado assets")
    report={"status":"PASS" if not errors else "FAIL","scope":"PNG/SVG/atlas/digitos/documentacion e importador estático; sin UI ni Blender",
            "asset_files_preserved":before==after,"checks":checks,"errors":errors,"warnings":warnings}
    REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":report["status"],"errors":errors,"warnings":warnings,
                      "asset_files_preserved":before==after,"report":str(REPORT)},ensure_ascii=False))
    return 1 if errors else 0


if __name__=="__main__":
    raise SystemExit(main())
