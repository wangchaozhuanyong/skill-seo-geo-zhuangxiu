import json
from datetime import date
from pathlib import Path
from types import SimpleNamespace

from tests.agents.skills.renovation_seo_geo_import import load_daily_automation


daily_automation = load_daily_automation()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def seed_workspace(tmp_path: Path) -> None:
    write(
        tmp_path / "seo-workspace" / "data" / "brand-profile.md",
        "- Brand name: FLASH CAST\n- Company name: FLASH CAST SDN. BHD.\n- Website: https://flashcast.com.my/\n",
    )
    write(
        tmp_path / "seo-workspace" / "data" / "keyword-map.csv",
        "keyword,search_intent,customer_stage,target_url,current_url,page_type,priority,service,location,notes\n"
        "kitchen renovation malaysia,commercial,ready,/en/services/kitchen,/en/services/kitchen,service,high,Kitchen renovation,Kuala Lumpur,\n"
        "paint ideas,informational,learn,/en/blog/paint,/en/blog/paint,article,low,Paint,,\n",
    )
    write(
        tmp_path / "seo-workspace" / "data" / "url-inventory.csv",
        "url,language,page_type,status_code,indexable,robots_allowed,meta_robots,canonical_url,canonical_self,hreflang_pair,title,meta_description,h1,word_count,internal_inlinks_count,internal_outlinks_count,schema_types,image_count,missing_alt_count,lastmod,sitemap_included,priority_issue\n"
        "https://flashcast.com.my/en/services/kitchen,en,service,200,yes,yes,,https://flashcast.com.my/en/services/kitchen,yes,yes,Kitchen Renovation,Kitchen renovation,Kitchen Renovation,500,1,1,WebPage,1,0,,yes,\n"
        "https://flashcast.com.my/zh/services/kitchen,zh,service,200,yes,yes,,https://flashcast.com.my/zh/services/kitchen,yes,yes,厨房装修,厨房装修,厨房装修,500,1,1,WebPage,1,0,,yes,\n"
        "https://flashcast.com.my/en/blog/paint,en,article,200,yes,yes,,https://flashcast.com.my/en/blog/paint,yes,yes,Paint Ideas,Paint ideas,Paint Ideas,500,1,1,WebPage,0,0,,yes,\n",
    )
    write(tmp_path / "seo-workspace" / "data" / "internal-links.csv", "source_url,target_url,anchor_text,context,priority\n")
    write(tmp_path / "seo-workspace" / "data" / "case-studies.csv", "project_name,service,related_url,location,scope,result\n")
    write(
        tmp_path / "seo-workspace" / "data" / "service-areas.csv",
        "area,country,state_or_region,city,neighborhoods,services_available,existing_url,local_project_examples,notes,verified\n"
        "Kuala Lumpur,Malaysia,Kuala Lumpur,Kuala Lumpur,,Kitchen renovation,/en/locations/kuala-lumpur,,,yes\n",
    )
    write(tmp_path / "seo-workspace" / "data" / "gsc-pages.csv", "page,clicks,impressions,ctr,position\n")
    write(tmp_path / "seo-workspace" / "data" / "gsc-queries.csv", "query,clicks,impressions,ctr,position\n")
    write(tmp_path / "seo-workspace" / "data" / "google-index-status.csv", "url,inspection_state,verdict,coverage_state\n")
    write(
        tmp_path / "seo-workspace" / "data" / "service-content-patterns.json",
        json.dumps(
            {
                "version": "test",
                "services": {
                    "kitchen": {
                        "urls": {
                            "en": "https://flashcast.com.my/en/services/kitchen",
                            "zh": "https://flashcast.com.my/zh/services/kitchen",
                        },
                        "keywords": {"en": "kitchen renovation malaysia", "zh": "厨房装修 吉隆坡"},
                        "service_name": {"en": "Kitchen Renovation", "zh": "厨房装修"},
                        "h1": {"en": "Kitchen Renovation Planning", "zh": "厨房装修规划"},
                        "positioning": {"en": "Plan kitchen layout and materials.", "zh": "规划厨房动线和材料。"},
                        "needs": {"en": ["layout", "storage"], "zh": ["动线", "收纳"]},
                        "sections": {"en": ["Layout planning"], "zh": ["动线规划"]},
                        "faq": {"en": ["Can renderings be used?|Yes, as concepts."], "zh": ["可以用效果图吗？|可以。"]},
                        "image_concepts": {"en": ["kitchen layout concept"], "zh": ["厨房动线效果图方案"]},
                        "cta": {"en": "Share kitchen photos.", "zh": "提交厨房照片。"},
                        "schema": ["Service", "FAQPage", "ImageObject"],
                        "owner_input_required": ["final CTA/contact display"],
                    }
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
    )


def test_daily_automation_brief_pipeline_writes_safe_report(tmp_path):
    seed_workspace(tmp_path)

    result, artifacts = daily_automation.run_daily_automation(tmp_path)

    assert result.ok
    assert result.status == "daily_brief_waiting_owner_review"
    assert result.selected_task["target_url"] == "https://flashcast.com.my/en/services/kitchen"
    assert [step.name for step in result.steps] == ["opportunity_finder", "content_brief"]
    run_json, report_path = artifacts
    payload = json.loads(run_json.read_text(encoding="utf-8"))
    assert payload["no_live_actions_executed"] is True
    assert "未登录 CMS" in report_path.read_text(encoding="utf-8")
    assert (tmp_path / "seo-workspace" / "drafts" / f"{date.today().isoformat()}-kitchen-content-brief.md").exists()


def test_daily_automation_uses_content_calendar_when_present(tmp_path):
    seed_workspace(tmp_path)
    write(
        tmp_path / "seo-workspace" / "data" / "daily-content-calendar.json",
        json.dumps(
            {
                "status": "content_calendar_ready_for_owner_review",
                "calendar": [
                    {
                        "date": date.today().isoformat(),
                        "target_url": "https://flashcast.com.my/en/blog/paint",
                        "paired_url": "https://flashcast.com.my/zh/blog/paint",
                        "calendar_score": "12",
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )

    result, _ = daily_automation.run_daily_automation(tmp_path)

    assert result.ok
    assert result.selected_task["target_url"] == "https://flashcast.com.my/en/blog/paint"
    assert result.selected_task["selection_source"] == "content-calendar"
    assert result.selected_task["calendar_target_url"] == "https://flashcast.com.my/en/blog/paint"
    assert any(step.name == "content_calendar" and step.status == "selected" for step in result.steps)
    assert (tmp_path / "seo-workspace" / "drafts" / f"{date.today().isoformat()}-paint-content-brief.md").exists()


def test_select_score_prefers_exact_explicit_target_before_pair_match():
    zh_score = daily_automation.OpportunityScore(
        url="https://flashcast.com.my/zh/services/kitchen",
        keyword="厨房装修",
        language="zh",
        total_score=50,
    )
    en_score = daily_automation.OpportunityScore(
        url="https://flashcast.com.my/en/services/kitchen",
        keyword="kitchen renovation",
        language="en",
        total_score=40,
    )

    selected = daily_automation.select_score([zh_score, en_score], "https://flashcast.com.my/en/services/kitchen")

    assert selected is en_score


def test_daily_automation_publish_prep_runs_handoff_without_publish(tmp_path):
    seed_workspace(tmp_path)

    result, artifacts = daily_automation.run_daily_automation(
        tmp_path,
        pipeline="publish-prep",
        research_fetch_remote=False,
    )

    assert result.ok
    assert result.status == "publish_prep_blocked_before_owner_authorization"
    assert any(step.name == "research_search" for step in result.steps)
    assert any(step.name == "research_search_intake" and step.status == "skipped" for step in result.steps)
    assert any(step.name == "research_discovery" for step in result.steps)
    assert any(step.name == "research_intake" and step.status == "skipped" for step in result.steps)
    assert any(step.name == "rich_editor" for step in result.steps)
    assert any(step.name == "rich_editor_apply" for step in result.steps)
    assert any(step.name == "service_pattern_package" for step in result.steps)
    assert any(step.name == "scheduled_publish_authorization" for step in result.steps)
    assert any(step.name == "website_publish_adapter" for step in result.steps)
    assert any(step.name == "publish_readiness" for step in result.steps)
    assert any(step.name == "publish_bundle" for step in result.steps)
    assert any(step.name == "publish_approved_executor" for step in result.steps)
    assert any(step.name == "publish_implementation_package" for step in result.steps)
    assert any(step.name == "publish_operator_package" for step in result.steps)
    assert result.handoff_blockers
    assert any("Owner has not approved" in blocker for blocker in result.handoff_blockers)
    assert any("Scheduled publish authorization is not ready" in blocker for blocker in result.handoff_blockers)
    assert any("Website publish adapter is not ready" in blocker for blocker in result.handoff_blockers)
    assert any("Approved executor simulation is not ready" in blocker for blocker in result.handoff_blockers)
    assert any("Implementation package is not ready" in blocker for blocker in result.handoff_blockers)
    assert any("Operator command package is not ready" in blocker for blocker in result.handoff_blockers)
    run_json, _ = artifacts
    payload = json.loads(run_json.read_text(encoding="utf-8"))
    assert payload["no_live_actions_executed"] is True
    assert any(step["name"] == "research_search" for step in payload["steps"])
    assert any(step["name"] == "research_search_intake" and step["status"] == "skipped" for step in payload["steps"])
    assert any(step["name"] == "research_discovery" for step in payload["steps"])
    assert any(step["name"] == "research_intake" and step["status"] == "skipped" for step in payload["steps"])
    assert any(step["name"] == "rich_editor" for step in payload["steps"])
    assert any(step["name"] == "rich_editor_apply" for step in payload["steps"])
    assert any(step["name"] == "service_pattern_package" for step in payload["steps"])
    assert any(step["name"] == "scheduled_publish_authorization" for step in payload["steps"])
    assert any(step["name"] == "website_publish_adapter" for step in payload["steps"])
    assert any(step["name"] == "publish_bundle" for step in payload["steps"])
    assert any(step["name"] == "publish_approved_executor" for step in payload["steps"])
    assert any(step["name"] == "publish_implementation_package" for step in payload["steps"])
    assert any(step["name"] == "publish_operator_package" for step in payload["steps"])
    discovery_path = tmp_path / "seo-workspace" / "data" / "research-discovery-candidates.json"
    discovery_payload = json.loads(discovery_path.read_text(encoding="utf-8"))
    assert discovery_payload["no_source_log_write"] is True
    assert discovery_payload["no_live_actions_executed"] is True
    assert (tmp_path / "seo-workspace" / "data" / "rich-content-cms-payload.editor-applied.json").exists()
    assert (tmp_path / "seo-workspace" / "data" / "kitchen-service-pattern-content-package-summary.json").exists()
    assert (tmp_path / "seo-workspace" / "data" / "scheduled-publish-authorization.json").exists()
    assert (tmp_path / "seo-workspace" / "data" / "website-publish-adapter.json").exists()
    assert (tmp_path / "seo-workspace" / "data" / "publish-readiness.json").exists()
    assert (tmp_path / "seo-workspace" / "data" / "publish-execution-bundle.json").exists()
    assert (tmp_path / "seo-workspace" / "data" / "publish-approved-execution-record.json").exists()
    assert (tmp_path / "seo-workspace" / "data" / "publish-implementation-package.json").exists()
    assert (tmp_path / "seo-workspace" / "data" / "publish-admin-helper-call.json").exists()
    assert (tmp_path / "seo-workspace" / "data" / "publish-operator-command.json").exists()
    assert (tmp_path / "seo-workspace" / "data" / "media-upload-execution-request.json").exists()


def test_daily_automation_passes_research_search_provider(monkeypatch, tmp_path):
    seed_workspace(tmp_path)
    seen: dict[str, str] = {}

    def fake_research_search(root, **kwargs):
        seen["provider"] = kwargs.get("provider", "")
        seen["feeds_config"] = kwargs.get("feeds_config", "")
        return (
            SimpleNamespace(
                status="research_search_queries_ready",
                candidates=[],
                blockers=[],
                warnings=[],
                ok=True,
            ),
            (
                tmp_path / "seo-workspace" / "data" / "research-search-candidates.csv",
                tmp_path / "seo-workspace" / "data" / "research-search-candidates.json",
                tmp_path / "seo-workspace" / "reports" / "research-search-report.md",
                tmp_path / "seo-workspace" / "drafts" / "research-search-handoff.md",
            ),
        )

    monkeypatch.setattr(daily_automation, "run_research_search", fake_research_search)

    result, _ = daily_automation.run_daily_automation(
        tmp_path,
        pipeline="rich-content",
        research_fetch_remote=False,
        research_search_provider="trusted-rss",
        research_search_feeds_config="seo-workspace/config/research-search-feeds.example.yml",
    )

    assert result.ok
    assert seen["provider"] == "trusted-rss"
    assert seen["feeds_config"] == "seo-workspace/config/research-search-feeds.example.yml"
