from app.agent.state_machine import AgentState, AgentStateMachine, AgentStepRecord
from app.agent.tools import ToolName


def test_state_machine_answers_directly_when_planner_requests_no_tools():
    def planner(question: str, steps: list[AgentStepRecord]):
        return None

    def tool_executor(tool_name, tool_input):
        raise AssertionError("tool_executor should not be called")

    def answerer(question: str, steps: list[AgentStepRecord]) -> str:
        return f"answer to: {question}"

    machine = AgentStateMachine(planner=planner, tool_executor=tool_executor, answerer=answerer)
    result = machine.run("走道加寬 200mm 後是否合法？")

    assert result.final_state == AgentState.DONE
    assert result.steps == []
    assert result.answer == "answer to: 走道加寬 200mm 後是否合法？"
    assert result.error is None


def test_state_machine_executes_tools_in_order_then_answers():
    plan = [
        (ToolName.QUERY_GRAPH, {"start_node_id": "corridor-3"}),
        (ToolName.RUN_RULES, {"elements": []}),
        None,
    ]

    def planner(question: str, steps: list[AgentStepRecord]):
        return plan[len(steps)]

    def tool_executor(tool_name, tool_input):
        return {"tool": tool_name.value, "echo": tool_input}

    def answerer(question: str, steps: list[AgentStepRecord]) -> str:
        return f"used {len(steps)} tools"

    machine = AgentStateMachine(planner=planner, tool_executor=tool_executor, answerer=answerer)
    result = machine.run("走道加寬 200mm 後是否合法？")

    assert result.final_state == AgentState.DONE
    assert len(result.steps) == 2
    assert result.steps[0].step_order == 1
    assert result.steps[0].tool_name == "query_graph"
    assert result.steps[0].tool_output == {"tool": "query_graph", "echo": {"start_node_id": "corridor-3"}}
    assert result.steps[1].tool_name == "run_rules"
    assert result.answer == "used 2 tools"


def test_state_machine_transitions_to_failed_when_tool_raises():
    def planner(question: str, steps: list[AgentStepRecord]):
        return (ToolName.QUERY_GRAPH, {})

    def tool_executor(tool_name, tool_input):
        raise RuntimeError("graph query timed out")

    def answerer(question: str, steps: list[AgentStepRecord]) -> str:
        raise AssertionError("answerer should not be called")

    machine = AgentStateMachine(planner=planner, tool_executor=tool_executor, answerer=answerer)
    result = machine.run("走道加寬 200mm 後是否合法？")

    assert result.final_state == AgentState.FAILED
    assert result.steps == []
    assert result.error == "graph query timed out"
    assert result.answer is None


def test_state_machine_fails_when_max_steps_exceeded():
    def planner(question: str, steps: list[AgentStepRecord]):
        return (ToolName.QUERY_GRAPH, {})

    def tool_executor(tool_name, tool_input):
        return {}

    def answerer(question: str, steps: list[AgentStepRecord]) -> str:
        raise AssertionError("answerer should not be called")

    machine = AgentStateMachine(planner=planner, tool_executor=tool_executor, answerer=answerer)
    result = machine.run("走道加寬 200mm 後是否合法？", max_steps=3)

    assert result.final_state == AgentState.FAILED
    assert result.error == "max_steps_exceeded"
    assert len(result.steps) == 3
