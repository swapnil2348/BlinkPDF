import os
import uuid
import tempfile
import random
import requests
import json

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
from utils.pdf_processor import PDFProcessor, PDFProcessorError

import fitz  # PyMuPDF

# ---------------- AI CONFIG ----------------
HF_TOKEN = os.getenv("HF_TOKEN")


def ask_ai(prompt, max_tokens=500):
    if not HF_TOKEN:
        return "AI Error: HF_TOKEN is not configured on the server."

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

    try:
        response = requests.post(
            "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1",
            headers=headers,
            json=payload,
            timeout=60,
        )
    except Exception as e:
        return f"AI Error: {e}"

    if response.status_code != 200:
        return "AI Error: " + response.text

    result = response.json()
    # Some HF endpoints return list, some dict; handle both
    if isinstance(result, list) and result:
        return result[0].get("generated_text", "")
    if isinstance(result, dict) and "generated_text" in result:
        return result["generated_text"]
    return str(result)


# ---------------- APP SETUP ----------------

app = Flask(__name__)
app.secret_key = "dev-secret"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
PROCESSED_FOLDER = os.path.join(BASE_DIR, "processed")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["PROCESSED_FOLDER"] = PROCESSED_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024

tempfile.tempdir = os.path.abspath(UPLOAD_FOLDER)

pdf = PDFProcessor()

# ---------------- TOOLS ----------------

TOOLS = [
    {'slug': 'merge-pdf', 'title': 'Merge PDF', 'desc': 'Combine multiple PDF documents easily.', 'icon': 'merge-pdf.svg'},
    {'slug': 'split-pdf', 'title': 'Split PDF', 'desc': 'Extract or split PDF pages.', 'icon': 'split-pdf.svg'},
    {'slug': 'compress-pdf', 'title': 'Compress PDF', 'desc': 'Reduce PDF file size smartly.', 'icon': 'compress-pdf.svg'},
    {'slug': 'optimize-pdf', 'title': 'Optimize PDF', 'desc': 'Advanced cleaning and optimization.', 'icon': 'optimize-pdf.svg'},
    {'slug': 'rotate-pdf', 'title': 'Rotate PDF', 'desc': 'Rotate pages of your PDF.', 'icon': 'rotate-pdf.svg'},
    {'slug': 'watermark-pdf', 'title': 'Watermark PDF', 'desc': 'Add watermark text or image.', 'icon': 'watermark-pdf.svg'},
    {'slug': 'number-pdf', 'title': 'Number Pages', 'desc': 'Add page numbers anywhere.', 'icon': 'number-pdf.svg'},
    {'slug': 'protect-pdf', 'title': 'Protect PDF', 'desc': 'Encrypt with password.', 'icon': 'protect-pdf.svg'},
    {'slug': 'unlock-pdf', 'title': 'Unlock PDF', 'desc': 'Remove password restrictions.', 'icon': 'unlock-pdf.svg'},
    {'slug': 'repair-pdf', 'title': 'Repair PDF', 'desc': 'Fix damaged or corrupted PDFs.', 'icon': 'repair-pdf.svg'},
    {'slug': 'organize-pdf', 'title': 'Organize PDF', 'desc': 'Reorder, delete, rotate pages visually.', 'icon': 'organize-pdf.svg'},
    {'slug': 'sign-pdf', 'title': 'Sign PDF', 'desc': 'Add digital signatures or images.', 'icon': 'sign-pdf.svg'},
    {'slug': 'annotate-pdf', 'title': 'Annotate PDF', 'desc': 'Highlight, underline or comment.', 'icon': 'annotate-pdf.svg'},
    {'slug': 'redact-pdf', 'title': 'Redact PDF', 'desc': 'Blackout sensitive information.', 'icon': 'redact-pdf.svg'},
    {'slug': 'pdf-to-word', 'title': 'PDF to Word', 'desc': 'Convert PDF into editable Word documents.', 'icon': 'pdf-to-word.svg'},
    {'slug': 'word-to-pdf', 'title': 'Word to PDF', 'desc': 'Convert DOC/DOCX to PDF.', 'icon': 'word-to-pdf.svg'},
    {'slug': 'pdf-to-image', 'title': 'PDF to Image', 'desc': 'Convert PDF pages to images.', 'icon': 'pdf-to-image.svg'},
    {'slug': 'image-to-pdf', 'title': 'Image to PDF', 'desc': 'Merge images into a PDF.', 'icon': 'image-to-pdf.svg'},
    {'slug': 'pdf-to-excel', 'title': 'PDF to Excel', 'desc': 'Extract tables into Excel.', 'icon': 'pdf-to-excel.svg'},
    {'slug': 'excel-to-pdf', 'title': 'Excel to PDF', 'desc': 'Convert spreadsheets to PDF.', 'icon': 'excel-to-pdf.svg'},
    {'slug': 'pdf-to-powerpoint', 'title': 'PDF to PowerPoint', 'desc': 'Convert PDF pages into PPTX slides.', 'icon': 'pdf-to-powerpoint.svg'},
    {'slug': 'powerpoint-to-pdf', 'title': 'PowerPoint to PDF', 'desc': 'Convert PPTX files to PDF.', 'icon': 'powerpoint-to-pdf.svg'},
    {'slug': 'ocr-pdf', 'title': 'OCR PDF', 'desc': 'Convert scanned PDFs into searchable text.', 'icon': 'ocr-pdf.svg'},
    {'slug': 'extract-text', 'title': 'Extract Text', 'desc': 'Extract plain text from PDF.', 'icon': 'extract-text.svg'},
    {'slug': 'extract-images', 'title': 'Extract Images', 'desc': 'Extract embedded images from PDF.', 'icon': 'extract-images.svg'},
    {'slug': 'deskew-pdf', 'title': 'Deskew PDF', 'desc': 'Auto-straighten scanned pages.', 'icon': 'deskew-pdf.svg'},
    {'slug': 'crop-pdf', 'title': 'Crop PDF', 'desc': 'Crop pages.', 'icon': 'crop-pdf.svg'},
    {'slug': 'resize-pdf', 'title': 'Resize PDF', 'desc': 'Change page size.', 'icon': 'resize-pdf.svg'},
    {'slug': 'flatten-pdf', 'title': 'Flatten PDF', 'desc': 'Flatten forms.', 'icon': 'flatten-pdf.svg'},
    {'slug': 'metadata-editor', 'title': 'Metadata Editor', 'desc': 'Edit metadata.', 'icon': 'metadata-editor.svg'},
    {'slug': 'fill-forms', 'title': 'Fill PDF Forms', 'desc': 'Fill PDF fields.', 'icon': 'fill-forms.svg'},
    {'slug': 'background-remover', 'title': 'Remove Background', 'desc': 'Remove background.', 'icon': 'background-remover.svg'}
]

AI_TOOLS = [
    {"slug": "ai-editor", "title": "AI PDF Editor", "desc": "Live editor", "url": "/ai/editor", "icon": "ai-editor.svg"},
    {"slug": "ai-summarizer", "title": "AI Summarizer", "desc": "Smart summary", "url": "/ai/summarizer-page", "icon": "ai-summarizer.svg"},
    {"slug": "ai-chat", "title": "Chat with PDF", "desc": "Ask questions", "url": "/ai/chat-page", "icon": "ai-chat.svg"},
    {"slug": "ai-translate", "title": "AI Translator", "desc": "Translate text", "url": "/ai/translate-page", "icon": "ai-translate.svg"},
    {"slug": "ai-table-extract", "title": "AI Table Extractor", "desc": "Extract tables", "url": "/ai/table-page", "icon": "ai-table.svg"}
]


def get_random_tools(n=10):
    combined = TOOLS + AI_TOOLS
    return random.sample(combined, min(n, len(combined)))


@app.context_processor
def inject_globals():
    return dict(tools=TOOLS, ai_tools=AI_TOOLS, random_tools=get_random_tools(10))


# ---------------- BASIC PAGES ----------------

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


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/tool/<slug>")
def tool_page(slug):
    tool = next((t for t in TOOLS if t["slug"] == slug), None)
    if not tool:
        flash("Tool not found", "error")
        return redirect(url_for("index"))
    return render_template("tool_page.html", tool=tool)


# Google verification
@app.route('/googlefe495bc7600f4865.html')
def google_verify():
    return send_from_directory(
        os.path.dirname(os.path.abspath(__file__)),
        'googlefe495bc7600f4865.html'
    )


# ---------------- MAIN PROCESS ROUTE FOR ALL TOOLS ----------------

@app.route("/process/<slug>", methods=["POST"])
def process_tool(slug):
    tool = next((t for t in TOOLS if t["slug"] == slug), None)
    if not tool:
        flash("Tool not found", "error")
        return redirect(url_for("index"))

    # Collect uploaded files: support "file" and "files"
    files = []
    if "files" in request.files:
        files.extend(request.files.getlist("files"))
    if "file" in request.files:
        f = request.files["file"]
        if f.filename:
            files.append(f)

    if not files:
        flash("Please upload at least one file.", "error")
        return redirect(url_for("tool_page", slug=slug))

    saved_paths = []
    for f in files:
        filename = secure_filename(f.filename)
        if not filename:
            continue
        unique_name = f"{uuid.uuid4().hex}_{filename}"
        save_path = os.path.join(UPLOAD_FOLDER, unique_name)
        f.save(save_path)
        saved_paths.append(save_path)

    if not saved_paths:
        flash("No valid files uploaded.", "error")
        return redirect(url_for("tool_page", slug=slug))

    # Collect advanced options: pass everything except file fields
    options = {k: v for k, v in request.form.items() if v not in ("", None)}

    # Special case: signature image for sign-pdf
    if slug == "sign-pdf" and "signature" in request.files:
        sig_file = request.files["signature"]
        if sig_file.filename:
            sig_name = secure_filename(sig_file.filename)
            sig_path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4().hex}_{sig_name}")
            sig_file.save(sig_path)
            options["signature_path"] = sig_path

    try:
        output_path, download_name, mimetype = pdf.process(slug, saved_paths, options)
    except PDFProcessorError as e:
        # For AJAX requests, it's nice to return JSON error, but your current
        # template probably expects a direct file response, so we flash + redirect.
        flash(str(e), "error")
        return redirect(url_for("tool_page", slug=slug))
    except Exception as e:
        flash(f"Unexpected error: {e}", "error")
        return redirect(url_for("tool_page", slug=slug))

    return send_file(
        output_path,
        mimetype=mimetype,
        as_attachment=True,
        download_name=download_name,
    )


# ---------------- AI TOOL PAGES ----------------

@app.route("/ai/editor")
def ai_editor_page():
    return render_template("ai_editor.html")


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
    return render_template("ai_table.html")


# ---------------- AI API ENDPOINTS ----------------

def extract_text_from_pdf(path: str, max_chars: int = 6000) -> str:
    doc = fitz.open(path)
    texts = []
    for page in doc:
        texts.append(page.get_text())
        if len("".join(texts)) > max_chars:
            break
    doc.close()
    return "".join(texts)[:max_chars]


@app.route("/api/ai/summarize", methods=["POST"])
def api_ai_summarize():
    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify({"error": "No file provided"}), 400

    filename = secure_filename(file.filename)
    path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4().hex}_{filename}")
    file.save(path)

    text = extract_text_from_pdf(path)
    prompt = (
        "Summarize the following PDF content in clear bullet points:\n\n" + text
    )
    answer = ask_ai(prompt, max_tokens=400)
    return jsonify({"summary": answer})


@app.route("/api/ai/chat", methods=["POST"])
def api_ai_chat():
    file = request.files.get("file")
    question = request.form.get("question", "").strip()

    if not question:
        return jsonify({"error": "Question is required"}), 400
    if not file or not file.filename:
        return jsonify({"error": "PDF file is required"}), 400

    filename = secure_filename(file.filename)
    path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4().hex}_{filename}")
    file.save(path)

    text = extract_text_from_pdf(path)
    prompt = (
        "You are a helpful assistant answering questions about a PDF document.\n"
        "Here is the content (truncated if long):\n\n"
        f"{text}\n\n"
        f"Question: {question}\n\n"
        "Answer clearly and concisely based only on the PDF content above."
    )
    answer = ask_ai(prompt, max_tokens=500)
    return jsonify({"answer": answer})


@app.route("/api/ai/translate", methods=["POST"])
def api_ai_translate():
    text = request.form.get("text", "").strip()
    target_lang = request.form.get("target_lang", "en")
    if not text:
        return jsonify({"error": "Text is required"}), 400

    prompt = (
        f"Translate the following text into {target_lang} and only output the translation:\n\n{text}"
    )
    answer = ask_ai(prompt, max_tokens=500)
    return jsonify({"translation": answer})


@app.route("/api/ai/table-extract", methods=["POST"])
def api_ai_table_extract():
    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify({"error": "PDF file is required"}), 400

    filename = secure_filename(file.filename)
    path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4().hex}_{filename}")
    file.save(path)

    text = extract_text_from_pdf(path)
    prompt = (
        "Extract any tabular data from the following PDF text. "
        "Return it as a clean markdown table:\n\n" + text
    )
    answer = ask_ai(prompt, max_tokens=600)
    return jsonify({"table_markdown": answer})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
