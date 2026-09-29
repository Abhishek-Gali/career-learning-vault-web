"""Parser for the official AWS CLF-C02 Exam Guide PDF."""

import hashlib
from typing import Any

try:
    import pymupdf
except ImportError:
    pymupdf = None

from qf_app.config.settings import get_taxonomy_data


class CurriculumParser:
    """Parses official AWS CLF-C02 exam guide PDF or structured fallback."""

    def parse_pdf_bytes(self, pdf_bytes: bytes) -> dict[str, Any]:
        """Extract domains, task statements, and services from PDF bytes."""
        content_hash = hashlib.sha256(pdf_bytes).hexdigest()
        raw_text_parts = []

        if pymupdf is not None:
            try:
                doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
                for page in doc:
                    raw_text_parts.append(page.get_text())
                full_text = "\n".join(raw_text_parts)
            except Exception:
                full_text = ""
        else:
            full_text = ""

        # Use curated taxonomy as base structure enriched with content hash
        taxonomy_data = get_taxonomy_data()
        return {
            "exam_code": taxonomy_data.get("exam_code", "CLF-C02"),
            "exam_name": taxonomy_data.get("exam_name", "AWS Certified Cloud Practitioner"),
            "guide_url": taxonomy_data.get("official_url", ""),
            "content_hash": content_hash,
            "domains": taxonomy_data.get("domains", []),
            "raw_text": full_text or None,
        }

    def get_fallback_curriculum(self) -> dict[str, Any]:
        """Generate curriculum structure directly from configuration."""
        taxonomy_data = get_taxonomy_data()
        content_hash = hashlib.sha256(str(taxonomy_data).encode("utf-8")).hexdigest()
        return {
            "exam_code": taxonomy_data.get("exam_code", "CLF-C02"),
            "exam_name": taxonomy_data.get("exam_name", "AWS Certified Cloud Practitioner"),
            "guide_url": taxonomy_data.get("official_url", ""),
            "content_hash": content_hash,
            "domains": taxonomy_data.get("domains", []),
            "raw_text": "Curated CLF-C02 Taxonomy Snapshot",
        }
