import logging
import sys
import re
from pathlib import Path
from datetime import datetime
import config

def setup_logging(name="pipeline"):
    config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = config.LOGS_DIR / f"{name}_{ts}.log"
    handlers = [logging.StreamHandler(sys.stdout)]
    if config.LOG_TO_FILE:
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL, logging.INFO),
        format="%(asctime)s %(levelname)-8s — %(message)s",
        datefmt="%H:%M:%S",
        handlers=handlers,
        force=True
    )
    return logging.getLogger(name)

def part_no_from_filename(filename):
    stem = Path(filename).stem
    parts = stem.split("_")
    return "_".join(parts[1:]) if len(parts) >= 3 else stem

def page_no_from_stem(page_stem):
    m = re.search(r'(\d+)', page_stem)
    return int(m.group(1)) if m else 0