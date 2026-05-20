from __future__ import annotations

import json
from pathlib import Path

from backend.models.test_case import TestCase
from backend.utils.logger import get_logger

logger = get_logger("test_config")

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
TEST_CASES_FILE = DATA_DIR / "test_cases.json"


def _ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_test_cases() -> dict[str, TestCase]:
    _ensure_data_dir()
    if not TEST_CASES_FILE.exists():
        return {}
    raw = json.loads(TEST_CASES_FILE.read_text(encoding="utf-8"))
    return {item["id"]: TestCase(**item) for item in raw}


def save_test_cases(cases: dict[str, TestCase]) -> None:
    _ensure_data_dir()
    items = [c.model_dump(mode="json") for c in cases.values()]
    TEST_CASES_FILE.write_text(
        json.dumps(items, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )


def save_test_case(case: TestCase) -> None:
    cases = load_test_cases()
    cases[case.id] = case
    save_test_cases(cases)


def delete_test_case(case_id: str) -> None:
    cases = load_test_cases()
    cases.pop(case_id, None)
    save_test_cases(cases)


def import_test_case(json_text: str) -> TestCase:
    data = json.loads(json_text)
    return TestCase(**data)
