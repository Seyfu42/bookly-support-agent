"""Render the deck spec to bookly-agent-deck.pptx and a preview.html.

    .venv/bin/python deck/build.py

Both renderers read deck/spec.py, so the HTML preview is a faithful stand-in for
the PowerPoint on a machine with no Office suite installed.
"""

import html
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

import spec

OUT = Path(__file__).parent
PX = 96.0  # inches -> CSS pixels

ALIGN = {"l": PP_ALIGN.LEFT, "c": PP_ALIGN.CENTER, "r": PP_ALIGN.RIGHT}
CSS_ALIGN = {"l": "left", "c": "center", "r": "right"}


def rgb(h):
    return RGBColor.from_string(h)


def runs_of(el):
    """Normalise `body` to a list of (text, overrides) tuples."""
    body = el["body"]
    return [(body, {})] if isinstance(body, str) else body


# ---------------------------------------------------------------- PowerPoint
def build_pptx(path):
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(spec.W), Inches(spec.H)
    blank = prs.slide_layouts[6]

    for sl in spec.SLIDES:
        slide = prs.slides.add_slide(blank)

        bg = slide.background.fill
        bg.solid()
        bg.fore_color.rgb = rgb(sl["bg"])

        for el in sl["el"]:
            if el["t"] == "rect":
                shape_type = MSO_SHAPE.ROUNDED_RECTANGLE if el["radius"] else MSO_SHAPE.RECTANGLE
                sh = slide.shapes.add_shape(
                    shape_type, Inches(el["x"]), Inches(el["y"]),
                    Inches(el["w"]), Inches(el["h"]),
                )
                if el["radius"]:
                    # adjustment is a fraction of the shorter side
                    sh.adjustments[0] = min(0.5, el["radius"] / min(el["w"], el["h"]))
                sh.fill.solid()
                sh.fill.fore_color.rgb = rgb(el["fill"])
                if el["line"]:
                    sh.line.color.rgb = rgb(el["line"])
                    sh.line.width = Pt(1)
                else:
                    sh.line.fill.background()
                sh.shadow.inherit = False
                sh.text_frame.text = ""

            elif el["t"] == "arrow":
                sh = slide.shapes.add_shape(
                    MSO_SHAPE.RIGHT_ARROW, Inches(el["x"]), Inches(el["y"] - 0.075),
                    Inches(el["w"]), Inches(0.15),
                )
                sh.fill.solid()
                sh.fill.fore_color.rgb = rgb(el["color"])
                sh.line.fill.background()
                sh.shadow.inherit = False

            elif el["t"] == "text":
                box = slide.shapes.add_textbox(
                    Inches(el["x"]), Inches(el["y"]), Inches(el["w"]), Inches(el["h"])
                )
                tf = box.text_frame
                tf.word_wrap = True
                tf.margin_left = tf.margin_right = 0
                tf.margin_top = tf.margin_bottom = 0
                tf.vertical_anchor = MSO_ANCHOR.TOP

                # Each "\n" in the spec is a real paragraph.
                lines = [[]]
                for txt, over in runs_of(el):
                    parts = txt.split("\n")
                    for i, part in enumerate(parts):
                        if i:
                            lines.append([])
                        lines[-1].append((part, over))

                for li, line in enumerate(lines):
                    para = tf.paragraphs[0] if li == 0 else tf.add_paragraph()
                    para.alignment = ALIGN[el["align"]]
                    para.line_spacing = el["spacing"]
                    if el["space_after"]:
                        para.space_after = Pt(el["space_after"])
                    for txt, over in line:
                        run = para.add_run()
                        run.text = txt
                        f = run.font
                        f.name = over.get("font", el["font"])
                        f.size = Pt(over.get("size", el["size"]))
                        f.bold = over.get("bold", el["bold"])
                        f.italic = over.get("italic", el["italic"])
                        f.color.rgb = rgb(over.get("color", el["color"]))

        if sl.get("notes"):
            slide.notes_slide.notes_text_frame.text = sl["notes"]

    prs.save(path)
    return path


# ---------------------------------------------------------------------- HTML
def build_html(path):
    css = """
body { margin:0; background:#3b3f42; font-family:Calibri,Carlito,sans-serif; }
.wrap { display:flex; flex-direction:column; align-items:center; gap:22px; padding:24px 24px 24px 48px; }
.slide { position:relative; flex:none; width:%dpx; height:%dpx;
         overflow:hidden; box-shadow:0 6px 26px rgba(0,0,0,.42); }
.el { position:absolute; box-sizing:border-box; }
.tx { white-space:pre-wrap; }
.num { position:absolute; left:-30px; top:0; color:#9aa0a4;
       font:600 13px Calibri,sans-serif; }
""" % (round(spec.W * PX), round(spec.H * PX))

    out = [
        "<meta charset='utf-8'><title>Deck preview</title>",
        "<style>" + css + "</style>",
        "<div class='wrap'>",
    ]
    for i, sl in enumerate(spec.SLIDES, 1):
        out.append(f"<div class='slide' style='background:#{sl['bg']}'>")
        out.append(f"<div class='num'>{i}</div>")
        for el in sl["el"]:
            L, T = el["x"] * PX, el["y"] * PX
            Wd = el["w"] * PX
            Ht = el.get("h", 0.0) * PX  # arrows carry no height
            if el["t"] == "rect":
                border = f"border:1px solid #{el['line']};" if el["line"] else ""
                out.append(
                    f"<div class='el' style='left:{L:.1f}px;top:{T:.1f}px;"
                    f"width:{Wd:.1f}px;height:{Ht:.1f}px;background:#{el['fill']};"
                    f"border-radius:{el['radius']*PX:.1f}px;{border}'></div>"
                )
            elif el["t"] == "arrow":
                out.append(
                    f"<div class='el' style='left:{L:.1f}px;top:{(el['y']-0.03)*PX:.1f}px;"
                    f"width:{Wd:.1f}px;height:{0.06*PX:.1f}px;background:#{el['color']};'></div>"
                )
            else:
                inner = "".join(
                    "<span style='"
                    f"font-family:{over.get('font', el['font'])},sans-serif;"
                    f"font-size:{over.get('size', el['size'])/0.75:.1f}px;"
                    f"font-weight:{700 if over.get('bold', el['bold']) else 400};"
                    f"font-style:{'italic' if over.get('italic', el['italic']) else 'normal'};"
                    f"color:#{over.get('color', el['color'])};"
                    f"'>{html.escape(t)}</span>"
                    for t, over in runs_of(el)
                )
                out.append(
                    f"<div class='el tx' style='left:{L:.1f}px;top:{T:.1f}px;"
                    f"width:{Wd:.1f}px;height:{Ht:.1f}px;"
                    f"line-height:{el['spacing']};text-align:{CSS_ALIGN[el['align']]};"
                    f"'>{inner}</div>"
                )
        out.append("</div>")
    out.append("</div>")
    Path(path).write_text("\n".join(out), encoding="utf-8")
    return path


if __name__ == "__main__":
    p = build_pptx(OUT / "bookly-agent-deck.pptx")
    h = build_html(OUT / "preview.html")
    print(f"wrote {p}")
    print(f"wrote {h}")
