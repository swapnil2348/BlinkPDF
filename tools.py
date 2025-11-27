# tools.py

# ---------------- PDF TOOLS (33) ----------------

TOOLS = [

    {"slug": "merge-pdf", "title": "Merge PDF", "icon": "merge-pdf.svg", "description": "Combine multiple PDF files into one document"},
    {"slug": "split-pdf", "title": "Split PDF", "icon": "split-pdf.svg", "description": "Split a PDF into multiple files"},
    {"slug": "compress-pdf", "title": "Compress PDF", "icon": "compress-pdf.svg", "description": "Reduce PDF size without losing quality"},
    {"slug": "optimize-pdf", "title": "Optimize PDF", "icon": "optimize-pdf.svg", "description": "Optimize PDF for web and mobile"},
    {"slug": "rotate-pdf", "title": "Rotate PDF", "icon": "rotate-pdf.svg", "description": "Rotate pages at any angle"},
    {"slug": "watermark-pdf", "title": "Watermark PDF", "icon": "watermark-pdf.svg", "description": "Add watermark text or image"},
    {"slug": "number-pdf", "title": "Number Pages", "icon": "number-pdf.svg", "description": "Insert page numbers in PDF"},
    {"slug": "protect-pdf", "title": "Protect PDF", "icon": "protect-pdf.svg", "description": "Add password to PDF file"},
    {"slug": "unlock-pdf", "title": "Unlock PDF", "icon": "unlock-pdf.svg", "description": "Remove password from a PDF"},
    {"slug": "repair-pdf", "title": "Repair PDF", "icon": "repair-pdf.svg", "description": "Fix corrupted PDF files"},
    {"slug": "organize-pdf", "title": "Organize PDF", "icon": "organize-pdf.svg", "description": "Rearrange PDF pages"},
    {"slug": "sign-pdf", "title": "Sign PDF", "icon": "sign-pdf.svg", "description": "Sign your PDF electronically"},
    {"slug": "annotate-pdf", "title": "Annotate PDF", "icon": "annotate-pdf.svg", "description": "Add notes & comments"},
    {"slug": "redact-pdf", "title": "Redact PDF", "icon": "redact-pdf.svg", "description": "Hide confidential content"},
    {"slug": "pdf-to-word", "title": "PDF to Word", "icon": "pdf-to-word.svg", "description": "Convert PDF to DOCX file"},
    {"slug": "word-to-pdf", "title": "Word to PDF", "icon": "word-to-pdf.svg", "description": "Convert DOCX to PDF"},
    {"slug": "pdf-to-image", "title": "PDF to Image", "icon": "pdf-to-image.svg", "description": "Convert PDF pages to images"},
    {"slug": "image-to-pdf", "title": "Image to PDF", "icon": "image-to-pdf.svg", "description": "Convert images to PDF"},
    {"slug": "pdf-to-excel", "title": "PDF to Excel", "icon": "pdf-to-excel.svg", "description": "Convert PDF data to Excel"},
    {"slug": "excel-to-pdf", "title": "Excel to PDF", "icon": "excel-to-pdf.svg", "description": "Convert XLSX to PDF"},
    {"slug": "pdf-to-powerpoint", "title": "PDF to PowerPoint", "icon": "pdf-to-powerpoint.svg", "description": "PDF to PPTX"},
    {"slug": "powerpoint-to-pdf", "title": "PowerPoint to PDF", "icon": "powerpoint-to-pdf.svg", "description": "PPTX to PDF"},
    {"slug": "ocr-pdf", "title": "OCR PDF", "icon": "ocr-pdf.svg", "description": "Extract text using OCR"},
    {"slug": "extract-text", "title": "Extract Text", "icon": "extract-text.svg", "description": "Extract text from PDF"},
    {"slug": "extract-images", "title": "Extract Images", "icon": "extract-images.svg", "description": "Extract images from PDF"},
    {"slug": "deskew-pdf", "title": "Deskew PDF", "icon": "deskew-pdf.svg", "description": "Fix tilted PDF pages"},
    {"slug": "crop-pdf", "title": "Crop PDF", "icon": "crop-pdf.svg", "description": "Crop PDF margins"},
    {"slug": "resize-pdf", "title": "Resize PDF", "icon": "resize-pdf.svg", "description": "Resize PDF pages"},
    {"slug": "flatten-pdf", "title": "Flatten PDF", "icon": "flatten-pdf.svg", "description": "Flatten form fields"},
    {"slug": "metadata-editor", "title": "Metadata Editor", "icon": "metadata-editor.svg", "description": "Edit PDF metadata"},
    {"slug": "fill-forms", "title": "Fill PDF Forms", "icon": "fill-forms.svg", "description": "Fill & save PDF forms"},
    {"slug": "background-remover", "title": "Remove Background", "icon": "background-remover.svg", "description": "Remove image background"},

]


# ---------------- AI TOOLS (5) ----------------

AI_TOOLS = [

    {
        "slug": "editor",
        "title": "AI PDF Editor",
        "icon": "ai-editor.svg",
        "description": "Edit PDF documents with AI"
    },
    {
        "slug": "summarizer",
        "title": "AI Summarizer",
        "icon": "ai-summarizer.svg",
        "description": "Summarize your PDF using AI"
    },
    {
        "slug": "chat",
        "title": "Chat with PDF",
        "icon": "ai-chat.svg",
        "description": "Ask questions from your PDF"
    },
    {
        "slug": "translator",
        "title": "AI Translator",
        "icon": "ai-translate.svg",
        "description": "Translate PDF into any language"
    },
    {
        "slug": "table-extract",
        "title": "AI Table Extractor",
        "icon": "ai-table.svg",
        "description": "Extract tables using AI"
    },

]


# ---------------- SLUG MAPS ----------------

SLUG_TO_TOOL = {tool["slug"]: tool for tool in TOOLS}
SLUG_TO_AI_TOOL = {tool["slug"]: tool for tool in AI_TOOLS}
