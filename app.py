from flask import Flask, render_template, request, send_file, abort, jsonify
import os
import uuid
from werkzeug.utils import secure_filename

import fitz  # PyMuPDF
from PyPDF2 import PdfReader, PdfWriter
from PIL import Image
from docx import Document
from pptx import Presentation
from reportlab.pdfgen import canvas
from pdf_processor import PDFProcessor

# -------------------
# APP INIT (FIXED)
# -------------------
app = Flask(__name__)

from werkzeug.exceptions import RequestEntityTooLarge

app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024

@app.errorhandler(RequestEntityTooLarge)
def file_too_large(e):
    return "File too large. Maximum allowed: 500MB", 413
    
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "outputs")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["OUTPUT_FOLDER"] = OUTPUT_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024  # 500MB

# ✅ FIXED CONSTRUCTOR CALL
pdf_processor = PDFProcessor(OUTPUT_FOLDER)

# --------------------------------------------------------------------
# FULL TOOL LIST (33 NORMAL TOOLS)
# --------------------------------------------------------------------
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
    {'slug': 'background-remover', 'title': 'Remove Background', 'icon': 'background-remover.svg'}
]

# --------------------------------------------------------------------
# AI TOOL LIST
# --------------------------------------------------------------------
AI_TOOLS = [
    {"slug": "ai-editor", "title": "AI PDF Editor", "url": "/ai/editor"},
    {"slug": "ai-summarizer", "title": "AI Summarizer", "url": "/ai/summarizer-page"},
    {"slug": "ai-chat", "title": "Chat with PDF", "url": "/ai/chat-page"},
    {"slug": "ai-translate", "title": "AI Translator", "url": "/ai/translate-page"},
    {"slug": "ai-table-extract", "title": "AI Table Extractor", "url": "/ai/table-page"},
]

SLUG_TO_TOOL = {tool["slug"]: tool for tool in TOOLS}

# ✅ FIX SLUG MISMATCHES
SLUG_ALIASES = {
    "pdf-to-jpg": "pdf-to-image",
    "jpg-to-pdf": "image-to-pdf",
    "pdf-to-ppt": "pdf-to-powerpoint",
    "ppt-to-pdf": "powerpoint-to-pdf"
}

# --------------------------------------------------------------------
# ROUTES
# --------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html", tools=TOOLS, ai_tools=AI_TOOLS)

@app.route("/ai-tools")
def ai_tools_page():
    return render_template("tool_page.html", tools=AI_TOOLS)
    
@app.route("/privacy")
def privacy():
    return render_template("privacy.html")

@app.route("/terms")
def terms():
    return render_template("terms.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/tool/<slug>")
def tool_page(slug):
    tool = SLUG_TO_TOOL.get(slug)
    if not tool:
        abort(404)
    return render_template("tool_page.html", tool=tool)


@app.route("/process/<tool_slug>", methods=["POST"])
def process_tool(tool_slug):
    tool_slug = SLUG_ALIASES.get(tool_slug, tool_slug)

    if tool_slug not in SLUG_TO_TOOL:
        return jsonify({"error": "Tool not found"}), 404

    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    filename = secure_filename(file.filename)
    unique_id = str(uuid.uuid4())

    input_path = os.path.join(UPLOAD_FOLDER, f"{unique_id}_{filename}")
    output_filename = f"BlinkPDF_{tool_slug}_{unique_id}.pdf"
    output_path = os.path.join(OUTPUT_FOLDER, output_filename)

    file.save(input_path)

    options = dict(request.form)

    ok = pdf_processor.process(tool_slug, input_path, output_path, options)

    if not ok or not os.path.exists(output_path):
        return jsonify({"error": "Processing failed"}), 500

    return send_file(
        output_path,
        as_attachment=True,
        download_name=output_filename
    )


# -----------------------------
# DOWNLOAD DIRECT
# -----------------------------
@app.route("/download/<filename>")
def download(filename):
    file_path = os.path.join(OUTPUT_FOLDER, filename)
    if not os.path.exists(file_path):
        abort(404)
    return send_file(file_path, as_attachment=True)


# -----------------------------
# HEALTH CHECK
# -----------------------------
@app.route("/health")
def health():
    return {"status": "OK"}


if __name__ == "__main__":
    app.run(debug=True)
