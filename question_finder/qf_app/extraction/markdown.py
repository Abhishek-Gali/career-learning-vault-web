"""Markdown practice exam extractor for open study repositories."""

import re
from qf_app.core.types import QuestionType
from qf_app.extraction.html import ExtractedOption, ExtractedQuestion

# Regex to match question start: e.g. "1. AWS allows users...", "## Question 1", "### Q1."
QUESTION_START_RE = re.compile(
    r"(?:^|\n)(?:###?\s*(?:Question\s*\d+|Q\d+[\.\:]?|\d+[\.\)])|\d+[\.\)]\s+)(.+?)(?=\n\s*[-*]\s*[A-Z][\.\)]|\n\s*[A-Z][\.\)])",
    re.DOTALL | re.IGNORECASE,
)

OPTION_LINE_RE = re.compile(
    r"^\s*[-*]?\s*([A-E])[\.\)]\s*(.+)$",
    re.MULTILINE,
)

ANSWER_BLOCK_RE = re.compile(
    r"(?:Correct\s*answer|Answer|Ans)[\s\:\-]+([A-E,\s]+)",
    re.IGNORECASE,
)

EXPLANATION_BLOCK_RE = re.compile(
    r"(?:Explanation|Rationale)[\s\:\-]+(.+?)(?=(?:\n\d+[\.\)]|\n###|\Z))",
    re.DOTALL | re.IGNORECASE,
)


class MarkdownQuestionExtractor:
    """Extracts questions from structured Markdown practice exam files."""

    def extract_from_markdown(self, text: str, source_url: str = "") -> list[ExtractedQuestion]:
        """Parse markdown text and extract all multiple choice questions."""
        questions: list[ExtractedQuestion] = []

        # Split into blocks by question number e.g. "\n1. ", "\n2. ", "\n### Question "
        raw_blocks = re.split(r"\n(?=(?:\d+[\.\)]\s+[A-Z]|###?\s*Question|\bQuestion\s*\d+[\.\:]))", text, flags=re.IGNORECASE)

        for block in raw_blocks:
            lines = [l.strip() for l in block.splitlines() if l.strip()]
            if not lines:
                continue

            # First line(s) usually contain stem
            stem_lines = []
            options: list[ExtractedOption] = []
            explanation = ""
            answer_keys: list[str] = []
            in_options = False

            for line in lines:
                opt_match = re.match(r"^[-*]?\s*([A-E])[\.\)]\s*(.+)", line)
                if opt_match:
                    in_options = True
                    k = opt_match.group(1).upper()
                    t = opt_match.group(2).strip()
                    options.append(ExtractedOption(key=k, text=t, is_correct=False))
                    continue

                ans_match = ANSWER_BLOCK_RE.search(line)
                if ans_match:
                    ans_str = ans_match.group(1).upper()
                    # Extract single or multiple letters
                    letters = re.findall(r"[A-E]", ans_str)
                    answer_keys.extend(letters)
                    continue

                if "explanation" in line.lower():
                    explanation = line.split(":", 1)[-1].strip()
                    continue

                if not in_options and not line.startswith("#") and not line.startswith("---"):
                    stem_lines.append(line)

            stem = " ".join(stem_lines).strip()
            # Clean leading number from stem
            stem_cleaned = re.sub(r"^(?:Question\s*\d+[\.\:]?|\d+[\.\)])\s*", "", stem).strip()

            # Mark correct options
            if options and answer_keys:
                for opt in options:
                    if opt.key in answer_keys:
                        opt.is_correct = True

            if len(stem_cleaned) >= 15 and len(options) >= 2:
                q_type = QuestionType.MULTIPLE_RESPONSE.value if len(answer_keys) > 1 else QuestionType.SINGLE_CHOICE.value
                questions.append(
                    ExtractedQuestion(
                        stem=stem_cleaned,
                        options=options,
                        explanation=explanation,
                        question_type=q_type,
                        extraction_strategy="MARKDOWN_STUDY_PARSER",
                    )
                )

        return questions
