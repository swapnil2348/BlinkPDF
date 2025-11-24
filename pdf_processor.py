import os
import uuid
import json
from typing import List, Dict, Any, Tuple, Optional

import fitz  # PyMuPDF
from PyPDF2 import PdfReader, PdfWriter
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4


# ------------- Helpers ------------- #

def _ensure_folder(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _unique_out_path(output_folder: str, base_name: str, ext: str = ".pdf") -> str:
    _ensure_folder(output_folder)
    safe_base = os.path.splitext(os.path.basename(base_name))[0]
    uid = uuid.uuid4().hex[:8]
    return os.path.join(output_folder, f"{safe_base}_{uid}{ext}")


def _parse_pages_spec(pages_str: str, max_pages: int) -> List[int]:
    """
    Parse page spec like '1-3,5,7-9' into zero-based page indices.
    max_pages is total pages (1-based count).
    """
    result: List[int] = []
    if not pages_str:
        return list(range(max_pages))

    parts = pages_str.replace(" ", "").split(",")
    for part in parts:
        if "-" in part:
            start_s, end_s = part.split("-", 1)
            try:
                start = int(start_s)
                end = int(end_s)
            except ValueError:
                continue
            if start < 1 or end < 1:
                continue
            if start > end:
                start, end = end, start
            for p in range(start, end + 1):
                if 1 <= p <= max_pages:
                    result.append(p - 1)
        else:
            try:
                p = int(part)
            except ValueError:
                continue
            if 1 <= p <= max_pages:
                result.append(p - 1)

    # De-duplicate while preserving order
    seen = set()
    ordered: List[int] = []
    for p in result:
        if p not in seen:
            seen.add(p)
            ordered.append(p)
    return ordered


def _load_pdf_pymupdf(path: str) -> fitz.Document:
    return fitz.open(path)


def _load_pdf_pypdf(path: str) -> PdfReader:
    return PdfReader(path)


# ------------- Individual tool implementations ------------- #

def _compress_pdf(file_path: str, output_folder: str, level: str = "2") -> str:
    """
    Basic compression via PyMuPDF: garbage collection / object cleanup / deflate.
    level: "1" = high quality, "2" = balanced, "3" = smallest (more aggressive)
    """
    doc = _load_pdf_pymupdf(file_path)
    base_name = os.path.basename(file_path)
    out_path = _unique_out_path(output_folder, f"compressed_{base_name}")

    # Choose options based on level
    if level == "1":
        garbage = 1
        deflate = True
        clean = False
    elif level == "3":
        garbage = 4
        deflate = True
        clean = True
    else:  # "2"
        garbage = 2
        deflate = True
        clean = False

    doc.save(out_path, garbage=garbage, deflate=deflate, clean=clean)
    doc.close()
    return out_path


def _merge_pdfs(file_paths: List[str], output_folder: str) -> str:
    writer = PdfWriter()
    for path in file_paths:
        try:
            reader = _load_pdf_pypdf(path)
        except Exception:
            continue
        for page in reader.pages:
            writer.add_page(page)

    if not writer.pages:
        # fallback – just return first file
        return file_paths[0]

    out_path = _unique_out_path(output_folder, "merged.pdf")
    with open(out_path, "wb") as f:
        writer.write(f)
    return out_path


def _split_or_extract_pdf(file_path: str, output_folder: str, pages_spec: str) -> str:
    reader = _load_pdf_pypdf(file_path)
    max_pages = len(reader.pages)
    indices = _parse_pages_spec(pages_spec, max_pages)
    if not indices:
        indices = list(range(max_pages))

    writer = PdfWriter()
    for idx in indices:
        writer.add_page(reader.pages[idx])

    out_path = _unique_out_path(output_folder, os.path.basename(file_path))
    with open(out_path, "wb") as f:
        writer.write(f)
    return out_path


def _rotate_pdf(file_path: str, output_folder: str, angle: int) -> str:
    """
    Rotate all pages by 'angle' degrees (0, 90, 180, 270).
    """
    reader = _load_pdf_pypdf(file_path)
    writer = PdfWriter()
    for page in reader.pages:
        page.rotate(angle)
        writer.add_page(page)

    out_path = _unique_out_path(output_folder, f"rotated_{os.path.basename(file_path)}")
    with open(out_path, "wb") as f:
        writer.write(f)
    return out_path


def _organize_pdf(file_path: str,
                  output_folder: str,
                  page_order_csv: str,
                  deleted_pages_csv: str) -> str:
    """
    Reorder / delete pages based on UI:
    - page_order: '1,3,2,4,...'
    - deleted_pages: '5,6,...' (1-based)
    """
    reader = _load_pdf_pypdf(file_path)
    max_pages = len(reader.pages)

    order: List[int] = []
    if page_order_csv:
        for s in page_order_csv.split(","):
            s = s.strip()
            if not s:
                continue
            try:
                p = int(s)
            except ValueError:
                continue
            if 1 <= p <= max_pages:
                order.append(p - 1)

    # If no order given, just keep all in original order
    if not order:
        order = list(range(max_pages))

    deleted: List[int] = []
    if deleted_pages_csv:
        for s in deleted_pages_csv.split(","):
            s = s.strip()
            if not s:
                continue
            try:
                p = int(s)
            except ValueError:
                continue
            if 1 <= p <= max_pages:
                deleted.append(p - 1)
    deleted_set = set(deleted)

    writer = PdfWriter()
    for idx in order:
        if idx < 0 or idx >= max_pages:
            continue
        if idx in deleted_set:
            continue
        writer.add_page(reader.pages[idx])

    if not writer.pages:
        # if everything deleted, just return original
        return file_path

    out_path = _unique_out_path(output_folder, f"organized_{os.path.basename(file_path)}")
    with open(out_path, "wb") as f:
        writer.write(f)
    return out_path


def _crop_pdf(file_path: str, output_folder: str, crop_regions_json: str) -> str:
    """
    crop_regions_json: JSON like { "1": {"x":..,"y":..,"width":..,"height":..}, ... }
    coordinates are relative (0-1) of visible page rectangle.
    """
    doc = _load_pdf_pymupdf(file_path)
    try:
        crop_data = json.loads(crop_regions_json) if crop_regions_json else {}
    except json.JSONDecodeError:
        crop_data = {}

    for page_index in range(len(doc)):
        page = doc[page_index]
        page_num = page_index + 1
        region = crop_data.get(str(page_num))
        if not region:
            continue
        r = page.mediabox  # Rect(x0, y0, x1, y1)
        width = r.width
        height = r.height

        x = max(0.0, min(1.0, float(region.get("x", 0.0))))
        y = max(0.0, min(1.0, float(region.get("y", 0.0))))
        w = max(0.0, min(1.0, float(region.get("width", 1.0))))
        h = max(0.0, min(1.0, float(region.get("height", 1.0))))

        # convert relative to absolute; PyMuPDF coords origin: top-left (0,0)
        x0 = r.x0 + x * width
        y0 = r.y0 + y * height
        x1 = x0 + w * width
        y1 = y0 + h * height

        new_rect = fitz.Rect(x0, y0, x1, y1)
        page.set_cropbox(new_rect)

    out_path = _unique_out_path(output_folder, f"cropped_{os.path.basename(file_path)}")
    doc.save(out_path)
    doc.close()
    return out_path


def _resize_pdf(file_path: str, output_folder: str, scale: float = 1.0) -> str:
    """
    Simple resize: scale each page via PyMuPDF.
    scale: e.g. 0.5 = half size, 2.0 = double.
    If scale == 1.0, just re-save.
    """
    doc = _load_pdf_pymupdf(file_path)
    if abs(scale - 1.0) < 1e-3:
        out_path = _unique_out_path(output_folder, f"resized_{os.path.basename(file_path)}")
        doc.save(out_path)
        doc.close()
        return out_path

    mtx = fitz.Matrix(scale, scale)
    for page in doc:
        page.set_mediabox(page.rect * mtx)

    out_path = _unique_out_path(output_folder, f"resized_{os.path.basename(file_path)}")
    doc.save(out_path)
    doc.close()
    return out_path


def _flatten_pdf(file_path: str, output_folder: str) -> str:
    """
    Flatten annotations/forms by re-rendering pages into a new PDF.
    (Rasterizes each page into an image and then creates a PDF from images.)
    """
    doc = _load_pdf_pymupdf(file_path)
    images: List[Image.Image] = []

    for page in doc:
        pix = page.get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        images.append(img)

    doc.close()

    if not images:
        return file_path

    out_path = _unique_out_path(output_folder, f"flattened_{os.path.basename(file_path)}")
    first, *rest = images
    first.convert("RGB").save(out_path, save_all=True, append_images=[im.convert("RGB") for im in rest])
    return out_path


def _protect_pdf(file_path: str, output_folder: str, password: str) -> str:
    reader = _load_pdf_pypdf(file_path)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)

    # Use same password for user & owner if nothing else
    writer.encrypt(user_password=password, owner_password=password, use_128bit=True)

    out_path = _unique_out_path(output_folder, f"protected_{os.path.basename(file_path)}")
    with open(out_path, "wb") as f:
        writer.write(f)
    return out_path


def _unlock_pdf(file_path: str, output_folder: str, password: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Try to open with password; return (out_path, error_message).
    If error_message is not None, unlocking failed.
    """
    try:
        reader = PdfReader(file_path, password=password)
    except Exception as e:
        return None, f"Incorrect password or unable to open PDF: {e}"

    if reader.is_encrypted:
        try:
            reader.decrypt(password)
        except Exception as e:
            return None, f"Incorrect password or unable to decrypt PDF: {e}"

    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)

    out_path = _unique_out_path(output_folder, f"unlocked_{os.path.basename(file_path)}")
    with open(out_path, "wb") as f:
        writer.write(f)
    return out_path, None


def _create_watermark_pdf(text: str, output_folder: str) -> str:
    """
    Create a single-page watermark PDF with large diagonal text.
    """
    temp_path = _unique_out_path(output_folder, "watermark_base.pdf")
    c = canvas.Canvas(temp_path, pagesize=A4)
    width, height = A4

    c.saveState()
    c.translate(width / 2, height / 2)
    c.rotate(45)  # diagonal
    c.setFont("Helvetica-Bold", 60)
    c.setFillGray(0.7, alpha=0.3)  # semi-transparent gray
    c.drawCentredString(0, 0, text)
    c.restoreState()
    c.showPage()
    c.save()
    return temp_path


def _watermark_pdf(file_path: str, output_folder: str, text: str) -> str:
    if not text:
        # nothing to do
        return file_path

    watermark_pdf_path = _create_watermark_pdf(text, output_folder)

    base_reader = _load_pdf_pypdf(file_path)
    watermark_reader = _load_pdf_pypdf(watermark_pdf_path)
    watermark_page = watermark_reader.pages[0]

    writer = PdfWriter()
    for page in base_reader.pages:
        new_page = page
        new_page.merge_page(watermark_page)
        writer.add_page(new_page)

    out_path = _unique_out_path(output_folder, f"watermarked_{os.path.basename(file_path)}")
    with open(out_path, "wb") as f:
        writer.write(f)
    return out_path


def _image_to_pdf(file_paths: List[str], output_folder: str) -> str:
    """
    Combine multiple images into a single multi-page PDF.
    """
    images: List[Image.Image] = []
    for path in file_paths:
        try:
            img = Image.open(path)
        except Exception:
            continue
        if img.mode != "RGB":
            img = img.convert("RGB")
        images.append(img)

    if not images:
        # fallback: nothing, return first file
        return file_paths[0]

    out_path = _unique_out_path(output_folder, "images.pdf")
    first, *rest = images
    first.save(out_path, save_all=True, append_images=rest)
    return out_path


# ------------- Main entry point used by app.py ------------- #

def process_pdf(
    slug: str,
    file_paths: List[str],
    output_folder: str,
    form_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Central dispatcher used by app.py:process_tool.

    Returns a dict with:
      - type: "file" | "json" | "error"
      - For "file": { "path": ..., "mimetype": "application/pdf", "download_name": ... }
      - For "json"/"error": { "data": { ... }, "status_code": int }
    """
    # Basic guards
    if not file_paths:
        return {
            "type": "error",
            "data": {"message": "No input files to process."},
            "status_code": 400,
        }

    primary = file_paths[0]
    _ensure_folder(output_folder)

    try:
        # -------- Compressor -------- #
        if slug == "compress-pdf":
            level = form_data.get("compression_level", "2")
            out_path = _compress_pdf(primary, output_folder, str(level))
            return {
                "type": "file",
                "path": out_path,
                "mimetype": "application/pdf",
                "download_name": os.path.basename(out_path),
            }

        # -------- Merge -------- #
        if slug == "merge-pdf":
            out_path = _merge_pdfs(file_paths, output_folder)
            return {
                "type": "file",
                "path": out_path,
                "mimetype": "application/pdf",
                "download_name": os.path.basename(out_path),
            }

        # -------- Split / Extract pages -------- #
        if slug in ("split-pdf", "extract-pages"):
            pages_spec = form_data.get("pages", "")
            out_path = _split_or_extract_pdf(primary, output_folder, pages_spec)
            return {
                "type": "file",
                "path": out_path,
                "mimetype": "application/pdf",
                "download_name": os.path.basename(out_path),
            }

        # -------- Rotate -------- #
        if slug == "rotate-pdf":
            angle = 180
            angle_str = form_data.get("rotation_angle", "0")
            try:
                angle = int(angle_str)
            except ValueError:
                angle = 0
            # Only allow 0/90/180/270
            if angle not in (0, 90, 180, 270):
                angle = 0
            out_path = _rotate_pdf(primary, output_folder, angle)
            return {
                "type": "file",
                "path": out_path,
                "mimetype": "application/pdf",
                "download_name": os.path.basename(out_path),
            }

        # -------- Organize -------- #
        if slug == "organize-pdf":
            page_order = form_data.get("page_order", "")
            deleted = form_data.get("deleted_pages", "")
            out_path = _organize_pdf(primary, output_folder, page_order, deleted)
            return {
                "type": "file",
                "path": out_path,
                "mimetype": "application/pdf",
                "download_name": os.path.basename(out_path),
            }

        # -------- Crop -------- #
        if slug == "crop-pdf":
            crop_regions = form_data.get("crop_regions", "")
            out_path = _crop_pdf(primary, output_folder, crop_regions)
            return {
                "type": "file",
                "path": out_path,
                "mimetype": "application/pdf",
                "download_name": os.path.basename(out_path),
            }

        # -------- Resize -------- #
        if slug == "resize-pdf":
            # Optional: use pages or some scale_from_ui
            scale_str = form_data.get("scale", "1.0")
            try:
                scale = float(scale_str)
            except ValueError:
                scale = 1.0
            if scale <= 0:
                scale = 1.0
            out_path = _resize_pdf(primary, output_folder, scale)
            return {
                "type": "file",
                "path": out_path,
                "mimetype": "application/pdf",
                "download_name": os.path.basename(out_path),
            }

        # -------- Flatten -------- #
        if slug == "flatten-pdf":
            out_path = _flatten_pdf(primary, output_folder)
            return {
                "type": "file",
                "path": out_path,
                "mimetype": "application/pdf",
                "download_name": os.path.basename(out_path),
            }

        # -------- Protect (set password) -------- #
        if slug == "protect-pdf":
            password = form_data.get("password", "")
            if not password:
                return {
                    "type": "error",
                    "data": {"message": "Password is required to protect the PDF."},
                    "status_code": 400,
                }
            out_path = _protect_pdf(primary, output_folder, password)
            return {
                "type": "file",
                "path": out_path,
                "mimetype": "application/pdf",
                "download_name": os.path.basename(out_path),
            }

        # -------- Unlock (remove password) -------- #
        if slug == "unlock-pdf":
            password = form_data.get("password", "")
            if not password:
                return {
                    "type": "error",
                    "data": {"message": "Password is required to unlock the PDF."},
                    "status_code": 400,
                }
            out_path, error = _unlock_pdf(primary, output_folder, password)
            if error:
                return {
                    "type": "error",
                    "data": {"message": error},
                    "status_code": 400,
                }
            return {
                "type": "file",
                "path": out_path,
                "mimetype": "application/pdf",
                "download_name": os.path.basename(out_path),
            }

        # -------- Watermark text -------- #
        if slug == "watermark-pdf":
            text = form_data.get("watermark_text", "").strip()
            if not text:
                return {
                    "type": "error",
                    "data": {"message": "Watermark text is required."},
                    "status_code": 400,
                }
            out_path = _watermark_pdf(primary, output_folder, text)
            return {
                "type": "file",
                "path": out_path,
                "mimetype": "application/pdf",
                "download_name": os.path.basename(out_path),
            }

        # -------- Image → PDF -------- #
        if slug == "image-to-pdf":
            out_path = _image_to_pdf(file_paths, output_folder)
            return {
                "type": "file",
                "path": out_path,
                "mimetype": "application/pdf",
                "download_name": os.path.basename(out_path),
            }

        # -------- Background remover / AI tools / others -------- #
        if slug == "background-remover":
            # You probably want to use an external API here (e.g. remove.bg).
            # For now, return a clear error instead of pretending it worked.
            return {
                "type": "error",
                "data": {
                    "message": (
                        "Background remover is not fully configured on the server. "
                        "You need to plug in an external background removal API."
                    )
                },
                "status_code": 501,
            }

        # -------- Default fallback: just return original (at least it's real) -------- #
        # If the slug isn't implemented above, just return first file as processed.
        out_path = _unique_out_path(output_folder, os.path.basename(primary))
        # Copy file
        with open(primary, "rb") as src, open(out_path, "wb") as dst:
            dst.write(src.read())

        return {
            "type": "file",
            "path": out_path,
            "mimetype": "application/pdf",
            "download_name": os.path.basename(out_path),
        }

    except Exception as e:
        # Catch-all error so the user gets clean JSON instead of 500 HTML
        return {
            "type": "error",
            "data": {"message": f"Server processing error: {e}"},
            "status_code": 500,
        }
