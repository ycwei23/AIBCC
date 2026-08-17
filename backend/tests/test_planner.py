from app.agent.planner import template_answerer
from app.agent.state_machine import AgentStepRecord
from app.agent.tools import ToolName


def _run_rules_step(violations: list[dict]) -> AgentStepRecord:
    return AgentStepRecord(
        step_order=1,
        tool_name=ToolName.RUN_RULES.value,
        tool_input={},
        tool_output={"violations": violations},
    )


def test_template_answerer_all_pass_reports_compliant():
    steps = [_run_rules_step([{"rule_id": "R1", "status": "pass"}, {"rule_id": "R2", "status": "pass"}])]

    answer = template_answerer("走廊淨寬是否符合規定？", steps)

    assert "皆符合規定" in answer
    assert "pass" in answer
    assert "2" in answer


def test_template_answerer_no_violations_reports_compliant_with_zero_count():
    # Regression guard for case_10_empty: zero violations must still produce
    # the plain pass-count message, not an insufficient_data message with
    # zero items in it.
    steps = [_run_rules_step([])]

    answer = template_answerer("走廊淨寬是否符合規定？", steps)

    assert "皆符合規定" in answer
    assert "insufficient_data" not in answer
    assert "資料不足" not in answer
    assert "共檢查 0 條規則" in answer


def test_template_answerer_all_fail_reports_noncompliant():
    steps = [_run_rules_step([{"rule_id": "R1", "status": "fail", "evidence": "淨寬不足"}])]

    answer = template_answerer("走廊淨寬是否符合規定？", steps)

    assert "fail" in answer
    assert "皆符合規定" not in answer


def test_template_answerer_all_insufficient_data_never_reports_pass():
    # This is the core regression for the Critical finding: a violation whose
    # status is insufficient_data must never be silently folded into the
    # "compliant" bucket.
    steps = [
        _run_rules_step(
            [
                {"rule_id": "R1", "status": "insufficient_data"},
                {"rule_id": "R2", "status": "insufficient_data"},
            ]
        )
    ]

    answer = template_answerer("走廊淨寬是否符合規定？", steps)

    assert "pass" not in answer
    assert "皆符合規定" not in answer
    assert "insufficient_data" in answer
    assert "資料不足" in answer
    assert "R1" in answer
    assert "R2" in answer


def test_template_answerer_mixed_fail_and_insufficient_data_reports_both():
    steps = [
        _run_rules_step(
            [
                {"rule_id": "R1", "status": "fail", "evidence": "淨寬不足"},
                {"rule_id": "R2", "status": "insufficient_data"},
                {"rule_id": "R3", "status": "pass"},
            ]
        )
    ]

    answer = template_answerer("走廊淨寬是否符合規定？", steps)

    assert "皆符合規定" not in answer
    assert "fail" in answer
    assert "insufficient_data" in answer
    assert "R1" in answer
    assert "R2" in answer
