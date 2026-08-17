from sqlalchemy.engine import Engine

from app.agent.tools import ToolName
from app.db import analysis_repo
from app.pipeline.run_analysis import MVP_BUNDLE_PATH
from app.rules.law_search import search_rules
from app.rules.loader import load_rules_from_file


def build_tool_executor(engine: Engine, analysis_run_id: str):
    def execute(tool_name: ToolName, tool_input: dict) -> dict:
        if tool_name == ToolName.QUERY_GRAPH:
            nodes, edges = analysis_repo.get_graph(engine, analysis_run_id)
            return {"nodes": nodes, "edges": edges}
        if tool_name == ToolName.RUN_RULES:
            violations = analysis_repo.get_violations(engine, analysis_run_id)
            return {"violations": violations}
        if tool_name == ToolName.RETRIEVE_LAW:
            rules = load_rules_from_file(MVP_BUNDLE_PATH)
            matches = search_rules(rules, query=tool_input.get("question", ""))
            return {"matches": [m.model_dump() for m in matches]}
        raise ValueError(f"tool {tool_name} not wired in this executor")

    return execute
