import os
import uuid
import base64
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

# ---------------- AI CONFIG ----------------
HF_TOKEN = os.getenv("HF_TOKEN")

def ask_ai(prompt, max_tokens=500):
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
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024  # 500MB

tempfile.tempdir = os.path.abspath(UPLOAD_FOLDER)

pdf = PDFProcessor()

# ---------------- TOOLS ----------------

TOOLS = [
    {'slug':'merge-pdf','title':'Merge PDF','desc':'Combine multiple PDF documents easily.','icon':'merge-pdf.svg'},
    {'slug':'split-pdf','title':'Split PDF','desc':'Extract or split PDF pages.','icon':'split-pdf.svg'},
    {'slug':'compress-pdf','title':'Compress PDF','desc':'Reduce PDF file size smartly.','icon':'compress-pdf.svg'},
    {'slug':'optimize-pdf','title':'Optimize PDF','desc':'Advanced cleaning and optimization.','icon':'optimize-pdf.svg'},
    {'slug':'rotate-pdf','title':'Rotate PDF','desc':'Rotate pages of your PDF.','icon':'rotate-pdf.svg'},
    {'slug':'watermark-pdf','title':'Watermark PDF','desc':'Add watermark text or image.','icon':'watermark-pdf.svg'},
    {'slug':'number-pdf','title':'Number Pages','desc':'Add page numbers anywhere.','icon':'number-pdf.svg'},
    {'slug':'protect-pdf','title':'Protect PDF','desc':'Encrypt with password.','icon':'protect-pdf.svg'},
    {'slug':'unlock-pdf','title':'Unlock PDF','desc':'Remove password restrictions.','icon':'unlock-pdf.svg'},
    {'slug':'repair-pdf','title':'Repair PDF','desc':'Fix damaged or corrupted PDFs.','icon':'repair-pdf.svg'},
    {'slug':'organize-pdf','title':'Organize PDF','desc':'Reorder, delete, rotate pages visually.','icon':'organize-pdf.svg'},
    {'slug':'sign-pdf','title':'Sign PDF','desc':'Add digital signatures or images.','icon':'sign-pdf.svg'},
    {'slug':'annotate-pdf','title':'Annotate PDF','desc':'Highlight, underline or comment.','icon':'annotate-pdf.svg'},
    {'slug':'redact-pdf','title':'Redact PDF','desc':'Blackout sensitive information.','icon':'redact-pdf.svg'},
    {'slug':'pdf-to-word','title':'PDF to Word','desc':'Convert PDF into editable Word documents.','icon':'pdf-to-word.svg'},
    {'slug':'word-to-pdf','title':'Word to PDF','desc':'Convert DOC/DOCX to PDF.','icon':'word-to-pdf.svg'},
    {'slug':'pdf-to-image','title':'PDF to Image','desc':'Convert PDF pages to images.','icon':'pdf-to-image.svg'},
    {'slug':'image-to-pdf','title':'Image to PDF','desc':'Merge images into a PDF.','icon':'image-to-pdf.svg'},
    {'slug':'pdf-to-excel','title':'PDF to Excel','desc':'Extract tables into Excel.','icon':'pdf-to-excel.svg'},
    {'slug':'excel-to-pdf','title':'Excel to PDF','desc':'Convert spreadsheets to PDF.','icon':'excel-to-pdf.svg'},
    {'slug':'pdf-to-powerpoint','title':'PDF to PowerPoint','desc':'Convert PDF pages into PPTX slides.','icon':'pdf-to-powerpoint.svg'},
    {'slug':'powerpoint-to-pdf','title':'PowerPoint to PDF','desc':'Convert PPTX files to PDF.','icon':'powerpoint-to-pdf.svg'},
    {'slug':'ocr-pdf','title':'OCR PDF','desc':'Convert scanned PDFs into searchable text.','icon':'ocr-pdf.svg'},
    {'slug':'extract-text','title':'Extract Text','desc':'Extract plain text from PDF.','icon':'extract-text.svg'},
    {'slug':'extract-images','title':'Extract Images','desc':'Extract embedded images from PDF.','icon':'extract-images.svg'},
    {'slug':'deskew-pdf','title':'Deskew PDF','desc':'Auto-straighten scanned pages.','icon':'deskew-pdf.svg'},
    {'slug':'crop-pdf','title':'Crop PDF','desc':'Crop pages.','icon':'crop-pdf.svg'},
    {'slug':'resize-pdf','title':'Resize PDF','desc':'Change page size.','icon':'resize-pdf.svg'},
    {'slug':'flatten-pdf','title':'Flatten PDF','desc':'Flatten forms.','icon':'flatten-pdf.svg'},
    {'slug':'metadata-editor','title':'Metadata Editor','desc':'Edit metadata.','icon':'metadata-editor.svg'},
    {'slug':'fill-forms','title':'Fill PDF Forms','desc':'Fill PDF fields.','icon':'fill-forms.svg'},
    {'slug':'background-remover','title':'Remove Background','desc':'Remove background.','icon':'background-remover.svg'}
]

AI_TOOLS = [
    {"slug":"ai-editor","title":"AI PDF Editor","desc":"Live editor","url":"/ai/editor","icon":"ai-editor.svg"},
    {"slug":"ai-summarizer","title":"AI Summarizer","desc":"Smart summary","url":"/ai/summarizer-page","icon":"ai-summarizer.svg"},
    {"slug":"ai-chat","title":"Chat with PDF","desc":"Ask questions","url":"/ai/chat-page","icon":"ai-chat.svg"},
    {"slug":"ai-translate","title":"AI Translator","desc":"Translate text","url":"/ai/translate-page","icon":"ai-translate.svg"},
    {"slug":"ai-table-extract","title":"AI Table Extractor","desc":"Extract tables","url":"/ai/table-page","icon":"ai-table.svg"}
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

# ---------------- GOOGLE VERIFICATION ----------------

@app.route('/googlefe495bc7600f4865.html')
def google_verify():
    return send_from_directory(
        os.path.dirname(os.path.abspath(__file__)),
        'googlefe495bc7600f4865.html'
    )

# ---------------- PRO++ TOOL PIPELINE ----------------

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
    """
    options = {}

    # Common fields
    pages = form.get("pages", "").strip()
    if pages:
        options["pages"] = pages
        options["page_range"] = pages  # alias, used by split internally

    password = form.get("password", "").strip()
    if password:
        options["password"] = password
        options["new_password"] = password  # for protect

    watermark_text = form.get("watermark_text", "").strip()
    if watermark_text:
        options["watermark_text"] = watermark_text

    # Keep filename flag (used here, not by processor)
    keep_filename = form.get("keep_filename_hidden")
    if keep_filename == "1":
        options["keep_filename"] = True

    # Tool specific
    if slug == "compress-pdf":
        # Slider sends 1,2,3 – map to quality profile
        level_raw = form.get("compression_level", "2")
        options["compression_level"] = level_raw

    if slug == "rotate-pdf":
        # Frontend sends rotation_angle; processor expects 'angle'
        angle_raw = form.get("rotation_angle", "0")
        try:
            options["angle"] = int(angle_raw)
        except ValueError:
            options["angle"] = 0

    if slug == "watermark-pdf":
        # Defaults if UI not exposing them yet
        options.setdefault("watermark_text", watermark_text or "CONFIDENTIAL")
        options["watermark_opacity"] = form.get("watermark_opacity", "0.15")
        options["watermark_position"] = form.get("watermark_position", "center")

    if slug == "organize-pdf":
        # If you add page reorder / delete inputs in UI, wire them here
        order = form.get("page_order", "").strip()
        delete = form.get("delete_pages", "").strip()
        if order:
            options["page_order"] = order
        if delete:
            options["delete_pages"] = delete

    if slug == "crop-pdf":
        # Hook for crop UI (values in points)
        options["crop_top"] = form.get("crop_top", "0")
        options["crop_right"] = form.get("crop_right", "0")
        options["crop_bottom"] = form.get("crop_bottom", "0")
        options["crop_left"] = form.get("crop_left", "0")

    if slug == "resize-pdf":
        options["page_size"] = form.get("page_size", "A4")

    if slug == "ocr-pdf":
        options["ocr_lang"] = form.get("ocr_lang", "eng")

    if slug == "metadata-editor":
        # Whatever meta fields you add in UI will be sent through as-is
        for key in ["title", "author", "subject", "keywords", "creator", "producer"]:
            val = form.get(key)
            if val:
                options[key] = val

    if slug == "fill-forms":
        # Expect JSON field if you add a form-mapper UI
        raw = form.get("form_data_json", "{}")
        options["form_data_json"] = raw

    # Background remover (nothing special needed, just a file)
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

    # Options mapped from advanced settings
    options = _map_options(slug, request.form)

    try:
        out_path, download_name, mimetype = pdf.process(slug, input_paths, options)

        # Optional: respect "keep original filename" where it makes sense
        if options.get("keep_filename") and files:
            base = os.path.splitext(secure_filename(files[0].filename))[0]
            ext = os.path.splitext(download_name)[1] or ".pdf"
            download_name = f"{base}{ext}"

        return send_file(
            out_path,
            as_attachment=True,
            download_name=download_name,
            mimetype=mimetype
        )
    except PDFProcessorError as e:
        flash(str(e), "error")
        return redirect(url_for("tool_page", slug=slug))
    except Exception as e:
        # Last-resort error – don't leak stacktrace to user
        print("Unexpected error in process_tool:", e)
        flash("Something went wrong while processing your file.", "error")
        return redirect(url_for("tool_page", slug=slug))

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
