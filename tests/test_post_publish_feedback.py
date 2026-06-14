import json
from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import load_post_publish_feedback


post_publish_feedback = load_post_publish_feedback()


TARGET_URL = "https://example.com/en/services/kitchen"
PAIRED_URL = "https://example.com/zh/services/kitchen"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def seed_ready_workspace(root: Path) -> None:
    write_json(
        root / "seo-workspace" / "data" / "publish-execution-receipt.json",
        {
            "receipt": {
                "status": "publish_execution_receipt_verified",
                "receipt_verified_for_post_publish_qa": True,
                "target_url": TARGET_URL,
                "paired_url": PAIRED_URL,
            }
        },
    )
    write(
        root / "seo-workspace" / "data" / "gsc-pages.csv",
        "page,clicks,impressions,ctr,position\n"
        f"{TARGET_URL},3,100,0.03,8.2\n"
        f"{PAIRED_URL},1,40,0.025,12.0\n",
    )
    write(
        root / "seo-workspace" / "data" / "google-index-status.csv",
        "url,inspection_state,verdict,coverage_state\n"
        f"{TARGET_URL},checked,PASS,Indexed\n",
    )
    write(
        root / "seo-workspace" / "data" / "lead-quality-log.csv",
        "date,source,campaign,ad_group,keyword,search_term,landing_page,contact_channel,service_type,service_area,lead_quality,quoted,won,revenue_myr,cost_myr,owner_notes,decision_label\n"
        f"2026-06-14,Organic,,,,,{TARGET_URL},WhatsApp,Kitchen,Kuala Lumpur,high,yes,no,,,owner confirmed,\n",
    )


def test_post_publish_feedback_creates_ready_watchlist_from_receipt_and_data(tmp_path):
    seed_ready_workspace(tmp_path)

    summary, artifacts = post_publish_feedback.run_post_publish_feedback(tmp_path)

    assert summary["status"] == "watch_ready"
    assert summary["target_url"] == TARGET_URL
    assert summary["receipt_verified"] is True
    assert summary["watchlist_count"] == 2
    assert summary["opportunity_feedback_count"] == 2
    assert all(path.exists() for path in artifacts)
    feedback = json.loads((tmp_path / "seo-workspace" / "data" / "post-publish-feedback.json").read_text(encoding="utf-8"))
    assert feedback["opportunity_feedback"][0]["score_delta"]
    assert "post-publish high-quality lead signal" in feedback["opportunity_feedback"][0]["feedback_events"]
    report = artifacts[-1].read_text(encoding="utf-8")
    assert "7_day_index_and_quality_check" in report
    assert "30_day_performance_and_lead_quality_review" in report


def test_post_publish_feedback_marks_missing_private_data_without_inference(tmp_path):
    write(
        tmp_path / "seo-workspace" / "data" / "seo-opportunity-scores.csv",
        "url,keyword,language,page_type,service,location,total_score,task_type,positive_events,penalty_events\n"
        f"{TARGET_URL},kitchen renovation,en,service,kitchen,Kuala Lumpur,30,service,,\n",
    )

    summary, _artifacts = post_publish_feedback.run_post_publish_feedback(tmp_path)

    assert summary["status"] == "watch_waiting_for_data"
    assert summary["opportunity_feedback_count"] == 2
    assert "GSC page/query export or API access" in summary["owner_input_needed"]
    assert "owner-confirmed WhatsApp/phone/form lead quality" in summary["owner_input_needed"]
