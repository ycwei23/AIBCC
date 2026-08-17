import json
from pathlib import Path

from pydantic import BaseModel

from app.ingest.document_ai_adapter import LayoutBlock
from app.ingest.vlm_adapter import VlmDetection, VlmRelation

FIXTURES_DIR = Path(__file__).resolve().parents[2] / "data" / "fixtures"


class FixtureBundle(BaseModel):
    fixture_key: str
    layout_blocks: list[LayoutBlock]
    vlm_detections: list[VlmDetection]
    vlm_relations: list[VlmRelation]
    element_geometry_overrides: dict[str, dict]
    element_type_overrides: dict[str, str]
    metadata_by_element_id: dict[str, dict]


def list_fixture_keys() -> list[str]:
    return sorted(path.stem for path in FIXTURES_DIR.glob("*.json"))


def load_fixture(fixture_key: str) -> FixtureBundle:
    path = FIXTURES_DIR / f"{fixture_key}.json"
    if not path.exists():
        raise FileNotFoundError(f"no fixture named {fixture_key!r} in {FIXTURES_DIR}")
    with path.open(encoding="utf-8") as f:
        raw = json.load(f)
    return FixtureBundle(**raw)
