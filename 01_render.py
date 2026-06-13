import fitz
import logging
from pathlib import Path
import config

logger = logging.getLogger(__name__)

def setup_dirs():
    for d in [config.IMAGES_DIR, config.CROPS_DIR, config.CSV_DIR,
              config.LOGS_DIR, config.DATABASE_DIR]:
        d.mkdir(parents=True, exist_ok=True)

def render_pdf(pdf_path: Path) -> list:
    output_base = config.IMAGES_DIR / pdf_path.stem
    output_base.mkdir(parents=True, exist_ok=True)
    saved_images = []
    doc = fitz.open(str(pdf_path))
    matrix = fitz.Matrix(config.RENDER_SCALE, config.RENDER_SCALE)
    for page_num in range(len(doc)):
        if config.SKIP_FIRST_PAGE and page_num == 0:
            continue
        page = doc[page_num]
        pix = page.get_pixmap(matrix=matrix, colorspace=fitz.csGRAY)
        out_path = output_base / f"page_{page_num + 1:04d}.png"
        pix.save(str(out_path))
        saved_images.append(out_path)
        logger.info(f"  Rendered page {page_num + 1} → {out_path.name}")
    doc.close()
    logger.info(f"[{pdf_path.name}] {len(saved_images)} pages rendered")
    return saved_images

def render_all_pdfs():
    pdf_files = sorted(config.PDF_DIR.glob("*.pdf"))
    if not pdf_files:
        logger.warning(f"No PDFs found in {config.PDF_DIR}")
        return {}
    results = {}
    for pdf_path in pdf_files:
        out_dir = config.IMAGES_DIR / pdf_path.stem
        if out_dir.exists() and any(out_dir.iterdir()) and not config.OVERWRITE_CSV:
            existing = sorted(out_dir.glob("*.png"))
            logger.info(f"[{pdf_path.name}] Already rendered, skipping")
            results[pdf_path.stem] = existing
            continue
        try:
            results[pdf_path.stem] = render_pdf(pdf_path)
        except Exception as e:
            logger.error(f"[{pdf_path.name}] Failed: {e}")
    return results

if __name__ == "__main__":
    from utils import setup_logging
    setup_logging()
    setup_dirs()
    render_all_pdfs()
    print("✓ Rendering complete")