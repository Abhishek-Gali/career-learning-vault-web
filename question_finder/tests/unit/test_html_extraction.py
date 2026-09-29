"""Unit tests for HTML question extraction."""

from qf_app.extraction.html import HtmlQuestionExtractor


def test_html_question_extraction(load_fixture):
    html = load_fixture("valid_recent_source.html")
    extractor = HtmlQuestionExtractor()
    questions = extractor.extract_questions(html)

    assert len(questions) == 2

    q1 = questions[0]
    assert "object storage" in q1.stem.lower()
    assert len(q1.options) == 4
    # Option B should be Amazon S3 and marked correct
    correct_opts = [o for o in q1.options if o.is_correct]
    assert len(correct_opts) == 1
    assert "amazon s3" in correct_opts[0].text.lower()
