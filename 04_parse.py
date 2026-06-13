import re
import logging
from dataclasses import dataclass
import config

logger = logging.getLogger(__name__)


@dataclass
class VoterRecord:
    serial_no: str = ""
    house_no: str = ""
    voter_name: str = ""
    gender: str = ""
    relative_name: str = ""
    relative_type: str = ""
    age: int = 0
    epic_no: str = ""
    part_no: str = ""
    page_no: int = 0
    source_pdf: str = ""
    raw_ocr_text: str = ""
    ocr_confidence: float = 0.0
    parse_ok: bool = False


EPIC_RE = re.compile(config.EPIC_PATTERN)


def clean_text(value):
    if value is None:
        return ""
    return str(value).strip()


def parse_voter_row(ocr) -> VoterRecord:
    rec = VoterRecord(
        raw_ocr_text=ocr.raw_text,
        ocr_confidence=ocr.confidence
    )

    text = clean_text(ocr.raw_text)

    if not text:
        return rec

    try:
        # Expected OCR format:
        # 1 | 4-8-4 | మాసన్న నాగరాజు | తం | మాసన్న కొమయ్య | పు | 49 | AP261810000000

        cols = [c.strip() for c in text.split("|")]

        if len(cols) < 8:
            logger.debug(
                f"Row {ocr.row_index}: insufficient columns ({len(cols)})"
            )
            return rec

        # Column 1
        rec.serial_no = cols[0]

        # Column 2
        rec.house_no = cols[1]

        # Column 3
        rec.voter_name = cols[2]

        # Column 4 - Relative Type
        rel_type = cols[3]

        if "తం" in rel_type:
            rec.relative_type = "F"  # Father
        elif "భ" in rel_type:
            rec.relative_type = "H"  # Husband
        elif "తల్లి" in rel_type:
            rec.relative_type = "M"  # Mother
        else:
            rec.relative_type = rel_type

        # Column 5
        rec.relative_name = cols[4]

        # Column 6 - Gender
        gender = cols[5]

        if "పు" in gender:
            rec.gender = "M"
        elif "స్త్రీ" in gender:
            rec.gender = "F"
        else:
            rec.gender = gender

        # Column 7 - Age
        try:
            rec.age = int(cols[6])
        except:
            rec.age = 0

        # Column 8 - EPIC
        epic = cols[7].replace(" ", "").upper()

        m = EPIC_RE.search(epic)
        if m:
            rec.epic_no = m.group(0)
        else:
            rec.epic_no = epic

        rec.parse_ok = True

        logger.debug(
            f"Row {ocr.row_index}: "
            f"{rec.serial_no} | "
            f"{rec.voter_name[:25]} | "
            f"{rec.epic_no}"
        )

    except Exception as e:
        logger.warning(
            f"Parse failed for row {ocr.row_index}: {e}"
        )

    return rec


def parse_page_results(
    ocr_results,
    part_no="",
    page_no=0,
    source_pdf=""
) -> list:

    records = []

    for ocr in ocr_results:
        rec = parse_voter_row(ocr)

        rec.part_no = part_no
        rec.page_no = page_no
        rec.source_pdf = source_pdf

        records.append(rec)

    ok = sum(1 for r in records if r.parse_ok)

    logger.info(
        f"  Page {page_no}: {ok}/{len(records)} records parsed"
    )

    return records