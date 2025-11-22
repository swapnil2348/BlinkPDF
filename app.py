import os
import uuid
import base64
import tempfile
import random
import requests
import json
import fitz  # PyMuPDF
from io import BytesIO

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


# --------------------------------------------------------------------
# AI TOOL LIST (5)
# --------------------------------------------------------------------

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


# --------------------------------------------------------------------
# BASIC PAGES
# --------------------------------------------------------------------
@app.route('/check-token')
def check_token():
    token = os.environ.get("HR_TOKEN")
    if token:
        return "✅ HR_TOKEN is working"
    else:
        return "❌ HR_TOKEN not found"

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/ai-tools")
def ai_tools_page():
    return render_template("ai_tools.html")


@app.route("/tool/<slug>")
def tool_page(slug):
    tool = next((t for t in TOOLS if t["slug"] == slug), None)
    if not tool:
        flash("Tool not found")
        return redirect(url_for("index"))
    return render_template("tool_page.html", tool=tool)


# Extra AI *page* routes so cards like /ai/chat-page work
@app.route("/ai/summarizer-page")
def ai_summarizer_page():
    return render_template("ai_summarizer.html")


@app.route("/ai/chat-page")
def ai_chat_page():
    return render_template("ai_chat.html")


@app.route("/ai/translate-page")
def ai_translate_page():
    return render_template("ai_translate.html")


@app.route("/ai/table-page")
def ai_table_page():
    return render_template("ai_table_extract.html")


# --------------------------------------------------------------------
# FILE UPLOAD HANDLER
# --------------------------------------------------------------------

ALLOWED_EXT = {"pdf", "png", "jpg", "jpeg", "docx", "xlsx", "pptx", "txt"}


def save_uploads(files):
    paths = []
    for f in files:
        if not f or not f.filename:
            continue
        fname = f"{uuid.uuid4().hex}_{secure_filename(f.filename)}"
        dest = os.path.join(UPLOAD_FOLDER, fname)
        f.save(dest)
        paths.append(dest)
    return paths


@app.route("/process/<slug>", methods=["POST"])
def process(slug):
    files = request.files.getlist("file")
    if not files:
        flash("Please upload at least one file")
        return redirect(url_for("tool_page", slug=slug))

    inputs = save_uploads(files)

    multi = {"merge-pdf", "image-to-pdf"}
    result = pdf.process(slug, inputs if slug in multi else inputs[0], PROCESSED_FOLDER)

    if isinstance(result, list):
        result = result[0]

    return send_file(result, as_attachment=True)


@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


# --------------------------------------------------------------------
# AI ROUTES (FULLY ONLINE WORKING)
# --------------------------------------------------------------------

@app.route("/ai/editor")
def ai_editor():
    return render_template("ai_editor.html")


@app.route("/ai/editor/upload", methods=["POST"])
def ai_editor_upload():
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "No file uploaded"}), 400

    filename = f"{uuid.uuid4().hex}_{secure_filename(f.filename)}"
    path = os.path.join(UPLOAD_FOLDER, filename)
    f.save(path)
    return jsonify({"url": url_for("uploaded_file", filename=filename)})


@app.route("/ai/summarizer", methods=["POST"])
def ai_summarizer():
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "No file uploaded"})

    import PyPDF2
    reader = PyPDF2.PdfReader(f)
    text = "".join([p.extract_text() or "" for p in reader.pages])

    summary = ask_ai(f"Summarize:\n{text[:6000]}", 300)
    return jsonify({"summary": summary})


# ================== AI CHAT ROUTES ==================

@app.route("/ai/chat/upload", methods=["POST"])
def ai_chat_upload():
    f = request.files.get("file")
    filename = f"{uuid.uuid4().hex}_{secure_filename(f.filename)}"
    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    f.save(path)
    return jsonify({"filepath": path})


@app.route("/ai/chat/ask", methods=["POST"])
def ai_chat_ask():
    data = request.get_json()
    question = data.get("question")
    file_path = data.get("file")

    import PyPDF2

    with open(file_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        text = "".join([p.extract_text() or "" for p in reader.pages])

    answer = ask_ai(f"Answer based on this PDF:\n{text[:7000]}\nQuestion: {question}")

    return jsonify({"answer": answer})



@app.route("/ai/translate", methods=["POST"])
def ai_translate():
    f = request.files.get("file")
    lang = request.form.get("language", "English")

    if not f:
        return jsonify({"error": "No file uploaded"})

    import PyPDF2
    reader = PyPDF2.PdfReader(f)
    text = "".join([p.extract_text() or "" for p in reader.pages])

    translated = ask_ai(f"Translate to {lang}:\n{text[:6000]}")
    return jsonify({"preview": translated})


@app.route("/ai/table-extract", methods=["POST"])
def ai_table_extract():
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "No file uploaded"})

    import PyPDF2
    reader = PyPDF2.PdfReader(f)
    text = "".join([p.extract_text() or "" for p in reader.pages])

    tables = ask_ai(f"Extract tables as CSV:\n{text[:6000]}")
    return jsonify({"tables": tables})

@app.route("/ai/real-replace", methods=["POST"])
def ai_real_replace():

    filename = request.form.get("filename")

    if not filename:
        return jsonify({"error": "Missing filename"}), 400

    source_path = os.path.join(UPLOAD_FOLDER, filename)

    if not os.path.exists(source_path):
        return jsonify({"error": "File not found on server"}), 404

    final_name = f"{uuid.uuid4().hex}_final.pdf"
    output_path = os.path.join(PROCESSED_FOLDER, final_name)

    # DEFAULT behavior since no user text input now
    find_text = "OLD TEXT"     # change later if needed
    replace_text = "NEW TEXT"

    # 1. REAL delete inside PDF
    redacted_file = pdf.redact_pdf(source_path, PROCESSED_FOLDER, {
        "text": find_text
    })

    # 2. REAL insert new text
    replaced_file = pdf.annotate_pdf(redacted_file, PROCESSED_FOLDER, {
        "text": replace_text,
        "x": 100,
        "y": 100,
        "size": 16
    })

    return send_file(replaced_file, as_attachment=True)
    
@app.route("/ai/apply-real-edits", methods=["POST"])
def apply_real_edits():
    import fitz, json, os, uuid
    from flask import request, send_file, jsonify

    filename = request.form.get("filename")
    edits_raw = request.form.get("edits")

    if not filename or not edits_raw:
        return jsonify({"error": "Missing data"}), 400

    edits = json.loads(edits_raw)

    source_path = os.path.join(UPLOAD_FOLDER, filename)

    if not os.path.exists(source_path):
        return jsonify({"error": "Source PDF not found"}), 404

    doc = fitz.open(source_path)

    for edit in edits:
        try:
            page_index = int(edit["page"]) - 1
            page = doc[page_index]

            r = edit["rect"]
            rect = fitz.Rect(r["x0"], r["y0"], r["x1"], r["y1"])

            # Remove original text
            page.add_redact_annot(rect, fill=(1, 1, 1))
            page.apply_redactions()

            # Insert new text
            page.insert_textbox(
                rect,
                edit["newText"],
                fontsize=edit.get("fontSize", 12),
                fontname="helv",
                color=(0, 0, 0)
            )

        except Exception as e:
            print("Edit error:", e)
            continue

    output_name = f"real_edit_{uuid.uuid4().hex}.pdf"
    output_path = os.path.join(PROCESSED_FOLDER, output_name)

    doc.save(output_path)
    doc.close()

    return send_file(output_path, as_attachment=True)
    
@app.route("/ai/upload-pdf", methods=["POST"])
def ai_upload_pdf():

    file = request.files.get("file")

    if not file:
        return {"success": False}, 400

    filename = f"{uuid.uuid4().hex}.pdf"
    save_path = os.path.join(UPLOAD_FOLDER, filename)

    file.save(save_path)

    return {
        "success": True,
        "filename": filename
    }

@app.route('/uploads/<path:filename>')
def serve_uploads(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)
   

# --------------------------------------------------------------------
@app.route("/health")
def health():
    return "BlinkPDF is running"
    
@app.route("/privacy")
def privacy():
    return render_template("privacy.html")

@app.route("/terms")
def terms():
    return render_template("terms.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")



if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
