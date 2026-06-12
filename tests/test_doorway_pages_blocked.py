from tests.agents.skills.renovation_seo_geo_import import load_qa
from tests.phase17_helpers import seed_qa_workspace


qa = load_qa()


def test_doorway_pages_blocked_for_thin_local_pages(tmp_path):
    seed_qa_workspace(tmp_path, target_overrides={"word_count": "40"})
    # Make the target a local page by rewriting the inventory URL metadata.
    path = tmp_path / "seo-workspace" / "data" / "url-inventory.csv"
    text = path.read_text(encoding="utf-8").replace(",zh,service,200,", ",zh,local,200,", 1)
    path.write_text(text, encoding="utf-8")

    result = qa.run_qa(tmp_path)

    assert not result.ok
    assert any("doorway" in issue.check for issue in result.issues)
