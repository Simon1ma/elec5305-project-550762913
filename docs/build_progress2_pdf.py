"""Render the English progress description; requires reportlab and pymupdf."""
from pathlib import Path
from html import escape
import re

import pymupdf
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, SimpleDocTemplate

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs/project_progress2_working_description.md"
OUTPUT = ROOT / "output/pdf/ELEC5305_Project_Progress2_Yixiang_Ma_550762913.pdf"


def main():
    source = SOURCE.read_text(encoding="utf-8")
    assert not re.search(r"[\u3400-\u9fff]", source)
    body = ParagraphStyle("Body", fontName="Helvetica", fontSize=10.5,
                          leading=15, spaceAfter=12)
    info = ParagraphStyle("Info", parent=body, fontSize=9.5, leading=14,
                          spaceAfter=8)
    title = ParagraphStyle("Title", fontName="Helvetica-Bold", fontSize=16,
                           leading=21, spaceAfter=15)
    story = []
    for block in source.strip().split("\n\n"):
        heading = block.startswith("# ")
        text = escape((block[2:] if heading else block).replace("\n", " "))
        text = re.sub(r"https://\S+", lambda match:
                      f'<a href="{match[0]}" color="#155f92">{match[0]}</a>', text)
        is_info = block.startswith(("Yixiang Ma", "Project site:", "Detailed results:"))
        story.append(Paragraph(text, title if heading else info if is_info else body))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    def footer(canvas, document):
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#666666"))
        canvas.drawString(50, 28, "ELEC5305 | Second Project Progress | Yixiang Ma | 550762913")
        canvas.drawRightString(A4[0] - 50, 28, str(document.page))

    SimpleDocTemplate(str(OUTPUT), pagesize=A4, leftMargin=50, rightMargin=50,
                      topMargin=48, bottomMargin=48, author="Yixiang Ma",
                      title="ELEC5305 Second Project Progress").build(
                          story, onFirstPage=footer, onLaterPages=footer)
    with pymupdf.open(OUTPUT) as document:
        assert len(document) == 1
        text = document[0].get_text()
        assert not re.search(r"[\u3400-\u9fff]", text)
        assert all(value in text for value in ("DeepFilterNet3", "0.7020", "0.9092", "12.93"))
        links = [link["uri"] for link in document[0].get_links() if "uri" in link]
        assert len(links) == 2 and all("simon1ma.github.io" in link for link in links)
    print("PASS: one-page English PDF, current metrics, two clickable site links")
    print(OUTPUT)


if __name__ == "__main__":
    main()
