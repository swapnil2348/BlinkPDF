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

    process(slug, input_files, options) -> (output_path, download_name, mimetype)
    """

    def process(
        self,
        slug: str,
        input_files: List[str],
        options: Dict[str, str]
    ) -> Tuple[str, str, str]:
        slug = (slug or "").strip().lower()

        if not input_files:
            raise PDFProcessorError("No input files provided.")

        primary = input_files[0]

        # --- Core tools ---

        if slug == "merge-pdf":
            return self.merge_pdfs(input_files)

        if slug == "split-pdf":
            pages = options.get("pages") or options.get("page_range") or ""
            return self.split_pdf(primary, pages)

        if slug == "compress-pdf":
            level = options.get("compression_level", "2")
            return self.compress_pdf(primary, level)

        if slug == "rotate-pdf":
            # 🔧 IMPORTANT:
            # app.py stores the angle in options["angle"]
            # (coming from form "rotation_angle").
            # We also fallback to "rotation_angle" just in case.
            angle_raw = (
                options.get("angle") or
                options.get("rotation_angle") or
                "0"
            )
            try:
                angle = int(angle_raw)
            except ValueError:
                angle = 0

            angle = angle % 360
            allowed = (0, 90, 180, 270)
            if angle not in allowed:
                angle = min(allowed, key=lambda a: abs(a - angle))

            return self.rotate_pdf(primary, angle)

        if slug == "watermark-pdf":
            text = options.get("watermark_text", "CONFIDENTIAL")
            try:
                opacity = float(options.get("watermark_opacity", "0.15"))
            except ValueError:
                opacity = 0.15
            position = options.get("watermark_position", "center")
            return self.watermark_pdf(primary, text, opacity, position)

        if slug == "extract-text":
            return self.extract_text(primary)

        # --- PRO++ page organize (reorder / include / pages) ---
        if slug == "organize-pdf":
            page_order = options.get("page_order", "")
            deleted_pages = options.get("deleted_pages", "")
            pages = options.get("pages", "")
            return self.organize_pdf(primary, page_order, deleted_pages, pages)

        # --- PRO++ visual crop (from crop_regions JSON) ---
        if slug == "crop-pdf":
            crop_regions = options.get("crop_regions", "{}")
            pages = options.get("pages", "")
            return self.crop_pdf(primary, crop_regions, pages)

        # Other tools can be added here later…
        raise PDFProcessorError(f"Unknown tool slug: {slug}")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _tmp_file(self, suffix: str) -> str:
        fd, path = tempfile.mkstemp(suffix=suffix)
        os.close(fd)
        return path

    def _page_ranges_to_list(self, spec: str, total_pages: int) -> List[int]:
        """
        Convert a range string like "1-3,5,8" to zero-based page indices.
        """
        if not spec:
            return list(range(total_pages))

        pages: set[int] = set()

        for part in spec.split(","):
            part = part.strip()
            if not part:
                continue

            if "-" in part:
                start_str, end_str = part.split("-", 1)
                start = int(start_str) if start_str.strip() else 1
                end = int(end_str) if end_str.strip() else total_pages
                if start > end:
                    start, end = end, start
                for p in range(start, end + 1):
                    if 1 <= p <= total_pages:
                        pages.add(p - 1)
            else:
                try:
                    p = int(part)
                except ValueError:
                    continue
                if 1 <= p <= total_pages:
                    pages.add(p - 1)

        return sorted(pages)

    # ------------------------------------------------------------------
    # Merge / Split
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # ✅ Fixed compression (no image_quality kwarg)
    # ------------------------------------------------------------------

    def compress_pdf(self, path: str, level: str) -> Tuple[str, str, str]:
        """
        Very safe compression: render each page to an image at a lower scale,
        then rebuild a PDF from those images.

        level:
            "1" -> high quality (bigger file)
            "2" -> balanced
            "3" -> smallest file (more aggressive)
        """
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

        # IMPORTANT: no image_quality param – this works with PyMuPDF 1.26.x
        new_doc.save(
            out_path,
            deflate=True,
            garbage=4,
            clean=True
        )

        doc.close()
        new_doc.close()

        return out_path, "compressed.pdf", "application/pdf"

    # ------------------------------------------------------------------
    # ✅ Rotate (now uses angle from app.py)
    # ------------------------------------------------------------------

    def rotate_pdf(self, path: str, angle: int) -> Tuple[str, str, str]:
        reader = PdfReader(path)
        writer = PdfWriter()

        for page in reader.pages:
            # PyPDF2 3.x: PageObject.rotate(clockwise=angle)
            try:
                page.rotate(angle)
            except TypeError:
                # Legacy fallback
                page.rotate_clockwise(angle)
            writer.add_page(page)

        out_path = self._tmp_file(".pdf")
        with open(out_path, "wb") as f:
            writer.write(f)

        return out_path, "rotated.pdf", "application/pdf"

    # ------------------------------------------------------------------
    # ✅ Watermark (text overlay, used by watermark-pdf)
    # ------------------------------------------------------------------

    def watermark_pdf(
        self,
        path: str,
        text: str,
        opacity: float,
        position: str
    ) -> Tuple[str, str, str]:
        doc = fitz.open(path)

        for page in doc:
            rect = page.rect

            if position == "top-left":
                point = fitz.Point(rect.x0 + 40, rect.y0 + 40)
            elif position == "top-right":
                point = fitz.Point(rect.x1 - 40, rect.y0 + 40)
            elif position == "bottom-left":
                point = fitz.Point(rect.x0 + 40, rect.y1 - 40)
            elif position == "bottom-right":
                point = fitz.Point(rect.x1 - 40, rect.y1 - 40)
            else:  # center (default)
                point = rect.center

            page.insert_text(
                point,
                text,
                fontsize=36,
                rotate=45,
                color=(0.7, 0.7, 0.7),
                fill_opacity=max(0.0, min(1.0, opacity)),
                render_mode=0,
            )

        out_path = self._tmp_file(".pdf")
        doc.save(out_path)
        doc.close()

        return out_path, "watermarked.pdf", "application/pdf"

    # ------------------------------------------------------------------
    # ✅ Extract text
    # ------------------------------------------------------------------

    def extract_text(self, path: str) -> Tuple[str, str, str]:
        doc = fitz.open(path)
        chunks: List[str] = []

        for i, page in enumerate(doc, 1):
            chunks.append(f"=== Page {i} ===\n")
            text = page.get_text() or ""
            chunks.append(text + "\n\n")

        doc.close()

        out_path = self._tmp_file(".txt")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("".join(chunks))

        return out_path, "extracted.txt", "text/plain"

    # ------------------------------------------------------------------
    # PRO++ Organize pages (reorder / include / basic range)
    # ------------------------------------------------------------------

    def organize_pdf(
        self,
        path: str,
        page_order_str: str,
        deleted_pages_str: str,
        pages_spec: str
    ) -> Tuple[str, str, str]:
        """
        Uses:
          - page_order: "3,1,2" (from live preview UI, only *included* pages)
          - deleted_pages: "4,7" (currently not required, but accepted)
          - pages: optional standard page-range filter string
        """
        reader = PdfReader(path)
        total = len(reader.pages)
        writer = PdfWriter()

        used_any = False

        if page_order_str.strip():
            # Use visual order from UI (page numbers are 1-based in the UI)
            for part in page_order_str.split(","):
                part = part.strip()
                if not part:
                    continue
                try:
                    p = int(part)
                except ValueError:
                    continue
                idx = p - 1
                if 0 <= idx < total:
                    writer.add_page(reader.pages[idx])
                    used_any = True
        else:
            # Fallback: use pages_spec if present, else all pages
            indices = self._page_ranges_to_list(pages_spec, total)
            if not indices:
                indices = list(range(total))

            for idx in indices:
                writer.add_page(reader.pages[idx])
                used_any = True

        if not used_any:
            raise PDFProcessorError("No pages selected for output.")

        out_path = self._tmp_file(".pdf")
        with open(out_path, "wb") as f:
            writer.write(f)

        return out_path, "organized.pdf", "application/pdf"

    # ------------------------------------------------------------------
    # PRO++ Crop (using crop_regions JSON from live preview)
    # ------------------------------------------------------------------

    def crop_pdf(
        self,
        path: str,
        crop_regions_json: str,
        pages_spec: str
    ) -> Tuple[str, str, str]:
        """
        crop_regions_json comes from the front-end as something like:
        {
          "1": {"x": 0.1, "y": 0.1, "width": 0.8, "height": 0.7},
          "2": {"x": 0.15, "y": 0.2, "width": 0.7, "height": 0.6}
        }

        x,y,width,height are all in [0,1] relative to page width/height.
        """
        try:
            regions = json.loads(crop_regions_json or "{}")
            if not isinstance(regions, dict):
                regions = {}
        except Exception:
            regions = {}

        doc = fitz.open(path)
        total = len(doc)

        # Optional additional filter by pages_spec
        allowed_indices = None
        if pages_spec.strip():
            indices = self._page_ranges_to_list(pages_spec, total)
            allowed_indices = set(indices)

        for page_index in range(total):
            if allowed_indices is not None and page_index not in allowed_indices:
                continue

            page = doc[page_index]
            page_num_str = str(page_index + 1)

            cfg = regions.get(page_num_str) or regions.get(page_index + 1)
            if not cfg:
                # No crop box defined for this page => leave as is
                continue

            try:
                x = float(cfg.get("x", 0.0))
                y = float(cfg.get("y", 0.0))
                w = float(cfg.get("width", 1.0))
                h = float(cfg.get("height", 1.0))
            except Exception:
                continue

            x = max(0.0, min(1.0, x))
            y = max(0.0, min(1.0, y))
            w = max(0.0, min(1.0, w))
            h = max(0.0, min(1.0, h))

            rect = page.rect
            left = rect.x0 + x * rect.width
            top = rect.y0 + y * rect.height
            right = left + w * rect.width
            bottom = top + h * rect.height

            new_rect = fitz.Rect(left, top, right, bottom)

            # This effectively "crops" the page visually.
            try:
                page.set_cropbox(new_rect)
            except AttributeError:
                # Older PyMuPDF versions
                page.set_crop_box(new_rect)

        out_path = self._tmp_file(".pdf")
        doc.save(out_path)
        doc.close()

        return out_path, "cropped.pdf", "application/pdf"
