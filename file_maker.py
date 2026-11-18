from io import BytesIO
from datetime import datetime
from docx import Document
from openpyxl import Workbook
from pptx import Presentation
import re
import requests
from ddgs import DDGS
from pptx.util import Inches, Pt
# Generate a formatted Word (.docx) document with topic, timestamp, content, and sources
def create_word_doc(topic: str, content: str, sources: str = "") -> str:
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
    doc = Document()
    doc.add_heading(topic, level=1)
    doc.add_paragraph(f"Created at: {now.strftime("%Y-%m-%d_%H-%M-%S")}")
    doc.add_paragraph(content)
    if sources:
        doc.add_heading("Sources", level=2)
        doc.add_paragraph(sources)
    file_stream = BytesIO()
    doc.save(file_stream)
    file_stream.seek(0)
    return file_stream
# Generate a formatted Word (.docx) document with topic, timestamp, content, and sources
def create_excel_table(topic: str, csv_content: str, sources: str = "") -> str:
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
    wb = Workbook()
    ws = wb.active
    ws.title = "Data"
    ws.append([topic, f"Created at: {timestamp}"])
    ws.append([])
    for line in csv_content.strip().split("\n"):
        ws.append([cell.strip() for cell in line.split(";")])
    if sources:
        ws.append([])
        ws.append(["Sources:", sources])
    file_stream = BytesIO()
    wb.save(file_stream)
    file_stream.seek(0)
    return file_stream
# Generate a PowerPoint (.pptx) presentation by splitting text into slides using '---' markers
def create_presentation(topic: str, slides_content: str, sources: str = "") -> str:
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
    prs = Presentation()
    titel_slide = prs.slides.add_slide(prs.slide_layouts[0])
    titel_slide.shapes.title.text = topic
    titel_slide.placeholders[1].text = f"Created at: {timestamp}"
    clean_content = slides_content.replace("\u202f", " ").replace("\xa0", " ")
    if "===SLIDE===" in clean_content:
        slides = clean_content.strip().split("===SLIDE===")
    else:
        slides = re.split(r'\n\s*(?=[\*\#\-\s]*(?:Слайд|Slide)\s*\d+)', clean_content.strip(), flags=re.IGNORECASE)
    if len(slides) <= 1 :
        slides = [p for p in slides_content.strip().split("\n\n") if p.strip()]
    image_urls = []
    try:
        img_results = DDGS().images(topic, max_results=15)
        image_urls = [item["image"] for item in img_results if item.get("image")]
    except Exception as e:
        print(f"Image search warning: {e}")
    for slide_text in slides:
        lines = [line.strip() for line in slide_text.strip().split("\n") if line.strip()]
        if lines and re.match(r'^[\*\#\-\s]*(?:Слайд|Slide)\s*\d+[\:\-\.\*\#\s]*$', lines[0], flags=re.IGNORECASE):
            lines.pop(0)
        if len(lines) >=2:
            slide = prs.slides.add_slide(prs.slide_layouts[1])
            slide.shapes.title.text = lines[0].replace("*", "").replace("#", "").strip()
            slide.shapes.title.text_frame.paragraphs[0].font.size = Pt(24)
            clean_body = [line.replace("**", "").replace("###", "").strip() for line in lines[1:]]
            body_shape = slide.placeholders[1]
            body_shape.left = Inches(0.5)
            body_shape.top = Inches(1.8)
            body_shape.width = Inches(5.0)
            body_shape.height = Inches(5.0)
            body_shape.text = "\n".join(clean_body)
            for p in body_shape.text_frame.paragraphs:
                p.font.size = Pt(16)
            while image_urls:
                url = image_urls.pop(0)
                try:
                    resp = requests.get(url, timeout=4, headers={"User-Agent": "Mozilla/5.0"})
                    if resp.status_code == 200 and "image" in resp.headers.get("Content-Type", ""):
                        img_stream = BytesIO(resp.content)
                        slide.shapes.add_picture(img_stream, Inches(5.8), Inches(1.8), width=Inches(3.7))
                        break
                except Exception:
                    continue     
    if sources:
            sources_slide = prs.slides.add_slide(prs.slide_layouts[1])
            sources_slide.shapes.title.text = "Sources"
            sources_slide.placeholders[1].text = sources
    file_stream = BytesIO()
    prs.save(file_stream)
    file_stream.seek(0)
    return file_stream