from app.graph.builder import (
    CIRCULATION_RELATIONS,
    build_sample_building_graph,
    find_escape_path,
    to_networkx_graph,
)


def test_build_sample_building_graph_covers_all_node_types():
    nodes, edges = build_sample_building_graph()
    node_types = {n.node_type for n in nodes}
    assert node_types == {"Building", "Floor", "Space", "Element", "Path", "Exit"}
    assert len(nodes) == 8
    assert len(edges) == 8


def test_to_networkx_graph_builds_full_graph():
    nodes, edges = build_sample_building_graph()
    graph = to_networkx_graph(nodes, edges)
    assert graph.number_of_nodes() == 8
    assert graph.number_of_edges() == 8
    assert graph.nodes["exit-1"]["node_type"] == "Exit"
    assert graph.nodes["building-1"]["node_type"] == "Building"


def test_to_networkx_graph_filters_by_relation():
    nodes, edges = build_sample_building_graph()
    circulation = to_networkx_graph(nodes, edges, relations=CIRCULATION_RELATIONS)
    assert circulation.number_of_edges() == 4
    assert not circulation.has_edge("building-1", "floor-1")


def test_find_escape_path_from_room_101():
    nodes, edges = build_sample_building_graph()
    circulation = to_networkx_graph(nodes, edges, relations=CIRCULATION_RELATIONS)
    path = find_escape_path(circulation, "space-room-101")
    assert path == [
        "space-room-101",
        "element-door-101",
        "space-corridor-1",
        "path-corridor-to-exit",
        "exit-1",
    ]


def test_find_escape_path_returns_none_for_isolated_room():
    nodes, edges = build_sample_building_graph()
    circulation = to_networkx_graph(nodes, edges, relations=CIRCULATION_RELATIONS)
    path = find_escape_path(circulation, "space-room-103")
    assert path is None
