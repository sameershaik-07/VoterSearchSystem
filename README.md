# ఓటర్ శోధన / Voter Search System
### శాసనసభ నియోజకవర్గం 181 · ఓటర్ల జాబితా 2002

Complete pipeline to extract Telugu voter records from 2002 Election Commission PDFs and serve them via an offline Android app.

---

## System Overview

```
PDF Files (Telugu, 2002 EC)
        ↓
  Python Pipeline (Windows VM)
  ├── PyMuPDF    → Render pages as images
  ├── OpenCV     → Detect voter row boundaries
  ├── Tesseract  → OCR (Telugu + English)
  └── SQLite     → Store structured records
        ↓
   voters.db
        ↓
  Flutter Android App
  └── Offline search by name / house no / EPIC
```

---

## Tech Stack

| Layer | Tool | Version | Purpose |
|---|---|---|---|
| PDF Rendering | PyMuPDF | 1.24.x | PDF → PNG images |
| Row Detection | OpenCV | 4.9.x | Automatic row segmentation |
| OCR | Tesseract | 5.5.x | Telugu + English text recognition |
| OCR Bridge | pytesseract | 0.3.13 | Python ↔ Tesseract |
| Database | SQLite | built-in | Structured voter storage |
| Language | Python | 3.11 | Pipeline scripting |
| Mobile App | Flutter | 3.44.x | Android app |
| App DB | sqflite | 2.4.x | SQLite on Android |
| Sharing | share_plus | 11.x | WhatsApp sharing |

---

## Environment Setup (Fresh Windows VM)

### Step 1 — Create Folder Structure

Open **PowerShell as Administrator** and run:

```powershell
mkdir C:\VoterSearch
mkdir C:\VoterSearch\PDFs
mkdir C:\VoterSearch\Scripts
mkdir C:\VoterSearch\Output
mkdir C:\VoterSearch\Output\images
mkdir C:\VoterSearch\Output\crops
mkdir C:\VoterSearch\Output\csv
mkdir C:\VoterSearch\Output\logs
mkdir C:\VoterSearch\Output\debug
mkdir C:\VoterSearch\Database
```

### Step 2 — Install All Tools (Automated)

Run this single PowerShell script:

```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force

# Install Chocolatey
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Install Python 3.11, VS Code, Tesseract
choco install python311 vscode tesseract -y

# Refresh PATH
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# Install Telugu language pack for Tesseract
$tessdata = "C:\Program Files\Tesseract-OCR\tessdata"
Invoke-WebRequest "https://github.com/tesseract-ocr/tessdata/raw/main/tel.traineddata" -OutFile "$tessdata\tel.traineddata"

# Install Python packages
pip install pymupdf==1.24.14 opencv-python==4.9.0.80 pytesseract==0.3.13 Pillow==10.4.0 tqdm
pip install "numpy<2" --force-reinstall
```

### Step 3 — Verify Installation

```powershell
python --version                          # Python 3.11.x
tesseract --version                       # tesseract v5.x
tesseract --list-langs | findstr tel      # tel
python -c "import fitz, cv2, pytesseract, PIL; print('ALL OK')"
```

---

## Pipeline Scripts

All scripts live in `C:\VoterSearch\Scripts\`

| File | Purpose |
|---|---|
| `config.py` | All settings — DPI, thresholds, paths |
| `utils.py` | Logging, filename helpers |
| `01_render.py` | PDF → PNG images (skips page 1) |
| `02_segment.py` | OpenCV horizontal projection → row bboxes |
| `03_ocr.py` | Tesseract OCR per row with 10s timeout |
| `04_parse.py` | Extract 8 fields from OCR text |
| `05_store.py` | Write CSV + SQLite |
| `pipeline.py` | Master orchestrator — run this |
| `debug_view.py` | Visual debugging of row detection |

---

## Running the Pipeline

### Process all PDFs
```powershell
cd C:\VoterSearch\Scripts
python pipeline.py
```

### Process one specific PDF
```powershell
python pipeline.py S01_181_46.pdf
```

### Check progress (run in separate window)
```powershell
# Voter count so far
python -c "import sqlite3; c=sqlite3.connect(r'C:\VoterSearch\Database\voters.db'); print('Voters:', c.execute('SELECT COUNT(*) FROM voters').fetchone()[0])"

# Last log line
Get-Content C:\VoterSearch\Output\logs\*.log -Tail 3
```

### Search after processing
```powershell
python pipeline.py --search "రాముడు"
python pipeline.py --search "4-8-4" --search-field house_no
python pipeline.py --search "AP261810" --search-field epic_no
python pipeline.py --stats
```

---

## PDF Characteristics

- **Source**: Election Commission of India, 2002 voter lists
- **Constituency**: శాసనసభ నియోజకవర్గం 181
- **Page size**: Rect(0, 0, 936, 936)
- **Font encoding**: Non-Unicode Telugu (direct text extraction = garbage)
- **OCR required**: Yes — Tesseract `tel+eng`
- **Pages per PDF**: ~50
- **Rows per page**: ~21 voter records
- **Page 1**: Metadata (skipped)
- **Last page**: Summary (auto-detected and skipped if < 5 rows)

### Filename Convention
```
S01_181_46.pdf
 │    │   └─ Serial number
 │    └───── Part number (భాగం)
 └────────── State/segment code
```

---

## SQLite Schema

```sql
CREATE TABLE voters (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    serial_no       TEXT,    -- వరుస సంఖ్య
    house_no        TEXT,    -- ఇంటి నంబరు
    voter_name      TEXT,    -- ఓటరు పేరు
    gender          TEXT,    -- లింగం (M/F)
    relative_name   TEXT,    -- బంధువు పేరు
    relative_type   TEXT,    -- బంధువు రకం (F=తండ్రి, M=తల్లి, H=భర్త)
    age             INTEGER, -- వయసు
    epic_no         TEXT,    -- ఓటరు కార్డు నంబరు
    part_no         TEXT,    -- భాగం నంబరు
    page_no         INTEGER, -- పేజీ నంబరు
    source_pdf      TEXT,    -- మూల PDF ఫైలు
    raw_ocr_text    TEXT,    -- డీబగ్గింగ్ కోసం పూర్తి OCR టెక్స్ట్
    ocr_confidence  REAL,    -- OCR నమ్మకం స్కోరు (0-100)
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Search indexes
CREATE INDEX idx_voter_name    ON voters(voter_name);
CREATE INDEX idx_house_no      ON voters(house_no);
CREATE INDEX idx_relative_name ON voters(relative_name);
CREATE INDEX idx_epic_no       ON voters(epic_no);
CREATE INDEX idx_part_no       ON voters(part_no);
```

---

## Configuration (config.py)

Key settings to tune if results are poor:

| Setting | Default | Effect |
|---|---|---|
| `RENDER_DPI` | 300 | Increase to 400 for better OCR on faded print |
| `PROJECTION_MIN_GAP` | 8 | Increase if voter rows are merging together |
| `ROW_MIN_HEIGHT` | 20 | Increase to filter out noise/divider lines |
| `ROW_MAX_HEIGHT` | 200 | Decrease to exclude header rows |
| `TABLE_TOP_SKIP_FRAC` | 0.08 | Increase to skip more of page header |
| `SAVE_ROW_CROPS` | False | Set True only for debugging (very slow) |
| `OVERWRITE_CSV` | True | Set False to skip already-processed PDFs |

---

## Troubleshooting

### Pipeline is very slow (> 2 min per page)
The `SAVE_ROW_CROPS = True` setting saves thousands of image files and is extremely slow.
```python
# config.py
SAVE_ROW_CROPS = False   # ← must be False for production runs
```

### Tesseract hanging on certain pages
Some pages cause Tesseract to hang indefinitely. The 10-second timeout in `03_ocr.py` handles this:
```python
data = pytesseract.image_to_data(..., timeout=10)
```
If you see pages taking > 30 seconds, verify the timeout is present in `03_ocr.py`.

### NumPy version conflict
```
AttributeError: _ARRAY_API not found
```
Fix:
```powershell
pip install "numpy<2" --force-reinstall
```

### OCR confidence < 50%
- Increase `RENDER_DPI` to 400 in `config.py`
- Run `debug_view.py` to check row detection quality

### Header rows appearing in results (serial_no = "(1)")
These are table header rows OCR'd as voter records. The Flutter app filters them:
```dart
WHERE serial_no NOT LIKE '(%' AND voter_name NOT LIKE '(%'
```
To clean from DB permanently:
```powershell
python -c "
import sqlite3
conn = sqlite3.connect(r'C:\VoterSearch\Database\voters.db')
conn.execute(\"DELETE FROM voters WHERE serial_no LIKE '(%'\")
conn.commit()
print('Cleaned')
"
```

### Row detection is wrong (rows merging or splitting)
Run debug viewer:
```powershell
cd C:\VoterSearch\Scripts
python debug_view.py
```
Opens `Output\debug\` with annotated images showing:
- **Green boxes** = detected voter rows
- **Blue box** = table region boundary

Tune `PROJECTION_MIN_GAP`, `ROW_MIN_HEIGHT`, `ROW_MAX_HEIGHT` in `config.py`.

### Pipeline stopped midway — resume without reprocessing
Set `OVERWRITE_CSV = False` in `config.py` and re-run. Already-rendered PDFs will be skipped.

---

## Flutter App

### Project Location
```
C:\voter_search_app\
├── lib\
│   └── main.dart         ← entire app in one file
├── assets\
│   └── db\
│       └── voters.db     ← copy final DB here before building APK
└── pubspec.yaml
```

### pubspec.yaml Dependencies
```yaml
dependencies:
  flutter:
    sdk: flutter
  cupertino_icons: ^1.0.8
  sqflite: ^2.4.2
  path: ^1.9.1
  path_provider: ^2.1.5
  share_plus: ^11.0.0
  flutter_typeahead: ^5.2.0
```

### Build Steps

**Step 1 — Copy completed database**
```powershell
copy C:\VoterSearch\Database\voters.db C:\voter_search_app\assets\db\voters.db
```

**Step 2 — Build release APK**
```powershell
cd C:\voter_search_app
flutter build apk --release
```

**Step 3 — APK location**
```
C:\voter_search_app\build\app\outputs\flutter-apk\app-release.apk
```

**Step 4 — Install on Android phone**
```powershell
# Via USB (ADB)
adb install build\app\outputs\flutter-apk\app-release.apk

# Or copy APK to phone and install manually
# Enable: Settings → Security → Install unknown apps
```

### App Features
- Search by voter name (పేరు)
- Search by house number (ఇంటి నం.)
- Search by EPIC number (ఓటరు కార్డు నం.)
- Search by relative name (బంధువు పేరు)
- Shows: serial no, part no, age, gender, relative, EPIC
- WhatsApp sharing with formatted Telugu message
- 100% offline — no internet required
- Filters header rows automatically

---

## Expected Output

For 32 PDFs (~50 pages each, ~21 rows per page):
```
PDFs processed  : 32
Pages rendered  : ~1,600
Rows detected   : ~33,600
Rows parsed     : ~30,000+
Total in DB     : ~28,000–32,000 voters
Processing time : ~3 hours (2 CPU cores)
```

---

## File Locations Summary

| Item | Path |
|---|---|
| PDF inputs | `C:\VoterSearch\PDFs\` |
| Rendered page images | `C:\VoterSearch\Output\images\` |
| Per-PDF CSV exports | `C:\VoterSearch\Output\csv\` |
| Processing logs | `C:\VoterSearch\Output\logs\` |
| Debug row images | `C:\VoterSearch\Output\debug\` |
| Master database | `C:\VoterSearch\Database\voters.db` |
| Flutter app | `C:\voter_search_app\` |
| Release APK | `C:\voter_search_app\build\app\outputs\flutter-apk\app-release.apk` |

---

## Known Limitations

1. **Field parsing accuracy** — Telugu OCR is ~91% confident but name splitting (voter name vs relative name) uses a midpoint heuristic. Some names may split incorrectly. Check `raw_ocr_text` column to verify.
2. **EPIC number** — Some 2002 records have placeholder EPICs (`AP2618100000`). These are in the original PDF, not an extraction error.
3. **Age** — Reflects age in 2002, not current age.
4. **Village/గ్రామం** — Not extracted (not present in voter row columns, only in page 1 metadata which is skipped).
5. **Processing speed** — ~7 seconds per page on 2-core VM. Upgrade to 4–8 cores to reduce to ~1–2 hours.

---

*Last updated: June 2026 · Built for offline Android voter record search*
