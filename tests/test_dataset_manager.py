import csv
from pathlib import Path

from atlas.datasets import (
    DATASET_MODEL_VERSION,
    dataset_load_result_to_dict,
    load_dataset,
)


def test_load_missing_file(tmp_path: Path):
    result = load_dataset(tmp_path / "missing.csv")

    assert result.version == DATASET_MODEL_VERSION
    assert result.valid_count == 0
    assert result.invalid_count == 1
    assert result.issues[0].code == "missing_file"


def test_load_unsupported_file_type(tmp_path: Path):
    file_path = tmp_path / "batch.xlsx"
    file_path.write_text("fake", encoding="utf-8")

    result = load_dataset(file_path)

    assert result.invalid_count == 1
    assert result.issues[0].code == "unsupported_file_type"


def test_load_txt_dataset(tmp_path: Path):
    file_path = tmp_path / "names.txt"
    file_path.write_text(
        "Albert Einstein\n\nIsaac Newton\n",
        encoding="utf-8",
    )

    result = load_dataset(file_path)

    assert result.record_count == 2
    assert result.valid_count == 2
    assert result.issue_count == 1
    assert result.records[0].name == "Albert Einstein"
    assert result.records[1].name == "Isaac Newton"


def test_load_csv_dataset(tmp_path: Path):
    file_path = tmp_path / "historical_batch.csv"

    with file_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "name",
                "birth_date",
                "birth_time",
                "birth_place",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "name": "Albert Einstein",
                "birth_date": "1879-03-14",
                "birth_time": "11:30",
                "birth_place": "Ulm Germany",
            }
        )

    result = load_dataset(file_path)

    assert result.record_count == 1
    assert result.valid_count == 1
    assert result.invalid_count == 0
    assert result.records[0].name == "Albert Einstein"
    assert result.records[0].birth_date == "1879-03-14"
    assert result.records[0].birth_time == "11:30"
    assert result.records[0].birth_place == "Ulm Germany"


def test_load_csv_missing_required_name_column(tmp_path: Path):
    file_path = tmp_path / "bad.csv"

    with file_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "birth_date",
                "birth_time",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "birth_date": "1879-03-14",
                "birth_time": "11:30",
            }
        )

    result = load_dataset(file_path)

    assert result.record_count == 0
    assert result.invalid_count == 1
    assert result.issues[0].code == "missing_required_columns"


def test_load_csv_empty_name_row_is_invalid(tmp_path: Path):
    file_path = tmp_path / "bad_row.csv"

    with file_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "name",
                "birth_date",
                "birth_time",
                "birth_place",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "name": "",
                "birth_date": "1879-03-14",
                "birth_time": "11:30",
                "birth_place": "Ulm Germany",
            }
        )

    result = load_dataset(file_path)

    assert result.record_count == 0
    assert result.valid_count == 0
    assert result.invalid_count == 1
    assert result.issues[0].code == "empty_name"


def test_load_csv_unknown_birth_time_info_issue(tmp_path: Path):
    file_path = tmp_path / "unknown_time.csv"

    with file_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "name",
                "birth_date",
                "birth_time",
                "birth_place",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "name": "Isaac Newton",
                "birth_date": "1643-01-04",
                "birth_time": "",
                "birth_place": "Woolsthorpe England",
            }
        )

    result = load_dataset(file_path)

    assert result.record_count == 1
    assert result.valid_count == 1
    assert result.invalid_count == 0
    assert result.records[0].birth_time == "Unknown"
    assert result.issues[0].code == "unknown_birth_time"


def test_dataset_load_result_to_dict(tmp_path: Path):
    file_path = tmp_path / "names.txt"
    file_path.write_text("Ada Lovelace\n", encoding="utf-8")

    result = load_dataset(file_path)
    data = dataset_load_result_to_dict(result)

    assert data["version"] == DATASET_MODEL_VERSION
    assert data["record_count"] == 1
    assert data["records"][0]["name"] == "Ada Lovelace"