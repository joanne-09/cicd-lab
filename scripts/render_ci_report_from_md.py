from pathlib import Path
import html
import re

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, KeepTogether, Paragraph, Preformatted, SimpleDocTemplate, Spacer


ROOT = Path(__file__).resolve().parents[1]
MD_PATH = ROOT / "output" / "pdf" / "112062309_姓名_CICD_作業.md"
PDF_PATH = ROOT / "output" / "pdf" / "112062309_姓名_CICD_作業.pdf"


def register_fonts() -> None:
    font = Path("C:/Windows/Fonts/msjh.ttc")
    bold = Path("C:/Windows/Fonts/msjhbd.ttc")
    pdfmetrics.registerFont(TTFont("MSJH", str(font)))
    pdfmetrics.registerFont(TTFont("MSJH-Bold", str(bold if bold.exists() else font)))


def make_styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "title",
            parent=base["Title"],
            fontName="MSJH-Bold",
            fontSize=22,
            leading=30,
            alignment=TA_CENTER,
            spaceAfter=16,
            textColor=colors.HexColor("#111827"),
            wordWrap="CJK",
        ),
        "h2": ParagraphStyle(
            "h2",
            parent=base["Heading2"],
            fontName="MSJH-Bold",
            fontSize=14,
            leading=20,
            spaceBefore=12,
            spaceAfter=7,
            textColor=colors.HexColor("#111827"),
            wordWrap="CJK",
        ),
        "body": ParagraphStyle(
            "body",
            parent=base["BodyText"],
            fontName="MSJH",
            fontSize=10.5,
            leading=16,
            spaceAfter=7,
            textColor=colors.HexColor("#1f2937"),
            wordWrap="CJK",
        ),
        "bullet": ParagraphStyle(
            "bullet",
            parent=base["BodyText"],
            fontName="MSJH",
            fontSize=10.5,
            leading=16,
            leftIndent=16,
            firstLineIndent=-9,
            spaceAfter=3,
            textColor=colors.HexColor("#1f2937"),
            wordWrap="CJK",
        ),
        "caption": ParagraphStyle(
            "caption",
            parent=base["BodyText"],
            fontName="MSJH",
            fontSize=9,
            leading=13,
            alignment=TA_CENTER,
            spaceBefore=5,
            spaceAfter=10,
            textColor=colors.HexColor("#4b5563"),
            wordWrap="CJK",
        ),
        "code": ParagraphStyle(
            "code",
            parent=base["Code"],
            fontName="Courier",
            fontSize=7.6,
            leading=9.6,
            borderColor=colors.HexColor("#d1d5db"),
            borderWidth=0.45,
            borderPadding=7,
            backColor=colors.HexColor("#f8fafc"),
        ),
    }


def inline(text: str) -> str:
    text = html.escape(text)
    text = re.sub(r"`([^`]+)`", r'<font name="Courier">\1</font>', text)
    return text.replace("**", "")


def add_paragraph(story, lines, style):
    if lines:
        story.append(Paragraph(inline(" ".join(lines)), style))
    return []


def add_image(story, md_dir: Path, src: str, caption: str | None, max_width: float, styles):
    path = (md_dir / src).resolve()
    width, height = ImageReader(str(path)).getSize()
    target_width = min(max_width * 0.82, 14.2 * cm)
    target_height = target_width * height / width
    if target_height > 8.2 * cm:
        target_height = 8.2 * cm
        target_width = target_height * width / height
    img = Image(str(path), width=target_width, height=target_height)
    img.hAlign = "CENTER"
    block = [img]
    if caption:
        block.append(Paragraph(inline(caption), styles["caption"]))
    story.append(KeepTogether(block))


def build() -> None:
    register_fonts()
    styles = make_styles()
    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=A4,
        rightMargin=1.45 * cm,
        leftMargin=1.45 * cm,
        topMargin=1.35 * cm,
        bottomMargin=1.35 * cm,
        title="112062309_姓名_CICD_作業",
        author="112062309",
    )
    max_width = A4[0] - doc.leftMargin - doc.rightMargin
    story = []
    paragraph = []
    code = []
    in_code = False
    pending_image = None

    for line in MD_PATH.read_text(encoding="utf-8").splitlines():
        if line.startswith("```"):
            if in_code:
                story.append(Preformatted("\n".join(code).rstrip(), styles["code"]))
                story.append(Spacer(1, 8))
                code = []
                in_code = False
            else:
                paragraph = add_paragraph(story, paragraph, styles["body"])
                in_code = True
            continue

        if in_code:
            code.append(line)
            continue

        image = re.match(r"!\[(.*?)\]\((.*?)\)", line)
        if image:
            paragraph = add_paragraph(story, paragraph, styles["body"])
            pending_image = image.group(2)
            continue

        if pending_image and line.startswith("圖 "):
            add_image(story, MD_PATH.parent, pending_image, line, max_width, styles)
            pending_image = None
            continue

        if line.startswith("# "):
            paragraph = add_paragraph(story, paragraph, styles["body"])
            story.append(Paragraph(inline(line[2:]), styles["title"]))
        elif line.startswith("## "):
            paragraph = add_paragraph(story, paragraph, styles["body"])
            story.append(Paragraph(inline(line[3:]), styles["h2"]))
        elif line.startswith("- "):
            paragraph = add_paragraph(story, paragraph, styles["body"])
            story.append(Paragraph("• " + inline(line[2:]), styles["bullet"]))
        elif not line.strip():
            paragraph = add_paragraph(story, paragraph, styles["body"])
            if not story or not isinstance(story[-1], Spacer):
                story.append(Spacer(1, 3))
        else:
            paragraph.append(line.strip())

    add_paragraph(story, paragraph, styles["body"])
    if pending_image:
        add_image(story, MD_PATH.parent, pending_image, None, max_width, styles)
    doc.build(story)
    print(PDF_PATH)


if __name__ == "__main__":
    build()
