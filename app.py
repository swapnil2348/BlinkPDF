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


# --------------------------------------------------------------------
# AI CONFIG (HUGGINGFACE MISTRAL)
# --------------------------------------------------------------------

# Prefer HR_TOKEN (your Render env), fallback to HF_TOKEN
HF_TOKEN = os.getenv("HR_TOKEN") or os.getenv("HF_TOKEN")


def ask_ai(prompt, max_tokens=500):
    if not HF_TOKEN:
        return "AI Error: API token not configured (HR_TOKEN / HF_TOKEN)."

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
        timeout=60,
    )

    if response.status_code != 200:
        return "AI Error: " + response.text

    result = response.json()
    try:
        return result[0]["generated_text"]
    except Exception:
        return "AI Error: Unexpected response format."


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
# BASIC PAGES + HEALTH + TOKEN CHECK
# --------------------------------------------------------------------

@app.route("/check-token")
def check_token():
    token = os.environ.get("HR_TOKEN") or os.environ.get("HF_TOKEN")
    if token:
        return "✅ HF/HR token is configured"
    else:
        return "❌ HR_TOKEN / HF_TOKEN not found"


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


# AI pages (UI only - cards on homepage)
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


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/health")
def health():
    return "BlinkPDF is running"


# Google Search Console verification file
@app.route('/googlefe495bc7600f4865.html')
def google_verify():
    # Make sure googlefe495bc7600f4865.html is in the project root folder
    return send_from_directory(
        os.path.dirname(os.path.abspath(__file__)),
        'googlefe495bc7600f4865.html'
    )


# --------------------------------------------------------------------
# FILE UPLOAD + MAIN PROCESS ROUTE
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

    # tools that accept multi-file input (list)
    multi = {"merge-pdf", "image-to-pdf"}
    input_arg = inputs if slug in multi else inputs[0]

    # This calls your real backend logic in utils/pdf_processor.PDFProcessor
    result = pdf.process(slug, input_arg, PROCESSED_FOLDER)

    # In some cases PDFProcessor may return a list of paths
    if isinstance(result, list):
        result = result[0]

    return send_file(result, as_attachment=True)


# unified /uploads route
@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


# Backwards compatible alias, in case some JS uses url_for("serve_uploads")
serve_uploads = uploaded_file


# --------------------------------------------------------------------
# AI ROUTES (REAL BACKEND, NOT FAKE)
# --------------------------------------------------------------------

# ------- AI Editor main page -------
@app.route("/ai/editor")
def ai_editor():
    return render_template("ai_editor.html")


# Used by AI Editor to get a URL for pdf.js
@app.route("/ai/editor/upload", methods=["POST"])
def ai_editor_upload():
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "No file uploaded"}), 400

    filename = f"{uuid.uuid4().hex}_{secure_filename(f.filename)}"
    path = os.path.join(UPLOAD_FOLDER, filename)
    f.save(path)
    return jsonify({"url": url_for("uploaded_file", filename=filename)})


# Alternative upload API used by some JS flows
@app.route("/ai/upload-pdf", methods=["POST"])
def ai_upload_pdf():
    file = request.files.get("file")
    if not file:
        return jsonify({"success": False, "error": "No file uploaded"}), 400

    filename = f"{uuid.uuid4().hex}.pdf"
    save_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(save_path)

    return jsonify({"success": True, "filename": filename})


# ------- AI Summarizer backend -------
@app.route("/ai/summarizer", methods=["POST"])
def ai_summarizer():
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "No file uploaded"})

    import PyPDF2
    reader = PyPDF2.PdfReader(f)
    text = "".join([p.extract_text() or "" for p in reader.pages])

    summary = ask_ai(f"Summarize the following PDF content:\n\n{text[:6000]}", 300)
    return jsonify({"summary": summary})


# ------- AI Chat with PDF backend -------
@app.route("/ai/chat/upload", methods=["POST"])
def ai_chat_upload():
    f = request.files.get("file")
    if not f or not f.filename:
        return jsonify({"error": "No file uploaded"}), 400

    filename = f"{uuid.uuid4().hex}_{secure_filename(f.filename)}"
    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    f.save(path)
    return jsonify({"filepath": path})


@app.route("/ai/chat/ask", methods=["POST"])
def ai_chat_ask():
    data = request.get_json() or {}
    question = data.get("question")
    file_path = data.get("file")

    if not question or not file_path:
        return jsonify({"error": "Missing question or file path"}), 400

    import PyPDF2

    with open(file_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        text = "".join([p.extract_text() or "" for p in reader.pages])

    answer = ask_ai(
        f"Answer this question based only on the PDF content below.\n\n"
        f"PDF CONTENT:\n{text[:7000]}\n\n"
        f"QUESTION: {question}\n\n"
        "If the answer is not clearly in the text, say you are not sure."
    )

    return jsonify({"answer": answer})


# ------- AI Translate backend -------
@app.route("/ai/translate", methods=["POST"])
def ai_translate():
    f = request.files.get("file")
    lang = request.form.get("language", "English")

    if not f:
        return jsonify({"error": "No file uploaded"})

    import PyPDF2
    reader = PyPDF2.PdfReader(f)
    text = "".join([p.extract_text() or "" for p in reader.pages])

    translated = ask_ai(f"Translate the following text into {lang}:\n\n{text[:6000]}")
    return jsonify({"preview": translated})


# ------- AI Table Extract backend -------
@app.route("/ai/table-extract", methods=["POST"])
def ai_table_extract():
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "No file uploaded"})

    import PyPDF2
    reader = PyPDF2.PdfReader(f)
    text = "".join([p.extract_text() or "" for p in reader.pages])

    tables = ask_ai(
        "Extract all tabular data from this PDF text and output as CSV-like tables:\n\n"
        f"{text[:6000]}"
    )
    return jsonify({"tables": tables})


# ------- AI Real Replace / Apply Real Edits (for AI Editor) -------
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

    # Placeholder real edit – you can evolve this later using AI instructions
    find_text = "OLD TEXT"
    replace_text = "NEW TEXT"

    # Real delete of text
    redacted_file = pdf.redact_pdf(source_path, PROCESSED_FOLDER, {
        "text": find_text
    })

    # Real insert of new text
    replaced_file = pdf.annotate_pdf(redacted_file, PROCESSED_FOLDER, {
        "text": replace_text,
        "x": 100,
        "y": 100,
        "size": 16
    })

    return send_file(replaced_file, as_attachment=True)


@app.route("/ai/apply-real-edits", methods=["POST"])
def apply_real_edits():
    filename = request.form.get("filename")
    edits_raw = request.form.get("edits")

    if not filename or not edits_raw:
        return jsonify({"error": "Missing data"}), 400

    try:
        edits = json.loads(edits_raw)
    except Exception:
        return jsonify({"error": "Invalid edits JSON"}), 400

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
    
@app.route("/process/<slug>", methods=["POST"])
def process_tool(slug):

    uploaded_files = request.files.getlist("file")

    if not uploaded_files or uploaded_files[0].filename == "":
        return jsonify({"error": "No file uploaded"}), 400

    file_paths = []

    for file in uploaded_files:
        filename = secure_filename(file.filename)
        unique_name = f"{uuid.uuid4()}_{filename}"
        input_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
        file.save(input_path)
        file_paths.append(input_path)

    output_name = f"{slug}_{uuid.uuid4()}.pdf"
    output_path = os.path.join(app.config["PROCESSED_FOLDER"], output_name)

    try:

        # MERGE
        if slug == "merge-pdf":
            pdf.merge(file_paths, output_path)

        # SPLIT
        elif slug == "split-pdf":
            pages = request.form.get("pages")
            pdf.split(file_paths[0], output_path, pages)

        # COMPRESS
        elif slug == "compress-pdf":
            level = request.form.get("level", "medium")
            pdf.compress(file_paths[0], output_path, level)

        # ROTATE
        elif slug == "rotate-pdf":
            angle = int(request.form.get("angle", 90))
            pdf.rotate(file_paths[0], output_path, angle)

        # WATERMARK
        elif slug == "watermark-pdf":
            text = request.form.get("text", "")
            x = int(request.form.get("x", 50))
            y = int(request.form.get("y", 100))
            size = int(request.form.get("size", 24))
            pdf.watermark(file_paths[0], output_path, text, x, y, size)

        # PAGE NUMBERS
        elif slug == "number-pdf":
            start = int(request.form.get("start", 1))
            pdf.number(file_paths[0], output_path, start)

        # PROTECT
        elif slug == "protect-pdf":
            password = request.form.get("password")
            pdf.protect(file_paths[0], output_path, password)

        # UNLOCK
        elif slug == "unlock-pdf":
            password = request.form.get("password")
            pdf.unlock(file_paths[0], output_path, password)

        # EXTRACT TEXT
        elif slug == "extract-text":
            text_file = pdf.extract_text(file_paths[0])
            return send_file(text_file, as_attachment=True)

        # EXTRACT IMAGES
        elif slug == "extract-images":
            zip_path = pdf.extract_images(file_paths[0])
            return send_file(zip_path, as_attachment=True)

        # CROP
        elif slug == "crop-pdf":
            width = int(request.form.get("width"))
            height = int(request.form.get("height"))
            pdf.crop(file_paths[0], output_path, width, height)

        # RESIZE
        elif slug == "resize-pdf":
            width = int(request.form.get("width"))
            height = int(request.form.get("height"))
            pdf.resize(file_paths[0], output_path, width, height)

        # CLEAN / OPTIMIZE
        elif slug == "optimize-pdf":
            pdf.optimize(file_paths[0], output_path)

        # METADATA
        elif slug == "metadata-editor":
            title = request.form.get("title")
            author = request.form.get("author")
            subject = request.form.get("subject")
            pdf.edit_metadata(file_paths[0], output_path, title, author, subject)

        # FLATTEN
        elif slug == "flatten-pdf":
            pdf.flatten(file_paths[0], output_path)

        # REPAIR
        elif slug == "repair-pdf":
            pdf.repair(file_paths[0], output_path)

        else:
            return jsonify({"error": "Tool not implemented yet"}), 400

        return send_file(output_path, as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)})

# --------------------------------------------------------------------
# MAIN ENTRYPOINT
# --------------------------------------------------------------------

if __name__ == "__main__":
    # For local testing; Render will run with gunicorn
    app.run(debug=True, host="0.0.0.0", port=5000)
