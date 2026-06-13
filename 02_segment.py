import cv2
import logging
from pathlib import Path
from dataclasses import dataclass
import config

logger = logging.getLogger(__name__)


@dataclass
class RowBBox:
    y_top: int
    y_bottom: int
    x_left: int
    x_right: int
    row_index: int

    @property
    def height(self):
        return self.y_bottom - self.y_top


def segment_page(image_path: Path, crops_dir=None, save_crops=None):

    if save_crops is None:
        save_crops = config.SAVE_ROW_CROPS

    if crops_dir is None:
        crops_dir = config.CROPS_DIR / image_path.parent.name

    if save_crops:
        crops_dir.mkdir(parents=True, exist_ok=True)

    gray = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)

    if gray is None:
        raise FileNotFoundError(f"Cannot load image: {image_path}")

    h, w = gray.shape

    # Remove footer area
    work_img = gray[:int(h * 0.90), :]

    # Binary image
    _, thresh = cv2.threshold(
        work_img,
        180,
        255,
        cv2.THRESH_BINARY_INV
    )

    # Detect horizontal table lines
    horizontal_kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (max(100, w // 6), 1)
    )

    horizontal = cv2.morphologyEx(
        thresh,
        cv2.MORPH_OPEN,
        horizontal_kernel,
        iterations=1
    )

    contours, hierarchy = cv2.findContours(
        horizontal,
        cv2.RETR_LIST,
        cv2.CHAIN_APPROX_SIMPLE
    )

    y_lines = []

    for cnt in contours:

        x, y, cw, ch = cv2.boundingRect(cnt)

        if cw > (w * 0.60):
            y_lines.append(y)

    y_lines = sorted(y_lines)

    filtered_lines = []

    for y in y_lines:

        if not filtered_lines:
            filtered_lines.append(y)
            continue

        if abs(y - filtered_lines[-1]) > 5:
            filtered_lines.append(y)

    bboxes = []
    row_index = 0

    for i in range(len(filtered_lines) - 1):

        y1 = filtered_lines[i]
        y2 = filtered_lines[i + 1]

        row_height = y2 - y1

        # Skip tiny gaps
        if row_height < 25:
            continue

        # Skip huge regions
        if row_height > 250:
            continue

        crop_top = max(0, y1 + 2)
        crop_bottom = min(work_img.shape[0], y2 - 2)

        bbox = RowBBox(
            y_top=crop_top,
            y_bottom=crop_bottom,
            x_left=0,
            x_right=w,
            row_index=row_index
        )

        bboxes.append(bbox)

        if save_crops:

            crop = gray[
                crop_top:crop_bottom,
                0:w
            ]

            cv2.imwrite(
                str(
                    crops_dir /
                    f"{image_path.stem}_row_{row_index:03d}.png"
                ),
                crop
            )

        row_index += 1

    logger.info(
        f"  {image_path.name}: {len(bboxes)} rows detected"
    )

    return bboxes


if __name__ == "__main__":

    pages = sorted(config.IMAGES_DIR.rglob("*.png"))

    if not pages:
        print("No rendered pages found.")
    else:
        rows = segment_page(pages[0])

        print(
            f"{pages[0].name}: "
            f"{len(rows)} rows detected"
        )