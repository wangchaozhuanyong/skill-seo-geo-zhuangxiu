from tests.agents.skills.renovation_seo_geo_import import load_qa, load_schema_validator
from tests.phase17_helpers import seed_qa_workspace


qa = load_qa()
schema_validator = load_schema_validator()


def test_fake_reviews_blocked_in_content_and_schema(tmp_path):
    seed_qa_workspace(tmp_path, draft_extra="\n客户评价: five-star renovation service.\n")

    qa_result = qa.run_qa(tmp_path)
    schema_result = schema_validator.validate_schemas(
        tmp_path,
        [{"@context": "https://schema.org", "@type": "Review", "reviewBody": "Fake review"}],
    )

    assert not qa_result.ok
    assert any(issue.check == "no fake reviews" for issue in qa_result.issues)
    assert not schema_result.ok
