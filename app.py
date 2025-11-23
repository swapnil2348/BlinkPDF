import os
import uuid
from flask import Flask, render_template, request, send_file, abort, jsonify
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

from pdf_processor import PDFProcessor
from tools import TOOLS, AI_TOOLS, SLUG_TO_TOOL

app = Flask(__name__)

# ---------------- CONFIG ----------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "outputs")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["OUTPUT_FOLDER"] = OUTPUT_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024  # 500 MB


# ---------------- ERRORS ----------------
@app.errorhandler(RequestEntityTooLarge)
def file_too_large(e):
    return "File too large. Maximum allowed: 500MB", 413


# ---------------- ROUTES ----------------
@app.route("/")
def index():
    return render_template("index.html", tools=TOOLS, ai_tools=AI_TOOLS)


# ✅ FIX: AI TOOLS PAGE ROUTE (for navbar)
@app.route("/ai-tools")
def ai_tools_page():
    return render_template("ai_tools.html", ai_tools=AI_TOOLS)


# ✅ FIX: PRIVACY PAGE ROUTE (for footer)
@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ✅ FIX: CONTACT PAGE ROUTE (optional if used anywhere)
@app.route("/contact")
def contact():
    return render_template("contact.html")


# ✅ TOOL PAGE
@app.route("/tool/<slug>")
def tool_page(slug):
    tool = SLUG_TO_TOOL.get(slug)
    if not tool:
        return abort(404)
    return render_template("tool_page.html", tool=tool)


# ✅ MAIN PROCESSING ENGINE (PRO+++)
@app.route("/process/<slug>", methods=["POST"])
def process_tool(slug):

    tool = SLUG_TO_TOOL.get(slug)
    if not tool:
        return abort(404)

    files = request.files.getlist("files")
    if not files or files[0].filename == "":
        return jsonify({"error": "No files uploaded"}), 400

    # ---------------- SAVE FILES ----------------
    saved_paths = []
    for file in files:
        filename = secure_filename(f"{uuid.uuid4().hex}_{file.filename}")
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)
        saved_paths.append(filepath)

    # ---------------- READ OPTIONS ----------------
    options = {}

    for key, value in request.form.items():

        # Convert booleans
        if value.lower() in ["true", "false"]:
            value = (value.lower() == "true")

        # Convert numbers if possible
        else:
            try:
                if "." in value:
                    value = float(value)
                else:
                    value = int(value)
            except:
                pass

        options[key] = value

    # ---------------- PROCESS ----------------
    try:
        processor = PDFProcessor()

        output_path = processor.process(
            tool_slug=slug,
            input_paths=saved_paths,
            options=options
        )

        if not output_path or not os.path.exists(output_path):
            return jsonify({"error": "Processing failed for this tool"}), 500

        return send_file(
            output_path,
            as_attachment=True,
            download_name=os.path.basename(output_path)
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------- MAIN ----------------
if __name__ == "__main__":
    app.run(debug=True)
