from tests.agents.skills.renovation_seo_geo_import import load_qa
from tests.phase17_helpers import seed_qa_workspace


qa = load_qa()


def test_wrong_canonical_blocks_publish(tmp_path):
    seed_qa_workspace(tmp_path, target_overrides={"canonical_self": "no"})

    result = qa.run_qa(tmp_path)

    assert not result.ok
    assert any(issue.check == "no wrong canonical" for issue in result.issues)
