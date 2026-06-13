from pathlib import Path

BASE_DIR       = Path(r"C:\VoterSearch")
PDF_DIR        = BASE_DIR / "PDFs"
OUTPUT_DIR     = BASE_DIR / "Output"
DATABASE_DIR   = BASE_DIR / "Database"
IMAGES_DIR     = OUTPUT_DIR / "images"
CROPS_DIR      = OUTPUT_DIR / "crops"
CSV_DIR        = OUTPUT_DIR / "csv"
LOGS_DIR       = OUTPUT_DIR / "logs"
DB_PATH        = DATABASE_DIR / "voters.db"

RENDER_DPI             = 300
RENDER_SCALE           = RENDER_DPI / 72
BINARIZE_THRESH        = 180
MORPH_KERNEL_WIDTH     = 40
MORPH_KERNEL_HEIGHT    = 1
PROJECTION_MIN_GAP     = 8
ROW_MIN_HEIGHT         = 20
ROW_MAX_HEIGHT         = 200
ROW_PADDING            = 4
TABLE_TOP_SKIP_FRAC    = 0.08
TABLE_BOTTOM_SKIP_FRAC = 0.05
TESSERACT_LANG         = "tel+eng"
TESSERACT_CONFIG       = r"--oem 1 --psm 6"
EPIC_PATTERN           = r"[A-Z]{2,3}[0-9]{6,10}"
MALE_KEYWORDS          = ["పురుషుడు", "male", "m"]
FEMALE_KEYWORDS        = ["స్త్రీ", "female", "f"]
RELATIVE_FATHER        = ["తండ్రి", "father", "s/o", "f/o"]
RELATIVE_MOTHER        = ["తల్లి", "mother", "m/o"]
RELATIVE_HUSBAND       = ["భర్త", "husband", "h/o", "w/o"]
SKIP_FIRST_PAGE        = True
MIN_ROWS_FOR_DATA_PAGE = 5
SAVE_ROW_CROPS = False
OVERWRITE_CSV  = False
LOG_LEVEL              = "INFO"
LOG_TO_FILE            = True