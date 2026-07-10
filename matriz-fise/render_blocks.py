# -*- coding: utf-8 -*-
"""
Renderiza los 5 bloques de texto de "COND. DE DEVOLUCION PN" como PNG,
con el texto NUEVO del Word CONDICONES_PERSONA_NATURAL.docx.
Cada PNG respeta exactamente la relación de aspecto del anclaje existente
en drawing3.xml para no distorsionar ni mover nada en la hoja.
"""
import docx
from docx.text.hyperlink import Hyperlink
from docx.text.run import Run
from PIL import Image, ImageDraw, ImageFont

DPI = 300
EMU_PER_INCH = 914400
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
BLACK = (0, 0, 0)
BLUE = (5, 99, 193)  # hipervínculo (correo)

d = docx.Document("CONDICIONES.docx")
paras = d.paragraphs

def get_runs(p):
    """Extrae runs incluyendo hipervínculos: [(texto, bold, underline, color)]."""
    out = []
    for item in p.iter_inner_content():
        if isinstance(item, Run):
            if item.text:
                color = BLACK
                fc = item.font.color
                if fc is not None and fc.type is not None and fc.rgb is not None:
                    color = tuple(bytes.fromhex(str(fc.rgb)))
                out.append((item.text, bool(item.bold), bool(item.underline), color))
        elif isinstance(item, Hyperlink):
            for r in item.runs:
                if r.text:
                    out.append((r.text, True, True, BLUE))
    # El Word parte el correo en 'fise' (negro) + '@minem.gob.pe' (hipervínculo):
    # unificar la parte previa en azul subrayado para que se vea como un solo enlace
    for i in range(len(out) - 1):
        if out[i][0].endswith("fise") and out[i + 1][3] == BLUE and out[i + 1][0].startswith("@"):
            t, b, u, c = out[i]
            out[i] = (t, b, True, BLUE) if t == "fise" else (t, b, u, c)
            if t != "fise" and t.endswith("fise"):
                out[i] = (t[:-4], b, u, c)
                out.insert(i + 1, ("fise", True, True, BLUE))
            break
    return out

# ---- construir párrafos lógicos con etiqueta de lista ----
def P(idx, label=None, kind="body"):
    """kind: body|item ; label: prefijo de lista ('a.', '6.1', '-')"""
    runs = get_runs(paras[idx])
    return {"runs": runs, "label": label, "kind": kind}

letters = "abcdefghijklmn"

blockA = [
    P(2),
    P(4),
    P(6),
] + [P(7 + i, label=f"{letters[i]}.", kind="item") for i in range(7)] + [
    P(15),
    P(17),
] + [P(18 + i, label=f"{letters[i]}.", kind="item") for i in range(3)] + [
    P(22),
]

blockB = [P(24), P(25)]

blockC = [
    P(28), P(29), P(30),
    P(32),
] + [P(33 + i, label=f"6.{i+1}", kind="item") for i in range(6)]

blockD = [P(39 + i, label=f"6.{i+7}", kind="item") for i in range(7)] + [
    P(47), P(49), P(51), P(53),
]

# Párrafo 64 empieza con "-Carta..." literal: normalizar a viñeta
p64 = P(64, label="-", kind="item")
if p64["runs"] and p64["runs"][0][0].startswith("-"):
    t, b, u, c = p64["runs"][0]
    p64["runs"][0] = (t.lstrip("-").lstrip(), b, u, c)

blockE = [
    P(55),
    P(56, label="-", kind="item"),
    P(57, label="-", kind="item"),
    P(58, label="-", kind="item"),
    P(59),
    P(61),
    P(62, label="-", kind="item"),
    P(63, label="-", kind="item"),
    p64,
    P(66),
]

# ---- destino: (archivo, cx EMU, cy EMU) según anclajes de drawing3.xml ----
BLOCKS = [
    ("image21.png", blockA, 3114260, 3727175),  # rId3: intro..QUINTA
    ("image20.png", blockB, 3034862, 326571),   # rId2: desembolso/devolución
    ("image22.png", blockC, 3048000, 3138535),  # rId4: post-tabla + 6.1-6.6
    ("image23.png", blockD, 3089414, 3992218),  # rId5: 6.7-6.13 + 7a-10a
    ("image24.png", blockE, 3089413, 1863586),  # rId6: 11a-13a
]

# ---- tokenizador: palabras con segmentos de estilo ----
def tokenize(runs):
    """Devuelve lista de tokens; cada token = lista de (texto, estilo)."""
    tokens, cur = [], []
    for text, b, u, c in runs:
        for ch in text:
            if ch.isspace():
                if cur:
                    tokens.append(cur)
                    cur = []
            else:
                if cur and cur[-1][1] == (b, u, c):
                    cur[-1] = (cur[-1][0] + ch, (b, u, c))
                else:
                    cur.append((ch, (b, u, c)))
    if cur:
        tokens.append(cur)
    return tokens

class Fonts:
    def __init__(self, size):
        self.reg = ImageFont.truetype(FONT_REG, size)
        self.bold = ImageFont.truetype(FONT_BOLD, size)
        self.size = size
    def of(self, style):
        return self.bold if style[0] else self.reg

def token_width(tok, fonts):
    return sum(fonts.of(st).getlength(txt) for txt, st in tok)

def layout_block(block, W, fonts, measure_only, draw=None):
    """Coloca el bloque; devuelve altura total usada."""
    size = fonts.size
    line_h = int(size * 1.16)
    gap_body = int(size * 0.52)   # espacio antes de párrafo normal
    gap_item = int(size * 0.10)   # espacio antes de ítem de lista
    space_w = fonts.reg.getlength(" ")
    y = 0
    first = True
    for para in block:
        if not first:
            y += gap_item if para["kind"] == "item" else gap_body
        first = False
        label = para["label"]
        if label:
            indent0 = int(size * 0.9)
            label_w = max(fonts.reg.getlength(x) for x in ("6.13", label))
            indent1 = indent0 + int(label_w + size * 0.55)
        else:
            indent0 = indent1 = 0
        tokens = tokenize(para["runs"])
        # partir en líneas
        lines, cur, cur_w = [], [], 0.0
        avail0 = W - indent1 if label else W
        for tok in tokens:
            tw = token_width(tok, fonts)
            add = tw if not cur else tw + space_w
            if cur and cur_w + add > avail0:
                lines.append((cur, cur_w))
                cur, cur_w = [tok], tw
            else:
                cur.append(tok)
                cur_w += add
        if cur:
            lines.append((cur, cur_w))
        # dibujar
        for li, (ltoks, lw) in enumerate(lines):
            x0 = indent1 if label else 0
            last = li == len(lines) - 1
            n_gaps = len(ltoks) - 1
            extra = 0.0
            if not last and n_gaps > 0:
                extra = (W - x0 - lw) / n_gaps
                if extra > space_w * 2.2:  # no justificar líneas muy cortas
                    extra = 0.0
            if draw is not None:
                if label and li == 0:
                    dfont = fonts.reg
                    draw.text((indent0, y), label, font=dfont, fill=BLACK)
                x = x0
                for tok in ltoks:
                    for txt, st in tok:
                        f = fonts.of(st)
                        draw.text((x, y), txt, font=f, fill=st[2])
                        seg_w = f.getlength(txt)
                        if st[1]:  # subrayado
                            uy = y + int(size * 1.02)
                            draw.line([(x, uy), (x + seg_w, uy)],
                                      fill=st[2], width=max(1, size // 14))
                        x += seg_w
                    x += space_w + extra
            y += line_h
    return y

def render(fname, block, cx, cy):
    W = round(cx / EMU_PER_INCH * DPI)
    H = round(cy / EMU_PER_INCH * DPI)
    # auto-ajuste: mayor tamaño de fuente <= 25px (6pt @300dpi) que quepa en H
    best = None
    for size in range(25, 13, -1):
        fonts = Fonts(size)
        used = layout_block(block, W, fonts, True)
        if used <= H:
            best = size
            break
    if best is None:
        raise SystemExit(f"{fname}: el texto no cabe ni a 14px")
    fonts = Fonts(best)
    img = Image.new("RGB", (W, H), "white")
    draw = ImageDraw.Draw(img)
    used = layout_block(block, W, fonts, False, draw)
    img.save(fname, dpi=(DPI, DPI))
    print(f"{fname}: {W}x{H}px  fuente={best}px ({best*72/DPI:.1f}pt @impresión)  usado={used}px de {H}px")

for fname, block, cx, cy in BLOCKS:
    render(fname, block, cx, cy)
