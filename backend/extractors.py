import json
from pathlib import Path

import pymupdf
import pandas as pd

import pytesseract
from PIL import Image

from docx import Document
from openpyxl import load_workbook
from pptx import Presentation
from bs4 import BeautifulSoup


def extract_pdf(pdf_path):
    pdf = pymupdf.open(pdf_path)
    all_text = ""

    for page in pdf:
        text = page.get_text()
        if not text or len(text.strip()) < 30:
            # Automatic OCR fallback for scanned or image-based PDFs
            try:
                import io
                from PIL import Image
                import pytesseract
                pix = page.get_pixmap(dpi=200)
                img = Image.open(io.BytesIO(pix.tobytes()))
                ocr_text = pytesseract.image_to_string(img)
                if ocr_text and len(ocr_text.strip()) > len(text.strip()):
                    text = ocr_text
            except Exception as e:
                print(f"PDF OCR extraction note for {pdf_path}: {e}")

        all_text += (text or "") + "\n"

    pdf.close()
    return all_text


def extract_txt(txt_path):
    with open(txt_path, "r", encoding="utf-8") as file:
        return file.read()


def extract_docx(docx_path):
    document = Document(docx_path)

    all_text = ""

    for paragraph in document.paragraphs:
        all_text += paragraph.text + "\n"

    return all_text


def extract_csv(csv_path):
    data = pd.read_csv(csv_path)

    return data.to_string(index=False)


def extract_xlsx(xlsx_path):
    workbook = load_workbook(xlsx_path, data_only=True)

    all_text = ""

    for sheet in workbook.worksheets:
        all_text += f"\nSheet: {sheet.title}\n"

        for row in sheet.iter_rows(values_only=True):
            row_text = " | ".join(
                str(cell) if cell is not None else ""
                for cell in row
            )

            all_text += row_text + "\n"

    return all_text


def extract_pptx(pptx_path):
    presentation = Presentation(pptx_path)

    all_text = ""

    for slide_number, slide in enumerate(
        presentation.slides, start=1
    ):
        all_text += f"\nSlide {slide_number}\n"

        for shape in slide.shapes:
            if hasattr(shape, "text"):
                all_text += shape.text + "\n"

    return all_text


def extract_json(json_path):
    with open(json_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    return json.dumps(data, indent=2)


def extract_html(html_path):
    with open(html_path, "r", encoding="utf-8") as file:
        html = file.read()

    soup = BeautifulSoup(html, "html.parser")

    return soup.get_text(separator="\n", strip=True)

def extract_image(image_path):
    image = Image.open(image_path)

    text = pytesseract.image_to_string(image)

    return text


def extract_text(file_path):
    extension = Path(file_path).suffix.lower()

    if extension == ".pdf":
        return extract_pdf(file_path)

    elif extension == ".txt":
        return extract_txt(file_path)

    elif extension == ".docx":
        return extract_docx(file_path)

    elif extension == ".csv":
        return extract_csv(file_path)

    elif extension == ".xlsx":
        return extract_xlsx(file_path)

    elif extension == ".pptx":
        return extract_pptx(file_path)

    elif extension == ".json":
        return extract_json(file_path)

    elif extension == ".html":
        return extract_html(file_path)

    elif extension in [".png", ".jpg", ".jpeg", ".webp"]:
        return extract_image(file_path)

    else:
        return f"Unsupported file format: {extension}"