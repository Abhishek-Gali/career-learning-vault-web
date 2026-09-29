"""Multi-strategy HTML question extractor."""

import re
from bs4 import BeautifulSoup
from pydantic import BaseModel

from qf_app.core.types import QuestionType


class ExtractedOption(BaseModel):
    """Raw extracted option item."""

    key: str  # e.g., 'A', 'B', '1', 'a'
    text: str
    is_correct: bool = False


class ExtractedQuestion(BaseModel):
    """Raw extracted question item from page."""

    stem: str
    options: list[ExtractedOption]
    explanation: str = ""
    question_type: str = QuestionType.SINGLE_CHOICE.value
    raw_evidence: str = ""
    extraction_strategy: str = "HTML_SEMANTIC"


QUESTION_NUMBER_REGEX = re.compile(
    r"^(?:question\s*\d+|q\d+[\.\:]?|\d+[\.\)])\s*",
    re.IGNORECASE,
)

ANSWER_LINE_REGEX = re.compile(
    r"(?:correct\s*(?:answer|option)|answer|ans)[\s\:\-]+([a-d\d\s\,]+)",
    re.IGNORECASE,
)


class HtmlQuestionExtractor:
    """Extracts structured questions from generic and educational HTML pages."""

    def extract_questions(self, html: str) -> list[ExtractedQuestion]:
        """Run extraction strategies and return all discovered question objects."""
        soup = BeautifulSoup(html, "lxml")

        # 1. Try structured accordion / details elements
        questions = self._extract_from_details(soup)
        if questions:
            return questions

        # 2. Try heading + list pattern
        questions = self._extract_from_headings_and_lists(soup)
        if questions:
            return questions

        # 3. Try paragraphs with question markers
        questions = self._extract_from_paragraphs(soup)
        return questions

    def _extract_from_details(self, soup: BeautifulSoup) -> list[ExtractedQuestion]:
        """Extract questions formatted as <details><summary> or collapsible FAQ items."""
        results = []
        for details in soup.find_all("details"):
            summary = details.find("summary")
            if not summary:
                continue

            stem_text = summary.get_text(strip=True)
            stem_cleaned = QUESTION_NUMBER_REGEX.sub("", stem_text).strip()

            options = []
            answer_text = ""
            explanation = ""

            # Check for list of options inside details
            ul = details.find(["ul", "ol"])
            if ul:
                for idx, li in enumerate(ul.find_all("li")):
                    opt_text = li.get_text(strip=True)
                    key = chr(65 + idx)
                    options.append(ExtractedOption(key=key, text=opt_text, is_correct=False))

            # Look for answer text in paragraphs
            for p in details.find_all("p"):
                p_text = p.get_text(strip=True)
                ans_match = ANSWER_LINE_REGEX.search(p_text)
                if ans_match:
                    answer_text = ans_match.group(1).strip().upper()
                elif "explanation:" in p_text.lower():
                    explanation = p_text.split(":", 1)[-1].strip()

            # Mark correct options
            if options and answer_text:
                for opt in options:
                    if opt.key in answer_text:
                        opt.is_correct = True

            if len(stem_cleaned) > 15 and len(options) >= 2:
                results.append(
                    ExtractedQuestion(
                        stem=stem_cleaned,
                        options=options,
                        explanation=explanation,
                        question_type=QuestionType.MULTIPLE_RESPONSE.value if len(answer_text.split(",")) > 1 else QuestionType.SINGLE_CHOICE.value,
                        extraction_strategy="HTML_DETAILS_ACCORDION",
                    )
                )
        return results

    def _extract_from_headings_and_lists(self, soup: BeautifulSoup) -> list[ExtractedQuestion]:
        """Extract questions with heading tags (h2/h3/h4) followed by option lists."""
        results = []
        for heading in soup.find_all(["h2", "h3", "h4", "h5", "p"]):
            text = heading.get_text(strip=True)
            if not QUESTION_NUMBER_REGEX.match(text) and "which" not in text.lower() and "what" not in text.lower() and "how" not in text.lower():
                continue

            stem_cleaned = QUESTION_NUMBER_REGEX.sub("", text).strip()
            if len(stem_cleaned) < 15:
                continue

            # Find next sibling list or options container
            next_elem = heading.find_next_sibling(["ul", "ol", "div"])
            if not next_elem:
                continue

            options = []
            if next_elem.name in ("ul", "ol"):
                for idx, li in enumerate(next_elem.find_all("li")):
                    opt_raw = li.get_text(strip=True)
                    # Strip leading A., B., 1., etc.
                    opt_text = re.sub(r"^[A-Da-d\d][\.\)]\s*", "", opt_raw).strip()
                    options.append(ExtractedOption(key=chr(65 + idx), text=opt_text, is_correct=False))

            # Look for answer indicator
            answer_elem = next_elem.find_next_sibling(["p", "div"])
            explanation = ""
            if answer_elem:
                ans_text = answer_elem.get_text(strip=True)
                ans_match = ANSWER_LINE_REGEX.search(ans_text)
                if ans_match:
                    ans_key = ans_match.group(1).strip().upper()
                    for opt in options:
                        if opt.key in ans_key:
                            opt.is_correct = True
                if "explanation" in ans_text.lower():
                    explanation = ans_text

            if len(options) >= 2:
                results.append(
                    ExtractedQuestion(
                        stem=stem_cleaned,
                        options=options,
                        explanation=explanation,
                        extraction_strategy="HTML_HEADING_LIST",
                    )
                )
        return results

    def _extract_from_paragraphs(self, soup: BeautifulSoup) -> list[ExtractedQuestion]:
        """Extract questions embedded directly in formatted text paragraphs."""
        results = []
        paragraphs = soup.find_all("p")

        for idx, p in enumerate(paragraphs):
            text = p.get_text(strip=True)
            if not QUESTION_NUMBER_REGEX.match(text):
                continue

            stem_cleaned = QUESTION_NUMBER_REGEX.sub("", text).strip()
            options = []
            explanation = ""

            # Check if following paragraphs contain A), B), C), D)
            curr_idx = idx + 1
            while curr_idx < len(paragraphs) and len(options) < 6:
                next_p = paragraphs[curr_idx].get_text(strip=True)
                opt_match = re.match(r"^([A-D])[\.\)]\s*(.+)", next_p, re.IGNORECASE)
                if opt_match:
                    key = opt_match.group(1).upper()
                    opt_text = opt_match.group(2).strip()
                    options.append(ExtractedOption(key=key, text=opt_text, is_correct=False))
                    curr_idx += 1
                else:
                    ans_match = ANSWER_LINE_REGEX.search(next_p)
                    if ans_match:
                        ans_key = ans_match.group(1).strip().upper()
                        for opt in options:
                            if opt.key in ans_key:
                                opt.is_correct = True
                    break

            if len(stem_cleaned) > 15 and len(options) >= 2:
                results.append(
                    ExtractedQuestion(
                        stem=stem_cleaned,
                        options=options,
                        explanation=explanation,
                        extraction_strategy="HTML_PARAGRAPH_STREAM",
                    )
                )
        return results
