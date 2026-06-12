import json
from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import load_content_studio_approval_packet


approval_packet = load_content_studio_approval_packet()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def seed_packet_inputs(tmp_path: Path) -> None:
    write_json(
        tmp_path / "seo-workspace" / "data" / "content-studio-publish-prep.json",
        {
            "status": "publish_prep_ready_for_owner_review",
            "target_url": "https://flashcast.com.my/en/services/kitchen",
            "paired_url": "https://flashcast.com.my/zh/services/kitchen",
            "blocker_summary": [
                "Owner approval flag missing (--owner-approved).",
                "Explicit execution flag missing (--explicit-execution).",
                "QA passed flag missing (--qa-passed).",
                "Missing media-url-map.json. Upload/select media and provide confirmed public URLs first.",
                "Storage readiness is not confirmed (--storage-ready missing).",
                "Missing publish-execution-receipt.json after operator package ready.",
            ],
        },
    )
    write_json(
        tmp_path / "seo-workspace" / "data" / "content-studio-publish-candidate.json",
        {
            "status": "content_studio_publish_candidate_waiting_owner_review",
            "target_url": "https://flashcast.com.my/en/services/kitchen",
            "paired_url": "https://flashcast.com.my/zh/services/kitchen",
        },
    )
    write_json(
        tmp_path / "seo-workspace" / "data" / "media-upload-plan.json",
        {
            "status": "owner_review_required",
            "queue": [
                {
                    "queue_id": "media-upload-001",
                    "placeholder_filename": "flash-cast-hero-rendering-concept.webp",
                    "expected_object_path": "media/seo-generated/2026-06-11/flash-cast-hero-rendering-concept.svg",
                    "asset_kind": "generated_design_rendering_concept",
                    "claim_boundary": "Generated visual for design/rendering concept only.",
                }
            ],
        },
    )


def test_approval_packet_summarizes_owner_actions(tmp_path):
    seed_packet_inputs(tmp_path)

    packet, artifacts = approval_packet.run_content_studio_approval_packet(tmp_path)

    assert packet["status"] == "approval_packet_waiting_owner_review"
    assert packet["target_url"] == "https://flashcast.com.my/en/services/kitchen"
    assert packet["no_publish_executed"] is True
    categories = {item["category"] for item in packet["action_items"]}
    assert {"owner_approval", "execution_instruction", "qa", "media", "storage", "receipt"} <= categories
    media_action = next(item for item in packet["action_items"] if item["category"] == "media")
    assert media_action["media_items"][0]["placeholder_filename"] == "flash-cast-hero-rendering-concept.webp"
    assert any(command["step"] == "media_after_urls" for command in packet["recommended_commands"])
    decision_path = tmp_path / "seo-workspace" / "data" / "content-studio-owner-decision.template.json"
    decision = json.loads(decision_path.read_text(encoding="utf-8"))
    assert decision["approval_is_not_execution"] is True
    assert decision["decision"]["explicit_execution_requested"] is False
    assert decision["decision"]["allowed_execution_scope"] == "owner_review_only"
    assert "operator_ready_handoff_only" in decision["decision"]["allowed_execution_scope_options"]
    assert all(path.exists() for path in artifacts)


def test_approval_packet_blocks_when_inputs_missing(tmp_path):
    packet, _ = approval_packet.run_content_studio_approval_packet(tmp_path)

    assert packet["status"] == "approval_packet_blocked_missing_inputs"
    assert any("content-studio-publish-prep.json" in blocker for blocker in packet["blockers"])


def test_approval_packet_preserves_existing_owner_decision_for_same_page(tmp_path):
    seed_packet_inputs(tmp_path)
    approval_packet.run_content_studio_approval_packet(tmp_path)
    decision_path = tmp_path / "seo-workspace" / "data" / "content-studio-owner-decision.template.json"
    decision = json.loads(decision_path.read_text(encoding="utf-8"))
    decision["decision"].update(
        {
            "content_approved": True,
            "media_urls_confirmed": True,
            "qa_approved": True,
            "latest_research_verified": True,
            "explicit_execution_requested": True,
            "allowed_execution_scope": "approved_dry_run_only",
            "owner_notes": "Approved for dry-run only.",
        }
    )
    write_json(decision_path, decision)

    approval_packet.run_content_studio_approval_packet(tmp_path)
    refreshed = json.loads(decision_path.read_text(encoding="utf-8"))

    assert refreshed["decision_preserved_from_previous_template"] is True
    assert refreshed["decision"]["content_approved"] is True
    assert refreshed["decision"]["media_urls_confirmed"] is True
    assert refreshed["decision"]["qa_approved"] is True
    assert refreshed["decision"]["latest_research_verified"] is True
    assert refreshed["decision"]["explicit_execution_requested"] is True
    assert refreshed["decision"]["allowed_execution_scope"] == "approved_dry_run_only"
    assert refreshed["decision"]["owner_notes"] == "Approved for dry-run only."
    assert refreshed["action_items_snapshot"]


def test_approval_packet_resets_owner_decision_when_target_changes(tmp_path):
    seed_packet_inputs(tmp_path)
    approval_packet.run_content_studio_approval_packet(tmp_path)
    decision_path = tmp_path / "seo-workspace" / "data" / "content-studio-owner-decision.template.json"
    decision = json.loads(decision_path.read_text(encoding="utf-8"))
    decision["decision"]["content_approved"] = True
    decision["decision"]["allowed_execution_scope"] = "approved_dry_run_only"
    write_json(decision_path, decision)

    prep_path = tmp_path / "seo-workspace" / "data" / "content-studio-publish-prep.json"
    prep = json.loads(prep_path.read_text(encoding="utf-8"))
    prep["target_url"] = "https://flashcast.com.my/en/services/bathroom"
    prep["paired_url"] = "https://flashcast.com.my/zh/services/bathroom"
    write_json(prep_path, prep)

    approval_packet.run_content_studio_approval_packet(tmp_path)
    refreshed = json.loads(decision_path.read_text(encoding="utf-8"))

    assert refreshed["decision_preserved_from_previous_template"] is False
    assert refreshed["target_url"] == "https://flashcast.com.my/en/services/bathroom"
    assert refreshed["decision"]["content_approved"] is False
    assert refreshed["decision"]["allowed_execution_scope"] == "owner_review_only"
