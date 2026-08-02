from enum import StrEnum
from typing import Protocol

from pydantic import BaseModel

from app.agent.tools import ToolName


class AgentState(StrEnum):
    RECEIVED = "received"
    PLANNING = "planning"
    EXECUTING_TOOL = "executing_tool"
    ANSWERING = "answering"
    DONE = "done"
    FAILED = "failed"


class AgentStepRecord(BaseModel):
    step_order: int
    tool_name: str
    tool_input: dict
    tool_output: dict


class AgentRunResult(BaseModel):
    final_state: AgentState
    steps: list[AgentStepRecord]
    answer: str | None = None
    error: str | None = None


class Planner(Protocol):
    def __call__(self, question: str, steps: list[AgentStepRecord]) -> tuple[ToolName, dict] | None: ...


class ToolExecutor(Protocol):
    def __call__(self, tool_name: ToolName, tool_input: dict) -> dict: ...


class Answerer(Protocol):
    def __call__(self, question: str, steps: list[AgentStepRecord]) -> str: ...


class AgentStateMachine:
    def __init__(self, planner: Planner, tool_executor: ToolExecutor, answerer: Answerer):
        self._planner = planner
        self._tool_executor = tool_executor
        self._answerer = answerer

    def run(self, question: str, max_steps: int = 10) -> AgentRunResult:
        steps: list[AgentStepRecord] = []
        state = AgentState.PLANNING

        while state == AgentState.PLANNING:
            if len(steps) >= max_steps:
                return AgentRunResult(final_state=AgentState.FAILED, steps=steps, error="max_steps_exceeded")

            action = self._planner(question, steps)
            if action is None:
                state = AgentState.ANSWERING
                break

            tool_name, tool_input = action
            state = AgentState.EXECUTING_TOOL
            try:
                tool_output = self._tool_executor(tool_name, tool_input)
            except Exception as exc:
                return AgentRunResult(final_state=AgentState.FAILED, steps=steps, error=str(exc))

            steps.append(
                AgentStepRecord(
                    step_order=len(steps) + 1,
                    tool_name=tool_name.value,
                    tool_input=tool_input,
                    tool_output=tool_output,
                )
            )
            state = AgentState.PLANNING

        answer = self._answerer(question, steps)
        return AgentRunResult(final_state=AgentState.DONE, steps=steps, answer=answer)
