import json
from unittest.mock import patch

from src.resume_parser import ResumeParser, hiring_decision


def test_matching_saas_candidate_moves_to_interview():
    profile = {"skills": ["Python", "SaaS", "SQL"], "years_experience": 5}
    assert hiring_decision(profile) == "interview"


def test_incomplete_profile_stays_in_review():
    assert hiring_decision({"skills": ["Python"], "years_experience": 5}) == "review"


def test_live_parse_shape_supplies_hiring_inputs():
    class Response:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def read(self):
            return json.dumps({"ok": True, "data": {
                "pdf_id": "pdf_example",
                "metadata": {},
                "text_per_page": ["Jane Doe | Python SaaS engineer | 5 years experience"],
            }}).encode()

    with patch("src.resume_parser.request.urlopen", return_value=Response()):
        profile = ResumeParser(api_key="test").parse_pdf(b"pdf")

    assert profile["pdf_id"] == "pdf_example"
    assert hiring_decision(profile) == "interview"
