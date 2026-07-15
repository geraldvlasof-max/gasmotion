#!/usr/bin/env python3
"""Llena la MATRIZ FISE (plantilla v2) desde un JSON de datos extraídos del SCANFILE 1.

Edita el XML interno del .xlsx directamente (sin openpyxl para escribir), de modo que
las imágenes, firmas, logos y formatos de la plantilla se conservan intactos.

Uso: python llenar_matriz.py MATRIZ_A_RELLENAR.xlsx datos.json salida.xlsx
"""
import json
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime, date

NS_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def fail(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def q(tag):
    return f"{{{NS_MAIN}}}{tag}"


def register_namespaces(xml_bytes):
    """Registra todos los xmlns del documento para que ET los re-serialice igual."""
    for prefix, uri in re.findall(rb'xmlns(?::(\w+))?="([^"]+)"', xml_bytes):
        ET.register_namespace(prefix.decode() if prefix else "", uri.decode())


def col_num(ref):
    n = 0
    for ch in re.match(r"[A-Z]+", ref).group(0):
        n = n * 26 + ord(ch) - 64
    return n


def excel_serial(d):
    return (date(d.year, d.month, d.day) - date(1899, 12, 30)).days


class Sheet:
    def __init__(self, xml_bytes):
        register_namespaces(xml_bytes)
        self.root = ET.fromstring(xml_bytes)
        self.sheet_data = self.root.find(q("sheetData"))

    def _row(self, num):
        for r in self.sheet_data.findall(q("row")):
            if int(r.get("r")) == num:
                return r
        row = ET.Element(q("row"), {"r": str(num)})
        rows = self.sheet_data.findall(q("row"))
        idx = next((i for i, r in enumerate(rows) if int(r.get("r")) > num), len(rows))
        self.sheet_data.insert(idx, row)
        return row

    def _cell(self, ref):
        rownum = int(re.search(r"\d+", ref).group(0))
        row = self._row(rownum)
        for c in row.findall(q("c")):
            if c.get("r") == ref:
                return c
        cell = ET.Element(q("c"), {"r": ref})
        cells = row.findall(q("c"))
        idx = next((i for i, c in enumerate(cells)
                    if col_num(c.get("r")) > col_num(ref)), len(cells))
        row.insert(idx, cell)
        return cell

    def set(self, ref, value):
        """value: None | int | float | str | '=formula' | datetime/date"""
        c = self._cell(ref)
        for child in list(c):
            c.remove(child)
        c.attrib.pop("t", None)
        if value is None or value == "":
            return
        if isinstance(value, (datetime, date)):
            ET.SubElement(c, q("v")).text = str(excel_serial(value))
        elif isinstance(value, str) and value.startswith("="):
            ET.SubElement(c, q("f")).text = value[1:]
        elif isinstance(value, (int, float)):
            ET.SubElement(c, q("v")).text = repr(value)
        else:
            c.set("t", "inlineStr")
            is_el = ET.SubElement(c, q("is"))
            t = ET.SubElement(is_el, q("t"))
            t.text = str(value)
            if str(value) != str(value).strip():
                t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")

    def get_formula(self, ref):
        rownum = int(re.search(r"\d+", ref).group(0))
        for r in self.sheet_data.findall(q("row")):
            if int(r.get("r")) == rownum:
                for c in r.findall(q("c")):
                    if c.get("r") == ref:
                        f = c.find(q("f"))
                        return f.text if f is not None else None
        return None

    def strip_cached_formula_values(self):
        """Borra los valores cacheados de las fórmulas para forzar recálculo al abrir."""
        for r in self.sheet_data.findall(q("row")):
            for c in r.findall(q("c")):
                if c.find(q("f")) is not None:
                    v = c.find(q("v"))
                    if v is not None:
                        c.remove(v)
                    if c.get("t") in ("str", "e"):
                        c.attrib.pop("t", None)

    def tobytes(self):
        return ET.tostring(self.root, encoding="UTF-8", xml_declaration=True)


def main(tpl_path, json_path, out_path):
    with open(json_path, encoding="utf-8") as f:
        d = json.load(f)
    sol, veh, chk = d["solicitante"], d["vehiculo"], d["checklist"]

    # ── Validaciones obligatorias ──
    dni = str(sol.get("dni", "")).strip()
    if not re.fullmatch(r"\d{8}", dni):
        fail(f"DNI debe ser texto de 8 dígitos (conservar cero inicial), recibido: {dni!r}")
    if not veh.get("placa"):
        fail("Falta la placa del vehículo (TIV)")
    fecha_str = str(chk.get("fecha_ingreso", "")).strip()
    try:
        fecha = datetime.strptime(fecha_str, "%d/%m/%Y")
    except ValueError:
        fail(f"fecha_ingreso debe ser DD/MM/YYYY, recibido: {fecha_str!r}")
    for campo in ("celular", "kilometraje", "litros", "galones", "kit_marca", "precio"):
        if not str(chk.get(campo, "")).strip():
            fail(f"Falta el campo obligatorio del checklist: {campo}")
    correlativo = str(d.get("correlativo", "")).strip()
    if correlativo and not re.fullmatch(r"\d{4}", correlativo):
        fail(f"El correlativo debe tener 4 dígitos, recibido: {correlativo!r}")

    fecha_txt = fecha.strftime("%d/%m/%Y")
    garantia_txt = fecha.replace(year=fecha.year + 1).strftime("%d/%m/%Y")

    def num(v):
        s = str(v).replace(",", "").replace("S/", "").strip()
        try:
            f = float(s)
            return int(f) if f == int(f) else f
        except ValueError:
            return s

    zin = zipfile.ZipFile(tpl_path)

    # Mapa nombre de hoja -> archivo XML
    wb_xml = zin.read("xl/workbook.xml").decode("utf-8")
    rels_xml = zin.read("xl/_rels/workbook.xml.rels").decode("utf-8")
    rid_to_target = dict(re.findall(r'Id="(rId\d+)"[^>]*Target="([^"]+)"', rels_xml))
    name_to_file = {}
    for name, rid in re.findall(r'<sheet name="([^"]+)"[^>]*r:id="(rId\d+)"', wb_xml):
        name_to_file[name] = "xl/" + rid_to_target[rid].lstrip("/")

    sheets = {n: Sheet(zin.read(f)) for n, f in name_to_file.items()}

    # ── Hoja DATOS (maestra) ──
    datos = sheets["DATOS"]
    datos.set("B8", sol["nombre"].upper().strip())
    datos.set("B9", (sol.get("ruc") or "").strip())
    datos.set("B10", sol["direccion"].upper().strip())
    datos.set("B11", sol["dep_prov_dist"].upper().strip())
    datos.set("B12", dni)  # texto: conserva ceros a la izquierda
    datos.set("B13", (sol.get("rep_legal") or "").strip())
    datos.set("B14", (sol.get("dni_rep_legal") or "").strip())
    datos.set("B15", str(chk["celular"]).strip())
    datos.set("B16", f"{veh['marca'].strip()} {veh['modelo'].strip()}".upper())
    datos.set("B17", veh["marca"].upper().strip())
    datos.set("B18", veh["modelo"].upper().strip())
    datos.set("B19", str(veh["anio"]).strip())
    datos.set("B20", veh["placa"].upper().strip())
    datos.set("B21", veh["color"].upper().strip())
    datos.set("B22", veh["combustible"].upper().strip())
    datos.set("B23", str(veh["cilindrada"]).strip())
    datos.set("B24", veh.get("categoria", "M1").upper().strip())
    datos.set("B25", fecha)  # fecha Excel: alimenta C25/D25/E25 y G46 de COND PN/PJ
    datos.set("B26", int(chk.get("cant_cilindros", 1)))
    datos.set("B27", str(chk.get("ubicacion_cilindro", "Maletera")).strip())
    datos.set("B28", str(chk["litros"]).strip())
    datos.set("B29", str(chk["galones"]).strip())
    datos.set("B30", str(chk["litros"]).strip())
    datos.set("B31", chk["kit_marca"].upper().strip())
    datos.set("B32", num(chk["precio"]))
    datos.set("B33", num(chk.get("descuento_glp") or 0))
    datos.set("B34", num(chk["kilometraje"]))
    datos.set("B35", str(chk.get("correo", "")).strip())
    datos.set("B37", fecha_txt)
    datos.set("B45", garantia_txt)
    datos.set("B46", veh["vin"].upper().strip())
    datos.set("B47", str(veh["partida"]).strip())
    for ref in ("C35", "E36", "F29"):  # residuos de la plantilla
        datos.set(ref, None)

    # ── Celdas literales fuera de DATOS ──
    prof = sheets["PROF."]
    prof.set("J6", fecha_txt)
    prof.set("F17", "=DATOS!B29")  # corrige el '2+2' fijo de la plantilla
    prof.set("G22", fecha_txt)

    dec = sheets["DECLARACIÒN."]
    dec.set("C6", f"{sol['nombre'].upper().strip()}, ")
    dec.set("K6", f"{dni},")
    dec.set("H7", veh["placa"].upper().strip())
    dec.set("D11", (f"Que el día {fecha.day} de {MESES[fecha.month - 1]} de {fecha.year}, "
                    "he entregado correctamente el kit de conversión a GLP, "
                    "financiado a través del"))
    dec.set("D12", "Programa FISE, correspondiente al siguiente vehículo:")
    dec.set("F14", veh["placa"].upper().strip())
    dec.set("F15", veh["marca"].upper().strip())
    dec.set("F16", veh["modelo"].upper().strip())
    dec.set("F17", str(veh["anio"]).strip())
    for ref in ("F43", "F45", "H43", "H45"):  # datos de tanque aún no existen
        dec.set(ref, None)

    if correlativo:
        sheets["COND. DE DEVOLUCION PN"].set("I2", correlativo)

    sheets["CHECK"].set("C43", fecha_txt)
    gar = sheets["GARANTIA"]
    gar.set("C12", str(veh["anio"]).strip())
    gar.set("E20", fecha_txt)

    # ── Plantilla v2: G46 de COND PN/PJ debe ser fórmula =DATOS!B25 ──
    for hoja in ("COND. DE DEVOLUCION PN", "COND. DE DEVOLUCION PJ"):
        f = sheets[hoja].get_formula("G46")
        if not f or "B25" not in f:
            print(f"AVISO: {hoja}!G46 no es la fórmula esperada ({f!r}) — "
                  "¿plantilla antigua? Se escribe la fecha literal como respaldo.",
                  file=sys.stderr)
            sheets[hoja].set("G46", fecha_txt)

    # Forzar recálculo de TODAS las fórmulas al abrir el archivo
    for s in sheets.values():
        s.strip_cached_formula_values()
    wb_xml = re.sub(r"<calcPr ", '<calcPr fullCalcOnLoad="1" ', wb_xml, count=1)

    # ── Escribir el zip de salida preservando todo lo demás (imágenes, firmas…) ──
    modified = {name_to_file[n]: s.tobytes() for n, s in sheets.items()}
    modified["xl/workbook.xml"] = wb_xml.encode("utf-8")
    # calcChain queda obsoleto al cambiar fórmulas: Excel lo reconstruye solo
    calc_rid = next((rid for rid, tgt in rid_to_target.items()
                     if tgt.endswith("calcChain.xml")), None)
    if calc_rid:
        rels_xml = re.sub(rf'<Relationship Id="{calc_rid}"[^>]*/>', "", rels_xml)
        modified["xl/_rels/workbook.xml.rels"] = rels_xml.encode("utf-8")
    ct = zin.read("[Content_Types].xml").decode("utf-8")
    ct = re.sub(r'<Override PartName="/xl/calcChain\.xml"[^>]*/>', "", ct)
    modified["[Content_Types].xml"] = ct.encode("utf-8")

    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if item.filename == "xl/calcChain.xml":
                continue
            zout.writestr(item, modified.get(item.filename, zin.read(item.filename)))

    print(f"OK — matriz generada: {out_path}")
    print(f"  Placa {veh['placa']} | DNI {dni} | Fecha {fecha_txt} | Garantía {garantia_txt} | "
          f"Correlativo {correlativo or '(no indicado, quedó el de la plantilla)'}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        fail("Uso: python llenar_matriz.py <plantilla.xlsx> <datos.json> <salida.xlsx>")
    main(sys.argv[1], sys.argv[2], sys.argv[3])
