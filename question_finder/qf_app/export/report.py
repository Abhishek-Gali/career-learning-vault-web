"""Research Run HTML & JSON report generation."""

import json
from datetime import datetime, timezone
from pathlib import Path
from qf_app.core.paths import EXPORTS_DIR
from qf_app.pipeline.orchestrator import PipelineStats


class ResearchReportGenerator:
    """Generates research run audit reports in JSON and HTML."""

    def __init__(self, export_dir: Path = EXPORTS_DIR) -> None:
        self.export_dir = export_dir
        self.export_dir.mkdir(parents=True, exist_ok=True)

    def generate_reports(self, stats: PipelineStats) -> tuple[Path, Path]:
        """Generate research_report.json and research_report.html."""
        json_path = self.export_dir / "research_report.json"
        html_path = self.export_dir / "research_report.html"

        # 1. JSON Report
        json_path.write_text(stats.model_dump_json(indent=2), encoding="utf-8")

        # 2. HTML Report
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>CLF-C02 Research Report — Run #{stats.run_id}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 40px; background: #f8fafc; color: #1e293b; }}
        .card {{ background: white; padding: 24px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 24px; }}
        h1 {{ margin-top: 0; color: #0f172a; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-top: 16px; }}
        .stat-box {{ background: #f1f5f9; padding: 16px; border-radius: 6px; border-left: 4px solid #3b82f6; }}
        .stat-val {{ font-size: 28px; font-weight: bold; color: #0f172a; }}
        .stat-lbl {{ font-size: 13px; color: #64748b; text-transform: uppercase; margin-top: 4px; }}
    </style>
</head>
<body>
    <div class="card">
        <h1>AWS CLF-C02 Research Execution Report</h1>
        <p><b>Run ID:</b> #{stats.run_id} | <b>Generated:</b> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
        <p><b>Research Window:</b> {stats.window_start} &rarr; {stats.window_end} (6 Calendar Months)</p>
    </div>

    <div class="card">
        <h2>Dataset Yield & Status Summary</h2>
        <div class="grid">
            <div class="stat-box" style="border-color: #10b981;">
                <div class="stat-val">{stats.recent_source_questions}</div>
                <div class="stat-lbl">Recent Public Source Questions</div>
            </div>
            <div class="stat-box" style="border-color: #6366f1;">
                <div class="stat-val">{stats.questions_generated}</div>
                <div class="stat-lbl">Generated Practice Questions</div>
            </div>
            <div class="stat-box" style="border-color: #0ea5e9;">
                <div class="stat-val">{stats.total_study_questions}</div>
                <div class="stat-lbl">Total Study Pool</div>
            </div>
            <div class="stat-box" style="border-color: #f59e0b;">
                <div class="stat-val">{stats.duplicates_found}</div>
                <div class="stat-lbl">Duplicates Clustered</div>
            </div>
        </div>
    </div>

    <div class="card">
        <h2>Ingestion Pipeline Metrics</h2>
        <div class="grid">
            <div class="stat-box"><div class="stat-val">{stats.queries_generated}</div><div class="stat-lbl">Queries Executed</div></div>
            <div class="stat-box"><div class="stat-val">{stats.candidates_discovered}</div><div class="stat-lbl">URLs Discovered</div></div>
            <div class="stat-box"><div class="stat-val">{stats.pages_fetched}</div><div class="stat-lbl">Pages Fetched</div></div>
            <div class="stat-box"><div class="stat-val">{stats.questions_extracted}</div><div class="stat-lbl">Candidate Questions</div></div>
            <div class="stat-box"><div class="stat-val">{stats.questions_verified}</div><div class="stat-lbl">Answers Verified</div></div>
            <div class="stat-box"><div class="stat-val">{stats.questions_quarantined}</div><div class="stat-lbl">Quarantined</div></div>
        </div>
    </div>
</body>
</html>
"""
        html_path.write_text(html_content, encoding="utf-8")
        return json_path, html_path
