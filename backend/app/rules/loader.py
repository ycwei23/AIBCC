import json
from pathlib import Path
from typing import Any

from app.models.ir import Rule


def load_rules_from_file(path: str | Path) -> list[Rule]:
    """Read a building-law-etl Rule Spec v0 bundle from disk and load its active rules."""
    with Path(path).open(encoding="utf-8") as f:
        return load_rule_bundle(json.load(f))


def load_rule_bundle(bundle: dict[str, Any]) -> list[Rule]:
    """Convert a building-law-etl Rule Spec v0 bundle into internal Rule models.

    Only ``review_status == "active"`` rules load — drafts and rules still
    pending human review must never reach the engine (see
    building-law-etl-main/docs/rule_engine_interface.md, constraint 1).
    """
    return [
        Rule(
            rule_id=raw["rule_id"],
            law_code=raw.get("law_code", ""),
            law_name=raw["law_name"],
            article=raw["article"],
            version=raw["version"],
            scope=raw.get("scope", {}),
            target=raw["target"],
            operator=raw["operator"],
            threshold=raw["threshold"],
            unit=raw["unit"],
            severity=raw["severity"],
            source_quote=raw.get("source_quote", ""),
        )
        for raw in bundle["rules"]
        if raw.get("review_status") == "active"
    ]
