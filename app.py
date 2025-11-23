from flask import Flask, render_template, request, send_file, jsonify
from werkzeug.utils import secure_filename
import os
import uuid

from utils.pdf_processor import PDFProcessor, PDFProcessorError

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "outputs")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["OUTPUT_FOLDER"] = OUTPUT_FOLDER


pdf_processor = PDFProcessor(OUTPUT_FOLDER)


TOOLS = [
    {"name": "Merge PDF", "slug": "merge-pdf"},
    {"name": "Split PDF", "slug": "split-pdf"},
    {"name": "Compress PDF", "slug": "compress-pdf"},
    {"name": "Rotate PDF", "slug": "rotate-pdf"},
    {"name": "Optimize PDF", "slug": "optimize-pdf"},
]


# ================= ROUTES ===================

@app.route('/')
def index():
    return render_template("index.html", tools=TOOLS)


@app.route('/ai-tools')
def ai_tools_page():
    return render_template("ai_tools.html")


# ✅ FIX: Accept BOTH slug + tool_slug
@app.route('/<slug>')
def tool_page(slug):     # ← renamed only inside function (no front-end change)
    tool = next((t for t in TOOLS if t["slug"] == slug), None)

    if not tool:
        return "Tool not found", 404

    return render_template("tool_page.html", tool=tool)


@app.route('/process/<slug>', methods=['POST'])
def process_file(slug):
    try:
        files = request.files.getlist("file")

        if not files or files[0].filename == "":
            return jsonify({"error": "No file uploaded"}), 400

        saved_paths = []
        for f in files:
            filename = secure_filename(f.filename)
            unique_name = f"{uuid.uuid4().hex}_{filename}"
            save_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
            f.save(save_path)
            saved_paths.append(save_path)

        options = request.form.to_dict()

        output_path, download_name, mime = pdf_processor.process(
            slug,
            saved_paths,
            options
        )

        return send_file(
            output_path,
            as_attachment=True,
            download_name=download_name,
            mimetype=mime
        )

    except PDFProcessorError as e:
        return jsonify({"error": str(e)}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
