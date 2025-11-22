import os
import io
import zipfile
import uuid
import pytesseract
from shutil import copyfile
from PIL import Image
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import fitz  # PyMuPDF


class PDFProcessor:

    # ---------------- HELPERS ----------------
    def _out(self, outdir, name):
        return os.path.join(outdir, name)

    def _ts(self):
        return uuid.uuid4().hex

    # ---------------- SAFE COPY ----------------
    def clone_pdf(self, input_path, outdir):
        out = self._out(outdir, f"processed_{self._ts()}.pdf")
        copyfile(input_path, out)
        return out

    def clean_copy(self, input_path, outdir):
        reader = PdfReader(input_path)
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)

        out = self._out(outdir, f"clean_{self._ts()}.pdf")
        with open(out, "wb") as f:
            writer.write(f)
        return out

    # ---------------- REAL COMPRESS ----------------
    def compress_pdf(self, input_path, out_dir, form):
        # quality: 20–80 recommended
        quality = int(form.get("quality", 50))
        quality = max(10, min(quality, 90))
        scale = quality / 100.0  # 0.1 – 0.9

        doc = fitz.open(input_path)
        new_doc = fitz.open()
        matrix = fitz.Matrix(scale, scale)

        for page in doc:
            pix = page.get_pixmap(matrix=matrix)
            new_page = new_doc.new_page(width=pix.width, height=pix.height)
            new_page.insert_image(new_page.rect, pixmap=pix)

        output = self._out(out_dir, f"compressed_{self._ts()}.pdf")
        new_doc.save(output, deflate=True, garbage=4)
        new_doc.close()
        doc.close()
        return output

    # ---------------- REAL CROP ----------------
    def crop_pdf(self, input_path, out_dir, form):
        try:
            x = float(form.get("x", 0))
            y = float(form.get("y", 0))
            w = float(form.get("w", 400))
            h = float(form.get("h", 400))
        except:
            x, y, w, h = 0, 0, 400, 400

        doc = fitz.open(input_path)

        for page in doc:
            page_rect = page.rect

            left = max(0, x)
            top = max(0, y)
            right = min(page_rect.width, x + w)
            bottom = min(page_rect.height, y + h)

            if right <= left or bottom <= top:
                continue

            rect = fitz.Rect(left, top, right, bottom)
            page.set_cropbox(rect)

        output = self._out(out_dir, f"cropped_{self._ts()}.pdf")
        doc.save(output)
        doc.close()
        return output


    # ---------------- REAL RESIZE ----------------
    def resize_pdf(self, input_path, out_dir, form):
        # scale > 1 = bigger, < 1 = smaller
        scale = float(form.get("scale", 1.5))
        scale = max(0.1, min(scale, 5.0))

        doc = fitz.open(input_path)
        new_doc = fitz.open()
        matrix = fitz.Matrix(scale, scale)

        for page in doc:
            pix = page.get_pixmap(matrix=matrix)
            new_page = new_doc.new_page(width=pix.width, height=pix.height)
            new_page.insert_image(new_page.rect, pixmap=pix)

        output = self._out(out_dir, f"resized_{self._ts()}.pdf")
        new_doc.save(output, deflate=True, garbage=4)
        new_doc.close()
        doc.close()
        return output

        # ---------------- PROTECT PDF (REAL WORKING) ----------------
    def protect_pdf(self, input_path, out_dir, form):
        password = str(form.get("password", "")).strip()

        if not password:
            password = "12345"  # fallback if user forgets

        reader = PdfReader(input_path)
        writer = PdfWriter()

        for page in reader.pages:
            writer.add_page(page)

        writer.encrypt(password, algorithm="AES-256")

        out = self._out(out_dir, f"protected_{self._ts()}.pdf")
        with open(out, "wb") as f:
            writer.write(f)

        return out



        # ---------------- UNLOCK (REAL) ----------------
    def unlock_pdf(self, input_path, out_dir, form):
        password = str(form.get("password", "")).strip()

        reader = PdfReader(input_path)

        if reader.is_encrypted:
            if not reader.decrypt(password):
                raise ValueError("Incorrect password")

        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)

        out = self._out(out_dir, f"unlocked_{self._ts()}.pdf")
        with open(out, "wb") as f:
            writer.write(f)

        return out



    # ---------------- REAL OPTIMIZE ----------------
    def optimize_pdf(self, input_path, out_dir, form):
        doc = fitz.open(input_path)
        output = self._out(out_dir, f"optimized_{self._ts()}.pdf")
        # garbage=4 cleans unused objects; deflate compresses streams
        doc.save(output, garbage=4, deflate=True)
        doc.close()
        return output

    # ---------------- REAL FLATTEN (RENDER-BASED) ----------------
    def flatten_pdf(self, input_path, out_dir, form):
        # Render each page to an image, then rebuild PDF = fully flattened
        doc = fitz.open(input_path)
        new_doc = fitz.open()

        for page in doc:
            pix = page.get_pixmap()
            new_page = new_doc.new_page(width=pix.width, height=pix.height)
            new_page.insert_image(new_page.rect, pixmap=pix)

        output = self._out(out_dir, f"flattened_{self._ts()}.pdf")
        new_doc.save(output, deflate=True, garbage=4)
        new_doc.close()
        doc.close()
        return output

    # ---------------- REAL DESKEW (USER ANGLE) ----------------
    def deskew_pdf(self, input_path, out_dir, form):
        try:
            angle = float(form.get("angle", 0))
        except:
            angle = 0

        if angle == 0:
            return self.clean_copy(input_path, out_dir)

        doc = fitz.open(input_path)
        new_doc = fitz.open()

        for page in doc:
            matrix = fitz.Matrix(1, 1).prerotate(angle)
            pix = page.get_pixmap(matrix=matrix)

            new_page = new_doc.new_page(width=pix.width, height=pix.height)
            new_page.insert_image(new_page.rect, pixmap=pix)

        output = self._out(out_dir, f"deskewed_{self._ts()}.pdf")
        new_doc.save(output, deflate=True, garbage=4)
        new_doc.close()
        doc.close()

        return output


    # ---------------- REAL ANNOTATE (TEXT STAMP) ----------------
    def annotate_pdf(self, input_path, out_dir, form):
        text = form.get("text", "Note")
        size = int(form.get("size", 16))
        x = int(form.get("x", 100))
        y = int(form.get("y", 100))

        reader = PdfReader(input_path)
        writer = PdfWriter()

        for page in reader.pages:
            packet = io.BytesIO()
            can = canvas.Canvas(packet, pagesize=(page.mediabox.width, page.mediabox.height))
            can.setFont("Helvetica", size)
            can.drawString(x, y, text)
            can.save()

            packet.seek(0)
            overlay = PdfReader(packet)
            page.merge_page(overlay.pages[0])
            writer.add_page(page)

        out = self._out(out_dir, f"annotated_{self._ts()}.pdf")
        with open(out, "wb") as f:
            writer.write(f)
        return out

    # ---------------- REAL REDACT (TEXT) ----------------
    def redact_pdf(self, input_path, out_dir, form):
        target = form.get("text", "").strip()
        if not target:
            # nothing to redact; return clean copy
            return self.clean_copy(input_path, out_dir)

        doc = fitz.open(input_path)

        for page in doc:
            areas = page.search_for(target)
            for rect in areas:
                page.add_redact_annot(rect, fill=(0, 0, 0))
            if areas:
                page.apply_redactions()

        output = self._out(out_dir, f"redacted_{self._ts()}.pdf")
        doc.save(output, garbage=4, deflate=True)
        doc.close()
        return output

    # ---------------- REAL FILL FORMS ----------------
    def fill_forms(self, input_path, out_dir, form):
        field_name = form.get("field_name", "").strip()
        field_value = form.get("field_value", "").strip()

        reader = PdfReader(input_path)
        writer = PdfWriter()

        for page in reader.pages:
            writer.add_page(page)

        if field_name and field_value:
            # Try to update first page; if multiple fields, user can repeat
            try:
                writer.update_page_form_field_values(
                    writer.pages[0],
                    {field_name: field_value}
                )
            except Exception:
                pass

        # Keep AcroForm if exists
        if "/AcroForm" in reader.trailer["/Root"]:
            writer._root_object.update(
                {"/AcroForm": reader.trailer["/Root"]["/AcroForm"]}
            )

        out = self._out(out_dir, f"filled_{self._ts()}.pdf")
        with open(out, "wb") as f:
            writer.write(f)
        return out

    # ---------------- MERGE ----------------
    def merge_pdf(self, inputs, out_dir):
        writer = PdfWriter()
        for path in inputs:
            reader = PdfReader(path)
            for page in reader.pages:
                writer.add_page(page)

        out = self._out(out_dir, f"merged_{self._ts()}.pdf")
        with open(out, "wb") as f:
            writer.write(f)
        return out

    # ---------------- SPLIT ----------------
    def split_pdf(self, input_path, outdir, form):
        reader = PdfReader(input_path)
        outzip = self._out(outdir, f"split_{self._ts()}.zip")

        with zipfile.ZipFile(outzip, "w") as z:
            for i, page in enumerate(reader.pages):
                writer = PdfWriter()
                writer.add_page(page)
                mem = io.BytesIO()
                writer.write(mem)
                mem.seek(0)
                z.writestr(f"page_{i + 1}.pdf", mem.read())
        return outzip

    # ---------------- ROTATE ----------------
    def rotate_pdf(self, input_path, out_dir, form):
        angle = int(form.get("angle", 90))

        if angle not in [90, 180, 270]:
            angle = 90

        reader = PdfReader(input_path)
        writer = PdfWriter()

        for page in reader.pages:
            page.rotate_clockwise(angle)
            writer.add_page(page)

        out = self._out(out_dir, f"rotated_{self._ts()}.pdf")
        with open(out, "wb") as f:
            writer.write(f)

        return out


    # ---------------- WATERMARK ----------------
    def watermark_pdf(self, input_path, out_dir, form):
        reader = PdfReader(input_path)
        writer = PdfWriter()

        watermark_text = form.get("text", "BlinkPDF")
        size = int(form.get("size", 28))
        x = int(form.get("x", 100))
        y = int(form.get("y", 100))

        for page in reader.pages:
            packet = io.BytesIO()
            can = canvas.Canvas(packet, pagesize=(page.mediabox.width, page.mediabox.height))
            can.setFont("Helvetica-Bold", size)
            can.drawString(x, y, watermark_text)
            can.save()

            packet.seek(0)
            overlay = PdfReader(packet)
            page.merge_page(overlay.pages[0])
            writer.add_page(page)

        out = self._out(out_dir, f"watermark_{self._ts()}.pdf")
        with open(out, "wb") as f:
            writer.write(f)
        return out

    # ---------------- PAGE NUMBERS ----------------
    def number_pdf(self, input_path, out_dir, form):
        start = int(form.get("start", 1))
        reader = PdfReader(input_path)
        writer = PdfWriter()

        for i, page in enumerate(reader.pages):
            packet = io.BytesIO()
            c = canvas.Canvas(packet, pagesize=(page.mediabox.width, page.mediabox.height))
            c.drawString(300, 20, str(start + i))
            c.save()

            packet.seek(0)
            overlay = PdfReader(packet)
            page.merge_page(overlay.pages[0])
            writer.add_page(page)

        out = self._out(out_dir, f"numbered_{self._ts()}.pdf")
        with open(out, "wb") as f:
            writer.write(f)
        return out

    # ---------------- SIGN ----------------
    def sign_pdf(self, input_path, out_dir, form):
        name = form.get("text", "Signature")
        x = int(form.get("x", 100))
        y = int(form.get("y", 100))

        reader = PdfReader(input_path)
        writer = PdfWriter()

        for page in reader.pages:
            packet = io.BytesIO()
            can = canvas.Canvas(packet, pagesize=(page.mediabox.width, page.mediabox.height))
            can.setFont("Helvetica-Oblique", 26)
            can.drawString(x, y, name)
            can.save()

            packet.seek(0)
            overlay = PdfReader(packet)
            page.merge_page(overlay.pages[0])
            writer.add_page(page)

        out = self._out(out_dir, f"signed_{self._ts()}.pdf")
        with open(out, "wb") as f:
            writer.write(f)
        return out

    # ---------------- IMAGE → PDF ----------------
    def image_to_pdf(self, inputs, out_dir):
        imgs = [Image.open(i).convert("RGB") for i in inputs]
        out = self._out(out_dir, f"img2pdf_{self._ts()}.pdf")
        imgs[0].save(out, save_all=True, append_images=imgs[1:])
        return out

    # ---------------- EXTRACT TEXT (NORMAL + OCR) ----------------
    def extract_text(self, input_path, out_dir):
        reader = PdfReader(input_path)
        text = ""

        # First try normal text extraction
        for p in reader.pages:
            extracted = p.extract_text()
            if extracted:
                text += extracted + "\n"

        # If text is too short -> run OCR
        if len(text.strip()) < 100:
            # OCR using PyMuPDF instead of pdf2image
            doc = fitz.open(input_path)

            for page in doc:
                pix = page.get_pixmap(dpi=300)
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                ocr_text = pytesseract.image_to_string(img)
                text += ocr_text + "\n"

            doc.close()

        if not text.strip():
            text = "No text found in this document."

        out = self._out(out_dir, f"text_{self._ts()}.txt")
        with open(out, 'w', encoding='utf-8') as f:
            f.write(text)

        return out

    # ---------------- METADATA ----------------
    def metadata_editor(self, input_path, out_dir, form):
        reader = PdfReader(input_path)
        writer = PdfWriter()

        for p in reader.pages:
            writer.add_page(p)

        writer.add_metadata({
            "/Title": form.get("title", ""),
            "/Author": form.get("author", ""),
            "/Keywords": form.get("keywords", "")
        })

        out = self._out(out_dir, f"meta_{self._ts()}.pdf")
        with open(out, "wb") as f:
            writer.write(f)
        return out

    # ---------------- MAIN DISPATCH ----------------
    def process(self, slug, inputs, out_dir, form=None):
        form = form or {}
        input_path = inputs[0] if isinstance(inputs, list) else inputs

        if slug == "merge-pdf":
            return self.merge_pdf(inputs, out_dir)

        if slug == "split-pdf":
            return self.split_pdf(input_path, out_dir, form)

        if slug == "rotate-pdf":
            return self.rotate_pdf(input_path, out_dir, form)

        if slug == "compress-pdf":
            return self.compress_pdf(input_path, out_dir, form)

        if slug == "resize-pdf":
            return self.resize_pdf(input_path, out_dir, form)

        if slug == "crop-pdf":
            return self.crop_pdf(input_path, out_dir, form)

        if slug == "protect-pdf":
            return self.protect_pdf(input_path, out_dir, form)

        if slug == "unlock-pdf":
            return self.unlock_pdf(input_path, out_dir, form)

        if slug == "optimize-pdf":
            return self.optimize_pdf(input_path, out_dir, form)

        if slug == "flatten-pdf":
            return self.flatten_pdf(input_path, out_dir, form)

        if slug == "deskew-pdf":
            return self.deskew_pdf(input_path, out_dir, form)

        if slug == "annotate-pdf":
            return self.annotate_pdf(input_path, out_dir, form)

        if slug == "redact-pdf":
            return self.redact_pdf(input_path, out_dir, form)

        if slug == "fill-forms":
            return self.fill_forms(input_path, out_dir, form)

        if slug == "watermark-pdf":
            return self.watermark_pdf(input_path, out_dir, form)

        if slug == "number-pdf":
            return self.number_pdf(input_path, out_dir, form)

        if slug == "sign-pdf":
            return self.sign_pdf(input_path, out_dir, form)

        if slug == "image-to-pdf":
            return self.image_to_pdf(inputs, out_dir)

        if slug == "extract-text":
            return self.extract_text(input_path, out_dir)
            
        if slug == "metadata-editor":
            return self.metadata_editor(input_path, out_dir, form)

        # Unknown tool – safe copy
        return self.clone_pdf(input_path, out_dir)
