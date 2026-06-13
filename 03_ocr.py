import cv2
import numpy as np
import pytesseract
import logging
import signal
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
import config

logger = logging.getLogger(__name__)

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

@dataclass
class OCRResult:
    row_index: int
    page_stem: str
    raw_text: str
    confidence: float
    crop_path: Optional[Path] = None

def ocr_crop(crop: np.ndarray):
    _, binary = cv2.threshold(crop, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    try:
        data = pytesseract.image_to_data(
            binary,
            lang=config.TESSERACT_LANG,
            config=r"--oem 1 --psm 6",
            timeout=10,        # ← 10 second max per row
            output_type=pytesseract.Output.DICT
        )
        words, confs = [], []
        for i, word in enumerate(data["text"]):
            if not word.strip(): continue
            try:
                conf = int(float(data["conf"][i]))
            except:
                conf = -1
            if conf > 0:
                words.append(word.strip())
                confs.append(conf)
        return " ".join(words), (float(np.mean(confs)) if confs else 0.0)
    except RuntimeError:
        logger.warning("  OCR timeout on crop — skipping")
        return "", 0.0

def ocr_page(page_image_path: Path, bboxes: list, crops_dir=None) -> list:
    results = []
    try:
        page_gray = cv2.imread(str(page_image_path), cv2.IMREAD_GRAYSCALE)
        if page_gray is None:
            raise FileNotFoundError(f"Cannot load: {page_image_path}")

        for bbox in bboxes:
            try:
                crop = page_gray[bbox.y_top:bbox.y_bottom, bbox.x_left:bbox.x_right]
                raw_text, conf = ocr_crop(crop)
                results.append(OCRResult(
                    row_index=bbox.row_index,
                    page_stem=page_image_path.stem,
                    raw_text=raw_text,
                    confidence=round(conf, 1)
                ))
            except Exception as e:
                logger.warning(f"  Row {bbox.row_index} failed: {e}")
                results.append(OCRResult(
                    row_index=bbox.row_index,
                    page_stem=page_image_path.stem,
                    raw_text="", confidence=0.0
                ))

        avg = np.mean([r.confidence for r in results]) if results else 0
        logger.info(f"  {page_image_path.name}: {len(results)} rows, avg confidence={avg:.1f}%")

    except Exception as e:
        logger.error(f"  OCR failed for {page_image_path.name}: {e}")
        results = [OCRResult(row_index=b.row_index, page_stem=page_image_path.stem,
                             raw_text="", confidence=0.0) for b in bboxes]
    return results