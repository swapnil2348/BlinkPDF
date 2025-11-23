import os
import uuid

from flask import (
    Flask,
    render_template,
    request,
    send_file,
    abort,
    jsonify,
    redirect,
    url_for,
)

from werkzeug.utils import secure_filename

# Our centralized tools definition
from tools import TOOLS, AI_TOOLS, SLUG_TO_TOOL

# Central processing engine
from pdf_processor import process_pdf


# ---------------------------------------------------
# BASIC FLASK SETUP
# ---------------------------------------------------
app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "outputs")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["OUTPUT_FOLDER"] = OUTPUT_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024  # 200 MB


# ---------------------------------------------------
# ROUTES
# ---------------------------------------------------


@app.route("/")
def index():
    """
    Homepage with 33 main tools + AI tools grid.
    """
    return render_template("index.html", tools=TOOLS, ai_tools=AI_TOOLS)


@app.route("/tool/<slug>")
def tool_page(slug):
    """
    Individual tool page.
    """
    tool = SLUG_TO_TOOL.get(slug)
    if not tool:
        return abort(404)

    return render_template("tool_page.html", tool=tool)


@app.route("/process/<slug>", methods=["POST"])
def process_tool(slug):
    """
    Handle file uploads and delegate actual work to pdf_processor.process_pdf.
    """
    tool = SLUG_TO_TOOL.get(slug)
    if not tool:
        return abort(404)

    if "files" not in request.files:
        return "No files uploaded", 400

    files = request.files.getlist("files")
    if not files:
        return "No files selected", 400

    saved_paths = []

    # Save uploaded files
    for f in files:
        if not f or f.filename == "":
            continue
        filename = secure_filename(f"{uuid.uuid4().hex}_{f.filename}")
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        f.save(filepath)
        saved_paths.append(filepath)

    if not saved_paths:
        return "No valid files uploaded", 400

    # Extra options from the form (rotation, password, etc.)
    form_data = request.form.to_dict()

    # Call central processing engine
    result = process_pdf(
        slug=slug,
        file_paths=saved_paths,
        output_folder=app.config["OUTPUT_FOLDER"],
        form_data=form_data,
    )

    # Handle response from processing engine
    if not isinstance(result, dict):
        return "Processing engine error", 500

    rtype = result.get("type")

    if rtype == "file":
        path = result.get("path")
        mimetype = result.get("mimetype", "application/octet-stream")
        download_name = result.get("download_name") or os.path.basename(path)
        if not path or not os.path.exists(path):
            return "Output file missing", 500
        return send_file(path, as_attachment=True, download_name=download_name, mimetype=mimetype)

    if rtype == "json":
        data = result.get("data", {})
        status_code = result.get("status_code", 200)
        return jsonify(data), status_code

    if rtype == "error":
        data = result.get("data", {})
        status_code = result.get("status_code", 400)
        return jsonify(data), status_code

    # Fallback – should not happen
    return jsonify({"message": "Unknown processing response"}), 500


# ---------------------------------------------------
# AI TOOLS PAGE (NAVBAR LINK)
# ---------------------------------------------------


@app.route("/ai-tools")
def ai_tools_page():
    """
    Page for AI tools link in navbar.
    If you don't have a separate template, this can simply
    redirect to the homepage section.
    """
    # If you have templates/ai_tools.html, you can do:
    # return render_template("ai_tools.html", ai_tools=AI_TOOLS)

    # For now, redirect to the homepage and anchor to the AI section.
    return redirect(url_for("index") + "#ai-tools")


# ---------------------------------------------------
# STATIC LEGAL / INFO PAGES
# ---------------------------------------------------


@app.route("/terms")
def terms_page():
    """
    Terms & Conditions page.
    Make sure you have templates/terms.html.
    """
    return render_template("terms.html")


@app.route("/privacy")
def privacy_page():
    """
    Privacy Policy page.
    Make sure you have templates/privacy.html.
    """
    return render_template("privacy.html")


@app.route("/contact")
def contact_page():
    """
    Contact page.
    Make sure you have templates/contact.html.
    """
    return render_template("contact.html")


# ---------------------------------------------------
# HEALTHCHECK / DEBUG
# ---------------------------------------------------


@app.route("/health")
def health():
    return {"status": "ok"}


# ---------------------------------------------------
# MAIN
# ---------------------------------------------------

if __name__ == "__main__":
    # For local testing
    app.run(debug=True, host="0.0.0.0", port=5000)
