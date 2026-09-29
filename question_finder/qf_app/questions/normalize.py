"""Text cleaning, option normalization, and hash computation."""

import hashlib
import html
import re
import unicodedata

from qf_app.extraction.html import ExtractedOption, ExtractedQuestion
from qf_app.questions.types import NormalizedOption, NormalizedQuestion


def normalize_text(text: str) -> str:
    """Normalize text: unescape HTML entities, normalize whitespace, and NFC unicode."""
    if not text:
        return ""
    unescaped = html.unescape(text)
    nfc = unicodedata.normalize("NFC", unescaped)
    cleaned = re.sub(r"\s+", " ", nfc).strip()
    return cleaned


def compute_stem_hash(stem: str) -> str:
    """Compute SHA-256 hash of normalized lowercased question stem."""
    normalized = normalize_text(stem).lower()
    # Strip non-alphanumeric for resilient hash
    alpha_only = re.sub(r"[^\w\s]", "", normalized)
    return hashlib.sha256(alpha_only.encode("utf-8")).hexdigest()


def compute_exact_hash(stem: str, options: list[NormalizedOption]) -> str:
    """Compute exact SHA-256 hash of stem + sorted option texts + correct flags."""
    stem_norm = normalize_text(stem).lower()
    opts_sorted = sorted(options, key=lambda o: normalize_text(o.text).lower())
    opts_repr = "|".join([f"{normalize_text(o.text).lower()}:{o.is_correct}" for o in opts_sorted])
    payload = f"{stem_norm}::{opts_repr}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def compute_content_hash(stem: str, options: list[NormalizedOption]) -> str:
    """Compute content SHA-256 hash of stem + sorted option texts (independent of answers)."""
    stem_norm = normalize_text(stem).lower()
    opts_sorted = sorted(options, key=lambda o: normalize_text(o.text).lower())
    opts_repr = "|".join([normalize_text(o.text).lower() for o in opts_sorted])
    payload = f"{stem_norm}::{opts_repr}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class QuestionNormalizer:
    """Normalizes raw extracted question objects into clean canonical representations."""

    def normalize(self, extracted: ExtractedQuestion) -> NormalizedQuestion:
        """Clean stems, options, and compute hashes."""
        clean_stem = normalize_text(extracted.stem)
        clean_explanation = normalize_text(extracted.explanation)

        normalized_options: list[NormalizedOption] = []
        for idx, opt in enumerate(extracted.options):
            clean_opt_text = normalize_text(opt.text)
            key = chr(65 + idx)
            normalized_options.append(
                NormalizedOption(
                    key=key,
                    text=clean_opt_text,
                    is_correct=opt.is_correct,
                    original_position=idx,
                    normalized_position=idx,
                )
            )

        exact_h = compute_exact_hash(clean_stem, normalized_options)
        stem_h = compute_stem_hash(clean_stem)
        content_h = compute_content_hash(clean_stem, normalized_options)

        return NormalizedQuestion(
            stem=clean_stem,
            options=normalized_options,
            explanation=clean_explanation,
            question_type=extracted.question_type,
            exact_hash=exact_h,
            stem_hash=stem_h,
            content_hash=content_h,
            extraction_method=extracted.extraction_strategy,
        )
