from tests.agents.skills.renovation_seo_geo_import import load_qa
from tests.phase17_helpers import seed_qa_workspace


qa = load_qa()


def test_unsupported_location_blocks_publish(tmp_path):
    seed_qa_workspace(tmp_path, keyword_location="Unverified City")

    result = qa.run_qa(tmp_path)

    assert not result.ok
    assert any(issue.check == "no unsupported service area" for issue in result.issues)
