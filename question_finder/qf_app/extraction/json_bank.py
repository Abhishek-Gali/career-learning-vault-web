"""Parser for structured JSON question banks."""

from typing import Any
from qf_app.core.types import QuestionType
from qf_app.extraction.html import ExtractedOption, ExtractedQuestion


class JsonBankExtractor:
    """Extracts questions from structured JSON datasets and test banks."""

    def extract_from_json(self, data: list[dict[str, Any]] | dict[str, Any], source_url: str = "") -> list[dict[str, Any]]:
        """Parse JSON list of question objects into normalized structures."""
        items: list[dict[str, Any]] = []

        if isinstance(data, dict):
            raw_questions = data.get("questions", data.get("items", [data]))
        elif isinstance(data, list):
            raw_questions = data
        else:
            return items

        for item in raw_questions:
            if not isinstance(item, dict):
                continue

            stem = item.get("question") or item.get("stem") or item.get("text", "")
            if not stem or len(stem.strip()) < 15:
                continue

            raw_options = item.get("options")
            options: list[ExtractedOption] = []
            answer_raw = item.get("answer") or item.get("correctAnswer") or item.get("correct")

            # Answer keys can be string "A" or list ["A", "C"]
            correct_keys: set[str] = set()
            if isinstance(answer_raw, list):
                correct_keys = {str(a).strip().upper() for a in answer_raw}
            elif isinstance(answer_raw, str):
                correct_keys = {a.strip().upper() for a in answer_raw.split(",") if a.strip()}

            # Options can be dict {"A": "text", "B": "text"} or list
            if isinstance(raw_options, dict):
                for k, v in raw_options.items():
                    key_str = str(k).strip().upper()
                    is_corr = key_str in correct_keys or (isinstance(v, dict) and v.get("isCorrect", False))
                    opt_text = v if isinstance(v, str) else v.get("text", str(v))
                    options.append(ExtractedOption(key=key_str, text=str(opt_text).strip(), is_correct=is_corr))
            elif isinstance(raw_options, list):
                for idx, opt in enumerate(raw_options):
                    key_str = chr(65 + idx)
                    if isinstance(opt, dict):
                        k = opt.get("key", opt.get("id", key_str))
                        t = opt.get("text", str(opt))
                        is_corr = str(k).upper() in correct_keys or opt.get("isCorrect", False)
                        options.append(ExtractedOption(key=str(k).upper(), text=str(t).strip(), is_correct=is_corr))
                    else:
                        is_corr = key_str in correct_keys
                        options.append(ExtractedOption(key=key_str, text=str(opt).strip(), is_correct=is_corr))

            if len(options) < 2:
                continue

            explanation = item.get("explanation") or ""
            is_multi = item.get("isMultiAnswer", len(correct_keys) > 1)
            q_type = QuestionType.MULTIPLE_RESPONSE.value if is_multi else QuestionType.SINGLE_CHOICE.value

            items.append({
                "stem": stem.strip(),
                "options": options,
                "explanation": str(explanation).strip(),
                "question_type": q_type,
                "task_statement": item.get("taskStatement"),
                "last_verified": item.get("lastVerified") or item.get("date"),
                "services": item.get("services") or [],
                "source_url": source_url,
                "extraction_strategy": "JSON_DATASET_BANK",
            })

        return items
