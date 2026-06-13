import cv2
import argparse
import sys
import logging
from pathlib import Path

import config
import utils
from 02_segment import segment_page, load_and_preprocess, detect_table_region

logger = logging.getLogger(__name__)

def draw_row_overlays(image_path: Path) -> Path:
    gray, _ = load_and_preprocess(image_path)
    bboxes  = segment_page(image_path, save_crops=False)
    vis     = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    h, w    = gray.shape

    ty, tb, tl, tr = detect_table_region(h, w)
    cv2.rectangle(vis, (tl, ty), (tr, tb), (255, 100, 0), 2)

    for bbox in bboxes:
        cv2.rectangle(vis, (bbox.x_left, bbox.y_top),
                      (bbox.x_right, bbox.y_bottom), (0, 200, 0), 2)
        cv2.putText(vis, str(bbox.row_index),
                    (bbox.x_left + 5, bbox.y_top + 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 0), 1)

    cv2.putText(vis, f"Rows detected: {len(bboxes)}",
                (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 80, 255), 2)

    out_dir = config.OUTPUT_DIR / "debug"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"debug_{image_path.name}"
    cv2.imwrite(str(out_path), vis)
    logger.info(f"Saved: {out_path}")
    return out_path

def main():
    utils.setup_logging()
    parser = argparse.ArgumentParser()
    parser.add_argument("image", nargs="?", help="Path to page PNG")
    parser.add_argument("--all", metavar="PDF_STEM")
    args = parser.parse_args()

    if args.all:
        pages = sorted((config.IMAGES_DIR / args.all).glob("*.png"))
        if not pages:
            print(f"No pages found for {args.all}")
            sys.exit(1)
        for p in pages:
            draw_row_overlays(p)
        print(f"✓ Debug images saved to Output/debug/")
        return

    if args.image:
        img_path = Path(args.image)
    else:
        pages = sorted(config.IMAGES_DIR.rglob("*.png"))
        if not pages:
            print("No images found. Run pipeline.py first.")
            sys.exit(1)
        img_path = pages[0]

    out = draw_row_overlays(img_path)
    print(f"✓ Saved: {out}")
    print(f"  Green = detected rows | Blue = table boundary")
    print(f"\n  Tune in config.py if rows look wrong:")
    print(f"    PROJECTION_MIN_GAP = {config.PROJECTION_MIN_GAP}")
    print(f"    ROW_MIN_HEIGHT     = {config.ROW_MIN_HEIGHT}")
    print(f"    ROW_MAX_HEIGHT     = {config.ROW_MAX_HEIGHT}")

if __name__ == "__main__":
    main()