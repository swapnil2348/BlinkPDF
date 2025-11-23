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

    # ---------------------------
    # GET FILES
    # ---------------------------
    files = request.files.getlist("files")
    if not files or files[0].filename == "":
        return jsonify({"error": "No files uploaded"}), 400

    # ---------------------------
    # SAVE FILES
    # ---------------------------
    saved_paths = []
    for file in files:
        filename = secure_filename(f"{uuid.uuid4().hex}_{file.filename}")
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)
        saved_paths.append(filepath)

    # ---------------------------
    # READ ADVANCED OPTIONS
    # ---------------------------
    options = {}

    for key, value in request.form.items():

        # Convert booleans
        if value.lower() in ["true", "false"]:
            value = (value.lower() == "true")

        # Convert numbers safely
        else:
            try:
                if "." in value:
                    value = float(value)
                else:
                    value = int(value)
            except:
                pass

        options[key] = value

    # ---------------------------
    # PROCESS USING REAL ENGINE
    # ---------------------------
    try:
        processor = PDFProcessor()
        output_path = processor.process(
            tool_slug=slug,
            input_paths=saved_paths,
            options=options
        )

        if not output_path or not os.path.exists(output_path):
            return jsonify({"error": "Processing failed for this tool"}), 500

        return send_file(
            output_path, 
            as_attachment=True,
            download_name=os.path.basename(output_path)
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ------------------ MAIN ------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
