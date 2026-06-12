import csv
from pathlib import Path

from validate_workspace import REQUIRED_CSV_FIELDS


def test_required_csv_files_are_dictreader_compatible():
    for path, required_fields in REQUIRED_CSV_FIELDS.items():
        assert path.exists(), f"missing CSV: {path}"
        with path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            rows = list(reader)
        assert reader.fieldnames is not None
        assert set(required_fields).issubset(reader.fieldnames)
        assert rows, f"CSV has no rows: {path}"
        assert all(None not in row for row in rows), f"malformed extra columns: {path}"


def test_csv_files_are_not_collapsed_into_one_line():
    for path in Path("seo-workspace/data").glob("*.csv"):
        with path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            rows = list(reader)
        assert reader.fieldnames is not None, f"CSV has no header: {path}"
        if path in REQUIRED_CSV_FIELDS:
            assert rows, f"required CSV has no rows: {path}"
