"""Validate Galaga OBJ exports against EntornVGI's actual parser.

Run with Python 3.10+ from any directory. The report is written to
Recursos_Galaga3D/validacion_obj.json unless --report is specified.
The exported models are only read, never normalized or modified.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path, PureWindowsPath
import re
from typing import Any


FACE_PATTERN = re.compile(
    r"f ([1-9][0-9]*/[1-9][0-9]*/[1-9][0-9]*)"
    r" ([1-9][0-9]*/[1-9][0-9]*/[1-9][0-9]*)"
    r" ([1-9][0-9]*/[1-9][0-9]*/[1-9][0-9]*)"
)
NORMAL_TOLERANCE = 1e-3
MIN_TRIANGLE_AREA = 1e-10


def problem(errors: list[dict[str, Any]], path: Path, line: int | None,
            code: str, message: str) -> None:
    item: dict[str, Any] = {"file": path.name, "code": code, "message": message}
    if line is not None:
        item["line"] = line
    errors.append(item)


def read_lines(path: Path, errors: list[dict[str, Any]]) -> list[str]:
    try:
        data = path.read_bytes()
    except OSError as error:
        problem(errors, path, None, "unreadable", str(error))
        return []
    if not data.endswith(b"\n"):
        problem(errors, path, None, "missing_final_newline",
                "El archivo debe terminar con un salto de línea.")
    try:
        text = data.decode("ascii")
    except UnicodeDecodeError:
        problem(errors, path, None, "non_ascii",
                "El export compatible debe usar nombres y contenido ASCII.")
        text = data.decode("utf-8", errors="replace")
    return text.splitlines()


def numbers(path: Path, line: int, fields: list[str], expected: int,
            errors: list[dict[str, Any]]) -> tuple[float, ...] | None:
    if len(fields) != expected:
        problem(errors, path, line, "numeric_arity",
                f"Se esperan {expected} valores y hay {len(fields)}.")
        return None
    try:
        values = tuple(float(field) for field in fields)
    except ValueError:
        problem(errors, path, line, "invalid_number", "Valor numérico no válido.")
        return None
    if not all(math.isfinite(value) for value in values):
        problem(errors, path, line, "non_finite", "Todos los valores deben ser finitos.")
        return None
    return values


def material_library(path: Path, errors: list[dict[str, Any]]) -> list[str]:
    names: list[str] = []
    current: str | None = None
    properties: dict[str, set[str]] = {}
    for line_number, line in enumerate(read_lines(path, errors), 1):
        if not line.strip() or line.startswith("#"):
            continue
        fields = line.split()
        token = fields[0]
        if token == "newmtl":
            if len(fields) != 2 or line != "newmtl " + fields[1]:
                problem(errors, path, line_number, "material_name_format",
                        "newmtl debe tener un nombre simple y un único espacio.")
                current = None
                continue
            current = fields[1]
            if current in names:
                problem(errors, path, line_number, "duplicate_material",
                        f"Material repetido: {current}.")
            names.append(current)
            properties.setdefault(current, set())
        elif token in {"Ka", "Kd", "Ks", "Ns"}:
            numbers(path, line_number, fields[1:], 1 if token == "Ns" else 3, errors)
            if current is None:
                problem(errors, path, line_number, "material_property_without_name",
                        f"{token} aparece antes de newmtl.")
            else:
                properties[current].add(token)
        elif token == "map_Kd":
            if current is None:
                problem(errors, path, line_number, "material_property_without_name",
                        "map_Kd aparece antes de newmtl.")
            texture_name = line[len("map_Kd "):] if line.startswith("map_Kd ") else ""
            texture_path = Path(texture_name.replace("\\", "/"))
            if not texture_name or texture_name.startswith("-"):
                problem(errors, path, line_number, "texture_options_unsupported",
                        "map_Kd debe ser una ruta simple sin opciones.")
            elif texture_path.is_absolute() or PureWindowsPath(texture_name).drive:
                problem(errors, path, line_number, "absolute_texture_path",
                        "map_Kd debe ser relativo al directorio del OBJ.")
            elif not (path.parent / texture_path).is_file():
                problem(errors, path, line_number, "missing_texture",
                        f"No existe la textura relativa: {texture_name}.")
    for name, present in properties.items():
        missing = {"Ka", "Kd", "Ks", "Ns"} - present
        if missing:
            problem(errors, path, None, "missing_material_properties",
                    f"{name} no define: {', '.join(sorted(missing))}.")
    if len(names) > 8:
        problem(errors, path, None, "too_many_materials",
                f"Hay {len(names)} materiales; el pack admite como máximo 8 por recurso.")
    return names


def triangle_area(vertices: list[tuple[float, ...] | None],
                  references: list[tuple[int, int, int]]) -> float | None:
    points = [vertices[reference[0] - 1] for reference in references]
    if any(point is None for point in points):
        return None
    a, b, c = points
    assert a is not None and b is not None and c is not None
    u = tuple(b[i] - a[i] for i in range(3))
    v = tuple(c[i] - a[i] for i in range(3))
    cross = (u[1] * v[2] - u[2] * v[1],
             u[2] * v[0] - u[0] * v[2],
             u[0] * v[1] - u[1] * v[0])
    return math.hypot(*cross) / 2


def validate_obj(path: Path, pack_root: Path) -> dict[str, Any]:
    errors: list[dict[str, Any]] = []
    vertices: list[tuple[float, ...] | None] = []
    uv: list[tuple[float, ...] | None] = []
    normals: list[tuple[float, ...] | None] = []
    faces: list[tuple[int, list[tuple[int, int, int]], str | None]] = []
    libraries: list[str] = []
    used_materials: list[str] = []
    current_material: str | None = None
    for line_number, line in enumerate(read_lines(path, errors), 1):
        if not line.strip() or line.startswith("#"):
            continue
        fields = line.split()
        token = fields[0]
        if token in {"v", "vt", "vn"}:
            values = numbers(path, line_number, fields[1:], 2 if token == "vt" else 3,
                             errors)
            if token == "v":
                vertices.append(values)
            elif token == "vt":
                uv.append(values)
            else:
                normals.append(values)
                if values is not None:
                    length = math.hypot(*values)
                    if abs(length - 1) > NORMAL_TOLERANCE:
                        problem(errors, path, line_number, "non_unit_normal",
                                f"La normal mide {length:.9g}; debe medir 1.")
        elif token == "mtllib":
            if len(fields) != 2 or line != "mtllib " + fields[1]:
                problem(errors, path, line_number, "mtllib_format",
                        "mtllib debe contener una ruta simple y un único espacio.")
            else:
                libraries.append(fields[1])
        elif token == "usemtl":
            if not libraries:
                problem(errors, path, line_number, "material_library_after_use",
                        "mtllib debe aparecer antes del primer usemtl.")
            if len(fields) != 2 or line != "usemtl " + fields[1]:
                problem(errors, path, line_number, "usemtl_format",
                        "usemtl debe tener un nombre simple y un único espacio.")
                current_material = None
            else:
                current_material = fields[1]
        elif token == "f":
            match = FACE_PATTERN.fullmatch(line)
            if match is None:
                problem(errors, path, line_number, "face_format",
                        "Cada cara debe ser f v/vt/vn v/vt/vn v/vt/vn, con índices "
                        "positivos y un único espacio entre referencias.")
                continue
            references = [tuple(int(value) for value in reference.split("/"))
                          for reference in match.groups()]
            for reference in references:
                for index, count, kind in zip(reference, (len(vertices), len(uv), len(normals)),
                                              ("v", "vt", "vn")):
                    if index > count:
                        problem(errors, path, line_number, "index_before_definition",
                                f"La referencia {kind}={index} debe definirse antes de la cara.")
            faces.append((line_number, references, current_material))
            if current_material is None:
                problem(errors, path, line_number, "face_without_material",
                        "Cada cara debe tener un usemtl válido anterior.")
            elif current_material not in used_materials:
                used_materials.append(current_material)

    if not vertices or not uv or not normals or not faces:
        problem(errors, path, None, "empty_geometry",
                "El OBJ debe tener v, vt, vn y al menos una cara triangular.")
    minimum_area: float | None = None
    for line_number, references, _ in faces:
        in_range = True
        for reference in references:
            for index, count, kind in zip(reference, (len(vertices), len(uv), len(normals)),
                                          ("v", "vt", "vn")):
                if index > count:
                    in_range = False
                    problem(errors, path, line_number, "index_out_of_range",
                            f"Índice {kind}={index} fuera de rango 1..{count}.")
        if in_range:
            area = triangle_area(vertices, references)
            if area is not None:
                if math.isfinite(area):
                    minimum_area = area if minimum_area is None else min(minimum_area, area)
                if not math.isfinite(area) or area <= MIN_TRIANGLE_AREA:
                    problem(errors, path, line_number, "degenerate_triangle",
                            f"Área del triángulo {area:.9g}; mínimo {MIN_TRIANGLE_AREA:g}.")

    names: list[str] = []
    if len(libraries) != 1:
        problem(errors, path, None, "material_library_count",
                f"Se exige un mtllib; encontrados {len(libraries)}.")
    for library in libraries:
        relative_path = Path(library.replace("\\", "/"))
        if relative_path.is_absolute() or PureWindowsPath(library).drive:
            problem(errors, path, None, "absolute_material_path",
                    "mtllib debe ser una ruta relativa.")
            continue
        mtl_path = path.parent / relative_path
        if not mtl_path.is_file():
            problem(errors, path, None, "missing_material_library",
                    f"No existe la biblioteca relativa: {library}.")
            continue
        names.extend(material_library(mtl_path, errors))
    if names != used_materials:
        problem(errors, path, None, "material_order_or_usage",
                "newmtl debe definir solo materiales usados, en el mismo orden "
                f"de primera aparición en las caras. MTL={names}; caras={used_materials}.")
    if len(used_materials) > 8:
        problem(errors, path, None, "too_many_used_materials",
                f"Se utilizan {len(used_materials)} materiales; máximo 8.")

    valid_vertices = [vertex for vertex in vertices if vertex is not None]
    bounds = None
    if valid_vertices:
        low = [min(vertex[axis] for vertex in valid_vertices) for axis in range(3)]
        high = [max(vertex[axis] for vertex in valid_vertices) for axis in range(3)]
        dimensions = [high[axis] - low[axis] for axis in range(3)]
        if not all(math.isfinite(value) for value in dimensions):
            problem(errors, path, None, "non_finite_bounds",
                    "Las dimensiones de la malla no son finitas.")
            dimensions = None
        bounds = {"min": low, "max": high, "dimensions": dimensions}
    return {"id": path.stem, "file": path.relative_to(pack_root).as_posix(),
            "ok": not errors, "vertices": len(vertices), "uv": len(uv),
            "normals": len(normals), "triangles": len(faces), "materials": names,
            "minimum_triangle_area": minimum_area, "bounds": bounds, "errors": errors}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1],
                        help="Directorio Recursos_Galaga3D")
    parser.add_argument("--report", type=Path, help="Destino JSON alternativo")
    args = parser.parse_args()
    pack_root = args.root.resolve()
    models = sorted((pack_root / "modelos" / "obj").glob("*.obj"))
    assets = [validate_obj(path, pack_root) for path in models]
    errors = []
    if not models:
        errors.append({"code": "no_models", "message": "No hay modelos/obj/*.obj."})
    report = {"schema": "galaga-obj-validation-v1", "ok": bool(models) and
              all(asset["ok"] for asset in assets), "parser": "Practica1/EntornVGI/objLoader.cpp",
              "rules": {"face_format": "f v/vt/vn v/vt/vn v/vt/vn", "positive_indices": True,
                        "max_materials_per_asset": 8, "normal_length_tolerance": NORMAL_TOLERANCE,
                        "minimum_triangle_area": MIN_TRIANGLE_AREA,
                        "material_order": "first appearance in faces",
                        "finite_values": True, "final_newlines": True},
              "asset_count": len(assets), "triangle_count": sum(asset["triangles"] for asset in assets),
              "error_count": len(errors) + sum(len(asset["errors"]) for asset in assets),
              "errors": errors, "assets": assets}
    report_path = args.report or (pack_root / "validacion_obj.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
                           encoding="utf-8")
    print(f"{'OK' if report['ok'] else 'ERROR'}: {len(assets)} recursos, "
          f"{report['triangle_count']} triángulos, {report['error_count']} errores. "
          f"Informe: {report_path}")
    for asset in assets:
        if asset["errors"]:
            print(f"  {asset['id']}: {len(asset['errors'])} errores")
            for error in asset["errors"][:5]:
                print(f"    {error['file']}:{error.get('line', '-')} {error['code']}: {error['message']}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
