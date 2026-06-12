from tests.agents.skills.renovation_seo_geo_import import load_qa
from tests.phase17_helpers import seed_qa_workspace


qa = load_qa()


def test_keyword_stuffing_blocked_before_publish(tmp_path):
    repeated = "住宅装修 吉隆坡 " * 10
    seed_qa_workspace(tmp_path, draft_extra="\n" + repeated)

    result = qa.run_qa(tmp_path)

    assert not result.ok
    assert any(issue.check == "no keyword stuffing" for issue in result.issues)
