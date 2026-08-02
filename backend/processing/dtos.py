from dataclasses import dataclass, field


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

@dataclass(slots=True, frozen=True)
class OCRResult:
    """
    Represents the result of an OCR extraction.
    """

    text: str
