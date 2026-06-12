from tests.agents.skills.renovation_seo_geo_import import load_qa
from tests.phase17_helpers import seed_qa_workspace


qa = load_qa()


def test_concept_image_label_required_is_reported_as_owner_input(tmp_path):
    seed_qa_workspace(
        tmp_path,
        draft_body="中文页面建议文案\n英文页面建议文案\nCTA: 获取免费报价\n`/zh/quote` `/en/quote`\n",
    )

    result = qa.run_qa(tmp_path)

    assert result.ok
    assert any(issue.check == "concept/rendering clearly labeled" and issue.severity == "owner_input" for issue in result.issues)
