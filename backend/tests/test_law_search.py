from pathlib import Path

from app.rules.law_search import search_rules
from app.rules.loader import load_rules_from_file

MVP_BUNDLE_PATH = Path(__file__).resolve().parents[1] / "data" / "rules" / "mvp_rules_active_v0.json"


def test_search_matches_exit_width_rule_by_keyword():
    rules = load_rules_from_file(MVP_BUNDLE_PATH)
    matches = search_rules(rules, query="出入口寬度", top_k=3)
    assert matches[0].rule_id in {"MVP-EXIT-WIDTH-90", "MVP-EXIT-WIDTH-91"}
    assert matches[0].relevance_score > 0


def test_search_filters_by_building_use_scope():
    rules = load_rules_from_file(MVP_BUNDLE_PATH)
    matches = search_rules(rules, query="走廊", building_use="A", top_k=10)
    assert all(
        not (r.scope.get("building_use")) or "A" in r.scope.get("building_use", [])
        for r in rules
        if r.rule_id in {m.rule_id for m in matches}
    )


def test_search_returns_empty_for_no_keyword_overlap():
    rules = load_rules_from_file(MVP_BUNDLE_PATH)
    matches = search_rules(rules, query="ZZZ完全無關鍵字QQQ", top_k=5)
    assert matches == []
