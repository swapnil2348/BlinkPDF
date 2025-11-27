# tools.py

TOOLS = [
    {'slug': 'merge-pdf', 'title': 'Merge PDF', 'desc': 'Combine multiple PDF files into one.', 'icon': 'merge-pdf.svg'},
    {'slug': 'split-pdf', 'title': 'Split PDF', 'desc': 'Split a PDF into multiple files.', 'icon': 'split-pdf.svg'},
    {'slug': 'compress-pdf', 'title': 'Compress PDF', 'desc': 'Reduce the size of your PDF.', 'icon': 'compress-pdf.svg'},
    {'slug': 'optimize-pdf', 'title': 'Optimize PDF', 'desc': 'Improve PDF size and structure.', 'icon': 'optimize-pdf.svg'},
    {'slug': 'rotate-pdf', 'title': 'Rotate PDF', 'desc': 'Rotate PDF pages to any angle.', 'icon': 'rotate-pdf.svg'},
    {'slug': 'watermark-pdf', 'title': 'Watermark PDF', 'desc': 'Add watermark to your PDF.', 'icon': 'watermark-pdf.svg'},
    {'slug': 'number-pdf', 'title': 'Number Pages', 'desc': 'Add page numbers to a PDF.', 'icon': 'number-pdf.svg'},
    {'slug': 'protect-pdf', 'title': 'Protect PDF', 'desc': 'Password protect your PDF.', 'icon': 'protect-pdf.svg'},
    {'slug': 'unlock-pdf', 'title': 'Unlock PDF', 'desc': 'Remove password from PDF.', 'icon': 'unlock-pdf.svg'},
    {'slug': 'repair-pdf', 'title': 'Repair PDF', 'desc': 'Fix corrupted PDF files.', 'icon': 'repair-pdf.svg'},
    {'slug': 'organize-pdf', 'title': 'Organize PDF', 'desc': 'Reorder pages in a PDF.', 'icon': 'organize-pdf.svg'},
    {'slug': 'sign-pdf', 'title': 'Sign PDF', 'desc': 'Add digital signature.', 'icon': 'sign-pdf.svg'},
    {'slug': 'annotate-pdf', 'title': 'Annotate PDF', 'desc': 'Add notes & highlights.', 'icon': 'annotate-pdf.svg'},
    {'slug': 'redact-pdf', 'title': 'Redact PDF', 'desc': 'Hide sensitive data.', 'icon': 'redact-pdf.svg'},
    {'slug': 'pdf-to-word', 'title': 'PDF to Word', 'desc': 'Convert PDF to Word file.', 'icon': 'pdf-to-word.svg'},
    {'slug': 'word-to-pdf', 'title': 'Word to PDF', 'desc': 'Convert Word to PDF.', 'icon': 'word-to-pdf.svg'},
    {'slug': 'pdf-to-image', 'title': 'PDF to Image', 'desc': 'Convert PDF pages to images.', 'icon': 'pdf-to-image.svg'},
    {'slug': 'image-to-pdf', 'title': 'Image to PDF', 'desc': 'Convert images into PDF.', 'icon': 'image-to-pdf.svg'},
    {'slug': 'pdf-to-excel', 'title': 'PDF to Excel', 'desc': 'Extract table data.', 'icon': 'pdf-to-excel.svg'},
    {'slug': 'excel-to-pdf', 'title': 'Excel to PDF', 'desc': 'Convert Excel to PDF.', 'icon': 'excel-to-pdf.svg'},
    {'slug': 'pdf-to-powerpoint', 'title': 'PDF to PowerPoint', 'desc': 'Convert PDF to PPT.', 'icon': 'pdf-to-powerpoint.svg'},
    {'slug': 'powerpoint-to-pdf', 'title': 'PowerPoint to PDF', 'desc': 'Convert PPT to PDF.', 'icon': 'powerpoint-to-pdf.svg'},
    {'slug': 'ocr-pdf', 'title': 'OCR PDF', 'desc': 'Extract text from scans.', 'icon': 'ocr-pdf.svg'},
    {'slug': 'extract-text', 'title': 'Extract Text', 'desc': 'Get text from PDF.', 'icon': 'extract-text.svg'},
    {'slug': 'extract-images', 'title': 'Extract Images', 'desc': 'Extract images from PDF.', 'icon': 'extract-images.svg'},
    {'slug': 'deskew-pdf', 'title': 'Deskew PDF', 'desc': 'Straighten scanned pages.', 'icon': 'deskew-pdf.svg'},
    {'slug': 'crop-pdf', 'title': 'Crop PDF', 'desc': 'Crop pages to size.', 'icon': 'crop-pdf.svg'},
    {'slug': 'resize-pdf', 'title': 'Resize PDF', 'desc': 'Resize page dimensions.', 'icon': 'resize-pdf.svg'},
    {'slug': 'flatten-pdf', 'title': 'Flatten PDF', 'desc': 'Flatten all layers.', 'icon': 'flatten-pdf.svg'},
    {'slug': 'metadata-editor', 'title': 'Metadata Editor', 'desc': 'Edit PDF information.', 'icon': 'metadata-editor.svg'},
    {'slug': 'fill-forms', 'title': 'Fill PDF Forms', 'desc': 'Fill interactive forms.', 'icon': 'fill-forms.svg'},
    {'slug': 'background-remover', 'title': 'Remove Background', 'desc': 'Remove PDF background.', 'icon': 'background-remover.svg'},
]

AI_TOOLS = [
    {"slug": "ai-editor", "title": "AI PDF Editor", "desc": "Edit PDF using AI.", "url": "/ai/editor", "icon": "ai-editor.svg"},
    {"slug": "ai-summarizer", "title": "AI Summarizer", "desc": "Summarize content.", "url": "/ai/summarizer-page", "icon": "ai-summarizer.svg"},
    {"slug": "ai-chat", "title": "Chat with PDF", "desc": "Chat with documents.", "url": "/ai/chat-page", "icon": "ai-chat.svg"},
    {"slug": "ai-translate", "title": "AI Translator", "desc": "Translate text.", "url": "/ai/translate-page", "icon": "ai-translate.svg"},
    {"slug": "ai-table-extract", "title": "AI Table Extractor", "desc": "Extract tables.", "url": "/ai/table-page", "icon": "ai-table.svg"},
]

SLUG_TO_TOOL = {t["slug"]: t for t in TOOLS}
SLUG_TO_AI_TOOL = {t["slug"]: t for t in AI_TOOLS}
