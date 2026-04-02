import re

def analyze_question(question, graph_data):
    text = str(question or "").strip()
    lowered = text.lower()

    entity_names = _get_graph_entity_names(graph_data)
    matched_entities = _match_entities(text, entity_names)

    if _is_relationship_path_question(lowered) and len(matched_entities) >= 2:
        return {
            "intent": "relationship_path",
            "matched_entities": matched_entities[:2],
            "strategy": "intent_query_builder",
            "fallback_used": False,
            "filters": {"max_hops": 3},
        }

    if _is_ranking_influence_question(lowered):
        return {
            "intent": "ranking_influence",
            "matched_entities": [],
            "strategy": "intent_query_builder",
            "fallback_used": False,
            "ranking_basis": "incoming_plus_outgoing_edges",
        }

    if _is_ranking_centrality_question(lowered):
        return {
            "intent": "ranking_centrality",
            "matched_entities": [],
            "strategy": "intent_query_builder",
            "fallback_used": False,
            "ranking_basis": "degree",
        }

    if _is_lookup_summary_question(lowered) and matched_entities:
        return {
            "intent": "lookup_summary",
            "matched_entities": matched_entities[:1],
            "strategy": "intent_query_builder",
            "fallback_used": False,
        }

    if _is_lookup_basic_question(lowered) and matched_entities:
        return {
            "intent": "lookup_basic",
            "matched_entities": matched_entities[:1],
            "strategy": "intent_query_builder",
            "fallback_used": False,
        }

    return {
        "intent": "generic_fallback",
        "matched_entities": matched_entities,
        "strategy": "llm_cypher_generation",
        "fallback_used": True,
    }


def _get_graph_entity_names(graph_data):
    names = []
    for node in (graph_data or {}).get("nodes", []):
        name = (node.get("name") or "").strip()
        if name:
            names.append(name)

        for alias in node.get("aliases", []):
            alias = (alias or "").strip()
            if alias:
                names.append(alias)

    return sorted(set(names), key=len, reverse=True)


def _match_entities(question, entity_names):
    
    question_lower = question.lower()
    spans = []

    for name in entity_names:
        name_lower = name.lower()
        pattern = r"(?<!\w)" + re.escape(name_lower) + r"(?!\w)"

        for match in re.finditer(pattern, question_lower):
            spans.append({
                "name": name,
                "start": match.start(),
                "end": match.end(),
                "length": len(name_lower),
            })

    # Prefer longer matches first, then earlier position
    spans.sort(key=lambda item: (-item["length"], item["start"]))

    selected = []
    occupied = []

    for span in spans:
        overlaps = any(
            not (span["end"] <= start or span["start"] >= end)
            for start, end in occupied
        )
        if overlaps:
            continue

        selected.append(span["name"])
        occupied.append((span["start"], span["end"]))

    return selected


def _is_lookup_basic_question(lowered):
    return (
        lowered.startswith("who is ")
        or lowered.startswith("what is ")
    )


def _is_lookup_summary_question(lowered):
    return (
        lowered.startswith("tell me about ")
        or lowered.startswith("what can you tell me about ")
    )


def _is_relationship_path_question(lowered):
    return (
        lowered.startswith("how are ") and " related" in lowered
    ) or (
        lowered.startswith("how is ") and " related" in lowered
    )


def _is_ranking_centrality_question(lowered):
    return (
        "who is central" in lowered
        or "what is central" in lowered
        or "most central" in lowered
    )


def _is_ranking_influence_question(lowered):
    return (
        "most influential" in lowered
        or "who is influential" in lowered
    )