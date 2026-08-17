from app.agent.state_machine import AgentStepRecord
from app.agent.tools import ToolName

_SEQUENCE = [ToolName.QUERY_GRAPH, ToolName.RUN_RULES, ToolName.RETRIEVE_LAW]


def fixed_sequence_planner(question: str, steps: list[AgentStepRecord]) -> tuple[ToolName, dict] | None:
    completed = {step.tool_name for step in steps}
    for tool_name in _SEQUENCE:
        if tool_name.value not in completed:
            return tool_name, {"question": question}
    return None


def template_answerer(question: str, steps: list[AgentStepRecord]) -> str:
    rule_step = next((s for s in steps if s.tool_name == ToolName.RUN_RULES.value), None)
    violations = (rule_step.tool_output or {}).get("violations", []) if rule_step else []
    fails = [v for v in violations if v.get("status") == "fail"]
    if not fails:
        return f"針對「{question}」：目前檢查結果皆符合規定（pass），共檢查 {len(violations)} 條規則。"
    detail = "；".join(f"{v['rule_id']}：{v.get('evidence', '')}" for v in fails)
    return f"針對「{question}」：發現 {len(fails)} 項不符合規定（fail）— {detail}"
