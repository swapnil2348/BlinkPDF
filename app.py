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
from utils.pdf_processor import PDFProcessor, PDFProcessorError

# ---------------- AI CONFIG (MISTRAL HF) ----------------

HF_TOKEN = os.getenv("HF_TOKEN")


def ask_ai(prompt, max_tokens=500):
    """
    Simple wrapper around HF Inference API.
    """
    if not HF_TOKEN:
        return "AI Error: HF_TOKEN not configured on server."

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
        resp = requests.post(
            "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1",
            headers=headers,
            json=payload,
            timeout=60,
        )
    except Exception as e:
        return f"AI Error: {e}"

    if resp.status_code != 200:
        return "AI Error: " + resp.text

    try:
        data = resp.json()
        return data[0]["generated_text"]
    except Exception:
        return str(resp.text)


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
     'desc': 'Extract plain text from PDF.', 'icon': 'extract-text.svg'},
    {'slug': 'extract-images', 'title': 'Extract Images',
     'desc': 'Extract embedded images from PDF.', 'icon': 'extract-images.svg'},
    {'slug': 'deskew-pdf', 'title': 'Deskew PDF',
     'desc': 'Auto-straighten scanned pages.', 'icon': 'deskew-pdf.svg'},
    {'slug': 'crop-pdf', 'title': 'Crop PDF',
     'desc': 'Crop pages.', 'icon': 'crop-pdf.svg'},
    {'slug': 'resize-pdf', 'title': 'Resize PDF',
     'desc': 'Change page size.', 'icon': 'resize-pdf.svg'},
    {'slug': 'flatten-pdf', 'title': 'Flatten PDF',
     'desc': 'Flatten forms.', 'icon': 'flatten-pdf.svg'},
    {'slug': 'metadata-editor', 'title': 'Metadata Editor',
     'desc': 'Edit metadata.', 'icon': 'metadata-editor.svg'},
    {'slug': 'fill-forms', 'title': 'Fill PDF Forms',
     'desc': 'Fill PDF fields.', 'icon': 'fill-forms.svg'},
    {'slug': 'background-remover', 'title': 'Remove Background',
     'desc': 'Remove background.', 'icon': 'background-remover.svg'},
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
        flash("Tool not found")
        return redirect(url_for("index"))
    return render_template("tool_page.html", tool=tool)


# Extra AI *page* routes for cards like /ai/chat-page
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


# Google verification (Search Console)
@app.route('/googlefe495bc7600f4865.html')
def google_verify():
    return send_from_directory(
        os.path.dirname(os.path.abspath(__file__)),
        'googlefe495bc7600f4865.html'
    )


# --------------------------------------------------------------------
# PRO++ TOOL PIPELINE (BACKEND FOR tool_page.html)
# --------------------------------------------------------------------

def _save_uploads(files):
    """Save uploaded FileStorage list to disk and return list of paths."""
    paths = []
    for f in files:
        if not f or not f.filename:
            continue
        filename = secure_filename(f.filename)
        if not filename:
            continue
        uid = uuid.uuid4().hex[:8]
        full_path = os.path.join(UPLOAD_FOLDER, f"{uid}_{filename}")
        f.save(full_path)
        paths.append(full_path)
    return paths


def _map_options(slug, form):
    """
    Map form fields from tool_page.html into the option keys
    expected by PDFProcessor.process().

    This is where we wire:
    - compression_level
    - rotation_angle
    - page_order / deleted_pages  ✅
    - crop_regions (PRO++ crop)   ✅
    and other advanced options.
    """
    options = {}

    # Common fields (pages)
    pages = form.get("pages", "").strip()
    if pages:
        options["pages"] = pages
        options["page_range"] = pages  # alias, used by split internally

    # Password (protect/unlock)
    password = form.get("password", "").strip()
    if password:
        options["password"] = password
        options["new_password"] = password  # for protect

    # Watermark text
    watermark_text = form.get("watermark_text", "").strip()
    if watermark_text:
        options["watermark_text"] = watermark_text

    # Keep filename flag (used here, not by processor)
    keep_filename = form.get("keep_filename_hidden")
    if keep_filename == "1":
        options["keep_filename"] = True

    # -------- Tool specific mapping --------

    # Compress
    if slug == "compress-pdf":
        # Slider sends 1,2,3 – map directly as "compression_level"
        level_raw = form.get("compression_level", "2")
        options["compression_level"] = level_raw

    # Rotate
    if slug == "rotate-pdf":
        angle_raw = form.get("rotation_angle", "0")
        try:
            options["angle"] = int(angle_raw)
        except ValueError:
            options["angle"] = 0

    # Watermark
    if slug == "watermark-pdf":
        options.setdefault("watermark_text", watermark_text or "CONFIDENTIAL")
        options["watermark_opacity"] = form.get("watermark_opacity", "0.15")
        options["watermark_position"] = form.get("watermark_position", "center")

    # ---------- REORDER / DELETE (Organize + Crop) --------------
    if slug in ("organize-pdf", "crop-pdf"):
        # From the live thumbnails UI:
        #  - hidden_page_order    -> "1,3,2,4"
        #  - hidden_deleted_pages -> "5,7"
        order = (form.get("page_order") or "").strip()
        deleted_ui = (form.get("deleted_pages") or "").strip()
        deleted_legacy = (form.get("delete_pages") or "").strip()

        if order:
            options["page_order"] = order

        # Backend expects "delete_pages" (range string).
        deleted_final = deleted_ui or deleted_legacy
        if deleted_final:
            options["delete_pages"] = deleted_final

    # ---------- PRO++ CROP PATCH --------------------
    if slug == "crop-pdf":
        # New PRO++ mode: per-page crop boxes from the preview UI.
        crop_regions = (form.get("crop_regions") or "").strip()
        if crop_regions:
            # JSON string built in tool_page.js, example:
            # {"1": {"x0":0.1,"y0":0.1,"x1":0.9,"y1":0.9}, "2": {...}}
            options["crop_regions"] = crop_regions
        else:
            # Fallback: old margin-based crop (if you ever add those inputs).
            options["crop_top"] = form.get("crop_top", "0")
            options["crop_right"] = form.get("crop_right", "0")
            options["crop_bottom"] = form.get("crop_bottom", "0")
            options["crop_left"] = form.get("crop_left", "0")

    # Resize
    if slug == "resize-pdf":
        options["page_size"] = form.get("page_size", "A4")

    # OCR language
    if slug == "ocr-pdf":
        options["ocr_lang"] = form.get("ocr_lang", "eng")

    # Metadata
    if slug == "metadata-editor":
        for key in ["title", "author", "subject", "keywords", "creator", "producer"]:
            val = form.get(key)
            if val:
                options[key] = val

    # Fill forms
    if slug == "fill-forms":
        raw = form.get("form_data_json", "{}")
        options["form_data_json"] = raw

    # Background remover – nothing extra, just a file.
    return options


@app.route("/tool/<slug>/process", methods=["POST"])
def process_tool(slug):
    # Validate tool exists
    tool = next((t for t in TOOLS if t["slug"] == slug), None)
    if not tool:
        flash("Unknown tool.", "error")
        return redirect(url_for("index"))

    # Files
    files = request.files.getlist("file")
    if not files or not files[0].filename:
        flash("Please upload at least one file.", "error")
        return redirect(url_for("tool_page", slug=slug))

    input_paths = _save_uploads(files)
    if not input_paths:
        flash("Failed to save uploaded files.", "error")
        return redirect(url_for("tool_page", slug=slug))

    # Map advanced options
    options = _map_options(slug, request.form)

    try:
        # For merge / image-to-pdf, we pass all inputs; others only first file
        multi_input_tools = {"merge-pdf", "image-to-pdf"}
        if slug in multi_input_tools:
            out_path, download_name, mimetype = pdf.process(slug, input_paths, options)
        else:
            out_path, download_name, mimetype = pdf.process(slug, [input_paths[0]], options)
    except PDFProcessorError as e:
        flash(str(e), "error")
        return redirect(url_for("tool_page", slug=slug))
    except Exception as e:
        print("Processing error:", e)
        flash("Something went wrong while processing your file.", "error")
        return redirect(url_for("tool_page", slug=slug))

    # Use original filename if requested and possible
    if options.get("keep_filename") and files and files[0].filename:
        base, _ = os.path.splitext(secure_filename(files[0].filename))
        ext = os.path.splitext(download_name)[1]
        download_name = f"{base}{ext}"

    return send_file(out_path, as_attachment=True, download_name=download_name)


# Also expose /uploads for AI editor, etc.
@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


# --------------------------------------------------------------------
# AI ROUTES (EDITOR / SUMMARIZER / CHAT / TRANSLATE / TABLE)
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

    summary = ask_ai(f"Summarize this PDF:\n{text[:6000]}", 300)
    return jsonify({"summary": summary})


@app.route("/ai/chat/upload", methods=["POST"])
def ai_chat_upload():
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "No file uploaded"}), 400

    filename = f"{uuid.uuid4().hex}_{secure_filename(f.filename)}"
    path = os.path.join(UPLOAD_FOLDER, filename)
    f.save(path)
    return jsonify({"filepath": path})


@app.route("/ai/chat/ask", methods=["POST"])
def ai_chat_ask():
    data = request.get_json() or {}
    question = data.get("question") or ""
    file_path = data.get("file")

    if not question or not file_path:
        return jsonify({"error": "Missing question or file"}), 400

    if not os.path.exists(file_path):
        return jsonify({"error": "File not found on server"}), 404

    import PyPDF2

    with open(file_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        text = "".join([p.extract_text() or "" for p in reader.pages])

    answer = ask_ai(
        f"Answer based ONLY on this PDF content:\n{text[:7000]}\n\nQuestion: {question}"
    )

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

    translated = ask_ai(f"Translate this PDF to {lang}:\n{text[:6000]}")
    return jsonify({"preview": translated})


@app.route("/ai/table-extract", methods=["POST"])
def ai_table_extract():
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "No file uploaded"})

    import PyPDF2
    reader = PyPDF2.PdfReader(f)
    text = "".join([p.extract_text() or "" for p in reader.pages])

    tables = ask_ai(f"Extract all tables from this PDF as CSV:\n{text[:6000]}")
    return jsonify({"tables": tables})


# -------- Extra AI real-edit helper routes (used by ai_editor) --------

@app.route("/ai/real-replace", methods=["POST"])
def ai_real_replace():
    """
    Example endpoint for "real replace" – you can adjust or remove if unused.
    """
    filename = request.form.get("filename")
    if not filename:
        return jsonify({"error": "filename missing"}), 400

    source_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(source_path):
        return jsonify({"error": "File not found on server"}), 404

    final_name = f"{uuid.uuid4().hex}_final.pdf"
    output_path = os.path.join(PROCESSED_FOLDER, final_name)

    # Dummy example: just copy using pdf_processor real redact/annotate if needed
    doc = fitz.open(source_path)
    doc.save(output_path)
    doc.close()

    return send_file(output_path, as_attachment=True)


@app.route("/ai/apply-real-edits", methods=["POST"])
def apply_real_edits():
    """
    Endpoint used by the canvas editor to apply multiple edits to a PDF.
    """
    filename = request.form.get("filename")
    edits_raw = request.form.get("edits")

    if not filename or not edits_raw:
        return jsonify({"error": "Missing data"}), 400

    try:
        edits = json.loads(edits_raw)
    except json.JSONDecodeError:
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


@app.route('/uploads-ai/<path:filename>')
def serve_uploads(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


# --------------------------------------------------------------------
# HEALTHCHECK
# --------------------------------------------------------------------

@app.route("/health")
def health():
    return "BlinkPDF is running"


# --------------------------------------------------------------------
# MAIN
# --------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
