import os
import uuid
import io
import zipfile

from PyPDF2 import PdfReader, PdfWriter
import fitz  # PyMuPDF
from PIL import Image


def _ensure_dir(path: str) -> None:
    """
    Make sure the directory exists.
    """
    if path and not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


def process_pdf(slug: str, file_paths, output_folder: str, form_data: dict):
    """
    Central processing engine for all PDF tools.

    Parameters
    ----------
    slug : str
        Tool identifier (e.g., 'merge-pdf', 'split-pdf', 'rotate-pdf', etc.)
    file_paths : list[str]
        List of saved input file paths (already uploaded).
    output_folder : str
        Folder where generated outputs should be written.
    form_data : dict
        Extra options from request.form (page ranges, rotation, quality, etc.)

    Returns
    -------
    dict
        {
          "type": "file" | "json" | "error",
          "path": <file_path>,          # for type="file"
          "mimetype": <mimetype>,       # for type="file"
          "download_name": <filename>,  # for type="file"
          "data": {...},                # for type="json"
          "status_code": int            # for type="json"/"error"
        }
    """
    _ensure_dir(output_folder)

    if not file_paths:
        return {
            "type": "error",
            "data": {"message": "No files provided to processing engine"},
            "status_code": 400,
        }

    # -----------------------------
    # 1. MERGE PDF
    # -----------------------------
    if slug == "merge-pdf":
        output_path = os.path.join(output_folder, f"merged_{uuid.uuid4().hex}.pdf")

        writer = PdfWriter()
        for path in file_paths:
            reader = PdfReader(path)
            for page in reader.pages:
                writer.add_page(page)

        with open(output_path, "wb") as f:
            writer.write(f)

        return {
            "type": "file",
            "path": output_path,
            "mimetype": "application/pdf",
            "download_name": "merged.pdf",
        }

    # -----------------------------
    # 2. SPLIT PDF  -> ZIP OF PER-PAGE PDFs
    # -----------------------------
    if slug == "split-pdf":
        input_path = file_paths[0]
        reader = PdfReader(input_path)

        zip_output_path = os.path.join(
            output_folder, f"split_{uuid.uuid4().hex}.zip"
        )

        # Write each page into the zip as a separate PDF
        with zipfile.ZipFile(zip_output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for i, page in enumerate(reader.pages, start=1):
                writer = PdfWriter()
                writer.add_page(page)
                page_bytes = io.BytesIO()
                writer.write(page_bytes)
                page_bytes.seek(0)
                zf.writestr(f"page_{i}.pdf", page_bytes.read())

        return {
            "type": "file",
            "path": zip_output_path,
            "mimetype": "application/zip",
            "download_name": "split_pages.zip",
        }

    # -----------------------------
    # 3. COMPRESS PDF (very basic)
    # -----------------------------
    if slug == "compress-pdf":
        # NOTE: True high-quality compression would use qpdf/ghostscript.
        # This is a placeholder – re-write pages into a new PDF.
        input_path = file_paths[0]
        reader = PdfReader(input_path)
        writer = PdfWriter()

        # Option: you can drop metadata / annotations for some size benefit
        for page in reader.pages:
            writer.add_page(page)

        output_path = os.path.join(output_folder, f"compressed_{uuid.uuid4().hex}.pdf")
        with open(output_path, "wb") as f:
            writer.write(f)

        return {
            "type": "file",
            "path": output_path,
            "mimetype": "application/pdf",
            "download_name": "compressed.pdf",
        }

    # -----------------------------
    # 4. ROTATE PDF
    # -----------------------------
    if slug == "rotate-pdf":
        input_path = file_paths[0]
        reader = PdfReader(input_path)
        writer = PdfWriter()

        # Default rotation is 90 degrees clockwise
        rotation_str = form_data.get("rotation", "90")
        try:
            rotation = int(rotation_str)
        except ValueError:
            rotation = 90

        for page in reader.pages:
            # PyPDF2 3.x uses rotate method returning a new page
            page = page.rotate(rotation)
            writer.add_page(page)

        output_path = os.path.join(output_folder, f"rotated_{uuid.uuid4().hex}.pdf")
        with open(output_path, "wb") as f:
            writer.write(f)

        return {
            "type": "file",
            "path": output_path,
            "mimetype": "application/pdf",
            "download_name": "rotated.pdf",
        }

    # -----------------------------
    # 5. UNLOCK PDF
    # -----------------------------
    if slug == "unlock-pdf":
        input_path = file_paths[0]
        reader = PdfReader(input_path)

        password = form_data.get("password", "")
        if reader.is_encrypted:
            # Try provided password, then blank as a fallback
            if password:
                reader.decrypt(password)
            else:
                reader.decrypt("")

        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)

        output_path = os.path.join(output_folder, f"unlocked_{uuid.uuid4().hex}.pdf")
        with open(output_path, "wb") as f:
            writer.write(f)

        return {
            "type": "file",
            "path": output_path,
            "mimetype": "application/pdf",
            "download_name": "unlocked.pdf",
        }

    # -----------------------------
    # 6. PDF TO IMAGE (support both slugs)
    # -----------------------------
    if slug in ("pdf-to-image", "pdf-to-jpg"):
        input_path = file_paths[0]

        doc = fitz.open(input_path)
        zip_output_path = os.path.join(
            output_folder, f"images_{uuid.uuid4().hex}.zip"
        )

        with zipfile.ZipFile(zip_output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for i in range(len(doc)):
                page = doc.load_page(i)
                pix = page.get_pixmap()
                img_name = f"page_{i+1}.jpg"
                img_bytes = pix.tobytes("jpeg")
                zf.writestr(img_name, img_bytes)

        return {
            "type": "file",
            "path": zip_output_path,
            "mimetype": "application/zip",
            "download_name": "pdf_images.zip",
        }

    # -----------------------------
    # 7. IMAGE TO PDF (support both slugs)
    # -----------------------------
    if slug in ("image-to-pdf", "jpg-to-pdf"):
        images = []

        for path in file_paths:
            img = Image.open(path).convert("RGB")
            images.append(img)

        if not images:
            return {
                "type": "error",
                "data": {"message": "No valid images found"},
                "status_code": 400,
            }

        output_path = os.path.join(output_folder, f"images_{uuid.uuid4().hex}.pdf")

        if len(images) == 1:
            images[0].save(output_path)
        else:
            images[0].save(output_path, save_all=True, append_images=images[1:])

        return {
            "type": "file",
            "path": output_path,
            "mimetype": "application/pdf",
            "download_name": "images.pdf",
        }

    # -----------------------------
    # PLACEHOLDER FOR OTHER TOOLS
    # -----------------------------
    # For now, for all remaining 33 tools that are not implemented yet,
    # we just confirm that upload + routing works.
    return {
        "type": "json",
        "data": {
            "status": "success",
            "tool": slug,
            "message": "Uploaded and processing engine connected successfully (placeholder).",
        },
        "status_code": 200,
    }
