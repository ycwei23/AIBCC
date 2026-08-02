from typing import Literal

import networkx as nx
from pydantic import BaseModel

NodeType = Literal["Building", "Floor", "Space", "Element", "Path", "Exit", "Rule"]

CIRCULATION_RELATIONS: set[str] = {"connects_via", "leads_to"}


class GraphNodeData(BaseModel):
    model_config = {"frozen": True}

    node_id: str
    node_type: NodeType
    properties: dict = {}


class GraphEdgeData(BaseModel):
    model_config = {"frozen": True}

    from_node: str
    relation: str
    to_node: str
    source: str = "poc_seed"
    confidence: float = 1.0


def build_sample_building_graph() -> tuple[list[GraphNodeData], list[GraphEdgeData]]:
    nodes = [
        GraphNodeData(node_id="building-1", node_type="Building", properties={"name": "示範大樓"}),
        GraphNodeData(node_id="floor-1", node_type="Floor", properties={"level": 1}),
        GraphNodeData(
            node_id="space-room-101", node_type="Space", properties={"room_no": "101", "area_m2": 18.0}
        ),
        GraphNodeData(
            node_id="space-corridor-1",
            node_type="Space",
            properties={"room_no": "corridor-1", "width_mm": 1400},
        ),
        GraphNodeData(
            node_id="space-room-103", node_type="Space", properties={"room_no": "103", "area_m2": 15.0}
        ),
        GraphNodeData(
            node_id="element-door-101",
            node_type="Element",
            properties={"element_type": "door", "width_mm": 900},
        ),
        GraphNodeData(
            node_id="path-corridor-to-exit", node_type="Path", properties={"length_m": 12.0}
        ),
        GraphNodeData(node_id="exit-1", node_type="Exit", properties={"exit_type": "final_exit"}),
    ]
    edges = [
        GraphEdgeData(from_node="building-1", relation="contains", to_node="floor-1"),
        GraphEdgeData(from_node="floor-1", relation="contains", to_node="space-room-101"),
        GraphEdgeData(from_node="floor-1", relation="contains", to_node="space-corridor-1"),
        GraphEdgeData(from_node="floor-1", relation="contains", to_node="space-room-103"),
        GraphEdgeData(from_node="space-room-101", relation="connects_via", to_node="element-door-101"),
        GraphEdgeData(from_node="element-door-101", relation="connects_via", to_node="space-corridor-1"),
        GraphEdgeData(from_node="space-corridor-1", relation="leads_to", to_node="path-corridor-to-exit"),
        GraphEdgeData(from_node="path-corridor-to-exit", relation="leads_to", to_node="exit-1"),
    ]
    return nodes, edges


def to_networkx_graph(
    nodes: list[GraphNodeData],
    edges: list[GraphEdgeData],
    relations: set[str] | None = None,
) -> nx.DiGraph:
    graph = nx.DiGraph()
    for node in nodes:
        graph.add_node(node.node_id, node_type=node.node_type, properties=node.properties)
    for edge in edges:
        if relations is not None and edge.relation not in relations:
            continue
        graph.add_edge(edge.from_node, edge.to_node, relation=edge.relation, confidence=edge.confidence)
    return graph


def find_escape_path(circulation_graph: nx.DiGraph, start_node_id: str) -> list[str] | None:
    exit_nodes = [
        node_id
        for node_id, data in circulation_graph.nodes(data=True)
        if data.get("node_type") == "Exit"
    ]
    best_path: list[str] | None = None
    for exit_node in exit_nodes:
        try:
            path = nx.shortest_path(circulation_graph, start_node_id, exit_node)
        except (nx.NodeNotFound, nx.NetworkXNoPath):
            continue
        if best_path is None or len(path) < len(best_path):
            best_path = path
    return best_path
