import os
import random
from datetime import datetime

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    send_file,
    abort,
    flash,
)

from utils.pdf_processor import PDFProcessor, PDFProcessorError

# -----------------------------------------------------------------------------
# Flask app & config
# -----------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "processed")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "blinkpdf-dev-key")
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024  # 500MB limit

pdf_processor = PDFProcessor(OUTPUT_FOLDER)

# -----------------------------------------------------------------------------
# Tool registry (single source of truth)
# -----------------------------------------------------------------------------
TOOLS = [
    # Core PDF
    {
        "slug": "compress-pdf",
        "title": "Compress PDF",
        "desc": "Reduce PDF file size while keeping good quality.",
        "icon": "compress-pdf.svg",
        "category": "pdf",
    },
    {
        "slug": "merge-pdf",
        "title": "Merge PDF",
        "desc": "Combine multiple PDF files into one.",
        "icon": "merge-pdf.svg",
        "category": "pdf",
    },
    {
        "slug": "split-pdf",
        "title": "Split PDF",
        "desc": "Split a PDF into multiple smaller PDFs.",
        "icon": "split-pdf.svg",
        "category": "pdf",
    },
    {
        "slug": "extract-pages",
        "title": "Extract Pages",
        "desc": "Extract selected pages into a new PDF.",
        "icon": "extract-pages.svg",
        "category": "pdf",
    },
    {
        "slug": "organize-pdf",
        "title": "Organize PDF",
        "desc": "Reorder, delete and arrange PDF pages.",
        "icon": "organize-pdf.svg",
        "category": "pdf",
    },
    {
        "slug": "rotate-pdf",
        "title": "Rotate PDF",
        "desc": "Rotate pages in your PDF permanently.",
        "icon": "rotate-pdf.svg",
        "category": "pdf",
    },
    {
        "slug": "crop-pdf",
        "title": "Crop PDF",
        "desc": "Visually crop margins and content in your PDF.",
        "icon": "crop-pdf.svg",
        "category": "pdf",
    },
    {
        "slug": "resize-pdf",
        "title": "Resize PDF",
        "desc": "Change the page size of your PDF.",
        "icon": "resize-pdf.svg",
        "category": "pdf",
    },
    {
        "slug": "flatten-pdf",
        "title": "Flatten PDF",
        "desc": "Flatten annotations and forms for better compatibility.",
        "icon": "flatten-pdf.svg",
        "category": "pdf",
    },
    {
        "slug": "number-pdf",
        "title": "Number PDF Pages",
        "desc": "Add page numbers to your PDF.",
        "icon": "number-pdf.svg",
        "category": "pdf",
    },
    {
        "slug": "protect-pdf",
        "title": "Protect PDF",
        "desc": "Add password protection to your PDF.",
        "icon": "protect-pdf.svg",
        "category": "security",
    },
    {
        "slug": "unlock-pdf",
        "title": "Unlock PDF",
        "desc": "Remove password from your PDF (if you know it).",
        "icon": "unlock-pdf.svg",
        "category": "security",
    },
    {
        "slug": "watermark-pdf",
        "title": "Watermark PDF",
        "desc": "Add text watermark to every page.",
        "icon": "watermark-pdf.svg",
        "category": "edit",
    },
    {
        "slug": "metadata-editor",
        "title": "Edit PDF Metadata",
        "desc": "Change title, author and other metadata.",
        "icon": "metadata-editor.svg",
        "category": "edit",
    },
    {
        "slug": "fill-forms",
        "title": "Fill & Flatten Forms",
        "desc": "Fill PDF forms and flatten them.",
        "icon": "fill-forms.svg",
        "category": "edit",
    },
    {
        "slug": "redact-pdf",
        "title": "Redact PDF",
        "desc": "Permanently hide sensitive content.",
        "icon": "redact-pdf.svg",
        "category": "edit",
    },
    {
        "slug": "extract-text",
        "title": "Extract Text",
        "desc": "Extract all text from your PDF.",
        "icon": "extract-text.svg",
        "category": "convert",
    },
    {
        "slug": "extract-images",
        "title": "Extract Images",
        "desc": "Pull out all images embedded in your PDF.",
        "icon": "extract-images.svg",
        "category": "convert",
    },
    {
        "slug": "repair-pdf",
        "title": "Repair PDF",
        "desc": "Try to fix corrupted or damaged PDFs.",
        "icon": "repair-pdf.svg",
        "category": "utility",
    },
    {
        "slug": "deskew-pdf",
        "title": "Deskew PDF",
        "desc": "Straighten scanned PDF pages.",
        "icon": "deskew-pdf.svg",
        "category": "utility",
    },

    # PDF ↔ Office / Images
    {
        "slug": "pdf-to-word",
        "title": "PDF to Word",
        "desc": "Convert PDF to editable DOCX.",
        "icon": "pdf-to-word.svg",
        "category": "convert",
    },
    {
        "slug": "pdf-to-excel",
        "title": "PDF to Excel",
        "desc": "Convert tables in PDF to XLSX.",
        "icon": "pdf-to-excel.svg",
        "category": "convert",
    },
    {
        "slug": "pdf-to-powerpoint",
        "title": "PDF to PowerPoint",
        "desc": "Convert PDF slides to PPTX.",
        "icon": "pdf-to-powerpoint.svg",
        "category": "convert",
    },
    {
        "slug": "word-to-pdf",
        "title": "Word to PDF",
        "desc": "Convert DOCX to high-quality PDF.",
        "icon": "word-to-pdf.svg",
        "category": "convert",
    },
    {
        "slug": "excel-to-pdf",
        "title": "Excel to PDF",
        "desc": "Convert spreadsheets to PDF.",
        "icon": "excel-to-pdf.svg",
        "category": "convert",
    },
    {
        "slug": "powerpoint-to-pdf",
        "title": "PowerPoint to PDF",
        "desc": "Convert presentations to PDF.",
        "icon": "powerpoint-to-pdf.svg",
        "category": "convert",
    },
    {
        "slug": "image-to-pdf",
        "title": "Image to PDF",
        "desc": "Convert JPG, PNG, WEBP to PDF.",
        "icon": "image-to-pdf.svg",
        "category": "convert",
    },

    # AI tools
    {
        "slug": "ai-editor",
        "title": "AI PDF Editor",
        "desc": "Edit your PDF content with AI assistance.",
        "icon": "ai-editor.svg",
        "category": "ai",
        "is_ai": True,
    },
    {
        "slug": "ai-summarizer",
        "title": "AI Summarizer",
        "desc": "Summarize long PDFs into key points.",
        "icon": "ai-summarizer.svg",
        "category": "ai",
        "is_ai": True,
    },
    {
        "slug": "ai-chat",
        "title": "AI Chat with PDF",
        "desc": "Ask questions and chat with your PDF.",
        "icon": "ai-chat.svg",
        "category": "ai",
        "is_ai": True,
    },
    {
        "slug": "ai-table",
        "title": "AI Table Extractor",
        "desc": "Smartly extract tables from PDFs.",
        "icon": "ai-table.svg",
        "category": "ai",
        "is_ai": True,
    },
    {
        "slug": "ai-translate",
        "title": "AI Translate PDF",
        "desc": "Translate PDF content into any language.",
        "icon": "ai-translate.svg",
        "category": "ai",
        "is_ai": True,
    },

    # Image tools
    {
        "slug": "background-remover",
        "title": "Background Remover",
        "desc": "Remove image background using AI.",
        "icon": "background-remover.svg",
        "category": "image",
    },
]

TOOLS_BY_SLUG = {t["slug"]: t for t in TOOLS}


def get_tool_or_404(slug: str) -> dict:
    tool = TOOLS_BY_SLUG.get(slug)
    if not tool:
        abort(404)
    return tool


def get_random_tools(current_slug: str, limit: int = 8):
    candidates = [t for t in TOOLS if t["slug"] != current_slug]
    if len(candidates) <= limit:
        return candidates
    return random.sample(candidates, limit)


# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------
@app.route("/")
def index():
    """Homepage with full tools grid."""
    # You can group tools by category in the template if you want
    return render_template("index.html", tools=TOOLS)


@app.route("/tool/<slug>")
def tool_page(slug):
    """Single tool page with live preview."""
    tool = get_tool_or_404(slug)
    random_tools = get_random_tools(slug)
    return render_template("tool_page.html", tool=tool, random_tools=random_tools)


@app.route("/tool/<slug>/process", methods=["POST"])
def process_tool(slug):
    """
    Unified processing endpoint for ALL tools.

    - Accepts uploaded file(s)
    - Collects all advanced options (compression, pages, rotation, crop, etc.)
    - Delegates to PDFProcessor.process()
    - Streams back the processed file
    """
    tool = get_tool_or_404(slug)

    # File(s)
    files = request.files.getlist("file")
    if not files or not files[0] or files[0].filename == "":
        flash("Please upload a file first.", "error")
        return redirect(url_for("tool_page", slug=slug))

    # Only pass non-empty FileStorage objects
    valid_files = [f for f in files if f and f.filename]
    if not valid_files:
        flash("Please upload a file first.", "error")
        return redirect(url_for("tool_page", slug=slug))

    # Advanced / PRO+++ options from hidden fields
    form = request.form

    options = {
        # common UI options
        "compression_level": form.get("compression_level") or form.get("hidden_compression_level"),
        "pages": form.get("pages") or form.get("hidden_pages"),
        "password": form.get("password") or form.get("hidden_password"),
        "watermark_text": form.get("watermark_text") or form.get("hidden_watermark_text"),
        "keep_filename": form.get("keep_filename_hidden") == "1"
        or form.get("keep_filename") == "1",
        # rotate
        "rotation_angle": form.get("rotation_angle") or form.get("rotation_angle_input"),
        # PRO++ organize / crop
        "page_order": form.get("page_order") or form.get("hidden_page_order"),
        "deleted_pages": form.get("deleted_pages") or form.get("hidden_deleted_pages"),
        "crop_regions": form.get("crop_regions") or form.get("hidden_crop_regions"),
    }

    try:
        # Delegate to the PDFProcessor (handles all slugs internally)
        output_path, download_name, mimetype = pdf_processor.process(
            slug,
            valid_files,
            options,
        )
    except PDFProcessorError as e:
        app.logger.error(f"Processing error ({slug}): {e}")
        flash(str(e), "error")
        return redirect(url_for("tool_page", slug=slug))
    except Exception as e:
        app.logger.exception(f"Unexpected processing error for {slug}")
        flash("Something went wrong while processing your file. Please try again.", "error")
        return redirect(url_for("tool_page", slug=slug))

    if not output_path or not os.path.exists(output_path):
        flash("Processing failed. Output file was not created.", "error")
        return redirect(url_for("tool_page", slug=slug))

    # Stream file back to user, then let your background cleanup handle deletion
    return send_file(
        output_path,
        as_attachment=True,
        download_name=download_name,
        mimetype=mimetype or "application/octet-stream",
    )


# -----------------------------------------------------------------------------
# Error handlers
# -----------------------------------------------------------------------------
@app.errorhandler(404)
def not_found(e):
    return render_template("error.html", code=404, message="Page not found"), 404


@app.errorhandler(413)
def file_too_large(e):
    return (
        render_template(
            "error.html",
            code=413,
            message="File too large. Maximum allowed size is 500MB.",
        ),
        413,
    )


@app.errorhandler(500)
def server_error(e):
    app.logger.exception("Internal server error")
    return (
        render_template(
            "error.html",
            code=500,
            message="Something went wrong on our side. Please try again.",
        ),
        500,
    )


# -----------------------------------------------------------------------------
# Dev entry point
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "1") == "1"
    app.run(host="0.0.0.0", port=5000, debug=debug_mode)
