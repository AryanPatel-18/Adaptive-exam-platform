"""
Notes extraction module.

Extracts text from handwritten / scanned PDF notes using a
direct-text-first strategy with OCR fallback.

Logic ported from tests/Extraction Files Testing/hand_notes_extraction.py.
"""

from __future__ import annotations

import gc
import logging
import multiprocessing
import os
import re
from pathlib import Path
from statistics import median
from typing import Optional

import cv2
import easyocr
import fitz  # PyMuPDF
import numpy as np

from processing.dtos import NotesExtractionResult, PageResult

logger = logging.getLogger("processing")

# ============================================================
# CONFIG
# ============================================================

OCR_LANGS = ["en"]
OCR_ZOOM = 3.0
MIN_DIRECT_TEXT_CHARS = 80
MIN_OCR_CONFIDENCE = 0.3
POSTPROCESS_WORKERS = max(1, os.cpu_count() - 1)


# ============================================================
# GPU DETECTION
# ============================================================

def _detect_gpu() -> bool:
    """Return True if a CUDA-capable GPU is available."""
    try:
        import torch
        available = torch.cuda.is_available()
        if available:
            name = torch.cuda.get_device_name(0)
            logger.info("[GPU] CUDA device detected: %s", name)
        else:
            logger.info("[GPU] No CUDA device found – falling back to CPU.")
        return available
    except ImportError:
        logger.warning("[GPU] PyTorch not installed – cannot check CUDA. Using CPU.")
        return False


OCR_GPU = _detect_gpu()


# ============================================================
# TEXT HELPERS
# ============================================================

def clean_text(text: str) -> str:
    """Universal whitespace / null-byte normalisation – no word changes."""
    logger.debug("Cleaning text...")
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def unique_preserve_order(items: list[str]) -> list[str]:
    """Deduplicate a list of strings while preserving insertion order."""
    logger.debug("Deduplicating list of %d items while preserving order...", len(items))
    seen, out = set(), []
    for item in items:
        item = clean_text(item)
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out


def looks_like_heading(
    text: str,
    font_size: Optional[float] = None,
    median_font_size: Optional[float] = None,
) -> bool:
    """
    Heuristic: a line is a heading when it is short AND either
    mostly uppercase or rendered in a larger font than the page median.
    No domain vocabulary required.
    """
    text = clean_text(text)
    if not text:
        return False
    words = text.split()
    if len(words) > 12 or len(text) > 120:
        return False
    if text.endswith((".", ",", ";", "?", "!", ":")):
        return False
    alpha_chars = [c for c in text if c.isalpha()]
    if not alpha_chars:
        return False
    if text.isupper():
        return True
    upper_ratio = sum(c.isupper() for c in alpha_chars) / len(alpha_chars)
    if upper_ratio >= 0.6 and len(words) <= 10:
        return True
    if font_size is not None and median_font_size is not None:
        if font_size >= median_font_size * 1.2:
            return True
    return (
        len(words) <= 5
        and len(text) > 8
    )


# ============================================================
# DIRECT TEXT EXTRACTION (for digitally generated PDFs)
# ============================================================

def extract_direct_text(page: fitz.Page) -> tuple[str, list[str]]:
    """
    Extract text directly from a PDF page using PyMuPDF's
    structured text layer. Also detect headings via font size.

    Args:
        page: A PyMuPDF Page object.

    Returns:
        Tuple of (full_text, headings_list).
    """

    logger.debug("Extracting direct text and text dictionaries from page...")
    raw_text = clean_text(page.get_text("text"))
    text_dict = page.get_text("dict")
    line_records: list[tuple[float, float, str, Optional[float]]] = []
    font_sizes: list[float] = []

    for block in text_dict.get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            parts, local_sizes = [], []
            for span in line.get("spans", []):
                span_text = clean_text(span.get("text", ""))
                if span_text:
                    parts.append(span_text)
                size = span.get("size")
                if isinstance(size, (int, float)):
                    local_sizes.append(float(size))
                    font_sizes.append(float(size))
            line_text = clean_text(" ".join(parts))
            if not line_text:
                continue
            bbox = line.get("bbox", [0, 0, 0, 0])
            line_records.append((
                float(bbox[1]) if len(bbox) > 1 else 0.0,
                float(bbox[0]) if len(bbox) > 0 else 0.0,
                line_text,
                max(local_sizes) if local_sizes else None,
            ))

    line_records.sort(key=lambda r: (r[0], r[1]))
    median_fs = float(median(font_sizes)) if font_sizes else None
    headings = [t for _, _, t, fs in line_records if looks_like_heading(t, fs, median_fs)]
    return raw_text, unique_preserve_order(headings)


# ============================================================
# IMAGE / OCR HELPERS
# ============================================================

def render_page_to_image(page: fitz.Page) -> np.ndarray:
    """Render a PDF page to a numpy RGB array using PyMuPDF."""
    logger.debug("Rendering PDF page to image at zoom %s...", OCR_ZOOM)
    pix = page.get_pixmap(matrix=fitz.Matrix(OCR_ZOOM, OCR_ZOOM), alpha=False)
    image = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    if pix.n == 3:
        return image  # already RGB
    if pix.n == 4:
        return cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)
    return image


def preprocess_for_ocr(image_rgb: np.ndarray) -> dict[str, np.ndarray]:
    """
    Create preprocessed image variants for OCR.
    Lightweight: grayscale + light Gaussian blur.
    """
    logger.debug("Preprocessing image for OCR (grayscale + Gaussian blur)...")
    gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    return {"gray": gray}


def ocr_image(
    image: np.ndarray,
    reader: easyocr.Reader,
) -> tuple[str, list[str], float]:
    """
    Run EasyOCR on a single image (numpy array).

    Returns:
        Tuple of (text, headings, average_confidence).
    """
    try:
        results = reader.readtext(image, detail=1, paragraph=False)
    except Exception as e:
        logger.error("OCR execution failed: %s", e)
        return "", [], 0.0

    texts = []
    scores = []

    for detection in results:
        if not detection or len(detection) < 3:
            continue

        text = clean_text(str(detection[1]))
        score = float(detection[2])

        if not text:
            continue
        if score < MIN_OCR_CONFIDENCE:
            continue

        texts.append(text)
        scores.append(score)

    if not texts:
        logger.warning("No text detected above confidence threshold during OCR.")
        return "", [], 0.0

    page_text = "\n".join(texts)
    avg_conf = sum(scores) / len(scores)

    headings = [
        line for line in texts
        if looks_like_heading(line)
    ]

    logger.info(
        "OCR successful: extracted %d text blocks with average confidence %.2f",
        len(texts),
        avg_conf,
    )
    return page_text, unique_preserve_order(headings), avg_conf


# ============================================================
# PER-PAGE EXTRACTION
# ============================================================

def extract_page(
    page_number: int,
    page: fitz.Page,
    reader: easyocr.Reader,
    images_dir: str,
) -> dict:
    """
    Try direct text extraction first. If the page appears to be a scan /
    image-only, render it and run EasyOCR on preprocessed variants,
    keeping whichever scores highest (text length × confidence).
    """

    logger.info("Page %d: Attempting direct text extraction...", page_number)

    # Try direct text first (for digitally generated PDFs)
    direct_text, direct_headings = extract_direct_text(page)

    if len(direct_text) >= MIN_DIRECT_TEXT_CHARS:
        logger.info(
            "Page %d: Successfully extracted direct text (%d characters, %d headings). Skipping OCR.",
            page_number,
            len(direct_text),
            len(direct_headings),
        )
        return {
            "page": page_number,
            "content": direct_text,
            "headings": direct_headings,
            "extraction_method": "direct",
            "ocr_average_confidence": None,
        }

    logger.info(
        "Page %d: Insufficient direct text (%d characters). Rendering to image for OCR...",
        page_number,
        len(direct_text),
    )

    # Render page to image
    image = render_page_to_image(page)

    # Save the raw page image
    raw_path = os.path.join(images_dir, f"page_{page_number}.jpg")
    cv2.imwrite(raw_path, cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
    logger.debug("Page %d: Saved raw page image to %s", page_number, raw_path)

    # Preprocess and OCR
    logger.info("Page %d: Preprocessing image for OCR...", page_number)
    variants = preprocess_for_ocr(image)

    # Save processed variants
    for name, img in variants.items():
        proc_path = os.path.join(images_dir, f"processed_{page_number}_{name}.jpg")
        cv2.imwrite(proc_path, img)

    best_text, best_conf, best_headings, best_method = "", 0.0, [], ""

    for name, img in variants.items():
        logger.info("Page %d: Running EasyOCR on variant '%s'...", page_number, name)
        text, headings, conf = ocr_image(img, reader)
        if len(text) * max(conf, 0.01) > len(best_text) * max(best_conf, 0.01):
            best_text, best_conf, best_headings, best_method = (
                text, conf, headings, f"ocr:{name}"
            )

    logger.info(
        "Page %d: Best extraction method was '%s' (avg confidence: %.2f%%)",
        page_number,
        best_method,
        best_conf * 100,
    )

    return {
        "page": page_number,
        "content": best_text,
        "headings": best_headings,
        "extraction_method": best_method,
        "ocr_average_confidence": best_conf,
        "needs_review": best_conf < 0.75,
    }


# ============================================================
# POST-PROCESSING WORKER (runs inside multiprocessing.Pool)
# ============================================================

def _postprocess_page(page: dict) -> dict:
    """
    Light, domain-agnostic post-processing:
      - Recount words / chars on the cleaned text
      - Re-detect headings from the final text
    No word substitution or vocabulary matching.
    """
    logger.debug("Post-processing page %s...", page.get("page", "unknown"))
    content = clean_text(page.get("content", ""))
    headings = [
        ln.strip() for ln in content.split("\n")
        if ln.strip() and looks_like_heading(ln.strip())
    ]
    return {
        **page,
        "content": content,
        "headings": unique_preserve_order(headings),
        "word_count": len(content.split()),
        "char_count": len(content),
    }


# ============================================================
# NOTES EXTRACTOR CLASS
# ============================================================

class NotesExtractor:
    """
    Extracts text from notes PDFs using direct text extraction
    with OCR fallback, matching the logic from
    tests/Extraction Files Testing/hand_notes_extraction.py.
    """

    def extract(
        self,
        pdf_path: Path,
        output_directory: Path,
    ) -> NotesExtractionResult:
        """
        Extract text from a notes PDF.

        Args:
            pdf_path: Path to the notes PDF.
            output_directory: Directory to store temporary page images.

        Returns:
            NotesExtractionResult containing per-page extraction data.
        """

        if not pdf_path.exists():
            logger.error("PDF not found at path: %s", pdf_path)
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        # Create images directory
        images_dir = str(output_directory / "images")
        os.makedirs(images_dir, exist_ok=True)

        logger.info("Opening PDF document: %s", pdf_path)
        doc = fitz.open(str(pdf_path))
        num_pages = len(doc)

        logger.info(
            "PDF: %s | Pages: %d | GPU: %s | Zoom: %sx",
            pdf_path.name,
            num_pages,
            "enabled" if OCR_GPU else "disabled (CPU fallback)",
            OCR_ZOOM,
        )

        # Stage 1: Initialise EasyOCR
        logger.info("[1/3] Initialising EasyOCR reader...")
        ocr_reader = easyocr.Reader(OCR_LANGS, gpu=OCR_GPU)
        logger.info("[1/3] EasyOCR reader initialized.")

        # Stage 2: Text extraction (sequential — EasyOCR is not thread-safe)
        logger.info("[2/3] Starting extraction of %d pages...", num_pages)

        raw_pages: list[dict] = []

        for i in range(num_pages):
            logger.info("Starting page %d/%d...", i + 1, num_pages)
            try:
                page = doc.load_page(i)
                result = extract_page(i + 1, page, ocr_reader, images_dir)
            except Exception as e:
                logger.error(
                    "Page %d extraction failed: %s: %s",
                    i + 1,
                    type(e).__name__,
                    e,
                )
                result = {
                    "page": i + 1,
                    "content": "",
                    "headings": [],
                    "extraction_method": "error",
                    "ocr_average_confidence": 0.0,
                    "needs_review": True,
                    "error": str(e),
                }
            raw_pages.append(result)

            # Free memory between pages
            gc.collect()

        logger.info("[2/3] Finished extraction of all pages.")

        doc.close()

        # Stage 3: Post-processing
        logger.info(
            "[3/3] Starting post-processing using %d processes...",
            POSTPROCESS_WORKERS,
        )

        use_pool = POSTPROCESS_WORKERS > 1 and num_pages > 1
        if use_pool:
            with multiprocessing.Pool(processes=POSTPROCESS_WORKERS) as pool:
                pages = list(pool.imap(_postprocess_page, raw_pages, chunksize=4))
        else:
            pages = [_postprocess_page(p) for p in raw_pages]

        logger.info("Post-processing complete.")

        # Aggregate all headings
        all_headings: list[str] = []
        for p in pages:
            all_headings.extend(p.get("headings", []))

        # Build page result DTOs
        page_results = [
            PageResult(
                page=p["page"],
                content=p.get("content", ""),
                headings=p.get("headings", []),
                extraction_method=p.get("extraction_method", "unknown"),
                ocr_average_confidence=p.get("ocr_average_confidence"),
                needs_review=p.get("needs_review", False),
                word_count=p.get("word_count", 0),
                char_count=p.get("char_count", 0),
            )
            for p in pages
        ]

        pages_with_text = sum(1 for p in page_results if p.word_count > 0)
        total_words = sum(p.word_count for p in page_results)

        logger.info(
            "Extraction complete: %d/%d pages processed | ~%d words extracted | GPU: %s",
            pages_with_text,
            len(page_results),
            total_words,
            "on" if OCR_GPU else "off",
        )

        return NotesExtractionResult(
            source_pdf=pdf_path.name,
            total_pages=num_pages,
            pages_extracted=pages_with_text,
            gpu_used=OCR_GPU,
            pages=page_results,
            detected_headings=unique_preserve_order(all_headings),
        )