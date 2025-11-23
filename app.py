import os
import uuid
from datetime import datetime

from flask import (
    Flask,
    render_template,
    request,
    send_file,
    redirect,
    url_for,
    flash,
    abort,
)

from utils.pdf_processor import PDFProcessor, PDFProcessorError

# -------------------------------------------------------------------
# Flask app + basic config
# -------------------------------------------------------------------

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-this")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "processed")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# PDF processor (no arguments, as per your current class definition)
pdf_processor = PDFProcessor()

# -------------------------------------------------------------------
# Tools registry
# (KEEP this consistent with your existing templates/index.html)
# If you already have TOOLS defined elsewhere, use that and delete this.
# -------------------------------------------------------------------

TOOLS = [
    # --- Core PDF tools ---
    {
        "slug": "merge-pdf",
        "name": "Merge PDF",
        "description": "Combine multiple PDFs into a single file.",
        "category": "Organize PDFs",
        "icon": "merge-pdf.svg",
        "badge": "Popular",
    },
    {
        "slug": "split-pdf",
        "name": "Split PDF",
        "description": "Split PDF into multiple files by page ranges.",
        "category": "Organize PDFs",
        "icon": "split-pdf.svg",
        "badge": "",
    },
    {
        "slug": "compress-pdf",
        "name": "Compress PDF",
        "description": "Reduce PDF file size while keeping good quality.",
        "category": "Optimize PDFs",
        "icon": "compress-pdf.svg",
        "badge": "New",
    },
    {
        "slug": "rotate-pdf",
        "name": "Rotate PDF",
        "description": "Rotate pages and fix orientation.",
        "category": "Organize PDFs",
        "icon": "rotate-pdf.svg",
        "badge": "",
    },
    {
        "slug": "organize-pdf",
        "name": "Organize PDF",
        "description": "Reorder, duplicate or delete pages.",
        "category": "Organize PDFs",
        "icon": "organize-pdf.svg",
        "badge": "",
    },
    {
        "slug": "crop-pdf",
        "name": "Crop PDF",
        "description": "Crop margins from PDF pages.",
        "category": "Edit PDFs",
        "icon": "crop-pdf.svg",
        "badge": "",
    },
    {
        "slug": "resize-pdf",
        "name": "Resize PDF",
        "description": "Change PDF page size or scale.",
        "category": "Edit PDFs",
        "icon": "resize-pdf.svg",
        "badge": "",
    },
    {
        "slug": "deskew-pdf",
        "name": "Deskew PDF",
        "description": "Straighten scanned & skewed PDFs.",
        "category": "Fix PDFs",
        "icon": "deskew-pdf.svg",
        "badge": "",
    },
    {
        "slug": "flatten-pdf",
        "name": "Flatten PDF",
        "description": "Flatten annotations/forms into static content.",
        "category": "Fix PDFs",
        "icon": "flatten-pdf.svg",
        "badge": "",
    },
    {
        "slug": "repair-pdf",
        "name": "Repair PDF",
        "description": "Try to fix corrupted or unreadable PDFs.",
        "category": "Fix PDFs",
        "icon": "repair-pdf.svg",
        "badge": "",
    },

    # --- Security ---
    {
        "slug": "protect-pdf",
        "name": "Protect PDF",
        "description": "Add password protection to your PDF.",
        "category": "Security",
        "icon": "protect-pdf.svg",
        "badge": "",
    },
    {
        "slug": "unlock-pdf",
        "name": "Unlock PDF",
        "description": "Remove password from your PDF (if allowed).",
        "category": "Security",
        "icon": "unlock-pdf.svg",
        "badge": "",
    },

    # --- Conversion: PDF -> Office / images ---
    {
        "slug": "pdf-to-word",
        "name": "PDF to Word",
        "description": "Convert PDF to editable Word document.",
        "category": "Convert from PDF",
        "icon": "pdf-to-word.svg",
        "badge": "",
    },
    {
        "slug": "pdf-to-excel",
        "name": "PDF to Excel",
        "description": "Extract tables from PDF into Excel.",
        "category": "Convert from PDF",
        "icon": "pdf-to-excel.svg",
        "badge": "",
    },
    {
        "slug": "pdf-to-powerpoint",
        "name": "PDF to PowerPoint",
        "description": "Convert PDF slides to editable PowerPoint.",
        "category": "Convert from PDF",
        "icon": "pdf-to-powerpoint.svg",
        "badge": "",
    },
    {
        "slug": "pdf-to-images",
        "name": "PDF to Images",
        "description": "Export each PDF page as an image.",
        "category": "Convert from PDF",
        "icon": "pdf-to-image.svg",
        "badge": "",
    },

    # --- Conversion: Office / image -> PDF ---
    {
        "slug": "word-to-pdf",
        "name": "Word to PDF",
        "description": "Convert Word documents to PDF.",
        "category": "Convert to PDF",
        "icon": "word-to-pdf.svg",
        "badge": "",
    },
    {
        "slug": "excel-to-pdf",
        "name": "Excel to PDF",
        "description": "Convert Excel spreadsheets to PDF.",
        "category": "Convert to PDF",
        "icon": "excel-to-pdf.svg",
        "badge": "",
    },
    {
        "slug": "powerpoint-to-pdf",
        "name": "PowerPoint to PDF",
        "description": "Convert PowerPoint slides to PDF.",
        "category": "Convert to PDF",
        "icon": "powerpoint-to-pdf.svg",
        "badge": "",
    },
    {
        "slug": "image-to-pdf",
        "name": "Image to PDF",
        "description": "Convert JPG/PNG images to PDF.",
        "category": "Convert to PDF",
        "icon": "image-to-pdf.svg",
        "badge": "",
    },

    # --- Extraction / content tools ---
    {
        "slug": "extract-text",
        "name": "Extract Text",
        "description": "Extract all text from a PDF.",
        "category": "Extract",
        "icon": "extract-text.svg",
        "badge": "",
    },
    {
        "slug": "extract-images",
        "name": "Extract Images",
        "description": "Extract embedded images from a PDF.",
        "category": "Extract",
        "icon": "extract-images.svg",
        "badge": "",
    },
    {
        "slug": "metadata-editor",
        "name": "Metadata Editor",
        "description": "View and edit PDF metadata.",
        "category": "Edit PDFs",
        "icon": "metadata-editor.svg",
        "badge": "",
    },
    {
        "slug": "number-pdf",
        "name": "Number Pages",
        "description": "Add page numbers to your PDF.",
        "category": "Edit PDFs",
        "icon": "number-pdf.svg",
        "badge": "",
    },
    {
        "slug": "watermark-pdf",
        "name": "Watermark PDF",
        "description": "Add text or image watermark to your PDF.",
        "category": "Edit PDFs",
        "icon": "watermark-pdf.svg",
        "badge": "",
    },
    {
        "slug": "redact-pdf",
        "name": "Redact PDF",
        "description": "Blackout sensitive content permanently.",
        "category": "Security",
        "icon": "redact-pdf.svg",
        "badge": "",
    },

    # --- AI tools (frontend pages) ---
    {
        "slug": "ai-summarizer",
        "name": "AI Summarizer",
        "description": "Summarize long PDFs using AI.",
        "category": "AI Tools",
        "icon": "ai-summarizer.svg",
        "badge": "AI",
    },
    {
        "slug": "ai-chat",
        "name": "AI Chat with PDF",
        "description": "Chat with your PDF content using AI.",
        "category": "AI Tools",
        "icon": "ai-chat.svg",
        "badge": "AI",
    },
    {
        "slug": "ai-translate",
        "name": "AI Translate",
        "description": "Translate your PDFs into other languages.",
        "category": "AI Tools",
        "icon": "ai-translate.svg",
        "badge": "AI",
    },
    {
        "slug": "ai-table",
        "name": "AI Table Extractor",
        "description": "Use AI to clean complex tables.",
        "category": "AI Tools",
        "icon": "ai-table.svg",
        "badge": "AI",
    },
    {
        "slug": "ai-editor",
        "name": "AI PDF Editor",
        "description": "Edit PDF text using AI.",
        "category": "AI Tools",
        "icon": "ai-editor.svg",
        "badge": "AI",
    },

    # --- Image AI ---
    {
        "slug": "background-remover",
        "name": "Background Remover",
        "description": "Remove image backgrounds using AI.",
        "category": "Images",
        "icon": "background-remover.svg",
        "badge": "AI",
    },
]

SLUG_TO_TOOL = {tool["slug"]: tool for tool in TOOLS}


# -------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------

def _save_upload(file_storage, prefix: str = "input") -> str:
    """Save uploaded file to UPLOAD_FOLDER and return its path."""
    ext = os.path.splitext(file_storage.filename or "")[1]
    unique_name = f"{prefix}_{uuid.uuid4().hex}{ext}"
    path = os.path.join(UPLOAD_FOLDER, unique_name)
    file_storage.save(path)
    return path


# -------------------------------------------------------------------
# Routes: homepage + tool pages + static pages
# -------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html", tools=TOOLS)


@app.route("/tool/<tool_slug>")
def tool_page(tool_slug):
    tool = SLUG_TO_TOOL.get(tool_slug)
    if not tool:
        abort(404)
    return render_template("tool_page.html", tool=tool)


# If you have a separate AI tools page (grid), you can use this:
@app.route("/ai-tools")
def ai_tools_page():
    ai_tools = [t for t in TOOLS if t.get("category") == "AI Tools"]
    return render_template("ai_tools.html", tools=ai_tools)


# Basic static/information pages (used in base.html footer/navigation)
@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


# -------------------------------------------------------------------
# Global processing endpoint: ALL tools post here
#
# In your forms:
#   <form action="/process" method="post" enctype="multipart/form-data">
#       <input type="hidden" name="tool_slug" value="{{ tool.slug }}">
#       <input type="file" name="file" ...>
#       <!-- any additional options fields -->
#   </form>
# -------------------------------------------------------------------

@app.route("/process", methods=["POST"])
def process_file():
    """Global processing endpoint for all tools."""
    tool_slug = request.form.get("tool_slug") or request.form.get("tool")
    if not tool_slug:
        flash("Missing tool information.", "error")
        return redirect(url_for("index"))

    tool = SLUG_TO_TOOL.get(tool_slug)
    if not tool:
        flash("Unknown tool requested.", "error")
        return redirect(url_for("index"))

    if "file" not in request.files:
        flash("Please upload a file.", "error")
        return redirect(url_for("tool_page", tool_slug=tool_slug))

    file_storage = request.files["file"]
    if file_storage.filename == "":
        flash("Please upload a file.", "error")
        return redirect(url_for("tool_page", tool_slug=tool_slug))

    # Save primary input file
    input_paths = []
    try:
        main_input_path = _save_upload(file_storage, prefix=tool_slug)
        input_paths.append(main_input_path)
    except Exception:
        flash("Failed to save uploaded file.", "error")
        return redirect(url_for("tool_page", tool_slug=tool_slug))

    # Collect any extra files (e.g., for merge you might have multiple)
    # If your HTML uses multiple="multiple" with name="files[]", they will show here.
    extra_files = request.files.getlist("files[]")
    for extra in extra_files:
        if extra.filename:
            try:
                extra_path = _save_upload(extra, prefix=f"{tool_slug}_extra")
                input_paths.append(extra_path)
            except Exception:
                # We ignore individual failures and just proceed with what we have
                continue

    # Collect options from the form (everything except special keys)
    options = {}
    for key, value in request.form.items():
        if key in {"tool_slug", "tool"}:
            continue
        # Ignore empty strings
        if value is None or value == "":
            continue
        options[key] = value

    # Call PDFProcessor
    try:
        # EXPECTED signature:
        #   result = pdf_processor.process(tool_slug, input_paths, options)
        #
        # and result is:
        #   {
        #       "output_path": "/abs/path/to/file.pdf",
        #       "download_name": "nice-name.pdf",
        #       "mimetype": "application/pdf"
        #   }
        result = pdf_processor.process(tool_slug, input_paths, options)

        output_path = result.get("output_path")
        download_name = result.get("download_name")
        mimetype = result.get("mimetype", "application/pdf")

        if not output_path or not os.path.exists(output_path):
            raise PDFProcessorError("Processing failed: no output produced.")

        if not download_name:
            # Fallback filename
            base_name = f"{tool_slug}-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}.pdf"
            download_name = base_name

        return send_file(
            output_path,
            as_attachment=True,
            download_name=download_name,
            mimetype=mimetype,
        )

    except PDFProcessorError as e:
        app.logger.error(f"Processing error for tool {tool_slug}: {e}")
        flash(str(e), "error")
        return redirect(url_for("tool_page", tool_slug=tool_slug))
    except Exception as e:
        app.logger.exception(f"Unexpected error for tool {tool_slug}: {e}")
        flash("Unexpected error while processing your file.", "error")
        return redirect(url_for("tool_page", tool_slug=tool_slug))


# -------------------------------------------------------------------
# Healthcheck (optional for Render)
# -------------------------------------------------------------------

@app.route("/healthz")
def healthcheck():
    return "ok", 200


# -------------------------------------------------------------------
# Local dev entry
# -------------------------------------------------------------------

if __name__ == "__main__":
    # For local testing only; Render uses gunicorn
    app.run(host="0.0.0.0", port=5000, debug=True)
