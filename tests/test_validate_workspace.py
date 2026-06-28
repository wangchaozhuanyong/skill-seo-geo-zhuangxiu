from validate_workspace import build_parser, build_report, run_validation


def test_workspace_validation_passes_without_writing_report():
    result = run_validation(write_report=False)
    assert result.ok, result.errors


def test_workspace_validation_report_includes_status():
    result = run_validation(write_report=False)
    report = build_report(result)
    assert "# SEO/GEO Workspace Validation Report" in report
    assert "- Status: PASS" in report


def test_workspace_validation_parser_supports_no_report_aliases():
    parser = build_parser()

    args = parser.parse_args(["--no-report"])
    assert args.no_report is True
    assert args.check_only is False

    args = parser.parse_args(["--check-only"])
    assert args.no_report is False
    assert args.check_only is True
