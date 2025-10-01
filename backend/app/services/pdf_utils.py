import fitz  # PyMuPDF
import pdfplumber
import os

def pdf_to_images_pymupdf(pdf_path, output_folder="output_images", dpi=200, fmt="png"):
    """Convert PDF pages to images (unchanged)"""
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    doc = fitz.open(pdf_path)
    image_paths = []
    for i, page in enumerate(doc):
        zoom = dpi / 72
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        image_path = os.path.join(output_folder, f"page_{i+1}.{fmt}")
        pix.save(image_path)
        image_paths.append(image_path)
    return image_paths

def extract_text_from_pdf(pdf_path):
    """
    Extract text from PDF using pdfplumber.
    Returns a dictionary with page-wise text extraction.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        dict: {
            'full_text': str (all pages combined),
            'pages': list of dicts with page-wise data
        }
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            pages_data = []
            full_text = []
            
            for i, page in enumerate(pdf.pages, start=1):
                page_text = page.extract_text()
                if page_text:
                    pages_data.append({
                        'page_number': i,
                        'text': page_text.strip()
                    })
                    full_text.append(page_text.strip())
            
            return {
                'full_text': '\n\n'.join(full_text),
                'pages': pages_data,
                'total_pages': len(pdf.pages)
            }
    except Exception as e:
        print(f"[ERROR] Failed to extract text from PDF {pdf_path}: {e}")
        return {
            'full_text': '',
            'pages': [],
            'total_pages': 0,
            'error': str(e)
        }