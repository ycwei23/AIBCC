from typing import Literal

from pydantic import BaseModel

from app.graph.builder import GraphEdgeData
from app.models.ir import BuildingElement


class VlmDetection(BaseModel):
    model_config = {"frozen": True}

    detection_id: str
    page: int
    bbox: list[float]
    label: Literal["room", "door", "exit", "window", "wall"]
    confidence: float


class VlmRelation(BaseModel):
    model_config = {"frozen": True}

    from_detection_id: str
    relation: str
    to_detection_id: str
    confidence: float


def vlm_detections_to_building_elements(detections: list[VlmDetection]) -> list[BuildingElement]:
    return [
        BuildingElement(
            id=detection.detection_id,
            type=detection.label,
            page=detection.page,
            bbox=detection.bbox,
            geometry={},
            source="vlm",
            confidence=detection.confidence,
        )
        for detection in detections
    ]


def vlm_relations_to_graph_edges(relations: list[VlmRelation]) -> list[GraphEdgeData]:
    return [
        GraphEdgeData(
            from_node=relation.from_detection_id,
            relation=relation.relation,
            to_node=relation.to_detection_id,
            source="vlm",
            confidence=relation.confidence,
        )
        for relation in relations
    ]
