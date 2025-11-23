from flask import Flask, render_template, request, send_file, abort, jsonify
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
import os
import uuid

from PyPDF2 import PdfReader, PdfWriter
import fitz  # PyMuPDF
from PIL import Image

app = Flask(__name__)

# -------------------------------------------------------------------
# CONFIG
# -------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "outputs")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["OUTPUT_FOLDER"] = OUTPUT_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024  # 500MB limit

# -------------------------------------------------------------------
# 33 NON-AI TOOLS (EXACT FROM YOU)
# -------------------------------------------------------------------
TOOLS = [
    {'slug': 'merge-pdf', 'title': 'Merge PDF', 'icon': 'merge-pdf.svg'},
    {'slug': 'split-pdf', 'title': 'Split PDF', 'icon': 'split-pdf.svg'},
    {'slug': 'compress-pdf', 'title': 'Compress PDF', 'icon': 'compress-pdf.svg'},
    {'slug': 'optimize-pdf', 'title': 'Optimize PDF', 'icon': 'optimize-pdf.svg'},
    {'slug': 'rotate-pdf', 'title': 'Rotate PDF', 'icon': 'rotate-pdf.svg'},
    {'slug': 'watermark-pdf', 'title': 'Watermark PDF', 'icon': 'watermark-pdf.svg'},
    {'slug': 'number-pdf', 'title': 'Number Pages', 'icon': 'number-pdf.svg'},
    {'slug': 'protect-pdf', 'title': 'Protect PDF', 'icon': 'protect-pdf.svg'},
    {'slug': 'unlock-pdf', 'title': 'Unlock PDF', 'icon': 'unlock-pdf.svg'},
    {'slug': 'repair-pdf', 'title': 'Repair PDF', 'icon': 'repair-pdf.svg'},
    {'slug': 'organize-pdf', 'title': 'Organize PDF', 'icon': 'organize-pdf.svg'},
    {'slug': 'sign-pdf', 'title': 'Sign PDF', 'icon': 'sign-pdf.svg'},
    {'slug': 'annotate-pdf', 'title': 'Annotate PDF', 'icon': 'annotate-pdf.svg'},
    {'slug': 'redact-pdf', 'title': 'Redact PDF', 'icon': 'redact-pdf.svg'},
    {'slug': 'pdf-to-word', 'title': 'PDF to Word', 'icon': 'pdf-to-word.svg'},
    {'slug': 'word-to-pdf', 'title': 'Word to PDF', 'icon': 'word-to-pdf.svg'},
    {'slug': 'pdf-to-image', 'title': 'PDF to Image', 'icon': 'pdf-to-image.svg'},
    {'slug': 'image-to-pdf', 'title': 'Image to PDF', 'icon': 'image-to-pdf.svg'},
    {'slug': 'pdf-to-excel', 'title': 'PDF to Excel', 'icon': 'pdf-to-excel.svg'},
    {'slug': 'excel-to-pdf', 'title': 'Excel to PDF', 'icon': 'excel-to-pdf.svg'},
    {'slug': 'pdf-to-powerpoint', 'title': 'PDF to PowerPoint', 'icon': 'pdf-to-powerpoint.svg'},
    {'slug': 'powerpoint-to-pdf', 'title': 'PowerPoint to PDF', 'icon': 'powerpoint-to-pdf.svg'},
    {'slug': 'ocr-pdf', 'title': 'OCR PDF', 'icon': 'ocr-pdf.svg'},
    {'slug': 'extract-text', 'title': 'Extract Text', 'icon': 'extract-text.svg'},
    {'slug': 'extract-images', 'title': 'Extract Images', 'icon': 'extract-images.svg'},
    {'slug': 'deskew-pdf', 'title': 'Deskew PDF', 'icon': 'deskew-pdf.svg'},
    {'slug': 'crop-pdf', 'title': 'Crop PDF', 'icon': 'crop-pdf.svg'},
    {'slug': 'resize-pdf', 'title': 'Resize PDF', 'icon': 'resize-pdf.svg'},
    {'slug': 'flatten-pdf', 'title': 'Flatten PDF', 'icon': 'flatten-pdf.svg'},
    {'slug': 'metadata-editor', 'title': 'Metadata Editor', 'icon': 'metadata-editor.svg'},
    {'slug': 'fill-forms', 'title': 'Fill PDF Forms', 'icon': 'fill-forms.svg'},
    {'slug': 'background-remover', 'title': 'Remove Background', 'icon': 'background-remover.svg'},
]

# -------------------------------------------------------------------
# AI TOOLS
# -------------------------------------------------------------------
AI_TOOLS = [
    {"slug": "ai-editor", "title": "AI PDF Editor", "url": "/ai/editor"},
    {"slug": "ai-summarizer", "title": "AI Summarizer", "url": "/ai/summarizer-page"},
    {"slug": "ai-chat", "title": "Chat with PDF", "url": "/ai/chat-page"},
    {"slug": "ai-translate", "title": "AI Translator", "url": "/ai/translate-page"},
    {"slug": "ai-table-extract", "title": "AI Table Extractor", "url": "/ai/table-page"},
]

# Map
SLUG_TO_TOOL = {tool["slug"]: tool for tool in TOOLS}

# -------------------------------------------------------------------
# ERROR HANDLER (500MB limit)
# -------------------------------------------------------------------
@app.errorhandler(RequestEntityTooLarge)
def file_too_large(e):
    return "File too large. Maximum allowed: 500MB", 413


# -------------------------------------------------------------------
# ROUTES
# -------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html", tools=TOOLS, ai_tools=AI_TOOLS)

@app.route("/ai-tools")
def ai_tools_page():
    return render_template("ai_tools.html", ai_tools=AI_TOOLS)

@app.route("/privacy")
def privacy():
    return render_template("privacy.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")
    
@app.route("/terms")
def contact():
    return render_template("terms.html")
    
@app.route("/tool/<slug>")
def tool_page(slug):
    tool = SLUG_TO_TOOL.get(slug)
    if not tool:
        return abort(404)
    return render_template("tool_page.html", tool=tool)


# -------------------------------------------------------------------
# PROCESS ROUTE
# -------------------------------------------------------------------
@app.route("/process/<slug>", methods=["POST"])
def process_tool(slug):
    tool = SLUG_TO_TOOL.get(slug)
    if not tool:
        return abort(404)

    if "files" not in request.files:
        return "No files uploaded", 400

    files = request.files.getlist("files")
    if not files or all(f.filename == "" for f in files):
        return "No files selected", 400

    saved_paths = []
    for f in files:
        if not f or f.filename == "":
            continue
        filename = secure_filename(f"{uuid.uuid4().hex}_{f.filename}")
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        f.save(filepath)
        saved_paths.append(filepath)

    if not saved_paths:
        return "No valid files after upload", 400

    try:
        output_path, download_name, mimetype = process_pdf_tool(
            slug=slug,
            input_paths=saved_paths,
            output_dir=app.config["OUTPUT_FOLDER"],
            form=request.form,
        )
    except RequestEntityTooLarge:
        # handled by errorhandler
        raise
    except Exception as e:
        # log server-side and show friendly message
        print(f"[ERROR] processing tool {slug}: {e}", flush=True)
        return f"Error processing file for {slug}.", 500

    return send_file(
        output_path,
        as_attachment=True,
        download_name=download_name,
        mimetype=mimetype,
    )

   