import os
import io
import json
import tempfile
import zipfile
from typing import List, Dict, Tuple

import fitz  # PyMuPDF
from PyPDF2 import PdfReader, PdfWriter
from PIL import Image
import pytesseract
from docx import Document
from pptx import Presentation
import openpyxl
from reportlab.lib.pagesizes import A4, letter
from reportlab.pdfgen import canvas


class PDFProcessorError(Exception):
    pass


class PDFProcessor:

    # ==========================================================
    # MAIN CONTROLLER
    # ==========================================================

    def process(self, slug: str, input_files: List[str], options: Dict[str, str]) -> Tuple[str, str, str]:
        slug = slug.strip().lower()

        if not input_files:
            raise PDFProcessorError("No input files provided")

        first = input_files[0]

        # --- Core ---
        if slug == "merge-pdf":
            return self.merge_pdfs(input_files)

        if slug == "split-pdf":
            return self.split_pdf(first, options.get("pages", ""))

        if slug == "compress-pdf":
            return self.compress_pdf(first, options.get("compression_level", "2"))

        if slug == "optimize-pdf":
            return self.optimize_pdf(first)

        if slug == "rotate-pdf":
            return self.rotate_pdf(first, int(options.get("rotation_angle", "0")))

        if slug == "watermark-pdf":
            return self.watermark_pdf(first, options.get("watermark_text", ""))

        if slug == "number-pdf":
            return self.number_pdf(first)

        if slug == "protect-pdf":
            return self.protect_pdf(first, options.get("password"))

        if slug == "unlock-pdf":
            return self.unlock_pdf(first, options.get("password"))

        if slug == "repair-pdf":
            return self.repair_pdf(first)

        if slug == "organize-pdf":
            return self.organize_pdf(
                first,
                options.get("page_order", ""),
                options.get("deleted_pages", "")
            )

        if slug == "redact-pdf":
            return self.redact_pdf(first, options.get("redact_text"))

        # --- Conversion ---
        if slug == "pdf-to-word":
            return self.pdf_to_word(first)

        if slug == "word-to-pdf":
            return self.word_to_pdf(first)

        if slug == "pdf-to-image":
            return self.pdf_to_images(first)

        if slug == "image-to-pdf":
            return self.images_to_pdf(input_files)

        if slug == "pdf-to-excel":
            return self.pdf_to_excel(first)

        if slug == "excel-to-pdf":
            return self.excel_to_pdf(first)

        if slug == "pdf-to-powerpoint":
            return self.pdf_to_powerpoint(first)

        if slug == "powerpoint-to-pdf":
            return self.powerpoint_to_pdf(first)

        # --- OCR / Text ---
        if slug == "ocr-pdf":
            return self.ocr_pdf(first)

        if slug == "extract-text":
            return self.extract_text(first)

        if slug == "extract-images":
            return self.extract_images(first)

        if slug == "crop-pdf":
            return self.crop_pdf(first, options)

        if slug == "deskew-pdf":
            return self.deskew_pdf(first)

        if slug == "resize-pdf":
            return self.resize_pdf(first, options.get("page_size", "A4"))

        if slug == "flatten-pdf":
            return self.flatten_pdf(first)

        if slug == "background-remover":
            return self.remove_background(first)

        raise PDFProcessorError(f"Unknown tool: {slug}")


    # ==========================================================
    # BASIC HELPERS
    # ==========================================================

    def _tmp(self, ext):
        fd, path = tempfile.mkstemp(suffix=ext)
        os.close(fd)
        return path

    def parse_pages(self, spec, total):
        if not spec:
            return list(range(total))

        pages = set()
        for part in spec.split(","):
            if "-" in part:
                a, b = part.split("-")
                start = int(a)
                end = int(b)
                for p in range(start, end + 1):
                    pages.add(p - 1)
            else:
                pages.add(int(part) - 1)

        return [p for p in pages if 0 <= p < total]


    # ==========================================================
    # CORE PDF TOOLS
    # ==========================================================

    def merge_pdfs(self, paths):
        writer = PdfWriter()
        for p in paths:
            r = PdfReader(p)
            for page in r.pages:
                writer.add_page(page)

        out = self._tmp(".pdf")
        with open(out, "wb") as f:
            writer.write(f)
        return out, "merged.pdf", "application/pdf"

    def split_pdf(self, path, pages):
        reader = PdfReader(path)
        total = len(reader.pages)
        indexes = self.parse_pages(pages, total)

        writer = PdfWriter()
        for i in indexes:
            writer.add_page(reader.pages[i])

        out = self._tmp(".pdf")
        with open(out, "wb") as f:
            writer.write(f)
        return out, "split.pdf", "application/pdf"

    def compress_pdf(self, path, level):
        doc = fitz.open(path)

        level = str(level)
        if level == "1":
            dpi = 300
        elif level == "2":
            dpi = 150
        else:
            dpi = 72

        out = self._tmp(".pdf")
        doc.save(out, deflate=True, garbage=4, clean=True)
        doc.close()

        return out, "compressed.pdf", "application/pdf"

    def optimize_pdf(self, path):
        doc = fitz.open(path)
        out = self._tmp(".pdf")
        doc.save(out, garbage=4, deflate=True, linear=True)
        doc.close()
        return out, "optimized.pdf", "application/pdf"

    def rotate_pdf(self, path, angle):
        reader = PdfReader(path)
        writer = PdfWriter()

        for p in reader.pages:
            p.rotate(angle)
            writer.add_page(p)

        out = self._tmp(".pdf")
        with open(out, "wb") as f:
            writer.write(f)

        return out, "rotated.pdf", "application/pdf"


    # ==========================================================
    # ORGANIZE, DELETE, REORDER
    # ==========================================================

    def organize_pdf(self, path, order, deleted):
        reader = PdfReader(path)
        total = len(reader.pages)

        page_order = self.parse_pages(order, total) if order else list(range(total))
        delete_list = self.parse_pages(deleted, total) if deleted else []

        writer = PdfWriter()

        for i in page_order:
            if i not in delete_list:
                writer.add_page(reader.pages[i])

        out = self._tmp(".pdf")
        with open(out, "wb") as f:
            writer.write(f)

        return out, "organized.pdf", "application/pdf"


    # ==========================================================
    # WATERMARK
    # ==========================================================

    def watermark_pdf(self, path, text):
        doc = fitz.open(path)

        for page in doc:
            page.insert_text(
                page.rect.center,
                text,
                fontsize=36,
                rotate=45,
                color=(0.7, 0.2, 0.4),
                fill_opacity=0.35
            )

        out = self._tmp(".pdf")
        doc.save(out)
        doc.close()

        return out, "watermarked.pdf", "application/pdf"


    # ==========================================================
    # CROP (DRAG CROP SUPPORT)
    # ==========================================================

    def crop_pdf(self, path, options):
        doc = fitz.open(path)

        raw = options.get("crop_regions", "{}")
        regions = json.loads(raw)

        for i, page in enumerate(doc):
            if str(i + 1) not in regions:
                continue

            r = regions[str(i + 1)]
            rect = page.rect

            x = rect.width * (r["x"] / 100)
            y = rect.height * (r["y"] / 100)
            w = rect.width * (r["width"] / 100)
            h = rect.height * (r["height"] / 100)

            new = fitz.Rect(x, y, x + w, y + h)
            if new.width > 50 and new.height > 50:
                page.set_cropbox(new)

        out = self._tmp(".pdf")
        doc.save(out)
        doc.close()

        return out, "cropped.pdf", "application/pdf"


    # ==========================================================
    # OCR + TEXT + IMAGE
    # ==========================================================

    def ocr_pdf(self, path):
        doc = fitz.open(path)
        out = self._tmp(".pdf")

        content = b""
        for page in doc:
            pix = page.get_pixmap()
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            content += pytesseract.image_to_pdf_or_hocr(img, extension="pdf")

        with open(out, "wb") as f:
            f.write(content)

        return out, "ocr.pdf", "application/pdf"

    def extract_text(self, path):
        doc = fitz.open(path)
        out = self._tmp(".txt")

        with open(out, "w", encoding="utf-8") as f:
            for page in doc:
                f.write(page.get_text())

        return out, "extracted.txt", "text/plain"

    def extract_images(self, path):
        doc = fitz.open(path)
        temp = tempfile.mkdtemp()

        imgs = []
        for i in range(len(doc)):
            for img in doc.get_page_images(i):
                xref = img[0]
                img_data = doc.extract_image(xref)
                data = img_data["image"]
                ext = img_data["ext"]

                file = os.path.join(temp, f"{i}_{xref}.{ext}")
                with open(file, "wb") as f:
                    f.write(data)
                imgs.append(file)

        out = self._tmp(".zip")
        with zipfile.ZipFile(out, "w") as z:
            for img in imgs:
                z.write(img, os.path.basename(img))

        return out, "images.zip", "application/zip"


    # ==========================================================
    # BACKGROUND REMOVER
    # ==========================================================

    def remove_background(self, path):
        try:
            from rembg import remove
        except:
            raise PDFProcessorError("Install rembg package")

        with open(path, "rb") as f:
            res = remove(f.read())

        out = self._tmp(".png")
        with open(out, "wb") as f:
            f.write(res)

        return out, "bg_removed.png", "image/png"
