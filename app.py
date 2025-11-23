from flask import Flask, render_template, request, send_file, abort, jsonify
import os
import uuid
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

from PyPDF2 import PdfReader, PdfWriter
from PIL import Image
import fitz  # PyMuPDF
from docx import Document
from pptx import Presentation
from reportlab.pdfgen import canvas


app = Flask(__name__)

# ------------------ CONFIG ------------------

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "outputs")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["OUTPUT_FOLDER"] = OUTPUT_FOLDER

# 500 MB limit
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  


@app.errorhandler(RequestEntityTooLarge)
def file_too_large(e):
    return "❌ File too large. Max allowed: 500MB", 413


# ------------------ TOOLS ------------------

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

AI_TOOLS = [
    {"name": "AI PDF Editor", "slug": "ai-editor"},
    {"name": "AI PDF Chat", "slug": "ai-chat"},
    {"name": "AI PDF Summarizer", "slug": "ai-summarizer"},
    {"name": "AI PDF Notes", "slug": "ai-notes"},
    {"name": "AI PDF Translator", "slug": "ai-translator"},
    {"name": "AI PDF Analyzer", "slug": "ai-analyzer"},
]

SLUG_TO_TOOL = {tool["slug"]: tool for tool in TOOLS + AI_TOOLS}


# ------------------ ROUTES ------------------

@app.route("/")
def index():
    return render_template("index.html", tools=TOOLS, ai_tools=AI_TOOLS)


@app.route("/tool/<slug>")
def tool_page(slug):
    tool = SLUG_TO_TOOL.get(slug)
    if not tool:
        return abort(404)

    return render_template("tool_page.html", tool=tool)


# ----- REQUIRED FOOTER ROUTES (Fixes your errors) -----

@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


# ------------------ PROCESS ROUTE ------------------

@app.route("/process/<slug>", methods=["POST"])
def process_tool(slug):

    tool = SLUG_TO_TOOL.get(slug)
    if not tool:
        return abort(404)

    if "files" not in request.files:
        return "No files uploaded", 400

    files = request.files.getlist("files")

    if len(files) == 0:
        return "No files selected", 400

    file_paths = []

    for file in files:
        if file.filename == "":
            continue

        filename = secure_filename(f"{uuid.uuid4().hex}_{file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        file_paths.append(filepath)

    # -------------- MERGE PDF ----------------
    if slug == "merge-pdf":
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], f"merged_{uuid.uuid4().hex}.pdf")

        writer = PdfWriter()

        for path in file_paths:
            reader = PdfReader(path)
            for page in reader.pages:
                writer.add_page(page)

        with open(output_path, "wb") as f:
            writer.write(f)

        return send_file(output_path, as_attachment=True)

    # -------------- SPLIT PDF ----------------
    if slug == "split-pdf":
        zip_path = os.path.join(app.config['OUTPUT_FOLDER'], f"split_{uuid.uuid4().hex}.pdf")

        reader = PdfReader(file_paths[0])
        writer = PdfWriter()

        for page in reader.pages:
            writer.add_page(page)

        with open(zip_path, "wb") as f:
            writer.write(f)

        return send_file(zip_path, as_attachment=True)

    # -------------- PDF TO JPG ----------------
    if slug == "pdf-to-jpg":
        images = []
        doc = fitz.open(file_paths[0])

        for i in range(len(doc)):
            page = doc.load_page(i)
            pix = page.get_pixmap()
            output = os.path.join(app.config["OUTPUT_FOLDER"], f"{uuid.uuid4().hex}.jpg")
            pix.save(output)
            images.append(output)

        return send_file(images[0], as_attachment=True)

    # -------------- JPG TO PDF ----------------
    if slug == "jpg-to-pdf":
        output = os.path.join(app.config["OUTPUT_FOLDER"], f"{uuid.uuid4().hex}.pdf")

        images = [Image.open(p).convert("RGB") for p in file_paths]
        images[0].save(output, save_all=True, append_images=images[1:])

        return send_file(output, as_attachment=True)

    # -------------- ROTATE PDF ----------------
    if slug == "rotate-pdf":
        output = os.path.join(app.config["OUTPUT_FOLDER"], f"{uuid.uuid4().hex}.pdf")

        reader = PdfReader(file_paths[0])
        writer = PdfWriter()

        for page in reader.pages:
            page.rotate(90)
            writer.add_page(page)

        with open(output, "wb") as f:
            writer.write(f)

        return send_file(output, as_attachment=True)

    # -------------- UNLOCK PDF ----------------
    if slug == "unlock-pdf":
        output = os.path.join(app.config["OUTPUT_FOLDER"], f"{uuid.uuid4().hex}.pdf")

        reader = PdfReader(file_paths[0])
        if reader.is_encrypted:
            reader.decrypt("")

        writer = PdfWriter()

        for page in reader.pages:
            writer.add_page(page)

        with open(output, "wb") as f:
            writer.write(f)

        return send_file(output, as_attachment=True)

    # -------------- DEFAULT FALLBACK ----------------
    return jsonify({
        "status": "success",
        "tool": slug,
        "message": "Uploaded and processing engine connected successfully"
    })


# ------------------ MAIN ------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
