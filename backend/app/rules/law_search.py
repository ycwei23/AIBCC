from app.agent.tools import LawMatch
from app.models.ir import Rule


def search_rules(
    rules: list[Rule], query: str, building_use: str | None = None, top_k: int = 5
) -> list[LawMatch]:
    scored: list[tuple[float, Rule]] = []
    for rule in rules:
        scope_uses = rule.scope.get("building_use") or []
        if building_use and scope_uses and building_use not in scope_uses:
            continue
        haystack = f"{rule.law_name}{rule.article}{rule.source_quote}{rule.target}"
        score = _char_overlap_score(query, haystack)
        if score > 0:
            scored.append((score, rule))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [
        LawMatch(
            rule_id=rule.rule_id,
            law_name=rule.law_name,
            article=rule.article,
            snippet=rule.source_quote,
            relevance_score=score,
        )
        for score, rule in scored[:top_k]
    ]


def _char_overlap_score(query: str, text: str) -> float:
    query_chars = {ch for ch in query if not ch.isspace() and ch not in "？?，,。"}
    if not query_chars:
        return 0.0
    matched = sum(1 for ch in query_chars if ch in text)
    return matched / len(query_chars)
