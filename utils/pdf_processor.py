import os
import json
import tempfile
from typing import List, Tuple

import fitz  # PyMuPDF
from PyPDF2 import PdfReader, PdfWriter


class PDFProcessorError(Exception):
    pass


class PDFProcessor:
    def __init__(self, output_folder=None):
        self.output_folder = output_folder or tempfile.gettempdir()

    # ========================= MAIN ROUTER =========================

    def process(self, slug: str, files: List[str], options: dict):
        if not files:
            raise PDFProcessorError("No files provided")

        first = files[0]

        if slug == "merge-pdf":
            return self.merge_pdfs(files)

        if slug == "split-pdf":
            return self.split_pdf(first, options.get("pages", ""))

        if slug == "compress-pdf":
            return self.compress_pdf(first, options.get("compression_level", "2"))

        if slug == "rotate-pdf":
            angle = int(options.get("angle", 90))
            return self.rotate_pdf(first, angle)

        if slug == "optimize-pdf":
            return self.optimize_pdf(first)

        raise PDFProcessorError(f"Unknown tool slug: {slug}")

    # ========================= HELPERS =========================

    def _tmp_file(self, suffix: str) -> str:
        fd, path = tempfile.mkstemp(suffix=suffix, dir=self.output_folder)
        os.close(fd)
        return path

    def _page_ranges_to_list(self, spec: str, total_pages: int) -> List[int]:
        if not spec:
            return list(range(total_pages))

        pages = set()
        parts = [p.strip() for p in spec.split(",") if p.strip()]

        for part in parts:
            if "-" in part:
                start_str, end_str = part.split("-", 1)
                start = int(start_str) if start_str else 1
                end = int(end_str) if end_str else total_pages

                for p in range(start, end + 1):
                    if 1 <= p <= total_pages:
                        pages.add(p - 1)
            else:
                p = int(part)
                if 1 <= p <= total_pages:
                    pages.add(p - 1)

        return sorted(pages)

    # ========================= MERGE =========================

    def merge_pdfs(self, paths: List[str]) -> Tuple[str, str, str]:
        writer = PdfWriter()

        for path in paths:
            reader = PdfReader(path)
            for page in reader.pages:
                writer.add_page(page)

        out_path = self._tmp_file(".pdf")
        with open(out_path, "wb") as f:
            writer.write(f)

        return out_path, "merged.pdf", "application/pdf"

    # ========================= SPLIT =========================

    def split_pdf(self, path: str, pages_spec: str) -> Tuple[str, str, str]:
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

    # ========================= COMPRESS =========================

    def compress_pdf(self, path: str, level: str):
        level = str(level).strip()

        if level == "1":       # High quality
            scale = 1.0
        elif level == "3":     # Strong compression
            scale = 0.6
        else:                   # Balanced (2)
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

    # ========================= OPTIMIZE =========================

    def optimize_pdf(self, path: str) -> Tuple[str, str, str]:
        doc = fitz.open(path)

        out_path = self._tmp_file(".pdf")
        doc.save(
            out_path,
            garbage=4,
            deflate=True,
            clean=True,
            linear=True,
        )

        doc.close()
        return out_path, "optimized.pdf", "application/pdf"

    # ========================= ROTATE =========================

    def rotate_pdf(self, path: str, angle: int) -> Tuple[str, str, str]:
        reader = PdfReader(path)
        writer = PdfWriter()

        for page in reader.pages:
            page.rotate(angle)
            writer.add_page(page)

        out_path = self._tmp_file(".pdf")
        with open(out_path, "wb") as f:
            writer.write(f)

        return out_path, "rotated.pdf", "application/pdf"
