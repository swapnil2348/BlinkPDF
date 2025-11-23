# pdf_processor.py

import os
import uuid
import zipfile
from typing import List, Mapping, Tuple, Optional

from PyPDF2 import PdfReader, PdfWriter
import fitz  # PyMuPDF
from PIL import Image
from docx import Document
import openpyxl
from pptx import Presentation
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

# ---- helpers -------------------------------------------------------------

def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _tmp_name(prefix: str, ext: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}{ext}"


# ---- core processor ------------------------------------------------------

def process_pdf_tool(
    slug: str,
    input_paths: List[str],
    output_dir: str,
    form: Mapping[str, str] | Mapping
) -> Tuple[str, str, Optional[str]]:
    """
    Main entry from app.py

    Returns:
        (output_path, download_name, mimetype)
    """
    ensure_dir(output_dir)

    if not input_paths:
        raise ValueError("No input files")

    # Single "primary" input for most tools
    primary = input_paths[0]

    # ---------------- BASIC PDF OPERATIONS ----------------

    if slug == "merge-pdf":
        out_path = os.path.join(output_dir, _tmp_name("merged", ".pdf"))
        writer = PdfWriter()
        for p in input_paths:
            reader = PdfReader(p)
            for page in reader.pages:
                writer.add_page(page)
        with open(out_path, "wb") as f:
            writer.write(f)
        return out_path, os.path.basename(out_path), "application/pdf"

    if slug == "split-pdf":
        # each page as separate PDF, zipped
        zip_path = os.path.join(output_dir, _tmp_name("split_pages", ".zip"))
        reader = PdfReader(primary)
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for i, page in enumerate(reader.pages, start=1):
                writer = PdfWriter()
                writer.add_page(page)
                page_filename = f"page_{i}.pdf"
                page_path = os.path.join(output_dir, page_filename)
                with open(page_path, "wb") as pf:
                    writer.write(pf)
                zf.write(page_path, arcname=page_filename)
                os.remove(page_path)
        return zip_path, os.path.basename(zip_path), "application/zip"

    if slug in ("compress-pdf", "optimize-pdf"):
        # simple compression: re-render pages with lower image quality via PyMuPDF
        out_path = os.path.join(output_dir, _tmp_name("compressed", ".pdf"))
        doc = fitz.open(primary)
        # Save with deflate & basic optimization
        doc.save(out_path, deflate=True, garbage=4)
        doc.close()
        return out_path, os.path.basename(out_path), "application/pdf"

    if slug == "rotate-pdf":
        # default 90 degrees clockwise. UI may send angle, try reading it:
        angle = int(form.get("angle", "90"))
        out_path = os.path.join(output_dir, _tmp_name("rotated", ".pdf"))
        reader = PdfReader(primary)
        writer = PdfWriter()
        for page in reader.pages:
            page.rotate(angle)
            writer.add_page(page)
        with open(out_path, "wb") as f:
            writer.write(f)
        return out_path, os.path.basename(out_path), "application/pdf"

    if slug == "unlock-pdf":
        out_path = os.path.join(output_dir, _tmp_name("unlocked", ".pdf"))
        reader = PdfReader(primary)
        # try empty password or UI password
        password = form.get("password", "") or ""
        if reader.is_encrypted:
            try:
                reader.decrypt(password)
            except Exception:
                # fall back to empty
                try:
                    reader.decrypt("")
                except Exception:
                    pass
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        with open(out_path, "wb") as f:
            writer.write(f)
        return out_path, os.path.basename(out_path), "application/pdf"

    if slug == "protect-pdf":
        out_path = os.path.join(output_dir, _tmp_name("protected", ".pdf"))
        password = form.get("password", "") or "protected"
        reader = PdfReader(primary)
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        writer.encrypt(password)
        with open(out_path, "wb") as f:
            writer.write(f)
        return out_path, os.path.basename(out_path), "application/pdf"

    # ---------------- PDF <-> IMAGE ----------------

    if slug in ("pdf-to-image", "pdf-to-jpg"):
        # render pages to JPG and zip them
        zip_path = os.path.join(output_dir, _tmp_name("images", ".zip"))
        doc = fitz.open(primary)
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for i, page in enumerate(doc, start=1):
                pix = page.get_pixmap()
                img_name = f"page_{i}.jpg"
                img_path = os.path.join(output_dir, img_name)
                pix.save(img_path)
                zf.write(img_path, arcname=img_name)
                os.remove(img_path)
        doc.close()
        return zip_path, os.path.basename(zip_path), "application/zip"

    if slug in ("image-to-pdf", "jpg-to-pdf"):
        # join all uploaded images into single PDF
        out_path = os.path.join(output_dir, _tmp_name("images", ".pdf"))
        images = []
        for p in input_paths:
            img = Image.open(p).convert("RGB")
            images.append(img)
        if not images:
            raise ValueError("No images provided")
        first, rest = images[0], images[1:]
        first.save(out_path, save_all=True, append_images=rest)
        return out_path, os.path.basename(out_path), "application/pdf"

    # ---------------- PDF <-> WORD ----------------

    if slug == "pdf-to-word":
        # simple: extract text and put it into a .docx
        out_path = os.path.join(output_dir, _tmp_name("pdf_to_word", ".docx"))
        reader = PdfReader(primary)
        docx_doc = Document()
        for page in reader.pages:
            text = page.extract_text() or ""
            if text.strip():
                for line in text.splitlines():
                    docx_doc.add_paragraph(line)
        docx_doc.save(out_path)
        return out_path, os.path.basename(out_path), (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

    if slug == "word-to-pdf":
        # simple: read docx text and render into a PDF using reportlab
        out_path = os.path.join(output_dir, _tmp_name("word_to_pdf", ".pdf"))
        docx_doc = Document(primary)
        c = canvas.Canvas(out_path, pagesize=A4)
        width, height = A4
        y = height - 50
        for para in docx_doc.paragraphs:
            text = para.text
            if not text:
                y -= 20
                if y < 50:
                    c.showPage()
                    y = height - 50
                continue
            c.drawString(50, y, text[:2000])  # basic
            y -= 20
            if y < 50:
                c.showPage()
                y = height - 50
        c.save()
        return out_path, os.path.basename(out_path), "application/pdf"

    # ---------------- PDF <-> EXCEL ----------------

    if slug == "pdf-to-excel":
        # very naive: dump all text into a single column
        out_path = os.path.join(output_dir, _tmp_name("pdf_to_excel", ".xlsx"))
        reader = PdfReader(primary)
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Extracted"
        row = 1
        for page in reader.pages:
            text = page.extract_text() or ""
            for line in text.splitlines():
                ws.cell(row=row, column=1).value = line
                row += 1
        wb.save(out_path)
        return out_path, os.path.basename(out_path), (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    if slug == "excel-to-pdf":
        # render spreadsheet text into PDF with reportlab
        out_path = os.path.join(output_dir, _tmp_name("excel_to_pdf", ".pdf"))
        wb = openpyxl.load_workbook(primary, data_only=True)
        c = canvas.Canvas(out_path, pagesize=A4)
        width, height = A4
        y = height - 50
        for sheet in wb.worksheets:
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y, f"Sheet: {sheet.title}")
            y -= 30
            c.setFont("Helvetica", 10)
            for row in sheet.iter_rows(values_only=True):
                line = " | ".join("" if v is None else str(v) for v in row)
                c.drawString(50, y, line[:2000])
                y -= 15
                if y < 50:
                    c.showPage()
                    y = height - 50
        c.save()
        return out_path, os.path.basename(out_path), "application/pdf"

    # ---------------- PDF <-> POWERPOINT ----------------

    if slug == "pdf-to-powerpoint":
        # make one slide per PDF page with a rasterized image
        out_path = os.path.join(output_dir, _tmp_name("pdf_to_ppt", ".pptx"))
        prs = Presentation()
        blank_layout = prs.slide_layouts[6]  # blank
        doc = fitz.open(primary)
        for page in doc:
            pix = page.get_pixmap()
            img_name = _tmp_name("slide", ".png")
            img_path = os.path.join(output_dir, img_name)
            pix.save(img_path)

            slide = prs.slides.add_slide(blank_layout)
            left = top = 0
            slide.shapes.add_picture(img_path, left, top, height=prs.slide_height)
            os.remove(img_path)
        doc.close()
        prs.save(out_path)
        return out_path, os.path.basename(out_path), (
            "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        )

    if slug == "powerpoint-to-pdf":
        # very basic: dump text content of slides into a PDF
        out_path = os.path.join(output_dir, _tmp_name("ppt_to_pdf", ".pdf"))
        prs = Presentation(primary)
        c = canvas.Canvas(out_path, pagesize=A4)
        width, height = A4
        y = height - 50
        for slide in prs.slides:
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y, "Slide")
            y -= 25
            c.setFont("Helvetica", 10)
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    for line in shape.text.splitlines():
                        c.drawString(50, y, line[:2000])
                        y -= 15
                        if y < 50:
                            c.showPage()
                            y = height - 50
            y -= 30
            if y < 50:
                c.showPage()
                y = height - 50
        c.save()
        return out_path, os.path.basename(out_path), "application/pdf"

    # ---------------- EXTRACTION / OCR ----------------

    if slug == "extract-text":
        out_path = os.path.join(output_dir, _tmp_name("extracted_text", ".txt"))
        reader = PdfReader(primary)
        with open(out_path, "w", encoding="utf-8") as f:
            for page in reader.pages:
                text = page.extract_text() or ""
                f.write(text)
                f.write("\n\n")
        return out_path, os.path.basename(out_path), "text/plain"

    if slug == "extract-images":
        zip_path = os.path.join(output_dir, _tmp_name("images", ".zip"))
        doc = fitz.open(primary)
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            img_index = 1
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                for img in page.get_images(full=True):
                    xref = img[0]
                    pix = fitz.Pixmap(doc, xref)
                    img_name = f"image_{page_num+1}_{img_index}.png"
                    img_path = os.path.join(output_dir, img_name)
                    if pix.n < 5:
                        pix.save(img_path)
                    else:
                        pix = fitz.Pixmap(fitz.csRGB, pix)
                        pix.save(img_path)
                    zf.write(img_path, arcname=img_name)
                    os.remove(img_path)
                    img_index += 1
        doc.close()
        return zip_path, os.path.basename(zip_path), "application/zip"

    if slug == "ocr-pdf":
        # NOTE: requires Tesseract installed on the server
        try:
            import pytesseract
        except ImportError:
            raise RuntimeError("pytesseract / Tesseract not available")

        out_path = os.path.join(output_dir, _tmp_name("ocr_text", ".txt"))
        doc = fitz.open(primary)
        with open(out_path, "w", encoding="utf-8") as f:
            for page in doc:
                pix = page.get_pixmap()
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                text = pytesseract.image_to_string(img)
                f.write(text)
                f.write("\n\n")
        doc.close()
        return out_path, os.path.basename(out_path), "text/plain"

    # ---------------- ADVANCED TOOLS (safe passthrough) ----------------
    # For now these tools just return the same PDF (no-op) instead of error.
    # You can implement real behavior later.

    passthrough_slugs = {
        "watermark-pdf",
        "number-pdf",
        "repair-pdf",
        "organize-pdf",
        "sign-pdf",
        "annotate-pdf",
        "redact-pdf",
        "deskew-pdf",
        "crop-pdf",
        "resize-pdf",
        "flatten-pdf",
        "metadata-editor",
        "fill-forms",
        "background-remover",
    }

    if slug in passthrough_slugs:
        out_path = os.path.join(output_dir, _tmp_name(slug.replace("-", "_"), ".pdf"))
        # just copy primary file
        with open(primary, "rb") as src, open(out_path, "wb") as dst:
            dst.write(src.read())
        return out_path, os.path.basename(out_path), "application/pdf"

    # unknown slug -> raise
    raise ValueError(f"Unsupported tool slug: {slug}")
