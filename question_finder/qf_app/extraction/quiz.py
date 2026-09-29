"""Framework-specific quiz parsers (WordPress plugins, JSON schemas)."""

import json
from bs4 import BeautifulSoup
from qf_app.extraction.html import ExtractedOption, ExtractedQuestion


class StructuredQuizExtractor:
    """Extracts questions from structured quiz plugins and JSON-LD schema."""

    def extract_from_json_ld(self, json_ld_blocks: list[dict]) -> list[ExtractedQuestion]:
        """Extract questions defined in schema.org/Question format."""
        questions: list[ExtractedQuestion] = []

        for block in json_ld_blocks:
            # Handle @type == Question or Quiz
            if block.get("@type") in ("Question", "Quiz"):
                stem = block.get("name") or block.get("text", "")
                if not stem:
                    continue

                options: list[ExtractedOption] = []
                suggested = block.get("suggestedAnswer", [])
                accepted = block.get("acceptedAnswer", {})

                accepted_text = accepted.get("text", "") if isinstance(accepted, dict) else ""

                if isinstance(suggested, list):
                    for idx, ans in enumerate(suggested):
                        ans_text = ans.get("text", "") if isinstance(ans, dict) else str(ans)
                        key = chr(65 + idx)
                        is_correct = (ans_text == accepted_text) or (ans.get("@type") == "Answer" and ans.get("isCorrect", False))
                        options.append(ExtractedOption(key=key, text=ans_text, is_correct=is_correct))

                if len(options) >= 2:
                    questions.append(
                        ExtractedQuestion(
                            stem=stem,
                            options=options,
                            explanation=accepted.get("text", "") if isinstance(accepted, dict) else "",
                            extraction_strategy="JSON_LD_QUIZ",
                        )
                    )

        return questions

    def extract_from_wp_quiz(self, html: str) -> list[ExtractedQuestion]:
        """Extract from common WordPress quiz markup (.wp-quiz, .wp-pro-quiz)."""
        soup = BeautifulSoup(html, "lxml")
        questions: list[ExtractedQuestion] = []

        for q_block in soup.find_all(class_=lambda c: c and ("wpProQuiz_listItem" in c or "quiz-question" in c or "wp-quiz" in c)):
            question_text_elem = q_block.find(class_=lambda c: c and ("question_text" in c or "question-title" in c))
            if not question_text_elem:
                continue

            stem = question_text_elem.get_text(strip=True)
            options: list[ExtractedOption] = []

            for idx, opt_elem in enumerate(q_block.find_all(class_=lambda c: c and ("wpProQuiz_questionListItem" in c or "quiz-option" in c))):
                opt_text = opt_elem.get_text(strip=True)
                is_correct = "wpProQuiz_answerCorrect" in opt_elem.get("class", []) or "is-correct" in opt_elem.get("class", [])
                options.append(ExtractedOption(key=chr(65 + idx), text=opt_text, is_correct=is_correct))

            if len(stem) > 15 and len(options) >= 2:
                questions.append(
                    ExtractedQuestion(
                        stem=stem,
                        options=options,
                        explanation="",
                        extraction_strategy="WORDPRESS_QUIZ_PLUGIN",
                    )
                )

        return questions
