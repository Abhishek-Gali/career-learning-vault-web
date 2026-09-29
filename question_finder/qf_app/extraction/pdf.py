"""PDF question extractor using PyMuPDF."""

import re
try:
    import pymupdf
except ImportError:
    pymupdf = None

from qf_app.core.logging import get_logger
from qf_app.extraction.html import ExtractedOption, ExtractedQuestion

logger = get_logger(__name__)


class PdfQuestionExtractor:
    """Extracts questions and options from PDF documents."""

    def extract_from_bytes(self, pdf_bytes: bytes) -> list[ExtractedQuestion]:
        """Extract text from PDF stream and parse question blocks."""
        questions: list[ExtractedQuestion] = []
        if pymupdf is None:
            return questions
        try:
            doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
            full_text_pages = [page.get_text() for page in doc]
            full_text = "\n".join(full_text_pages)

            # Split on question numbers e.g. "Question 1", "1)", "1."
            raw_blocks = re.split(r"\n(?=(?:Question\s*\d+|\d+[\.\)]\s+[A-Z]))", full_text, flags=re.IGNORECASE)

            for block in raw_blocks:
                lines = [l.strip() for l in block.splitlines() if l.strip()]
                if not lines:
                    continue

                stem_lines = []
                options: list[ExtractedOption] = []
                explanation = ""
                reading_stem = True

                for line in lines:
                    opt_match = re.match(r"^([A-D])[\.\)]\s*(.+)", line, re.IGNORECASE)
                    if opt_match:
                        reading_stem = False
                        key = opt_match.group(1).upper()
                        text = opt_match.group(2).strip()
                        options.append(ExtractedOption(key=key, text=text, is_correct=False))
                    elif "answer:" in line.lower() or "correct:" in line.lower():
                        reading_stem = False
                        ans_key = line.split(":")[-1].strip().upper()
                        for opt in options:
                            if opt.key in ans_key:
                                opt.is_correct = True
                    elif "explanation:" in line.lower():
                        reading_stem = False
                        explanation = line.split(":", 1)[-1].strip()
                    elif reading_stem:
                        stem_lines.append(line)

                stem = " ".join(stem_lines)
                stem_cleaned = re.sub(r"^(?:Question\s*\d+|\d+[\.\)])\s*", "", stem).strip()

                if len(stem_cleaned) > 15 and len(options) >= 2:
                    questions.append(
                        ExtractedQuestion(
                            stem=stem_cleaned,
                            options=options,
                            explanation=explanation,
                            extraction_strategy="PDF_LAYOUT_PARSER",
                        )
                    )
        except Exception as err:
            logger.warning("PDF question extraction failed: %s", err)

        return questions
