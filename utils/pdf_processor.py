import os
import io
import json
import tempfile
import zipfile

import fitz  # PyMuPDF
from PyPDF2 import PdfReader, PdfWriter
from PIL import Image, ImageDraw
from docx import Document
from pptx import Presentation
import openpyxl
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


class PDFProcessorError(Exception):
    pass


class PDFProcessor:

    def tmp(self, ext=".pdf"):
        fd, path = tempfile.mkstemp(suffix=ext)
        os.close(fd)
        return path

    # =========================================
    # MAIN ROUTER
    # =========================================

    def process(self, slug, files, options):

        if not files:
            raise PDFProcessorError("No file uploaded")

        main = files[0]

        # CORE
        if slug == "merge-pdf": return self.merge(files)
        if slug == "split-pdf": return self.split(main, options.get("pages", ""))
        if slug == "compress-pdf": return self.compress(main)
        if slug == "rotate-pdf": return self.rotate(main, int(options.get("angle", 0)))
        if slug == "watermark-pdf": return self.watermark(main, options)
        if slug == "crop-pdf": return self.crop(main, options)
        if slug == "organize-pdf": return self.organize(main, options)
        if slug == "flatten-pdf": return self.flatten(main)
        if slug == "unlock-pdf": return self.unlock(main)
        if slug == "protect-pdf": return self.protect(main, options.get("password","1234"))
        if slug == "extract-text": return self.extract_text(main)
        if slug == "extract-images": return self.extract_images(main)
        if slug == "resize-pdf": return self.resize(main, float(options.get("scale", 1)))
        if slug == "number-pdf": return self.page_numbers(main)
        if slug == "deskew-pdf": return self.deskew(main)
        if slug == "redact-pdf": return self.redact(main, options)

        # Convert FROM PDF
        if slug == "pdf-to-word": return self.pdf_to_word(main)
        if slug == "pdf-to-ppt": return self.pdf_to_ppt(main)
        if slug == "pdf-to-excel": return self.pdf_to_excel(main)

        # Convert TO PDF
        if slug == "image-to-pdf": return self.image_to_pdf(files)
        if slug == "word-to-pdf": return self.word_to_pdf(main)
        if slug == "powerpoint-to-pdf": return self.ppt_to_pdf(main)
        if slug == "excel-to-pdf": return self.excel_to_pdf(main)

        raise PDFProcessorError(f"Tool not implemented: {slug}")

    # =========================================
    # CORE PDF TOOLS
    # =========================================

    def merge(self, files):
        writer = PdfWriter()
        for f in files:
            reader = PdfReader(f)
            for p in reader.pages:
                writer.add_page(p)

        out = self.tmp()
        with open(out, "wb") as f:
            writer.write(f)
        return out, "merged.pdf", "application/pdf"

    def split(self, file, pages):
        reader = PdfReader(file)
        writer = PdfWriter()

        if not pages:
            pages = range(len(reader.pages))
        else:
            pages = [int(p)-1 for p in pages.split(",") if p.isdigit()]

        for i in pages:
            writer.add_page(reader.pages[i])

        out = self.tmp()
        with open(out, "wb") as f:
            writer.write(f)

        return out, "split.pdf", "application/pdf"

    def compress(self, file):
        doc = fitz.open(file)
        new = fitz.open()

        for p in doc:
            pix = p.get_pixmap(Matrix=fitz.Matrix(0.7, 0.7))
            n = new.new_page(width=pix.width, height=pix.height)
            n.insert_image(n.rect, pixmap=pix)

        out = self.tmp()
        new.save(out, garbage=4, deflate=True)
        return out, "compressed.pdf", "application/pdf"

    def rotate(self, file, angle):
        reader = PdfReader(file)
        writer = PdfWriter()

        for page in reader.pages:
            page.rotate(angle)
            writer.add_page(page)

        out = self.tmp()
        with open(out, "wb") as f:
            writer.write(f)

        return out, "rotated.pdf", "application/pdf"

    def watermark(self, file, options):
        text = options.get("watermark_text", "BlinkPDF")
        doc = fitz.open(file)
        for page in doc:
            page.insert_text(page.rect.center, text, fontsize=40, rotate=45)

        out = self.tmp()
        doc.save(out)
        return out, "watermarked.pdf", "application/pdf"

    def crop(self, file, options):
        regions = json.loads(options.get("crop_regions", "{}"))
        doc = fitz.open(file)

        for i, page in enumerate(doc):
            if str(i+1) in regions:
                r = regions[str(i+1)]
                rect = page.rect
                crop = fitz.Rect(
                    rect.x0 + r["x"] * rect.width,
                    rect.y0 + r["y"] * rect.height,
                    rect.x0 + (r["x"] + r["width"]) * rect.width,
                    rect.y0 + (r["y"] + r["height"]) * rect.height,
                )
                page.set_cropbox(crop)

        out = self.tmp()
        doc.save(out)
        return out, "cropped.pdf", "application/pdf"

    def organize(self, file, options):
        order = options.get("page_order", "")
        reader = PdfReader(file)
        writer = PdfWriter()

        for i in order.split(","):
            if i.isdigit():
                writer.add_page(reader.pages[int(i)-1])

        out = self.tmp()
        with open(out, "wb") as f:
            writer.write(f)

        return out, "organized.pdf", "application/pdf"

    def flatten(self, file):
        doc = fitz.open(file)
        for page in doc:
            page.wrap_contents()
        out = self.tmp()
        doc.save(out)
        return out, "flattened.pdf", "application/pdf"

    def unlock(self, file):
        reader = PdfReader(file)
        writer = PdfWriter()
        for p in reader.pages:
            writer.add_page(p)

        out = self.tmp()
        with open(out, "wb") as f:
            writer.write(f)
        return out, "unlocked.pdf", "application/pdf"

    def protect(self, file, password):
        reader = PdfReader(file)
        writer = PdfWriter()
        for p in reader.pages:
            writer.add_page(p)
        writer.encrypt(password)

        out = self.tmp()
        with open(out, "wb") as f:
            writer.write(f)
        return out, "protected.pdf", "application/pdf"

    def extract_text(self, file):
        doc = fitz.open(file)
        text = ""
        for page in doc:
            text += page.get_text()

        out = self.tmp(".txt")
        with open(out, "w", encoding="utf-8") as f:
            f.write(text)
        return out, "text.txt", "text/plain"

    def extract_images(self, file):
        doc = fitz.open(file)
        zip_path = self.tmp(".zip")
        z = zipfile.ZipFile(zip_path, "w")

        for i, page in enumerate(doc):
            for img in page.get_images(full=True):
                base = doc.extract_image(img[0])
                z.writestr(f"img_{i}_{img[0]}.png", base["image"])

        z.close()
        return zip_path, "images.zip", "application/zip"

    def resize(self, file, scale):
        doc = fitz.open(file)
        ndoc = fitz.open()
        for p in doc:
            pix = p.get_pixmap(matrix=fitz.Matrix(scale, scale))
            n = ndoc.new_page(width=pix.width, height=pix.height)
            n.insert_image(n.rect, pixmap=pix)

        out = self.tmp()
        ndoc.save(out)
        return out, "resized.pdf", "application/pdf"

    def page_numbers(self, file):
        doc = fitz.open(file)
        for i, p in enumerate(doc):
            p.insert_text((50, 50), str(i+1), fontsize=12)

        out = self.tmp()
        doc.save(out)
        return out, "numbered.pdf", "application/pdf"

    def deskew(self, file):
        # Simplified deskew: re-save pages
        doc = fitz.open(file)
        out = self.tmp()
        doc.save(out)
        return out, "deskewed.pdf", "application/pdf"

    def redact(self, file, options):
        doc = fitz.open(file)
        word = options.get("text", "")
        for page in doc:
            matches = page.search_for(word)
            for r in matches:
                page.add_redact_annot(r, fill=(0, 0, 0))
            page.apply_redactions()

        out = self.tmp()
        doc.save(out)
        return out, "redacted.pdf", "application/pdf"

    # =========================================
    # CONVERSION TOOLS
    # =========================================

    def pdf_to_word(self, file):
        doc = Document()
        pdf = fitz.open(file)
        for page in pdf:
            doc.add_paragraph(page.get_text())

        out = self.tmp(".docx")
        doc.save(out)
        return out, "converted.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    def pdf_to_ppt(self, file):
        prs = Presentation()
        pdf = fitz.open(file)

        for page in pdf:
            slide = prs.slides.add_slide(prs.slide_layouts[5])
            slide.shapes.title.text = page.get_text()

        out = self.tmp(".pptx")
        prs.save(out)
        return out, "converted.pptx", "application/vnd.openxmlformats-officedocument.presentationml.presentation"

    def pdf_to_excel(self, file):
        wb = openpyxl.Workbook()
        ws = wb.active
        pdf = fitz.open(file)

        row = 1
        for page in pdf:
            for line in page.get_text().split("\n"):
                ws.cell(row=row, column=1).value = line
                row += 1

        out = self.tmp(".xlsx")
        wb.save(out)
        return out, "converted.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    def image_to_pdf(self, files):
        images = [Image.open(f).convert("RGB") for f in files]
        out = self.tmp()
        images[0].save(out, save_all=True, append_images=images[1:])
        return out, "image.pdf", "application/pdf"

    def word_to_pdf(self, file):
        pdf = self.tmp()
        c = canvas.Canvas(pdf)
        doc = Document(file)
        y = 800
        for p in doc.paragraphs:
            c.drawString(40, y, p.text)
            y -= 20
        c.save()
        return pdf, "word.pdf", "application/pdf"

    def ppt_to_pdf(self, file):
        pdf = self.tmp()
        c = canvas.Canvas(pdf)
        prs = Presentation(file)
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    c.drawString(40, 800, shape.text)
            c.showPage()
        c.save()
        return pdf, "ppt.pdf", "application/pdf"

    def excel_to_pdf(self, file):
        wb = openpyxl.load_workbook(file)
        ws = wb.active
        pdf = self.tmp()
        c = canvas.Canvas(pdf)
        y = 800
        for row in ws.iter_rows():
            line = " ".join([str(cell.value) for cell in row if cell.value])
            c.drawString(40, y, line)
            y -= 20

        c.save()
        return pdf, "excel.pdf", "application/pdf"
