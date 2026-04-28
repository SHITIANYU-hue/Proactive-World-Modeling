from pathlib import Path

from piwm_data.validate import validate_image_paths, validate_main_schema
from piwm_data.tests.test_exporters import make_record


def test_validate_import_and_valid_record_has_no_schema_errors():
    assert validate_main_schema(make_record()) == []


def test_validate_image_paths_reports_missing_file(tmp_path):
    record = make_record()
    errors = validate_image_paths(record, tmp_path)
    assert errors
    assert "missing frame path" in errors[0]

