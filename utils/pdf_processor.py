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
    """Custom error for PDF processing problems."""
    pass


class PDFProcessor:
    """
    Central processor for all BlinkPDF tools.
    """
    def process(self, slug: str, input_files: List[str], options: Dict[str, str]) -> Tuple[str, str, str]:
        slug = (slug or "").strip().lower()
        if not input_files:
            raise PDFProcessorError("No input files provided")

        first = input_files[0]

        if slug == "merge-pdf":
            return self.merge_pdfs(input_files)

        if slug == "split-pdf":
            pages = options.get("pages") or options.get("page_range") or ""
            return self.split_pdf(first, pages)

        if slug == "compress-pdf":
            level = options.get("compression_level", "2")
            return self.compress_pdf(first, level)

        if slug == "rotate-pdf":
            angle = int(options.get("rotation_angle", "0")) % 360
            if angle not in (0, 90, 180, 270):
                angle = min([0, 90, 180, 270], key=lambda a: abs(a - angle))
            return self.rotate_pdf(first, angle)

        if slug == "watermark-pdf":
            text = options.get("watermark_text", "CONFIDENTIAL")
            opacity = float(options.get("watermark_opacity", "0.15"))
            position = options.get("watermark_position", "center")
            return self.watermark_pdf(first, text, opacity, position)

        if slug == "extract-text":
            return self.extract_text(first)

        raise PDFProcessorError(f"Unknown tool slug: {slug}")

    # --------------------------------------------------------

    def _tmp_file(self, suffix: str) -> str:
        fd, path = tempfile.mkstemp(suffix=suffix)
        os.close(fd)
        return path

    def merge_pdfs(self, paths: List[str]):
        writer = PdfWriter()
        for path in paths:
            reader = PdfReader(path)
            for page in reader.pages:
                writer.add_page(page)

        out_path = self._tmp_file(".pdf")
        with open(out_path, "wb") as f:
            writer.write(f)

        return out_path, "merged.pdf", "application/pdf"


    def split_pdf(self, path: str, pages_spec: str):
        reader = PdfReader(path)
        total = len(reader.pages)

        indices = self._page_ranges_to_list(pages_spec, total)
        if not indices:
            indices = list(range(total))

        writer = PdfWriter()
        for i in indices:
            writer.add_page(reader.pages[i])

        out_path = self._tmp_file(".pdf")
        with open(out_path, "wb") as f:
            writer.write(f)

        return out_path, "split.pdf", "application/pdf"


    def _page_ranges_to_list(self, spec: str, total_pages: int) -> List[int]:
        if not spec:
            return list(range(total_pages))
        pages = set()
        for part in spec.split(","):
            if "-" in part:
                start, end = part.split("-")
                start = int(start) if start else 1
                end = int(end) if end else total_pages
                for p in range(start, end + 1):
                    if 1 <= p <= total_pages:
                        pages.add(p - 1)
            else:
                p = int(part)
                if 1 <= p <= total_pages:
                    pages.add(p - 1)
        return sorted(pages)


    # ✅ FULL FIXED COMPRESSION ENGINE
    def compress_pdf(self, path: str, level: str):
        level = str(level).strip()

        if level == "1":
            scale = 1.0
        elif level == "3":
            scale = 0.6
        else:
            scale = 0.8

        doc = fitz.open(path)
        new_doc = fitz.open()

        for page in doc:
            mat = fitz.Matrix(scale, scale)
            pix = page.get_pixmap(matrix=mat)

            new_page = new_doc.new_page(width=pix.width, height=pix.height)
            new_page.insert_image(
                fitz.Rect(0, 0, pix.width, pix.height),
                pixmap=pix
            )

        out_path = self._tmp_file(".pdf")

        new_doc.save(
            out_path,
            deflate=True,
            garbage=4,
            clean=True
        )

        doc.close()
        new_doc.close()

        return out_path, "compressed.pdf", "application/pdf"


    # ✅ ROTATE FIX
    def rotate_pdf(self, path: str, angle: int):
        reader = PdfReader(path)
        writer = PdfWriter()

        for page in reader.pages:
            page.rotate(angle)
            writer.add_page(page)

        out_path = self._tmp_file(".pdf")
        with open(out_path, "wb") as f:
            writer.write(f)

        return out_path, "rotated.pdf", "application/pdf"



    def watermark_pdf(self, path: str, text: str, opacity: float, position: str):
        doc = fitz.open(path)

        for page in doc:
            rect = page.rect
            point = rect.center

            page.insert_text(
                point,
                text,
                fontsize=36,
                rotate=45,
                color=(0.7, 0.7, 0.7),
                fill_opacity=opacity,
            )

        out_path = self._tmp_file(".pdf")
        doc.save(out_path)
        doc.close()

        return out_path, "watermarked.pdf", "application/pdf"


    def extract_text(self, path: str):
        doc = fitz.open(path)
        data = []

        for i, page in enumerate(doc, 1):
            data.append(f"=== Page {i} ===\n")
            data.append(page.get_text() + "\n\n")

        doc.close()

        out = self._tmp_file(".txt")
        with open(out, "w", encoding="utf-8") as f:
            f.write("".join(data))

        return out, "extracted.txt", "text/plain"
