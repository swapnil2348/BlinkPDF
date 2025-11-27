import os
import uuid
import json
from typing import List, Dict, Any, Tuple, Optional

import fitz  # PyMuPDF
from PyPDF2 import PdfReader, PdfWriter
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
def _ensure_folder(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _unique_out_path(output_folder: str, base_name: str, ext: str = ".pdf") -> str:
    _ensure_folder(output_folder)
    safe_base = os.path.splitext(os.path.basename(base_name))[0]
    uid = uuid.uuid4().hex[:8]
    return os.path.join(output_folder, f"{safe_base}_{uid}{ext}")

def _parse_pages_spec(pages_str: str, max_pages: int) -> List[int]:
    result: List[int] = []
    if not pages_str:
        return list(range(max_pages))

    parts = pages_str.replace(" ", "").split(",")
    for part in parts:
        if "-" in part:
            s, e = part.split("-", 1)
            try:
                start, end = int(s), int(e)
            except:
                continue
            for p in range(min(start, end), max(start, end) + 1):
                if 1 <= p <= max_pages:
                    result.append(p - 1)
        else:
            try:
                p = int(part)
                if 1 <= p <= max_pages:
                    result.append(p - 1)
            except:
                pass
    return list(dict.fromkeys(result))

def _compress_pdf(file_path: str, output_folder: str, level: str) -> str:
    doc = fitz.open(file_path)
    level = str(level)

    if level == "1":
        garbage = 1
    elif level == "3":
        garbage = 4
    else:
        garbage = 2

    out = _unique_out_path(output_folder, "compressed.pdf")
    doc.save(out, garbage=garbage, deflate=True, clean=True)
    doc.close()
    return out

def _merge_pdfs(file_paths: List[str], output_folder: str) -> str:
    writer = PdfWriter()
    for path in file_paths:
        reader = PdfReader(path)
        for page in reader.pages:
            writer.add_page(page)

    out = _unique_out_path(output_folder, "merged.pdf")
    with open(out, "wb") as f:
        writer.write(f)
    return out

def _split_pdf(file_path: str, output_folder: str, pages_spec: str) -> str:
    reader = PdfReader(file_path)
    indices = _parse_pages_spec(pages_spec, len(reader.pages))

    writer = PdfWriter()
    for idx in indices:
        writer.add_page(reader.pages[idx])

    out = _unique_out_path(output_folder, "split.pdf")
    with open(out, "wb") as f:
        writer.write(f)
    return out

def _rotate_pdf(file_path: str, output_folder: str, angle: int) -> str:
    reader = PdfReader(file_path)
    writer = PdfWriter()

    for page in reader.pages:
        page.rotate(angle)
        writer.add_page(page)

    out = _unique_out_path(output_folder, "rotated.pdf")
    with open(out, "wb") as f:
        writer.write(f)
    return out

def _watermark_pdf(file_path: str, output_folder: str, text: str) -> str:
    wm_path = _unique_out_path(output_folder, "wm.pdf", "")
    c = canvas.Canvas(wm_path, pagesize=A4)

    c.setFont("Helvetica-Bold", 60)
    c.setFillGray(0.4, 0.3)
    c.translate(300, 400)
    c.rotate(45)
    c.drawCentredString(0, 0, text)
    c.save()

    reader = PdfReader(file_path)
    wm = PdfReader(wm_path)
    writer = PdfWriter()

    for page in reader.pages:
        page.merge_page(wm.pages[0])
        writer.add_page(page)

    out = _unique_out_path(output_folder, "watermarked.pdf")
    with open(out, "wb") as f:
        writer.write(f)

    return out

def _image_to_pdf(paths: List[str], output_folder: str) -> str:
    images = []
    for p in paths:
        img = Image.open(p).convert("RGB")
        images.append(img)

    out = _unique_out_path(output_folder, "images.pdf")
    images[0].save(out, save_all=True, append_images=images[1:])
    return out

def _protect_pdf(file_path: str, output_folder: str, password: str) -> str:
    reader = PdfReader(file_path)
    writer = PdfWriter()

    for p in reader.pages:
        writer.add_page(p)

    writer.encrypt(password, password)

    out = _unique_out_path(output_folder, "protected.pdf")
    with open(out, "wb") as f:
        writer.write(f)
    return out

def _unlock_pdf(file_path: str, output_folder: str, password: str) -> Tuple[Optional[str], Optional[str]]:
    try:
        reader = PdfReader(file_path, password=password)
    except:
        return None, "Wrong password"

    writer = PdfWriter()
    for p in reader.pages:
        writer.add_page(p)

    out = _unique_out_path(output_folder, "unlocked.pdf")
    with open(out, "wb") as f:
        writer.write(f)

    return out, None

def process_pdf(slug: str, file_paths: List[str], output_folder: str, form_data: Dict[str, Any]) -> Dict[str, Any]:

    primary = file_paths[0]

    try:

        if slug == "compress-pdf":
            out = _compress_pdf(primary, output_folder, form_data.get("compression_level", "2"))

        elif slug == "merge-pdf":
            out = _merge_pdfs(file_paths, output_folder)

        elif slug == "split-pdf":
            out = _split_pdf(primary, output_folder, form_data.get("pages", ""))

        elif slug == "rotate-pdf":
            angle = int(form_data.get("rotation_angle", 0))
            out = _rotate_pdf(primary, output_folder, angle)

        elif slug == "watermark-pdf":
            out = _watermark_pdf(primary, output_folder, form_data.get("watermark_text", "CONFIDENTIAL"))

        elif slug == "image-to-pdf":
            out = _image_to_pdf(file_paths, output_folder)

        elif slug == "protect-pdf":
            out = _protect_pdf(primary, output_folder, form_data.get("password"))

        elif slug == "unlock-pdf":
            out, err = _unlock_pdf(primary, output_folder, form_data.get("password"))
            if err:
                return {"type":"error", "data":{"msg":err}, "status":400}

        else:
            out = primary

        return {
            "type": "file",
            "path": out,
            "download_name": os.path.basename(out),
            "mimetype": "application/pdf"
        }

    except Exception as e:
        return {"type":"error","data":{"error":str(e)},"status":500}
