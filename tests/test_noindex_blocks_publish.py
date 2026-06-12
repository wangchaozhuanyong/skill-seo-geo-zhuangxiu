from tests.agents.skills.renovation_seo_geo_import import load_qa
from tests.phase17_helpers import seed_qa_workspace


qa = load_qa()


def test_noindex_blocks_publish():
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        seed_qa_workspace(root, target_overrides={"indexable": "no", "meta_robots": "noindex"})
        result = qa.run_qa(root)

    assert not result.ok
    assert any(issue.check == "no noindex on target page" for issue in result.issues)
