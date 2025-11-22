import os
import uuid
import base64
import tempfile
import random
import requests
import json
import fitz  # PyMuPDF
from io import BytesIO
from flask import Flask, render_template
from flask import (
    Flask,
    render_template,
    request,
    send_file,
    redirect,
    url_for,
    flash,
    jsonify,
    send_from_directory,
)
from werkzeug.utils import secure_filename

from utils.pdf_processor import PDFProcessor


# ---------------- AI CONFIG (NEW - MISTRAL ONLINE) ----------------

# IMPORTANT: for safety, I removed your real token.
# Put your own token string here, like: "hf_xxxxx..."
HF_TOKEN = os.getenv("HF_TOKEN")


def ask_ai(prompt, max_tokens=500):
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}"
    }

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": max_tokens,
            "temperature": 0.7,
            "do_sample": True,
        },
    }

    response = requests.post(
        "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1",
        headers=headers,
        json=payload,
    )

    if response.status_code != 200:
        return "AI Error: " + response.text

    result = response.json()
    return result[0]["generated_text"]


# --------------------------------------------------------------------
# BASIC APP SETUP
# --------------------------------------------------------------------

app = Flask(__name__)
app.secret_key = "dev-secret"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
PROCESSED_FOLDER = os.path.join(BASE_DIR, "processed")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["PROCESSED_FOLDER"] = PROCESSED_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024  # 500 MB

tempfile.tempdir = os.path.abspath(UPLOAD_FOLDER)

pdf = PDFProcessor()


# --------------------------------------------------------------------
# MAIN TOOL LIST (33 TOOLS)
# --------------------------------------------------------------------

TOOLS = [
    {'slug': 'merge-pdf', 'title': 'Merge PDF',
     'desc': 'Combine multiple PDF documents easily.', 'icon': 'merge-pdf.svg'},
    {'slug': 'split-pdf', 'title': 'Split PDF',
     'desc': 'Extract or split PDF pages.', 'icon': 'split-pdf.svg'},
    {'slug': 'compress-pdf', 'title': 'Compress PDF',
     'desc': 'Reduce PDF file size smartly.', 'icon': 'compress-pdf.svg'},
    {'slug': 'optimize-pdf', 'title': 'Optimize PDF',
     'desc': 'Advanced cleaning and optimization.', 'icon': 'optimize-pdf.svg'},
    {'slug': 'rotate-pdf', 'title': 'Rotate PDF',
     'desc': 'Rotate pages of your PDF.', 'icon': 'rotate-pdf.svg'},
    {'slug': 'watermark-pdf', 'title': 'Watermark PDF',
     'desc': 'Add watermark text or image.', 'icon': 'watermark-pdf.svg'},
    {'slug': 'number-pdf', 'title': 'Number Pages',
     'desc': 'Add page numbers anywhere.', 'icon': 'number-pdf.svg'},
    {'slug': 'protect-pdf', 'title': 'Protect PDF',
     'desc': 'Encrypt with password.', 'icon': 'protect-pdf.svg'},
    {'slug': 'unlock-pdf', 'title': 'Unlock PDF',
     'desc': 'Remove password restrictions.', 'icon': 'unlock-pdf.svg'},
    {'slug': 'repair-pdf', 'title': 'Repair PDF',
     'desc': 'Fix damaged or corrupted PDFs.', 'icon': 'repair-pdf.svg'},
    {'slug': 'organize-pdf', 'title': 'Organize PDF',
     'desc': 'Reorder, delete, rotate pages visually.', 'icon': 'organize-pdf.svg'},
    {'slug': 'sign-pdf', 'title': 'Sign PDF',
     'desc': 'Add digital signatures or images.', 'icon': 'sign-pdf.svg'},
    {'slug': 'annotate-pdf', 'title': 'Annotate PDF',
     'desc': 'Highlight, underline or comment.', 'icon': 'annotate-pdf.svg'},
    {'slug': 'redact-pdf', 'title': 'Redact PDF',
     'desc': 'Blackout sensitive information.', 'icon': 'redact-pdf.svg'},
    {'slug': 'pdf-to-word', 'title': 'PDF to Word',
     'desc': 'Convert PDF into editable Word documents.', 'icon': 'pdf-to-word.svg'},
    {'slug': 'word-to-pdf', 'title': 'Word to PDF',
     'desc': 'Convert DOC/DOCX to PDF.', 'icon': 'word-to-pdf.svg'},
    {'slug': 'pdf-to-image', 'title': 'PDF to Image',
     'desc': 'Convert PDF pages to images.', 'icon': 'pdf-to-image.svg'},
    {'slug': 'image-to-pdf', 'title': 'Image to PDF',
     'desc': 'Merge images into a PDF.', 'icon': 'image-to-pdf.svg'},
    {'slug': 'pdf-to-excel', 'title': 'PDF to Excel',
     'desc': 'Extract tables into Excel.', 'icon': 'pdf-to-excel.svg'},
    {'slug': 'excel-to-pdf', 'title': 'Excel to PDF',
     'desc': 'Convert spreadsheets to PDF.', 'icon': 'excel-to-pdf.svg'},
    {'slug': 'pdf-to-powerpoint', 'title': 'PDF to PowerPoint',
     'desc': 'Convert PDF pages into PPTX slides.', 'icon': 'pdf-to-powerpoint.svg'},
    {'slug': 'powerpoint-to-pdf', 'title': 'PowerPoint to PDF',
     'desc': 'Convert PPTX files to PDF.', 'icon': 'powerpoint-to-pdf.svg'},
    {'slug': 'ocr-pdf', 'title': 'OCR PDF',
     'desc': 'Convert scanned PDFs into searchable text.', 'icon': 'ocr-pdf.svg'},
    {'slug': 'extract-text', 'title': 'Extract Text',
     'desc': 'Extract plain text or OCR text from PDF.', 'icon': 'extract-text.svg'},
    {'slug': 'extract-images', 'title': 'Extract Images',
     'desc': 'Extract embedded images from PDF.', 'icon': 'extract-images.svg'},
    {'slug': 'deskew-pdf', 'title': 'Deskew PDF',
     'desc': 'Auto-straighten scanned pages.', 'icon': 'deskew-pdf.svg'},
    {'slug': 'crop-pdf', 'title': 'Crop PDF',
     'desc': 'Crop pages with custom controls.', 'icon': 'crop-pdf.svg'},
    {'slug': 'resize-pdf', 'title': 'Resize PDF',
     'desc': 'Change page dimensions or scale.', 'icon': 'resize-pdf.svg'},
    {'slug': 'flatten-pdf', 'title': 'Flatten PDF',
     'desc': 'Flatten forms and annotations.', 'icon': 'flatten-pdf.svg'},
    {'slug': 'metadata-editor', 'title': 'Metadata Editor',
     'desc': 'Edit title, author, keywords and other metadata.', 'icon': 'metadata-editor.svg'},
    {'slug': 'fill-forms', 'title': 'Fill PDF Forms',
     'desc': 'Fill interactive PDF fields easily.', 'icon': 'fill-forms.svg'},
    {'slug': 'background-remover', 'title': 'Remove Background',
     'desc': 'Remove noisy backgrounds from scanned pages.', 'icon': 'background-remover.svg'},
]

AI_TOOLS = [
    {"slug": "ai-editor", "title": "AI PDF Editor", "desc": "Live editor",
     "url": "/ai/editor", "icon": "ai-editor.svg"},
    {"slug": "ai-summarizer", "title": "AI Summarizer", "desc": "Smart summary",
     "url": "/ai/summarizer-page", "icon": "ai-summarizer.svg"},
    {"slug": "ai-chat", "title": "Chat with PDF", "desc": "Ask questions",
     "url": "/ai/chat-page", "icon": "ai-chat.svg"},
    {"slug": "ai-translate", "title": "AI Translator", "desc": "Translate text",
     "url": "/ai/translate-page", "icon": "ai-translate.svg"},
    {"slug": "ai-table-extract", "title": "AI Table Extractor", "desc": "Extract tables",
     "url": "/ai/table-page", "icon": "ai-table.svg"},
]


def get_random_tools(n=10):
    combined = TOOLS + AI_TOOLS
    return random.sample(combined, min(n, len(combined)))


@app.context_processor
def inject_globals():
    return dict(tools=TOOLS, ai_tools=AI_TOOLS, random_tools=get_random_tools(10))


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/ai-tools")
def ai_tools_page():
    return render_template("ai_tools.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/tool/<slug>")
def tool_page(slug):
    tool = next((t for t in TOOLS if t["slug"] == slug), None)
    if not tool:
        flash("Tool not found")
        return redirect(url_for("index"))
    return render_template("tool_page.html", tool=tool)
    
@app.route('/googlefe495bc7600f4865.html')
def google_verify():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'googlefe495bc7600f4865.html')


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
