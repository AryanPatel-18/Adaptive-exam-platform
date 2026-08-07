from dataclasses import dataclass, field

# Slots true is so that python does not create a dict and use up RAM
@dataclass(slots=True)
class ExtractedOption:
    text: str
    is_correct: bool = False


@dataclass(slots=True)
class ExtractedQuestion:
    number: int
    text: str
    options: list[ExtractedOption] = field(default_factory=list)
    topics: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ExtractionResult:
    questions: list[ExtractedQuestion] = field(default_factory=list)


@dataclass(slots=True)
class OCRResult:
    """
    Represents the result of an OCR extraction for a single page.
    """

    text: str
    confidence: float = 0.0


@dataclass(slots=True)
class PageResult:
    """
    Per-page extraction result with confidence tracking.
    """

    page: int
    content: str
    headings: list[str] = field(default_factory=list)
    extraction_method: str = "direct"
    ocr_average_confidence: float | None = None
    needs_review: bool = False
    word_count: int = 0
    char_count: int = 0


@dataclass(slots=True)
class NotesExtractionResult:
    """
    Complete notes extraction output across all pages.
    """

    source_pdf: str = ""
    total_pages: int = 0
    pages_extracted: int = 0
    gpu_used: bool = False
    pages: list[PageResult] = field(default_factory=list)
    detected_headings: list[str] = field(default_factory=list)
