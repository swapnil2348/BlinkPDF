# tools.py

# 33 MAIN PDF TOOLS
TOOLS = [
    {
        "slug": "merge-pdf",
        "title": "Merge PDF",
        "icon": "merge-pdf.svg",
        "desc": "Combine multiple PDF files into a single, clean document."
    },
    {
        "slug": "split-pdf",
        "title": "Split PDF",
        "icon": "split-pdf.svg",
        "desc": "Split a PDF into separate pages or custom page ranges."
    },
    {
        "slug": "compress-pdf",
        "title": "Compress PDF",
        "icon": "compress-pdf.svg",
        "desc": "Reduce PDF file size while keeping readable quality."
    },
    {
        "slug": "optimize-pdf",
        "title": "Optimize PDF",
        "icon": "optimize-pdf.svg",
        "desc": "Clean, optimize and shrink PDFs for faster sharing."
    },
    {
        "slug": "rotate-pdf",
        "title": "Rotate PDF",
        "icon": "rotate-pdf.svg",
        "desc": "Rotate pages to the correct orientation and save permanently."
    },
    {
        "slug": "watermark-pdf",
        "title": "Watermark PDF",
        "icon": "watermark-pdf.svg",
        "desc": "Add custom text watermarks across your PDF pages."
    },
    {
        "slug": "number-pdf",
        "title": "Number Pages",
        "icon": "number-pdf.svg",
        "desc": "Add professional page numbers to your PDF documents."
    },
    {
        "slug": "protect-pdf",
        "title": "Protect PDF",
        "icon": "protect-pdf.svg",
        "desc": "Lock your PDF with a password to prevent unwanted access."
    },
    {
        "slug": "unlock-pdf",
        "title": "Unlock PDF",
        "icon": "unlock-pdf.svg",
        "desc": "Remove password protection from PDFs you own."
    },
    {
        "slug": "repair-pdf",
        "title": "Repair PDF",
        "icon": "repair-pdf.svg",
        "desc": "Try to fix corrupted or unreadable PDF files."
    },
    {
        "slug": "organize-pdf",
        "title": "Organize PDF",
        "icon": "organize-pdf.svg",
        "desc": "Reorder, delete or duplicate PDF pages visually."
    },
    {
        "slug": "sign-pdf",
        "title": "Sign PDF",
        "icon": "sign-pdf.svg",
        "desc": "Add your signature or initials to any PDF document."
    },
    {
        "slug": "annotate-pdf",
        "title": "Annotate PDF",
        "icon": "annotate-pdf.svg",
        "desc": "Highlight, comment and draw directly on your PDFs."
    },
    {
        "slug": "redact-pdf",
        "title": "Redact PDF",
        "icon": "redact-pdf.svg",
        "desc": "Permanently hide sensitive text and areas in your PDF."
    },
    {
        "slug": "pdf-to-word",
        "title": "PDF to Word",
        "icon": "pdf-to-word.svg",
        "desc": "Convert PDF documents into editable Word files (DOCX)."
    },
    {
        "slug": "word-to-pdf",
        "title": "Word to PDF",
        "icon": "word-to-pdf.svg",
        "desc": "Convert DOC or DOCX files into high-quality PDFs."
    },
    {
        "slug": "pdf-to-image",
        "title": "PDF to Image",
        "icon": "pdf-to-image.svg",
        "desc": "Turn PDF pages into JPG or PNG images."
    },
    {
        "slug": "image-to-pdf",
        "title": "Image to PDF",
        "icon": "image-to-pdf.svg",
        "desc": "Combine JPG/PNG/WEBP images into a single PDF file."
    },
    {
        "slug": "pdf-to-excel",
        "title": "PDF to Excel",
        "icon": "pdf-to-excel.svg",
        "desc": "Extract tables from PDF into editable Excel (XLSX)."
    },
    {
        "slug": "excel-to-pdf",
        "title": "Excel to PDF",
        "icon": "excel-to-pdf.svg",
        "desc": "Save Excel spreadsheets as clean, printable PDFs."
    },
    {
        "slug": "pdf-to-powerpoint",
        "title": "PDF to PowerPoint",
        "icon": "pdf-to-powerpoint.svg",
        "desc": "Convert PDF slides into editable PowerPoint files."
    },
    {
        "slug": "powerpoint-to-pdf",
        "title": "PowerPoint to PDF",
        "icon": "powerpoint-to-pdf.svg",
        "desc": "Export PPT/PPTX presentations as PDFs."
    },
    {
        "slug": "ocr-pdf",
        "title": "OCR PDF",
        "icon": "ocr-pdf.svg",
        "desc": "Recognize text in scanned PDFs using OCR."
    },
    {
        "slug": "extract-text",
        "title": "Extract Text",
        "icon": "extract-text.svg",
        "desc": "Pull all readable text out of a PDF file."
    },
    {
        "slug": "extract-images",
        "title": "Extract Images",
        "icon": "extract-images.svg",
        "desc": "Extract embedded images from a PDF document."
    },
    {
        "slug": "deskew-pdf",
        "title": "Deskew PDF",
        "icon": "deskew-pdf.svg",
        "desc": "Auto-straighten scanned or crooked PDF pages."
    },
    {
        "slug": "crop-pdf",
        "title": "Crop PDF",
        "icon": "crop-pdf.svg",
        "desc": "Trim unwanted margins and areas from PDF pages."
    },
    {
        "slug": "resize-pdf",
        "title": "Resize PDF",
        "icon": "resize-pdf.svg",
        "desc": "Change page size or scale pages to a new format."
    },
    {
        "slug": "flatten-pdf",
        "title": "Flatten PDF",
        "icon": "flatten-pdf.svg",
        "desc": "Flatten annotations, forms and layers into a single PDF."
    },
    {
        "slug": "metadata-editor",
        "title": "Metadata Editor",
        "icon": "metadata-editor.svg",
        "desc": "View and edit PDF title, author and metadata fields."
    },
    {
        "slug": "fill-forms",
        "title": "Fill PDF Forms",
        "icon": "fill-forms.svg",
        "desc": "Fill in interactive PDF forms and save your answers."
    },
    {
        "slug": "background-remover",
        "title": "Remove Background",
        "icon": "background-remover.svg",
        "desc": "Remove backgrounds from images for cleaner PDFs."
    },
]

# 5 AI TOOLS
AI_TOOLS = [
    {
        "slug": "ai-editor",
        "title": "AI PDF Editor",
        "icon": "ai-editor.svg",
        "url": "/ai/ai-editor",
        "desc": "Edit, rewrite or clean up text inside your PDF using AI."
    },
    {
        "slug": "ai-summarizer",
        "title": "AI Summarizer",
        "icon": "ai-summarizer.svg",
        "url": "/ai/ai-summarizer",
        "desc": "Get short, medium or detailed summaries of your PDFs."
    },
    {
        "slug": "ai-chat",
        "title": "Chat with PDF",
        "icon": "ai-chat.svg",
        "url": "/ai/ai-chat",
        "desc": "Ask questions and chat with your PDF content."
    },
    {
        "slug": "ai-translate",
        "title": "AI Translator",
        "icon": "ai-translate.svg",
        "url": "/ai/ai-translate",
        "desc": "Translate PDF text between multiple languages using AI."
    },
    {
        "slug": "ai-table-extract",
        "title": "AI Table Extractor",
        "icon": "ai-table-extract.svg",
        "url": "/ai/ai-table-extract",
        "desc": "Use AI to cleanly extract tables into CSV or Excel."
    },
]

# MAPPINGS
SLUG_TO_TOOL = {t["slug"]: t for t in TOOLS}
SLUG_TO_AI_TOOL = {t["slug"]: t for t in AI_TOOLS}
