"""Exporters for JSON, JSONL, CSV, Markdown, and HTML formats."""

import csv
import io
import json
from pathlib import Path
from qf_app.core.paths import EXPORTS_DIR
from qf_app.db.models.question import Question


def serialize_question_to_dict(q: Question) -> dict:
    """Transform Question model into schema-compliant dictionary."""
    opts = [{"id": o.option_key, "text": o.option_text} for o in q.options]
    correct_keys = [o.option_key for o in q.options if o.is_correct]

    return {
        "id": str(q.id),
        "uuid": q.uuid,
        "stem": q.stem,
        "question_type": q.question_type,
        "options": opts,
        "correct_option_ids": correct_keys,
        "explanation": q.explanation,
        "curriculum": {
            "domain": q.domain,
            "domain_name": q.domain_name,
            "task_statement": q.task_statement,
            "services": [s.service_name for s in q.services],
            "topics": [t.topic for t in q.topics],
        },
        "date": {
            "published_at": q.published_at.isoformat() if q.published_at else None,
            "updated_at": q.updated_at.isoformat() if q.updated_at else None,
            "retrieved_at": q.retrieved_at.isoformat() if q.retrieved_at else None,
            "confidence": q.date_confidence,
            "recentness_status": q.recentness_status,
        },
        "verification": {
            "status": q.answer_status,
            "confidence": q.answer_confidence,
        },
        "provenance": {
            "source_kind": q.source_kind,
            "source_url": q.sources[0].source_url if q.sources else None,
            "source_title": q.sources[0].source_title if q.sources else None,
            "extraction_method": q.sources[0].extraction_method if q.sources else None,
        },
        "is_generated": q.is_generated,
        "generation_method": q.generation_method,
        "quality_score": q.quality_score,
    }


class DatasetExporter:
    """Exports question collections into multiple file formats."""

    def __init__(self, export_dir: Path = EXPORTS_DIR) -> None:
        self.export_dir = export_dir
        self.export_dir.mkdir(parents=True, exist_ok=True)

    def export_json(self, questions: list[Question], filename: str = "questions.json") -> Path:
        """Export dataset as formatted JSON array."""
        out_path = self.export_dir / filename
        data = [serialize_question_to_dict(q) for q in questions]
        out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        return out_path

    def export_jsonl(self, questions: list[Question], filename: str = "questions.jsonl") -> Path:
        """Export dataset as newline-delimited JSON."""
        out_path = self.export_dir / filename
        lines = [json.dumps(serialize_question_to_dict(q), ensure_ascii=False) for q in questions]
        out_path.write_text("\n".join(lines), encoding="utf-8")
        return out_path

    def export_csv(self, questions: list[Question], filename: str = "questions.csv") -> Path:
        """Export dataset as tabular CSV."""
        out_path = self.export_dir / filename
        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow([
            "id", "domain", "task", "stem", "option_A", "option_B", "option_C", "option_D",
            "correct_answers", "explanation", "source_kind", "recency", "verification", "source_url"
        ])

        for q in questions:
            opts_map = {o.option_key: o.option_text for o in q.options}
            corrects = ", ".join([o.option_key for o in q.options if o.is_correct])
            src_url = q.sources[0].source_url if q.sources else ""

            writer.writerow([
                q.id,
                q.domain or "",
                q.task_statement or "",
                q.stem,
                opts_map.get("A", ""),
                opts_map.get("B", ""),
                opts_map.get("C", ""),
                opts_map.get("D", ""),
                corrects,
                q.explanation,
                q.source_kind,
                q.recentness_status,
                q.answer_status,
                src_url,
            ])

        out_path.write_text(output.getvalue(), encoding="utf-8")
        return out_path

    def export_markdown(self, questions: list[Question], filename: str = "study_guide.md") -> Path:
        """Export dataset as formatted Markdown study guide."""
        out_path = self.export_dir / filename
        doc = ["# AWS Certified Cloud Practitioner (CLF-C02) Practice Questions\n"]

        for idx, q in enumerate(questions, 1):
            doc.append(f"### Question {idx} ({q.source_kind})")
            doc.append(f"**Domain {q.domain or 3}** — {q.domain_name or 'Technology'}\n")
            doc.append(f"{q.stem}\n")

            for opt in q.options:
                doc.append(f"- **{opt.option_key})** {opt.option_text}")

            corrects = ", ".join([o.option_key for o in q.options if o.is_correct])
            doc.append(f"\n<details><summary><b>Reveal Answer</b></summary>\n")
            doc.append(f"**Correct Answer:** {corrects}\n")
            if q.explanation:
                doc.append(f"**Explanation:** {q.explanation}\n")
            doc.append(f"</details>\n\n---\n")

        out_path.write_text("\n".join(doc), encoding="utf-8")
        return out_path
