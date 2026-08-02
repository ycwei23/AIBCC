from app.ingest.vlm_adapter import (
    VlmDetection,
    VlmRelation,
    vlm_detections_to_building_elements,
    vlm_relations_to_graph_edges,
)


def test_vlm_detection_valid():
    detection = VlmDetection(
        detection_id="room-A101",
        page=3,
        bbox=[10.0, 10.0, 200.0, 200.0],
        label="room",
        confidence=0.88,
    )
    assert detection.label == "room"


def test_vlm_detections_to_building_elements():
    detections = [
        VlmDetection(
            detection_id="room-A101", page=3, bbox=[10.0, 10.0, 200.0, 200.0], label="room", confidence=0.88
        ),
        VlmDetection(
            detection_id="door-12", page=3, bbox=[190.0, 100.0, 210.0, 140.0], label="door", confidence=0.93
        ),
    ]
    elements = vlm_detections_to_building_elements(detections)
    assert len(elements) == 2
    assert elements[0].id == "room-A101"
    assert elements[0].type == "room"
    assert elements[0].source == "vlm"
    assert elements[1].type == "door"


def test_vlm_relations_to_graph_edges():
    relations = [
        VlmRelation(
            from_detection_id="room-A101", relation="connected_to", to_detection_id="door-12", confidence=0.91
        )
    ]
    edges = vlm_relations_to_graph_edges(relations)
    assert len(edges) == 1
    assert edges[0].from_node == "room-A101"
    assert edges[0].relation == "connected_to"
    assert edges[0].to_node == "door-12"
    assert edges[0].source == "vlm"
    assert edges[0].confidence == 0.91
