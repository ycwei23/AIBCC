from pathlib import Path

from sqlalchemy.engine import Engine

from app.db import analysis_repo
from app.graph.builder import GraphNodeData
from app.ingest.document_ai_adapter import layout_blocks_to_building_elements
from app.ingest.vlm_adapter import vlm_detections_to_building_elements, vlm_relations_to_graph_edges
from app.models.ir import BuildingElement
from app.pipeline.fixtures import load_fixture
from app.rules.engine import run_rules
from app.rules.geometry_validator import validate_elements
from app.rules.loader import load_rules_from_file

MVP_BUNDLE_PATH = Path(__file__).resolve().parents[2] / "data" / "rules" / "mvp_rules_active_v0.json"


def run_analysis(engine: Engine, analysis_run_id: str, fixture_key: str) -> None:
    try:
        _run(engine, analysis_run_id, fixture_key)
    except Exception:
        analysis_repo.update_analysis_status(engine, analysis_run_id, "failed")


def _run(engine: Engine, analysis_run_id: str, fixture_key: str) -> None:
    bundle = load_fixture(fixture_key)

    analysis_repo.update_analysis_status(engine, analysis_run_id, "document_parsing")
    dimension_elements = layout_blocks_to_building_elements(bundle.layout_blocks)

    analysis_repo.update_analysis_status(engine, analysis_run_id, "vlm_extracting")
    vlm_elements = vlm_detections_to_building_elements(bundle.vlm_detections)
    edges = vlm_relations_to_graph_edges(bundle.vlm_relations)

    elements = _apply_fixture_overrides(dimension_elements + vlm_elements, bundle)

    analysis_repo.update_analysis_status(engine, analysis_run_id, "geometry_validating")
    valid_elements, _geometry_errors = validate_elements(elements)

    analysis_repo.update_analysis_status(engine, analysis_run_id, "graph_building")
    nodes = [GraphNodeData(node_id=el.id, node_type="Element", properties={"type": el.type}) for el in valid_elements]
    analysis_repo.save_building_elements(engine, analysis_run_id, valid_elements)
    analysis_repo.save_graph(engine, analysis_run_id, nodes, edges)

    analysis_repo.update_analysis_status(engine, analysis_run_id, "rule_checking")
    rules = load_rules_from_file(MVP_BUNDLE_PATH)
    analysis_repo.upsert_rules(engine, rules)
    violations = run_rules(valid_elements, rules)
    analysis_repo.save_violations(engine, analysis_run_id, violations)

    analysis_repo.update_analysis_status(engine, analysis_run_id, "agent_explaining")
    analysis_repo.update_analysis_status(engine, analysis_run_id, "completed")


def _apply_fixture_overrides(elements: list[BuildingElement], bundle) -> list[BuildingElement]:
    result = []
    for element in elements:
        geometry_override = bundle.element_geometry_overrides.get(element.id)
        type_override = bundle.element_type_overrides.get(element.id)
        metadata = bundle.metadata_by_element_id.get(element.id, {})
        result.append(
            element.model_copy(
                update={
                    "geometry": {**element.geometry, **(geometry_override or {})},
                    "type": type_override or element.type,
                    "metadata": metadata,
                }
            )
        )
    return result
