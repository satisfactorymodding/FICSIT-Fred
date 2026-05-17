from typing import IO, List, Tuple
import time
import numpy as np
from PIL import Image, ImageEnhance
from pytesseract import image_to_string, TesseractError
from rapidocr_onnxruntime import RapidOCR

from fred.libraries.common import new_logger

logger = new_logger(__name__)

_ocr_engine = RapidOCR()


def get_box_geometry(box: list) -> Tuple[int, int, int, int]:
    left = min(p[0] for p in box)
    top = min(p[1] for p in box)
    right = max(p[0] for p in box)
    bottom = max(p[1] for p in box)
    return int(left), int(top), int(right), int(bottom)


def run_tesseract(image: Image.Image) -> Tuple[str, float]:
    start_time = time.time()
    try:
        text = image_to_string(image)
    except TesseractError as oops:
        logger.error("Tesseract processing failed")
        logger.exception(oops)
        text = ""
    return text, time.time() - start_time


def run_paddle(image: Image.Image, use_cls: bool = True) -> Tuple[str, List[float], List[float]]:
    img_array = np.array(image)
    result, elapse = _ocr_engine(img_array, use_cls=use_cls)
    texts = []
    scores = []
    if result:
        for line in result:
            texts.append(line[1])
            scores.append(line[2])
    return "\n".join(texts), scores, elapse or [0.0, 0.0, 0.0]


def run_complex_paddle(image: Image.Image, proximity_threshold: int = 15) -> Tuple[str, float]:
    start_time = time.time()
    img_array = np.array(image)
    img_w, img_h = image.size

    result, _ = _ocr_engine(img_array, use_cls=False)
    if not result:
        return "", time.time() - start_time

    candidates = []
    for line in result:
        box_coords = line[0]
        p_text = line[1].strip()
        l, t, r, b = get_box_geometry(box_coords)

        w, h = r - l, b - t
        aspect_ratio = w / h if h > 0 else 0

        if aspect_ratio < 1.2 or w < 10:
            continue

        center_x, center_y = (l + r) / 2, (t + b) / 2
        is_central = (0.15 * img_w < center_x < 0.85 * img_w) and (
            0.20 * img_h < center_y < 0.80 * img_h
        )

        if is_central:
            candidates.append({"box": [l, t, r, b], "text": p_text})

    merged_any = True
    while merged_any:
        merged_any = False
        new_candidates = []
        visited = set()

        for i in range(len(candidates)):
            if i in visited:
                continue

            curr = candidates[i]
            for j in range(i + 1, len(candidates)):
                if j in visited:
                    continue

                other = candidates[j]

                if not (
                    curr["box"][2] + proximity_threshold < other["box"][0]
                    or curr["box"][0] - proximity_threshold > other["box"][2]
                    or curr["box"][3] + proximity_threshold < other["box"][1]
                    or curr["box"][1] - proximity_threshold > other["box"][3]
                ):

                    curr["box"] = [
                        min(curr["box"][0], other["box"][0]),
                        min(curr["box"][1], other["box"][1]),
                        max(curr["box"][2], other["box"][2]),
                        max(curr["box"][3], other["box"][3]),
                    ]
                    curr["text"] = f"{curr['text']} {other['text']}"
                    visited.add(j)
                    merged_any = True

            new_candidates.append(curr)
        candidates = new_candidates

    total_text = "\n".join([c["text"] for c in candidates])
    return total_text, time.time() - start_time


def read(file: IO) -> str:
    try:
        raw_image = Image.open(file)

        tess_image = raw_image.copy()
        ratio = 2160 / tess_image.height
        if ratio > 1:
            tess_image = tess_image.resize(
                (round(tess_image.width * ratio), round(tess_image.height * ratio)),
                Image.Resampling.LANCZOS,
            )

        try:
            enhancer_contrast = ImageEnhance.Contrast(tess_image)
            tess_image = enhancer_contrast.enhance(2)
            enhancer_sharpness = ImageEnhance.Sharpness(tess_image)
            tess_image = enhancer_sharpness.enhance(10)
        except ValueError as e:
            logger.warning("Failed to enhance image preprocessing pipeline.")
            logger.exception(e)

        t_text, t_time = run_tesseract(tess_image)
        p_text, p_scores, p_time = run_paddle(raw_image, use_cls=True)
        po_text, po_scores, po_time = run_paddle(raw_image, use_cls=False)
        r_text, r_time = run_complex_paddle(raw_image)

        lines = [
            "================ RESULTS ================\n",
            "--- TESSERACT ---",
            f"Time: {t_time:.2f}s",
            t_text or "",
            "\n--- PURE PADDLE OCR ---",
            f"Time: {sum(p_time):.2f}s (det={p_time[0]:.2f}, cls={p_time[1]:.2f}, rec={p_time[2]:.2f})",
        ]
        if p_scores:
            lines.append(f"(avg score: {sum(p_scores)/len(p_scores):.3f}, lines: {len(p_scores)})")
        lines.append(p_text or "")

        lines.append("\n--- OPTIMIZED PADDLE OCR ---")
        lines.append(f"Time: {sum(po_time):.2f}s (det={po_time[0]:.2f}, cls={po_time[1]:.2f}, rec={po_time[2]:.2f})")
        if po_scores:
            lines.append(f"(avg score: {sum(po_scores)/len(po_scores):.3f}, lines: {len(po_scores)})")
        lines.append(po_text or "")

        lines.append("\n--- PADDLE COMPLEX SOLUTION ---")
        lines.append(f"Time: {r_time:.2f}s")
        lines.append(r_text or "")
        lines.append("\n=========================================")

        output = "\n".join(lines)
        print(output)
        logger.info("OCR engine benchmark profiling complete.")
        return output

    except Exception as oops:
        logger.error(f"OCR evaluation routine encountered an error: {oops}")
        return ""