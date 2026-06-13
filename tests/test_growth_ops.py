from pathlib import Path

from tests.agents.skills.renovation_seo_geo_import import load_growth_ops


growth_ops = load_growth_ops()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def seed_workspace(root: Path) -> None:
    write(
        root / "seo-workspace" / "data" / "brand-profile.md",
        "\n".join(
            [
                "- Company name: FLASH CAST SDN. BHD.",
                "- Website: https://flashcast.com.my/",
                "- Google Business Profile: NEEDS OWNER INPUT",
            ]
        )
        + "\n",
    )
    write(
        root / "seo-workspace" / "data" / "services.md",
        "# Services\n\n### Kitchen Renovation\n\n- Existing URL: https://flashcast.com.my/en/services/kitchen\n- Chinese URL: https://flashcast.com.my/zh/services/kitchen\n",
    )
    write(
        root / "seo-workspace" / "data" / "seo-opportunity-scores.csv",
        "url,keyword,language,page_type,service,location,total_score,task_type,positive_events,penalty_events\n"
        "https://flashcast.com.my/en/services/kitchen,kitchen renovation malaysia,en,service,kitchen,Kuala Lumpur,88,service page optimization,,\n"
        "https://flashcast.com.my/zh/services/kitchen,厨房装修 吉隆坡,zh,service,kitchen,Kuala Lumpur,84,service page optimization,,\n",
    )
    write(
        root / "seo-workspace" / "data" / "gsc-pages.csv",
        "page,clicks,impressions,ctr,position\n"
        "https://flashcast.com.my/en/services/kitchen,12,1000,0.012,9.8\n",
    )
    write(
        root / "seo-workspace" / "data" / "gsc-queries.csv",
        "query,clicks,impressions,ctr,position\n"
        "kitchen renovation malaysia,9,700,0.0128,8.4\n",
    )
    write(
        root / "seo-workspace" / "data" / "case-studies.csv",
        "project_name,location,property_type,size,budget_range,timeline,service,year,client_goal,main_problem,scope,materials,challenge,solution,result,photos_available,testimonial,related_url,notes\n"
        "Kitchen concept,Kuala Lumpur,Condo,,,,Kitchen,2026,,,,,,,,,no,,https://flashcast.com.my/en/services/kitchen,concept only\n",
    )
    write(
        root / "seo-workspace" / "data" / "lead-quality-log.csv",
        "date,source,campaign,ad_group,keyword,search_term,landing_page,contact_channel,service_type,service_area,lead_quality,quoted,won,revenue_myr,cost_myr,owner_notes,decision_label\n"
        "2026-06-13,Google Ads,Search - Renovation Leads - KL Selangor,广告组 1,附近装修公司,附近装修公司,https://flashcast.com.my/zh/services/renovation,WhatsApp,住宅装修,Kuala Lumpur,high,yes,no,,3,owner confirmed good lead,\n"
        "2026-06-13,Google Ads,Search - Renovation Leads - KL Selangor,广告组 1,装修课程,装修课程,https://flashcast.com.my/zh/services/renovation,WhatsApp,课程,Kuala Lumpur,spam,no,no,,2,not a renovation customer,\n",
    )
    write(
        root / "seo-workspace" / "data" / "google-ads-search-terms.csv",
        "date,campaign,ad_group,keyword,match_type,search_term,clicks,impressions,cost_myr,conversions,status\n"
        "2026-06-13,Search - Renovation Leads - KL Selangor,广告组 1,附近装修公司,phrase,附近装修公司,2,40,3,1,eligible\n"
        "2026-06-13,Search - Renovation Leads - KL Selangor,广告组 1,装修课程,phrase,装修课程,2,30,2,0,eligible\n",
    )
    write(
        root / "seo-workspace" / "data" / "google-ads-keyword-performance.csv",
        "date,campaign,ad_group,keyword,match_type,clicks,impressions,cost_myr,conversions,avg_cpc_myr,status\n"
        "2026-06-13,Search - Renovation Leads - KL Selangor,广告组 1,装修公司,broad,8,200,18,0,2.25,eligible\n",
    )


def test_growth_ops_reports_are_local_and_complete(tmp_path: Path):
    seed_workspace(tmp_path)

    commands = [
        growth_ops.run_daily_performance_digest,
        growth_ops.run_data_health_center,
        growth_ops.run_lead_quality_tracker,
        growth_ops.run_ads_decision_review,
        growth_ops.run_ai_search_monitor,
        growth_ops.run_local_citation_tracker,
        growth_ops.run_local_seo_verification,
        growth_ops.run_real_proof_asset_request,
        growth_ops.run_weekly_growth_control,
    ]
    for command in commands:
        summary, artifacts = command(tmp_path)
        assert summary["status"].endswith("_ready")
        assert artifacts
        assert all(path.exists() for path in artifacts)

    competitor_summary, competitor_artifacts = growth_ops.run_competitor_gap_audit(tmp_path)
    assert competitor_summary["status"] == "competitor_gap_audit_ready"
    assert all(path.exists() for path in competitor_artifacts)
    competitor_report = Path(competitor_summary["report"]).read_text(encoding="utf-8")
    assert "NEEDS OWNER INPUT" in competitor_report

    weekly_summary, weekly_artifacts = growth_ops.run_competitor_weekly_monitor(tmp_path)
    assert weekly_summary["status"] == "competitor_weekly_monitor_ready"
    assert all(path.exists() for path in weekly_artifacts)

    decisions = (tmp_path / "seo-workspace" / "data" / "google-ads-decision-review.csv").read_text(encoding="utf-8")
    assert "keep_and_consider_isolation" in decisions
    assert "negative_keyword_candidate" in decisions
    assert "tighten_match_type" in decisions

    audit_summary, audit_artifacts = growth_ops.run_growth_ops_audit(tmp_path)
    assert audit_summary["status"] == "growth_ops_audit_ready"
    assert all(path.exists() for path in audit_artifacts)

    report_text = Path(audit_summary["report"]).read_text(encoding="utf-8")
    assert "Daily Performance Digest" in report_text
    assert "Growth Data Health Center" in report_text
    assert "Lead Quality Tracker" in report_text
    assert "Google Ads Decision Review" in report_text
    assert "AI Search Monitor" in report_text
    assert "Competitor Gap Audit" in report_text
    assert "Competitor Weekly Monitor" in report_text
    assert "Local Citation Tracker" in report_text
    assert "Local SEO Verification" in report_text
    assert "Real Proof Asset Request" in report_text
    assert "Weekly Growth Control" in report_text

    assert (tmp_path / "seo-workspace" / "data" / "daily-performance-digest.json").exists()
    assert (tmp_path / "seo-workspace" / "data" / "growth-data-health.json").exists()
    assert (tmp_path / "seo-workspace" / "data" / "lead-quality-summary.json").exists()
    assert (tmp_path / "seo-workspace" / "data" / "google-ads-decision-review.json").exists()
    assert (tmp_path / "seo-workspace" / "data" / "ai-search-monitor-queries.csv").exists()
    assert (tmp_path / "seo-workspace" / "data" / "competitor-weekly-monitor.csv").exists()
    assert (tmp_path / "seo-workspace" / "data" / "local-citation-tracker.csv").exists()
    assert (tmp_path / "seo-workspace" / "data" / "local-seo-verification.csv").exists()
    assert (tmp_path / "seo-workspace" / "data" / "real-proof-asset-request.csv").exists()
    assert (tmp_path / "seo-workspace" / "data" / "weekly-growth-control.json").exists()
    assert (tmp_path / "seo-workspace" / "config" / "growth-intelligence.example.yml").exists()
    assert (tmp_path / "seo-workspace" / "config" / "lead-quality-log.example.csv").exists()
