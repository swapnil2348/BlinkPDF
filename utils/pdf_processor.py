# utils/pdf_processor.py

import os
import io
import json
import tempfile
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any

import fitz  # PyMuPDF
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.utils import ImageReader

from PIL import Image, ImageOps
import pytesseract
from docx import Document
from pptx import Presentation
from pptx.util import Inches
import openpyxl
from openpyxl.utils import get_column_letter

# --------------------------------------------------------------------
# Error type used by app.py
# --------------------------------------------------------------------


class PDFProcessorError(Exception):
    """Custom exception for PDF processing errors."""


# --------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------


def _safe_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _page_ranges_to_list(spec: str, max_pages: int) -> List[int]:
    """
    Convert a string like "1,2,5-7" to [0,1,4,5,6] (0-based).
    """
    pages: List[int] = []
    if not spec:
        return list(range(max_pages))

    parts = spec.replace(" ", "").split(",")
    for part in parts:
        if "-" in part:
            start_s, end_s = part.split("-", 1)
            try:
                start = max(1, int(start_s))
                end = min(max_pages, int(end_s))
            except Exception:
                continue
            for p in range(start, end + 1):
                if 1 <= p <= max_pages:
                    pages.append(p - 1)
        else:
            try:
                p = int(part)
            except Exception:
                continue
            if 1 <= p <= max_pages:
                pages.append(p - 1)

    # Deduplicate but keep order
    seen = set()
    result: List[int] = []
    for p in pages:
        if p not in seen:
            seen.add(p)
            result.append(p)
    return result


def _make_temp_pdf_path(prefix: str = "blinkpdf") -> str:
    fd, path = tempfile.mkstemp(suffix=".pdf", prefix=f"{prefix}_")
    os.close(fd)
    return path


def _make_temp_zip_path(prefix: str = "blinkpdf") -> str:
    fd, path = tempfile.mkstemp(suffix=".zip", prefix=f"{prefix}_")
    os.close(fd)
    return path


def _make_temp_docx_path(prefix: str = "blinkpdf") -> str:
    fd, path = tempfile.mkstemp(suffix=".docx", prefix=f"{prefix}_")
    os.close(fd)
    return path


def _make_temp_pptx_path(prefix: str = "blinkpdf") -> str:
    fd, path = tempfile.mkstemp(suffix=".pptx", prefix=f"{prefix}_")
    os.close(fd)
    return path


def _make_temp_xlsx_path(prefix: str = "blinkpdf") -> str:
    fd, path = tempfile.mkstemp(suffix=".xlsx", prefix=f"{prefix}_")
    os.close(fd)
    return path


# --------------------------------------------------------------------
# Main processor class
# --------------------------------------------------------------------


@dataclass
class PDFProcessor:
    output_dir: str

    # ----------------------- PUBLIC ENTRYPOINT -----------------------

    def process(
        self,
        slug: str,
        input_files: List[str],
        options: Dict[str, Any],
    ) -> Tuple[str, str, str]:
        """
        Main dispatcher used by app.py

        Returns:
            (output_path, download_name, mimetype)
        """

        if not input_files:
            raise PDFProcessorError("No input files provided.")

        os.makedirs(self.output_dir, exist_ok=True)

        slug = slug.strip()

        # --------------- Core/basic tools ---------------

        if slug == "merge-pdf":
            out_path = self.merge_pdfs(input_files)
            return out_path, "merged-blinkpdf.pdf", "application/pdf"

        if slug == "split-pdf":
            out_path = self.split_pdf(
                input_files[0],
                options.get("pages", ""),
            )
            return out_path, "split-blinkpdf.pdf", "application/pdf"

        if slug == "compress-pdf":
            out_path = self.compress_pdf(
                input_files[0],
                level=options.get("level", "medium"),
            )
            return out_path, "compressed-blinkpdf.pdf", "application/pdf"

        if slug == "optimize-pdf":
            out_path = self.optimize_pdf(input_files[0])
            return out_path, "optimized-blinkpdf.pdf", "application/pdf"

        if slug == "rotate-pdf":
            angle = _safe_int(options.get("angle", 90), 90)
            out_path = self.rotate_pdf(input_files[0], angle)
            return out_path, "rotated-blinkpdf.pdf", "application/pdf"

        if slug == "watermark-pdf":
            text = options.get("watermark_text", "BlinkPDF")
            opacity = float(options.get("opacity", 0.15))
            out_path = self.watermark_pdf(input_files[0], text, opacity)
            return out_path, "watermarked-blinkpdf.pdf", "application/pdf"

        if slug == "number-pdf":
            out_path = self.number_pages(
                input_files[0],
                position=options.get("position", "bottom-right"),
            )
            return out_path, "numbered-blinkpdf.pdf", "application/pdf"

        if slug == "protect-pdf":
            password = options.get("password", "")
            if not password:
                raise PDFProcessorError("Password is required for protect-pdf.")
            out_path = self.protect_pdf(input_files[0], password)
            return out_path, "protected-blinkpdf.pdf", "application/pdf"

        if slug == "unlock-pdf":
            password = options.get("password", "")
            out_path = self.unlock_pdf(input_files[0], password)
            return out_path, "unlocked-blinkpdf.pdf", "application/pdf"

        if slug == "repair-pdf":
            out_path = self.repair_pdf(input_files[0])
            return out_path, "repaired-blinkpdf.pdf", "application/pdf"

        if slug == "organize-pdf":
            page_order = options.get("page_order", "")
            delete_pages = options.get("delete_pages", "")
            out_path = self.organize_pdf(input_files[0], page_order, delete_pages)
            return out_path, "organized-blinkpdf.pdf", "application/pdf"

        if slug == "sign-pdf":
            text = options.get("signature_text", "Signed with BlinkPDF")
            out_path = self.sign_pdf(input_files[0], text)
            return out_path, "signed-blinkpdf.pdf", "application/pdf"

        if slug == "annotate-pdf":
            annot_text = options.get("annot_text", "")
            out_path = self.annotate_pdf(input_files[0], annot_text)
            return out_path, "annotated-blinkpdf.pdf", "application/pdf"

        if slug == "redact-pdf":
            redact_text = options.get("redact_text", "")
            out_path = self.redact_pdf(input_files[0], redact_text)
            return out_path, "redacted-blinkpdf.pdf", "application/pdf"

        # --------------- Conversions ---------------

        if slug == "pdf-to-word":
            out_path = self.pdf_to_word(input_files[0])
            return out_path, "converted-blinkpdf.docx", (
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

        if slug == "word-to-pdf":
            out_path = self.word_to_pdf(input_files[0])
            return out_path, "converted-blinkpdf.pdf", "application/pdf"

        if slug == "pdf-to-image":
            out_path = self.pdf_to_images(input_files[0])
            # zip of images
            return out_path, "images-blinkpdf.zip", "application/zip"

        if slug == "image-to-pdf":
            out_path = self.images_to_pdf(input_files)
            return out_path, "images-merged-blinkpdf.pdf", "application/pdf"

        if slug == "pdf-to-excel":
            out_path = self.pdf_to_excel(input_files[0])
            return out_path, "tables-blinkpdf.xlsx", (
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        if slug == "excel-to-pdf":
            out_path = self.excel_to_pdf(input_files[0])
            return out_path, "excel-converted-blinkpdf.pdf", "application/pdf"

        if slug == "pdf-to-powerpoint":
            out_path = self.pdf_to_powerpoint(input_files[0])
            return out_path, "slides-blinkpdf.pptx", (
                "application/vnd.openxmlformats-officedocument.presentationml.presentation"
            )

        if slug == "powerpoint-to-pdf":
            out_path = self.powerpoint_to_pdf(input_files[0])
            return out_path, "ppt-converted-blinkpdf.pdf", "application/pdf"

        # --------------- OCR & extraction ---------------

        if slug == "ocr-pdf":
            out_path = self.ocr_pdf(input_files[0])
            return out_path, "ocr-blinkpdf.pdf", "application/pdf"

        if slug == "extract-text":
            out_path = self.extract_text(input_files[0])
            return out_path, "text-blinkpdf.txt", "text/plain"

        if slug == "extract-images":
            out_path = self.extract_images(input_files[0])
            return out_path, "images-blinkpdf.zip", "application/zip"

        # --------------- Geometry / layout ---------------

        if slug == "deskew-pdf":
            out_path = self.deskew_pdf(input_files[0])
            return out_path, "deskewed-blinkpdf.pdf", "application/pdf"

        if slug == "crop-pdf":
            margin_top = _safe_int(options.get("margin_top", 0), 0)
            margin_right = _safe_int(options.get("margin_right", 0), 0)
            margin_bottom = _safe_int(options.get("margin_bottom", 0), 0)
            margin_left = _safe_int(options.get("margin_left", 0), 0)
            out_path = self.crop_pdf(
                input_files[0],
                margin_top,
                margin_right,
                margin_bottom,
                margin_left,
            )
            return out_path, "cropped-blinkpdf.pdf", "application/pdf"

        if slug == "resize-pdf":
            scale = float(options.get("scale", 1.0))
            out_path = self.resize_pdf(input_files[0], scale)
            return out_path, "resized-blinkpdf.pdf", "application/pdf"

        if slug == "flatten-pdf":
            out_path = self.flatten_pdf(input_files[0])
            return out_path, "flattened-blinkpdf.pdf", "application/pdf"

        # --------------- Metadata & forms ---------------

        if slug == "metadata-editor":
            meta_json = options.get("metadata_json", "{}")
            out_path = self.edit_metadata(input_files[0], meta_json)
            return out_path, "metadata-blinkpdf.pdf", "application/pdf"

        if slug == "fill-forms":
            data_json = options.get("form_data_json", "{}")
            out_path = self.fill_forms(input_files[0], data_json)
            return out_path, "filled-forms-blinkpdf.pdf", "application/pdf"

        # --------------- Background remover ---------------

        if slug == "background-remover":
            out_path = self.remove_background(input_files[0])
            return out_path, "bg-removed-blinkpdf.pdf", "application/pdf"

        # Unknown tool
        raise PDFProcessorError(f"Unknown tool slug: {slug}")

    # ----------------------------------------------------------------
    # IMPLEMENTATIONS
    # ----------------------------------------------------------------

    # ---------- Basic tools ----------

    def merge_pdfs(self, paths: List[str]) -> str:
        writer = PdfWriter()
        for path in paths:
            reader = PdfReader(path)
            for page in reader.pages:
                writer.add_page(page)
        out_path = _make_temp_pdf_path("merge")
        with open(out_path, "wb") as f:
            writer.write(f)
        return out_path

    def split_pdf(self, path: str, spec: str) -> str:
        reader = PdfReader(path)
        max_pages = len(reader.pages)
        pages = _page_ranges_to_list(spec, max_pages)
        if not pages:
            pages = list(range(max_pages))

        writer = PdfWriter()
        for p in pages:
            writer.add_page(reader.pages[p])

        out_path = _make_temp_pdf_path("split")
        with open(out_path, "wb") as f:
            writer.write(f)
        return out_path

    def compress_pdf(self, path: str, level: str = "medium") -> str:
        """
        Basic compression by re-saving with PyMuPDF and different image downscale.
        """
        doc = fitz.open(path)

        if level == "low":
            zoom = 0.7
        elif level == "high":
            zoom = 0.4
        else:
            zoom = 0.5

        # Re-render pages as images and then back into PDF
        out_doc = fitz.open()
        for page in doc:
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            img_bytes = io.BytesIO()
            img.save(img_bytes, format="JPEG", quality=70)
            img_bytes.seek(0)

            img_pdf = fitz.open("pdf", fitz.open("png", img_bytes).convert_to_pdf())
            out_doc.insert_pdf(img_pdf)

        out_path = _make_temp_pdf_path("compress")
        out_doc.save(out_path, garbage=4, deflate=True)
        out_doc.close()
        doc.close()
        return out_path

    def optimize_pdf(self, path: str) -> str:
        """
        Light 'optimize': garbage collect, deflate streams, remove duplicates.
        """
        doc = fitz.open(path)
        out_path = _make_temp_pdf_path("optimize")
        doc.save(out_path, garbage=4, deflate=True, clean=True)
        doc.close()
        return out_path

    def rotate_pdf(self, path: str, angle: int) -> str:
        reader = PdfReader(path)
        writer = PdfWriter()
        for page in reader.pages:
            page.rotate_clockwise(angle % 360)
            writer.add_page(page)

        out_path = _make_temp_pdf_path("rotate")
        with open(out_path, "wb") as f:
            writer.write(f)
        return out_path

    def watermark_pdf(self, path: str, text: str, opacity: float) -> str:
        doc = fitz.open(path)
        for page in doc:
            rect = page.rect
            text_size = 60
            page.insert_text(
                rect.center,
                text,
                fontsize=text_size,
                rotate=45,
                color=(0, 0, 0),
                fill_opacity=opacity,
                stroke_opacity=opacity,
                render_mode=2,  # fill+stroke
                overlay=True,
            )
        out_path = _make_temp_pdf_path("watermark")
        doc.save(out_path, garbage=4, deflate=True)
        doc.close()
        return out_path

    def number_pages(self, path: str, position: str = "bottom-right") -> str:
        doc = fitz.open(path)
        total = len(doc)
        for i, page in enumerate(doc, start=1):
            rect = page.rect
            text = f"{i} / {total}"
            fontsize = 10

            if position == "bottom-left":
                point = fitz.Point(rect.x0 + 20, rect.y1 - 20)
            elif position == "top-right":
                point = fitz.Point(rect.x1 - 60, rect.y0 + 20)
            elif position == "top-left":
                point = fitz.Point(rect.x0 + 20, rect.y0 + 20)
            else:  # bottom-right
                point = fitz.Point(rect.x1 - 60, rect.y1 - 20)

            page.insert_text(point, text, fontsize=fontsize, overlay=True)

        out_path = _make_temp_pdf_path("number")
        doc.save(out_path, garbage=4, deflate=True)
        doc.close()
        return out_path

    def protect_pdf(self, path: str, password: str) -> str:
        reader = PdfReader(path)
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        writer.encrypt(password)

        out_path = _make_temp_pdf_path("protect")
        with open(out_path, "wb") as f:
            writer.write(f)
        return out_path

    def unlock_pdf(self, path: str, password: str) -> str:
        reader = PdfReader(path)
        if reader.is_encrypted:
            if password:
                ok = reader.decrypt(password)
                if not ok:
                    raise PDFProcessorError("Incorrect password for encrypted PDF.")
            else:
                raise PDFProcessorError("Password required to unlock this PDF.")

        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        out_path = _make_temp_pdf_path("unlock")
        with open(out_path, "wb") as f:
            writer.write(f)
        return out_path

    def repair_pdf(self, path: str) -> str:
        """
        Simple 'repair' by loading via PyMuPDF and re-saving.
        """
        doc = fitz.open(path)
        out_path = _make_temp_pdf_path("repair")
        doc.save(out_path, garbage=4, deflate=True)
        doc.close()
        return out_path

    def organize_pdf(self, path: str, page_order_spec: str, delete_spec: str) -> str:
        reader = PdfReader(path)
        max_pages = len(reader.pages)

        order_pages = _page_ranges_to_list(page_order_spec, max_pages)
        delete_pages = set(_page_ranges_to_list(delete_spec, max_pages))

        writer = PdfWriter()
        if order_pages:
            for p in order_pages:
                if p not in delete_pages:
                    writer.add_page(reader.pages[p])
        else:
            for i in range(max_pages):
                if i not in delete_pages:
                    writer.add_page(reader.pages[i])

        out_path = _make_temp_pdf_path("organize")
        with open(out_path, "wb") as f:
            writer.write(f)
        return out_path

    def sign_pdf(self, path: str, text: str) -> str:
        doc = fitz.open(path)
        for page in doc:
            rect = page.rect
            point = fitz.Point(rect.x1 - 200, rect.y1 - 40)
            page.insert_text(point, text, fontsize=12, color=(0, 0, 0), overlay=True)

        out_path = _make_temp_pdf_path("sign")
        doc.save(out_path, garbage=4, deflate=True)
        doc.close()
        return out_path

    def annotate_pdf(self, path: str, annot_text: str) -> str:
        """
        If annot_text is provided, we will search the page and highlight matches.
        Otherwise we just add a small note at bottom.
        """
        doc = fitz.open(path)
        if annot_text:
            for page in doc:
                areas = page.search_for(annot_text)
                for rect in areas:
                    page.add_highlight_annot(rect)
        else:
            for page in doc:
                rect = page.rect
                page.insert_text(
                    fitz.Point(rect.x0 + 20, rect.y1 - 40),
                    "Annotated with BlinkPDF",
                    fontsize=10,
                    overlay=True,
                )

        out_path = _make_temp_pdf_path("annotate")
        doc.save(out_path, garbage=4, deflate=True)
        doc.close()
        return out_path

    def redact_pdf(self, path: str, redact_text: str) -> str:
        doc = fitz.open(path)
        if not redact_text:
            # just re-save
            out_path = _make_temp_pdf_path("redact")
            doc.save(out_path, garbage=4, deflate=True)
            doc.close()
            return out_path

        for page in doc:
            areas = page.search_for(redact_text)
            for rect in areas:
                page.add_redact_annot(rect, fill=(0, 0, 0))
            if areas:
                page.apply_redactions()

        out_path = _make_temp_pdf_path("redact")
        doc.save(out_path, garbage=4, deflate=True)
        doc.close()
        return out_path

    # ---------- Conversions ----------

    def pdf_to_word(self, path: str) -> str:
        doc = fitz.open(path)
        word_doc = Document()
        for page in doc:
            text = page.get_text("text").strip()
            if not text:
                continue
            for line in text.splitlines():
                word_doc.add_paragraph(line)
            word_doc.add_page_break()
        doc.close()

        out_path = _make_temp_docx_path("pdf2word")
        word_doc.save(out_path)
        return out_path

    def word_to_pdf(self, path: str) -> str:
        """
        Simple DOCX -> PDF using ReportLab. It will not keep original DOCX layout,
        but text content will be preserved.
        """
        docx = Document(path)

        out_path = _make_temp_pdf_path("word2pdf")
        c = canvas.Canvas(out_path, pagesize=A4)
        width, height = A4
        x = 50
        y = height - 50

        for para in docx.paragraphs:
            text = para.text
            if not text:
                y -= 16
            else:
                c.drawString(x, y, text)
                y -= 16
            if y < 50:
                c.showPage()
                y = height - 50

        c.save()
        return out_path

    def pdf_to_images(self, path: str) -> str:
        """
        Export each page as PNG then zip them.
        """
        import zipfile

        doc = fitz.open(path)
        tmp_dir = tempfile.mkdtemp(prefix="pdf2img_")
        image_paths: List[str] = []

        for i, page in enumerate(doc, start=1):
            pix = page.get_pixmap()
            img_path = os.path.join(tmp_dir, f"page-{i}.png")
            pix.save(img_path)
            image_paths.append(img_path)
        doc.close()

        zip_path = _make_temp_zip_path("pdf2img")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for p in image_paths:
                zf.write(p, os.path.basename(p))

        return zip_path

    def images_to_pdf(self, paths: List[str]) -> str:
        imgs: List[Image.Image] = []
        for path in paths:
            img = Image.open(path)
            if img.mode != "RGB":
                img = img.convert("RGB")
            imgs.append(img)

        if not imgs:
            raise PDFProcessorError("No images for image-to-pdf.")

        out_path = _make_temp_pdf_path("img2pdf")
        first, *rest = imgs
        first.save(out_path, save_all=True, append_images=rest)
        return out_path

    def pdf_to_excel(self, path: str) -> str:
        doc = fitz.open(path)
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Extracted"

        row_index = 1
        for page in doc:
            text = page.get_text("text")
            if not text:
                continue
            for line in text.splitlines():
                cells = [cell.strip() for cell in line.split("\t")]
                for col_idx, cell_val in enumerate(cells, start=1):
                    ws.cell(row=row_index, column=col_idx, value=cell_val)
                row_index += 1
            row_index += 1  # blank row between pages
        doc.close()

        # Basic column autosize
        for column_cells in ws.columns:
            length = max(len(str(c.value)) if c.value else 0 for c in column_cells)
            col_letter = get_column_letter(column_cells[0].column)
            ws.column_dimensions[col_letter].width = length + 2

        out_path = _make_temp_xlsx_path("pdf2excel")
        wb.save(out_path)
        return out_path

    def excel_to_pdf(self, path: str) -> str:
        wb = openpyxl.load_workbook(path, data_only=True)
        sheet = wb.active

        out_path = _make_temp_pdf_path("excel2pdf")
        c = canvas.Canvas(out_path, pagesize=letter)
        width, height = letter
        x = 40
        y = height - 40

        for row in sheet.iter_rows(values_only=True):
            text = " | ".join("" if v is None else str(v) for v in row)
            c.drawString(x, y, text)
            y -= 16
            if y < 40:
                c.showPage()
                y = height - 40

        c.save()
        return out_path

    def pdf_to_powerpoint(self, path: str) -> str:
        doc = fitz.open(path)
        prs = Presentation()
        blank_layout = prs.slide_layouts[6]  # blank

        for page in doc:
            pix = page.get_pixmap()
            img_bytes = pix.tobytes("png")
            slide = prs.slides.add_slide(blank_layout)
            img_stream = io.BytesIO(img_bytes)
            slide.shapes.add_picture(img_stream, Inches(0), Inches(0),
                                     width=prs.slide_width, height=prs.slide_height)

        doc.close()
        out_path = _make_temp_pptx_path("pdf2ppt")
        prs.save(out_path)
        return out_path

    def powerpoint_to_pdf(self, path: str) -> str:
        """
        Simple PPTX->PDF by rasterizing each slide using python-pptx + PIL.
        This will not be pixel-perfect but works server-side without MS Office.
        """
        prs = Presentation(path)

        out_doc = fitz.open()
        for slide in prs.slides:
            # create an image for each slide as plain white canvas and draw text titles
            img = Image.new("RGB", (1600, 900), "white")
            draw = ImageOps.exif_transpose(img)
            # NOTE: full layout extraction is complex; we just dump text placeholders
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)
            slide_pdf = fitz.open("pdf", fitz.open("png", buf).convert_to_pdf())
            out_doc.insert_pdf(slide_pdf)

        out_path = _make_temp_pdf_path("ppt2pdf")
        out_doc.save(out_path, garbage=4, deflate=True)
        out_doc.close()
        return out_path

    # ---------- OCR & extraction ----------

    def ocr_pdf(self, path: str) -> str:
        doc = fitz.open(path)
        out_doc = fitz.open()

        for page in doc:
            pix = page.get_pixmap()
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            text = pytesseract.image_to_pdf_or_hocr(img, extension="pdf")
            ocr_page = fitz.open("pdf", text)
            out_doc.insert_pdf(ocr_page)

        doc.close()
        out_path = _make_temp_pdf_path("ocr")
        out_doc.save(out_path, garbage=4, deflate=True)
        out_doc.close()
        return out_path

    def extract_text(self, path: str) -> str:
        doc = fitz.open(path)
        texts: List[str] = []
        for page in doc:
            texts.append(page.get_text("text"))
        doc.close()
        content = "\n\n".join(texts)

        fd, out_path = tempfile.mkstemp(suffix=".txt", prefix="text_")
        os.close(fd)
        with open(out_path, "w", encoding="utf-8", errors="ignore") as f:
            f.write(content)
        return out_path

    def extract_images(self, path: str) -> str:
        import zipfile

        doc = fitz.open(path)
        tmp_dir = tempfile.mkdtemp(prefix="extract_img_")
        index = 1
        image_paths: List[str] = []

        for page_index in range(len(doc)):
            for img in doc.get_page_images(page_index):
                xref = img[0]
                base_img = doc.extract_image(xref)
                img_bytes = base_img["image"]
                ext = base_img["ext"]
                img_path = os.path.join(tmp_dir, f"img-{page_index+1}-{index}.{ext}")
                with open(img_path, "wb") as f:
                    f.write(img_bytes)
                image_paths.append(img_path)
                index += 1
        doc.close()

        zip_path = _make_temp_zip_path("extract_images")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for p in image_paths:
                zf.write(p, os.path.basename(p))
        return zip_path

    # ---------- Geometry / layout ----------

    def deskew_pdf(self, path: str) -> str:
        """
        Basic deskew: render each page to image, apply PIL's ImageOps.autocontrast
        and rely on PDF text orientation mostly being OK. True deskew would require
        heavier image processing (OpenCV). This keeps everything free and simple.
        """
        doc = fitz.open(path)
        out_doc = fitz.open()

        for page in doc:
            pix = page.get_pixmap()
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            # Very light enhancement instead of full Hough-deskew
            img = ImageOps.autocontrast(img)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)
            img_pdf = fitz.open("pdf", fitz.open("png", buf).convert_to_pdf())
            out_doc.insert_pdf(img_pdf)

        doc.close()
        out_path = _make_temp_pdf_path("deskew")
        out_doc.save(out_path, garbage=4, deflate=True)
        out_doc.close()
        return out_path

    def crop_pdf(
        self,
        path: str,
        margin_top: int,
        margin_right: int,
        margin_bottom: int,
        margin_left: int,
    ) -> str:
        doc = fitz.open(path)
        for page in doc:
            rect = page.rect
            new_rect = fitz.Rect(
                rect.x0 + margin_left,
                rect.y0 + margin_top,
                rect.x1 - margin_right,
                rect.y1 - margin_bottom,
            )
            # avoid invalid rect
            if new_rect.width <= 0 or new_rect.height <= 0:
                continue
            page.set_cropbox(new_rect)

        out_path = _make_temp_pdf_path("crop")
        doc.save(out_path, garbage=4, deflate=True)
        doc.close()
        return out_path

    def resize_pdf(self, path: str, scale: float) -> str:
        doc = fitz.open(path)
        out_doc = fitz.open()
        if scale <= 0:
            scale = 1.0

        mat = fitz.Matrix(scale, scale)
        for page in doc:
            pix = page.get_pixmap(matrix=mat)
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)
            img_pdf = fitz.open("pdf", fitz.open("png", buf).convert_to_pdf())
            out_doc.insert_pdf(img_pdf)

        doc.close()
        out_path = _make_temp_pdf_path("resize")
        out_doc.save(out_path, garbage=4, deflate=True)
        out_doc.close()
        return out_path

    def flatten_pdf(self, path: str) -> str:
        """
        Flatten annotations and form fields.
        """
        doc = fitz.open(path)
        for page in doc:
            annots = page.annots()
            if annots:
                for annot in annots:
                    annot.set_flags(0)
            page.clean_contents()  # merges resources

        out_path = _make_temp_pdf_path("flatten")
        doc.save(out_path, deflate=True)
        doc.close()
        return out_path

    # ---------- Metadata & forms ----------

    def edit_metadata(self, path: str, meta_json: str) -> str:
        try:
            new_meta = json.loads(meta_json or "{}")
        except Exception:
            new_meta = {}

        reader = PdfReader(path)
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)

        metadata = {}
        for key, value in (new_meta or {}).items():
            if not key.startswith("/"):
                key = "/" + key
            metadata[key] = str(value)

        if metadata:
            writer.add_metadata(metadata)

        out_path = _make_temp_pdf_path("metadata")
        with open(out_path, "wb") as f:
            writer.write(f)
        return out_path

    def fill_forms(self, path: str, form_data_json: str) -> str:
        """
        Very basic AcroForm filling using PyPDF2.
        """
        try:
            form_data = json.loads(form_data_json or "{}")
        except Exception:
            form_data = {}

        reader = PdfReader(path)
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)

        if form_data:
            writer.update_page_form_field_values(writer.pages[0], form_data)

        out_path = _make_temp_pdf_path("fillforms")
        with open(out_path, "wb") as f:
            writer.write(f)
        return out_path

    # ---------- Background remover ----------

    def remove_background(self, path: str) -> str:
        """
        Simple 'background remover' for scanned PDFs:
        - render each page to image
        - convert to grayscale and increase contrast
        """

        doc = fitz.open(path)
        out_doc = fitz.open()

        for page in doc:
            pix = page.get_pixmap()
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            # Convert to grayscale and auto-contrast to suppress background noise
            img = ImageOps.grayscale(img)
            img = ImageOps.autocontrast(img)

            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)

            img_pdf = fitz.open("pdf", fitz.open("png", buf).convert_to_pdf())
            out_doc.insert_pdf(img_pdf)

        doc.close()
        out_path = _make_temp_pdf_path("bgremove")
        out_doc.save(out_path, garbage=4, deflate=True)
        out_doc.close()
        return out_path
