from app.rules.loader import load_rule_bundle


def _sample_bundle():
    return {
        "law_code": "D0070115",
        "rules": [
            {
                "rule_id": "MVP-EXIT-WIDTH-90",
                "law_code": "D0070115",
                "law_name": "建築技術規則建築設計施工編",
                "article": "90",
                "version": "2026-02-23",
                "scope": {"building_use": [], "conditions": ["location=evacuation_floor"]},
                "target": "exit.width_mm",
                "operator": ">=",
                "threshold": 1200,
                "unit": "mm",
                "severity": "high",
                "source_quote": "寬度不得小於一‧二公尺",
                "review_status": "active",
            },
            {
                "rule_id": "MVP-DRAFT-ONLY",
                "law_code": "D0070115",
                "law_name": "建築技術規則建築設計施工編",
                "article": "99",
                "version": "2026-02-23",
                "scope": {},
                "target": "exit.width_mm",
                "operator": ">=",
                "threshold": 1000,
                "unit": "mm",
                "severity": "low",
                "review_status": "draft",
            },
        ],
    }


def test_load_rule_bundle_filters_out_non_active_rules():
    rules = load_rule_bundle(_sample_bundle())
    assert [rule.rule_id for rule in rules] == ["MVP-EXIT-WIDTH-90"]


def test_load_rule_bundle_maps_external_fields_to_internal_rule():
    rules = load_rule_bundle(_sample_bundle())
    rule = rules[0]
    assert rule.law_code == "D0070115"
    assert rule.target == "exit.width_mm"
    assert rule.threshold == 1200
    assert rule.source_quote == "寬度不得小於一‧二公尺"
    assert rule.scope == {"building_use": [], "conditions": ["location=evacuation_floor"]}
