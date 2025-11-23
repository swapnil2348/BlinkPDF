from flask import Flask, render_template, request, redirect, url_for, send_file, abort, jsonify
import os
import uuid

from werkzeug.utils import secure_filename

import fitz  # PyMuPDF
from PyPDF2 import PdfReader, PdfWriter
from PIL import Image
from docx import Document
from pptx import Presentation
from reportlab.pdfgen import canvas


app = Flask(__name)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "outputs")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["OUTPUT_FOLDER"] = OUTPUT_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024  # 100MB


# ----------------------
# TOOL DATA (IMPORTANT)
# ----------------------

TOOLS = [
    {"name": "Compress PDF", "slug": "compress-pdf", "category": "PDF"},
    {"name": "Merge PDF", "slug": "merge-pdf", "category": "PDF"},
    {"name": "Split PDF", "slug": "split-pdf", "category": "PDF"},
    {"name": "PDF to JPG", "slug": "pdf-to-jpg", "category": "PDF"},
    {"name": "JPG to PDF", "slug": "jpg-to-pdf", "category": "PDF"},
    {"name": "PDF to Word", "slug": "pdf-to-word", "category": "PDF"},
    {"name": "Word to PDF", "slug": "word-to-pdf", "category": "PDF"},
    {"name": "PDF to PowerPoint", "slug": "pdf-to-ppt", "category": "PDF"},
    {"name": "PowerPoint to PDF", "slug": "ppt-to-pdf", "category": "PDF"},
    {"name": "Rotate PDF", "slug": "rotate-pdf", "category": "PDF"},
    {"name": "Unlock PDF", "slug": "unlock-pdf", "category": "PDF"},
    {"name": "Protect PDF", "slug": "protect-pdf", "category": "PDF"},
    {"name": "Sign PDF", "slug": "sign-pdf", "category": "PDF"},
    {"name": "OCR PDF", "slug": "ocr-pdf", "category": "PDF"},
]

SLUG_TO_TOOL = {tool["slug"]: tool for tool in TOOLS}


# ----------------------
# BASIC PAGES
# ----------------------

@app.route("/")
def index():
    return render_template("index.html", tools=TOOLS)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


# ----------------------
# TOOL DYNAMIC PAGE
# ----------------------

@app.route("/tool/<slug>")
def tool_page(slug):
    tool = next((t for t in TOOLS if t.get("slug") == slug), None)
    if not tool:
        return redirect(url_for("index"))

    return render_template("tool_page.html", tool=tool)


# ----------------------
# FILE PROCESSING
# ----------------------

@app.route("/process", methods=["POST"])
def process_file():

    tool_slug = request.form.get("tool")

    if tool_slug not in SLUG_TO_TOOL:
        return jsonify({"error": "Invalid tool"}), 400

    files = request.files.getlist("file")

    if not files or files[0].filename == "":
        return jsonify({"error": "No file uploaded"}), 400

    input_paths = []

    for file in files:
        filename = secure_filename(file.filename)
        unique_name = str(uuid.uuid4()) + "_" + filename
        input_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
        file.save(input_path)
        input_paths.append(input_path)

    try:
        if tool_slug == "merge-pdf":
            output_path = merge_pdf(input_paths)

        elif tool_slug == "split-pdf":
            output_path = split_pdf(input_paths[0])

        elif tool_slug == "compress-pdf":
            output_path = compress_pdf(input_paths[0])

        elif tool_slug == "pdf-to-jpg":
            output_path = pdf_to_jpg(input_paths[0])

        elif tool_slug == "jpg-to-pdf":
            output_path = jpg_to_pdf(input_paths)

        elif tool_slug == "pdf-to-word":
            output_path = pdf_to_word(input_paths[0])

        elif tool_slug == "word-to-pdf":
            output_path = word_to_pdf(input_paths[0])

        else:
            return redirect(url_for("tool_page", slug=tool_slug))

        return send_file(output_path, as_attachment=True)

    except Exception as e:
        print("ERROR:", str(e))
        return jsonify({"error": "Processing failed"}), 500


# ----------------------
# TOOL FUNCTIONS
# ----------------------

def merge_pdf(input_paths):
    output_path = os.path.join(OUTPUT_FOLDER, f"merged_{uuid.uuid4()}.pdf")

    writer = PdfWriter()

    for path in input_paths:
        reader = PdfReader(path)
        for page in reader.pages:
            writer.add_page(page)

    with open(output_path, "wb") as f:
        writer.write(f)

    return output_path


def split_pdf(input_path):
    output_path = os.path.join(OUTPUT_FOLDER, f"split_{uuid.uuid4()}.pdf")

    reader = PdfReader(input_path)
    writer = PdfWriter()

    if len(reader.pages) > 0:
        writer.add_page(reader.pages[0])

    with open(output_path, "wb") as f:
        writer.write(f)

    return output_path


def compress_pdf(input_path):
    output_path = os.path.join(OUTPUT_FOLDER, f"compressed_{uuid.uuid4()}.pdf")

    doc = fitz.open(input_path)
    doc.save(output_path, garbage=4, deflate=True)

    return output_path


def pdf_to_jpg(input_path):
    output_folder = os.path.join(OUTPUT_FOLDER, f"images_{uuid.uuid4()}")
    os.makedirs(output_folder, exist_ok=True)

    doc = fitz.open(input_path)

    image_paths = []

    for i, page in enumerate(doc):
        pix = page.get_pixmap(dpi=150)
        out_path = os.path.join(output_folder, f"page_{i+1}.jpg")
        pix.save(out_path)
        image_paths.append(out_path)

    return image_paths[0] if image_paths else None


def jpg_to_pdf(input_paths):
    output_path = os.path.join(OUTPUT_FOLDER, f"image_to_pdf_{uuid.uuid4()}.pdf")

    images = [Image.open(p).convert("RGB") for p in input_paths]

    images[0].save(output_path, save_all=True, append_images=images[1:])

    return output_path


def pdf_to_word(input_path):
    output_file = os.path.join(OUTPUT_FOLDER, f"converted_{uuid.uuid4()}.docx")

    doc = fitz.open(input_path)
    word = Document()

    for page in doc:
        text = page.get_text()
        if text.strip():
            word.add_paragraph(text)

    word.save(output_file)

    return output_file


def word_to_pdf(input_path):
    output_path = os.path.join(OUTPUT_FOLDER, f"word_to_pdf_{uuid.uuid4()}.pdf")

    doc = Document(input_path)
    c = canvas.Canvas(output_path)

    y = 800
    for para in doc.paragraphs:
        if y < 40:
            c.showPage()
            y = 800
        c.drawString(40, y, para.text)
        y -= 15

    c.save()

    return output_path


# ----------------------
# ERROR HANDLERS
# ----------------------

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(500)
def server_error(e):
    return render_template("500.html"), 500


# ----------------------
# RUN LOCAL
# ----------------------

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
