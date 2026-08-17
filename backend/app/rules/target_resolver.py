from typing import Any

from app.models.ir import BuildingElement

# Maps a Rule.target's leading segment (e.g. "exit.width_mm" -> "exit") to the
# BuildingElement.type values it may be evaluated against. BuildingElement stays
# a flat list (per ADR-0001) — this table is what lets `target` dotted paths
# resolve without a nested `floors[].exits[]` IR shape.
TARGET_ELEMENT_TYPES: dict[str, frozenset[str]] = {
    "exit": frozenset({"exit", "exit_entrance"}),
    "corridor": frozenset({"corridor"}),
    "stair": frozenset({"stair"}),
    "evac": frozenset({"room"}),
}


def _evaluate_condition(condition: str, metadata: dict[str, Any]) -> bool | None:
    """Evaluate one scope.conditions token against element metadata.

    Returns None when the metadata needed to decide isn't present — callers
    must treat that as "cannot evaluate", never as a silent pass or fail.
    """
    if condition == "location=evacuation_floor":
        value = metadata.get("is_evacuation_floor")
        return None if value is None else bool(value)
    if condition in ("location=non_evacuation_floor", "floor!=evacuation_floor"):
        value = metadata.get("is_evacuation_floor")
        return None if value is None else not bool(value)
    if condition == "corridor.both_sides_habitable":
        value = metadata.get("both_sides_habitable")
        return None if value is None else bool(value)
    if condition == "corridor.other":
        value = metadata.get("both_sides_habitable")
        return None if value is None else not bool(value)
    if condition.startswith("floor_index>="):
        value = metadata.get("floor_index")
        return None if value is None else value >= int(condition.split(">=", 1)[1])
    if condition.startswith("room_floor_area_sqm>="):
        value = metadata.get("room_floor_area_sqm")
        return None if value is None else value >= float(condition.split(">=", 1)[1])
    if condition.startswith("exclude="):
        value = metadata.get("building_use")
        excluded = set(condition.split("=", 1)[1].split(","))
        return None if value is None else value not in excluded
    return None


def scope_matches(scope: dict[str, Any], element: BuildingElement) -> bool | None:
    """Return True/False when scope is decidable from element.metadata, else None."""
    building_use_scope = scope.get("building_use") or []
    if building_use_scope:
        value = element.metadata.get("building_use")
        if value is None:
            return None
        if value not in building_use_scope:
            return False

    unresolved = False
    for condition in scope.get("conditions", []):
        result = _evaluate_condition(condition, element.metadata)
        if result is False:
            return False
        if result is None:
            unresolved = True

    return None if unresolved else True
