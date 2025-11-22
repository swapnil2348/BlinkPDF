import os
import io
import math
import fitz
import zipfile
import tempfile
from typing import List, Tuple, Dict, Any, Optional

import fitz  # PyMuPDF
from PyPDF2 import PdfReader, PdfWriter
from PIL import Image
import pytesseract
from reportlab.lib.pagesizes import A4, letter
from reportlab.pdfgen import canvas
from docx import Document
import openpyxl
from pptx import Presentation


import fitz
import zipfile
import os


class PDFProcessor:

    def merge(self, files, output):
        doc = fitz.open()
        for f in files:
            d = fitz.open(f)
            doc.insert_pdf(d)
            d.close()
        doc.save(output)
        doc.close()


    def split(self, file, output, pages):
        doc = fitz.open(file)
        new = fitz.open()

        if not pages:
            for page in doc:
                new.insert_pdf(doc, from_page=page.number, to_page=page.number)
        else:
            parts = pages.split(',')
            for part in parts:
                if '-' in part:
                    a,b = map(int, part.split('-'))
                    new.insert_pdf(doc, from_page=a-1, to_page=b-1)
                else:
                    p = int(part)
                    new.insert_pdf(doc, from_page=p-1, to_page=p-1)

        new.save(output)
        new.close()
        doc.close()


    def compress(self, file, output, level):
        doc = fitz.open(file)
        if level == "low":
            doc.save(output, deflate=True)
        elif level == "high":
            doc.save(output, deflate=True, clean=True, garbage=4)
        else:
            doc.save(output, deflate=True, garbage=2)
        doc.close()


    def rotate(self, file, output, angle):
        doc = fitz.open(file)
        for page in doc:
            page.set_rotation(angle)
        doc.save(output)
        doc.close()


    def watermark(self, file, output, text, x, y, size):
        doc = fitz.open(file)
        for page in doc:
            page.insert_text((x, y), text, fontsize=size, opacity=0.5)
        doc.save(output)
        doc.close()


    def number(self, file, output, start):
        doc = fitz.open(file)
        for i, page in enumerate(doc):
            page.insert_text((20, 20), str(start+i), fontsize=12)
        doc.save(output)
        doc.close()


    def protect(self, file, output, password):
        doc = fitz.open(file)
        doc.save(output, encryption=fitz.PDF_ENCRYPT_AES_256, owner_pw=password, user_pw=password)
        doc.close()


    def unlock(self, file, output, password):
        doc = fitz.open(file)
        if doc.is_encrypted:
            doc.authenticate(password)
        doc.save(output)
        doc.close()


    def extract_text(self, file):
        doc = fitz.open(file)
        path = file.replace(".pdf", ".txt")
        with open(path, "w", encoding="utf8") as f:
            for p in doc:
                f.write(p.get_text())
        doc.close()
        return path


    def extract_images(self, file):
        doc = fitz.open(file)
        zip_path = file.replace(".pdf", "_images.zip")

        zipf = zipfile.ZipFile(zip_path, 'w')

        for i in range(len(doc)):
            for img in doc.get_page_images(i):
                xref = img[0]
                pix = fitz.Pixmap(doc, xref)
                img_name = f"image_{i}_{xref}.png"
                pix.save(img_name)
                zipf.write(img_name)
                os.remove(img_name)

        zipf.close()
        doc.close()
        return zip_path


    def crop(self, file, output, width, height):
        doc = fitz.open(file)
        for page in doc:
            page.set_cropbox(fitz.Rect(0, 0, width, height))
        doc.save(output)
        doc.close()


    def resize(self, file, output, width, height):
        doc = fitz.open(file)
        new = fitz.open()

        for page in doc:
            mat = fitz.Matrix(width/page.rect.width, height/page.rect.height)
            pix = page.get_pixmap(matrix=mat)
            new_page = new.new_page(width=width, height=height)
            new_page.insert_image(new_page.rect, pixmap=pix)

        new.save(output)
        doc.close()
        new.close()


    def optimize(self, file, output):
        doc = fitz.open(file)
        doc.save(output, clean=True, garbage=4, deflate=True)
        doc.close()


    def flatten(self, file, output):
        doc = fitz.open(file)
        for page in doc:
            page.apply_redactions()
        doc.save(output)
        doc.close()


    def edit_metadata(self, file, output, title, author, subject):
        doc = fitz.open(file)
        meta = doc.metadata
        if title: meta["title"] = title
        if author: meta["author"] = author
        if subject: meta["subject"] = subject
        doc.set_metadata(meta)
        doc.save(output)
        doc.close()


    def repair(self, file, output):
        doc = fitz.open(file, filetype="pdf")
        doc.save(output)
        doc.close()
