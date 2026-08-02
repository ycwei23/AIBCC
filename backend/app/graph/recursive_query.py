from sqlalchemy import text
from sqlalchemy.engine import Engine

DESCENDANTS_QUERY = text(
    """
    WITH RECURSIVE descendants AS (
        SELECT from_node, to_node, relation, 1 AS depth
        FROM graph_edges
        WHERE analysis_run_id = :analysis_run_id
          AND from_node = :start_node_id
        UNION ALL
        SELECT e.from_node, e.to_node, e.relation, d.depth + 1
        FROM graph_edges e
        JOIN descendants d ON e.from_node = d.to_node
        WHERE e.analysis_run_id = :analysis_run_id
    )
    SELECT to_node, relation, depth FROM descendants ORDER BY depth, to_node
    """
)


def query_descendants(engine: Engine, analysis_run_id: str, start_node_id: str) -> list[dict]:
    with engine.connect() as conn:
        rows = conn.execute(
            DESCENDANTS_QUERY,
            {"analysis_run_id": analysis_run_id, "start_node_id": start_node_id},
        )
        return [dict(row._mapping) for row in rows]
