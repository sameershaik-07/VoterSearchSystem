import csv
import sqlite3
import logging
from pathlib import Path
from typing import Optional
import config

logger = logging.getLogger(__name__)

CSV_COLUMNS = [
    "serial_no", "house_no", "voter_name", "gender",
    "relative_name", "relative_type", "age", "epic_no",
    "part_no", "page_no", "source_pdf", "raw_ocr_text", "ocr_confidence"
]

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS voters (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    serial_no       TEXT,
    house_no        TEXT,
    voter_name      TEXT,
    gender          TEXT,
    relative_name   TEXT,
    relative_type   TEXT,
    age             INTEGER,
    epic_no         TEXT,
    part_no         TEXT,
    page_no         INTEGER,
    source_pdf      TEXT,
    raw_ocr_text    TEXT,
    ocr_confidence  REAL,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_voter_name    ON voters(voter_name);
CREATE INDEX IF NOT EXISTS idx_house_no      ON voters(house_no);
CREATE INDEX IF NOT EXISTS idx_relative_name ON voters(relative_name);
CREATE INDEX IF NOT EXISTS idx_epic_no       ON voters(epic_no);
CREATE INDEX IF NOT EXISTS idx_part_no       ON voters(part_no);
"""

UPSERT_SQL = """
INSERT INTO voters
    (serial_no, house_no, voter_name, gender, relative_name, relative_type,
     age, epic_no, part_no, page_no, source_pdf, raw_ocr_text, ocr_confidence)
VALUES
    (:serial_no, :house_no, :voter_name, :gender, :relative_name, :relative_type,
     :age, :epic_no, :part_no, :page_no, :source_pdf, :raw_ocr_text, :ocr_confidence)
ON CONFLICT DO NOTHING;
"""

def get_connection(db_path=None):
    if db_path is None: db_path = config.DB_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn

def init_database(db_path=None):
    conn = get_connection(db_path)
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    logger.info(f"Database ready: {db_path or config.DB_PATH}")
    return conn

def records_to_csv(records, pdf_stem="output"):
    config.CSV_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = config.CSV_DIR / f"{pdf_stem}.csv"
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for rec in records:
            writer.writerow({
                "serial_no": rec.serial_no, "house_no": rec.house_no,
                "voter_name": rec.voter_name, "gender": rec.gender,
                "relative_name": rec.relative_name, "relative_type": rec.relative_type,
                "age": rec.age, "epic_no": rec.epic_no, "part_no": rec.part_no,
                "page_no": rec.page_no, "source_pdf": rec.source_pdf,
                "raw_ocr_text": rec.raw_ocr_text, "ocr_confidence": rec.ocr_confidence,
            })
    logger.info(f"CSV saved: {csv_path} ({len(records)} rows)")
    return csv_path

def insert_records(records, conn=None, db_path=None):
    own_conn = conn is None
    if own_conn: conn = init_database(db_path)
    rows = [{"serial_no": r.serial_no, "house_no": r.house_no,
             "voter_name": r.voter_name, "gender": r.gender,
             "relative_name": r.relative_name, "relative_type": r.relative_type,
             "age": r.age, "epic_no": r.epic_no, "part_no": r.part_no,
             "page_no": r.page_no, "source_pdf": r.source_pdf,
             "raw_ocr_text": r.raw_ocr_text, "ocr_confidence": r.ocr_confidence}
            for r in records]
    cursor = conn.cursor()
    cursor.executemany(UPSERT_SQL, rows)
    inserted = cursor.rowcount
    conn.commit()
    if own_conn: conn.close()
    logger.info(f"DB: {inserted} rows inserted")
    return inserted

def get_stats(db_path=None):
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM voters")
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(DISTINCT source_pdf) FROM voters")
    pdfs = cur.fetchone()[0]
    conn.close()
    return {"total_voters": total, "source_pdfs": pdfs}

def search_voters(query, field="voter_name", db_path=None):
    allowed = {"voter_name", "house_no", "relative_name", "epic_no"}
    if field not in allowed: raise ValueError(f"Invalid field: {field}")
    conn = get_connection(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM voters WHERE {field} LIKE ? LIMIT 50", (f"%{query}%",))
    results = [dict(row) for row in cur.fetchall()]
    conn.close()
    return results