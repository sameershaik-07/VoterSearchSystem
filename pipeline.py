import sys
import time
import logging
import argparse
import sqlite3
import importlib
from pathlib import Path

import config
import utils

render_module      = importlib.import_module("01_render")
segment_module     = importlib.import_module("02_segment")
ocr_module         = importlib.import_module("03_ocr")
parse_module       = importlib.import_module("04_parse")
store_module       = importlib.import_module("05_store")

render_pdf         = render_module.render_pdf
setup_dirs         = render_module.setup_dirs
segment_page       = segment_module.segment_page
ocr_page           = ocr_module.ocr_page
parse_page_results = parse_module.parse_page_results
init_database      = store_module.init_database
insert_records     = store_module.insert_records
records_to_csv     = store_module.records_to_csv
get_stats          = store_module.get_stats
search_voters      = store_module.search_voters

logger = logging.getLogger("pipeline")

def process_pdf(pdf_path: Path, db_conn: sqlite3.Connection) -> dict:
    pdf_name = pdf_path.name
    part_no  = utils.part_no_from_filename(pdf_name)
    logger.info(f"{'='*60}")
    logger.info(f"Processing: {pdf_name}  (part_no={part_no})")
    t0 = time.time()
    stats = {"pages": 0, "rows_detected": 0, "rows_parsed": 0, "rows_stored": 0}

    try:
        image_paths = render_pdf(pdf_path)
    except Exception as e:
        logger.error(f"Render failed: {e}")
        return stats

    if not image_paths:
        logger.warning("No pages rendered")
        return stats

    stats["pages"] = len(image_paths)
    crops_dir   = config.CROPS_DIR / pdf_path.stem
    all_records = []

    for img_path in image_paths:
        page_no = utils.page_no_from_stem(img_path.stem)
        logger.info(f"  Page {page_no}/{stats['pages']} — {img_path.name}")

        try:
            bboxes = segment_page(img_path, crops_dir=crops_dir)
        except Exception as e:
            logger.warning(f"  Segment failed: {e}")
            continue

        if len(bboxes) < config.MIN_ROWS_FOR_DATA_PAGE:
            logger.info(f"  Only {len(bboxes)} rows — skipping summary page")
            continue

        stats["rows_detected"] += len(bboxes)

        try:
            ocr_results = ocr_page(img_path, bboxes, crops_dir=crops_dir)
        except Exception as e:
            logger.warning(f"  OCR failed: {e}")
            continue

        page_records = parse_page_results(
            ocr_results, part_no=part_no,
            page_no=page_no, source_pdf=pdf_name
        )
        all_records.extend(page_records)
        stats["rows_parsed"] += len(page_records)

    if not all_records:
        logger.warning(f"No records extracted from {pdf_name}")
        return stats

    records_to_csv(all_records, pdf_stem=pdf_path.stem)
    stats["rows_stored"] = insert_records(all_records, conn=db_conn)

    elapsed = time.time() - t0
    logger.info(f"✓ Done in {elapsed:.1f}s — {stats}")
    return stats

def run_pipeline(target_pdfs=None):
    utils.setup_logging("pipeline")
    setup_dirs()

    if target_pdfs is None:
        target_pdfs = sorted(config.PDF_DIR.glob("*.pdf"))

    if not target_pdfs:
        print(f"❌ No PDFs found in {config.PDF_DIR}")
        return

    logger.info(f"Found {len(target_pdfs)} PDF(s)")
    db_conn = init_database()
    totals  = {"pages": 0, "rows_detected": 0, "rows_parsed": 0, "rows_stored": 0}

    for i, pdf_path in enumerate(target_pdfs, 1):
        logger.info(f"\nPDF {i}/{len(target_pdfs)}")
        s = process_pdf(pdf_path, db_conn)
        for k in totals: totals[k] += s.get(k, 0)

    db_conn.close()
    db_stats = get_stats()

    print("\n" + "="*60)
    print("PIPELINE COMPLETE")
    print("="*60)
    print(f"  PDFs processed : {len(target_pdfs)}")
    print(f"  Pages rendered : {totals['pages']}")
    print(f"  Rows detected  : {totals['rows_detected']}")
    print(f"  Rows parsed    : {totals['rows_parsed']}")
    print(f"  Rows stored    : {totals['rows_stored']}")
    print(f"\n  DB location    : {config.DB_PATH}")
    print(f"  Total in DB    : {db_stats['total_voters']} voters")

def main():
    parser = argparse.ArgumentParser(description="Voter PDF Pipeline")
    parser.add_argument("pdfs", nargs="*", help="Specific PDF filenames")
    parser.add_argument("--search", metavar="QUERY")
    parser.add_argument("--search-field", default="voter_name",
                        choices=["voter_name","house_no","relative_name","epic_no"])
    parser.add_argument("--stats", action="store_true")
    args = parser.parse_args()

    if args.stats:
        utils.setup_logging()
        s = get_stats()
        print(f"Total voters: {s['total_voters']}  |  PDFs: {s['source_pdfs']}")
        return

    if args.search:
        utils.setup_logging()
        results = search_voters(args.search, field=args.search_field)
        print(f"\n{len(results)} result(s) for '{args.search}':")
        for r in results:
            print(f"  [{r['source_pdf']} p{r['page_no']}] "
                  f"#{r['serial_no']} {r['voter_name']} | "
                  f"H:{r['house_no']} | {r['gender']} | "
                  f"Age:{r['age']} | EPIC:{r['epic_no']}")
        return

    target_pdfs = [config.PDF_DIR / p for p in args.pdfs] if args.pdfs else None
    run_pipeline(target_pdfs)

if __name__ == "__main__":
    main()