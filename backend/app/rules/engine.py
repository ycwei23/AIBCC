from app.models.ir import BuildingElement, Rule, Violation
from app.rules.target_resolver import TARGET_ELEMENT_TYPES, scope_matches

_OPERATORS = {
    ">=": lambda actual, threshold: actual >= threshold,
    "<=": lambda actual, threshold: actual <= threshold,
    ">": lambda actual, threshold: actual > threshold,
    "<": lambda actual, threshold: actual < threshold,
    "==": lambda actual, threshold: actual == threshold,
    "!=": lambda actual, threshold: actual != threshold,
}


def run_rules(elements: list[BuildingElement], rules: list[Rule]) -> list[Violation]:
    violations: list[Violation] = []
    for rule in rules:
        prefix, field = rule.target.split(".", 1)
        matching_types = TARGET_ELEMENT_TYPES.get(prefix)
        if matching_types is None:
            continue
        candidates = [element for element in elements if element.type in matching_types]

        if field == "count":
            violations.extend(_evaluate_count_rule(rule, candidates))
            continue

        for element in candidates:
            violation = _evaluate_element_rule(rule, field, element)
            if violation is not None:
                violations.append(violation)
    return violations


def _evaluate_element_rule(rule: Rule, field: str, element: BuildingElement) -> Violation | None:
    scope_result = scope_matches(rule.scope, element)
    if scope_result is False:
        return None

    actual = element.geometry.get(field)
    if scope_result is None or actual is None:
        return _make_violation(
            rule, [element], measured=actual or 0.0, status="insufficient_data", page=element.page
        )

    status = "pass" if _OPERATORS[rule.operator](actual, rule.threshold) else "fail"
    return _make_violation(rule, [element], measured=actual, status=status, page=element.page)


def _evaluate_count_rule(rule: Rule, candidates: list[BuildingElement]) -> list[Violation]:
    # BuildingElement has no dedicated floor id yet, so `page` is the floor
    # proxy for aggregate targets like "stair.count" (one floor plan per page).
    by_page: dict[int, list[BuildingElement]] = {}
    for element in candidates:
        by_page.setdefault(element.page, []).append(element)

    violations: list[Violation] = []
    for page, page_elements in by_page.items():
        scope_result = scope_matches(rule.scope, page_elements[0])
        if scope_result is False:
            continue
        count = len(page_elements)
        status = "insufficient_data" if scope_result is None else (
            "pass" if _OPERATORS[rule.operator](count, rule.threshold) else "fail"
        )
        violations.append(
            _make_violation(rule, page_elements, measured=float(count), status=status, page=page)
        )
    return violations


def _make_violation(
    rule: Rule, elements: list[BuildingElement], measured: float, status: str, page: int
) -> Violation:
    citation = f"{rule.law_name} 第{rule.article}條"
    evidence = f"{citation}：{rule.source_quote}" if rule.source_quote else citation
    return Violation(
        violation_id=f"{rule.rule_id}:{'+'.join(element.id for element in elements)}",
        rule_id=rule.rule_id,
        element_ids=[element.id for element in elements],
        measured=measured,
        required=rule.threshold,
        status=status,
        page=page,
        highlight=[element.bbox for element in elements],
        evidence=evidence,
        suggestion="",
    )
