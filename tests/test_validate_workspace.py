from validate_workspace import build_report, run_validation


def test_workspace_validation_passes_without_writing_report():
    result = run_validation(write_report=False)
    assert result.ok, result.errors


def test_workspace_validation_report_includes_status():
    result = run_validation(write_report=False)
    report = build_report(result)
    assert "# SEO/GEO Workspace Validation Report" in report
    assert "- Status: PASS" in report
