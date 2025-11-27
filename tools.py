# tools.py

TOOLS = [
    {
        "slug": "merge-pdf",
        "title": "Merge PDF",
        "icon": "merge-pdf.svg",
        "desc": "Combine multiple PDF files into one."
    },
    {
        "slug": "split-pdf",
        "title": "Split PDF",
        "icon": "split-pdf.svg",
        "desc": "Extract specific pages into a new PDF."
    },
    {
        "slug": "compress-pdf",
        "title": "Compress PDF",
        "icon": "compress-pdf.svg",
        "desc": "Reduce PDF file size while keeping quality."
    },
    {
        "slug": "optimize-pdf",
        "title": "Optimize PDF",
        "icon": "optimize-pdf.svg",
        "desc": "Clean and optimize PDFs for smaller size."
    },
    {
        "slug": "rotate-pdf",
        "title": "Rotate PDF",
        "icon": "rotate-pdf.svg",
        "desc": "Rotate all or selected pages in your PDF."
    },
    {
        "slug": "watermark-pdf",
        "title": "Watermark PDF",
        "icon": "watermark-pdf.svg",
        "desc": "Add custom text watermark across PDF pages."
    },
    {
        "slug": "number-pdf",
        "title": "Number Pages",
        "icon": "number-pdf.svg",
        "desc": "Add page numbers to your PDF document."
    },
    {
        "slug": "protect-pdf",
        "title": "Protect PDF",
        "icon": "protect-pdf.svg",
        "desc": "Lock your PDF with a password."
    },
    {
        "slug": "unlock-pdf",
        "title": "Unlock PDF",
        "icon": "unlock-pdf.svg",
        "desc": "Remove password protection from PDFs."
    },
    {
        "slug": "repair-pdf",
        "title": "Repair PDF",
        "icon": "repair-pdf.svg",
        "desc": "Try to fix broken or corrupted PDFs."
    },
    {
        "slug": "organize-pdf",
        "title": "Organize PDF",
        "icon": "organize-pdf.svg",
        "desc": "Reorder, remove or duplicate PDF pages."
    },
    {
        "slug": "sign-pdf",
        "title": "Sign PDF",
        "icon": "sign-pdf.svg",
        "desc": "Add signatures to your PDF files."
    },
    {
        "slug": "annotate-pdf",
        "title": "Annotate PDF",
        "icon": "annotate-pdf.svg",
        "desc": "Highlight, comment and markup PDF pages."
    },
    {
        "slug": "redact-pdf",
        "title": "Redact PDF",
        "icon": "redact-pdf.svg",
        "desc": "Black out sensitive content in PDFs."
    },
    {
        "slug": "pdf-to-word",
        "title": "PDF to Word",
        "icon": "pdf-to-word.svg",
        "desc": "Convert PDFs into editable Word documents."
    },
    {
        "slug": "word-to-pdf",
        "title": "Word to PDF",
        "icon": "word-to-pdf.svg",
        "desc": "Convert DOC/DOCX files into PDF."
    },
    {
        "slug": "pdf-to-image",
        "title": "PDF to Image",
        "icon": "pdf-to-image.svg",
        "desc": "Export PDF pages as JPG or PNG images."
    },
    {
        "slug": "image-to-pdf",
        "title": "Image to PDF",
        "icon": "image-to-pdf.svg",
        "desc": "Combine JPG/PNG/WEBP images into a PDF."
    },
    {
        "slug": "pdf-to-excel",
        "title": "PDF to Excel",
        "icon": "pdf-to-excel.svg",
        "desc": "Convert PDF tables into Excel spreadsheets."
    },
    {
        "slug": "excel-to-pdf",
        "title": "Excel to PDF",
        "icon": "excel-to-pdf.svg",
        "desc": "Turn XLS/XLSX files into PDF."
    },
    {
        "slug": "pdf-to-powerpoint",
        "title": "PDF to PowerPoint",
        "icon": "pdf-to-powerpoint.svg",
        "desc": "Convert PDF slides into PowerPoint."
    },
    {
        "slug": "powerpoint-to-pdf",
        "title": "PowerPoint to PDF",
        "icon": "powerpoint-to-pdf.svg",
        "desc": "Export PPT/PPTX slides as PDF."
    },
    {
        "slug": "ocr-pdf",
        "title": "OCR PDF",
        "icon": "ocr-pdf.svg",
        "desc": "Recognize text in scanned PDF pages."
    },
    {
        "slug": "extract-text",
        "title": "Extract Text",
        "icon": "extract-text.svg",
        "desc": "Pull all text content from a PDF."
    },
    {
        "slug": "extract-images",
        "title": "Extract Images",
        "icon": "extract-images.svg",
        "desc": "Save all embedded images from a PDF."
    },
    {
        "slug": "deskew-pdf",
        "title": "Deskew PDF",
        "icon": "deskew-pdf.svg",
        "desc": "Straighten tilted scanned PDF pages."
    },
    {
        "slug": "crop-pdf",
        "title": "Crop PDF",
        "icon": "crop-pdf.svg",
        "desc": "Trim margins and crop PDF page content."
    },
    {
        "slug": "resize-pdf",
        "title": "Resize PDF",
        "icon": "resize-pdf.svg",
        "desc": "Change page size or scale content."
    },
    {
        "slug": "flatten-pdf",
        "title": "Flatten PDF",
        "icon": "flatten-pdf.svg",
        "desc": "Flatten annotations and form fields."
    },
    {
        "slug": "metadata-editor",
        "title": "Metadata Editor",
        "icon": "metadata-editor.svg",
        "desc": "View and edit PDF title, author, etc."
    },
    {
        "slug": "fill-forms",
        "title": "Fill PDF Forms",
        "icon": "fill-forms.svg",
        "desc": "Fill interactive form fields in PDFs."
    },
    {
        "slug": "background-remover",
        "title": "Remove Background",
        "icon": "background-remover.svg",
        "desc": "Erase background from images using AI."
    },
]

AI_TOOLS = [
    {
        "slug": "ai-editor",
        "title": "AI PDF Editor",
        "url": "/ai/editor",
        "desc": "Edit, rewrite and improve PDF text with AI."
    },
    {
        "slug": "ai-summarizer",
        "title": "AI Summarizer",
        "url": "/ai/summarizer-page",
        "desc": "Generate short summaries of long PDFs."
    },
    {
        "slug": "ai-chat",
        "title": "Chat with PDF",
        "url": "/ai/chat-page",
        "desc": "Ask questions and chat with your document."
    },
    {
        "slug": "ai-translate",
        "title": "AI Translator",
        "url": "/ai/translate-page",
        "desc": "Translate PDF content into any language."
    },
    {
        "slug": "ai-table-extract",
        "title": "AI Table Extractor",
        "url": "/ai/table-page",
        "desc": "Pull clean tables from PDFs using AI."
    },
]


SLUG_TO_TOOL = {t["slug"]: t for t in TOOLS}
