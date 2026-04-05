from typing import Any

from ...models import Document


def build_intent_cypher(
    document: Document,
    question_analysis: dict[str, Any],
) -> str | None:
    """
    Build deterministic Cypher for a supported QA intent.

    Returns None when the question should fall back to generic LLM Cypher generation.
    """
    intent = question_analysis.get("intent")
    matched_entities = question_analysis.get("matched_entities", [])

    if intent == "lookup_basic" and matched_entities:
        entity_name = matched_entities[0]
        return f"""
            MATCH (n:Entity)
            WHERE n.document_id = {document.id}
            AND toLower(n.name) = toLower("{_escape(entity_name)}")
            RETURN n.name AS entity_name, n.label AS label
            LIMIT 1
        """.strip()

    if intent == "lookup_summary" and matched_entities:
        entity_name = matched_entities[0]
        return f"""
            MATCH (n:Entity)
            WHERE n.document_id = {document.id}
            AND toLower(n.name) = toLower("{_escape(entity_name)}")
            OPTIONAL MATCH (n)-[r]-(m:Entity)
            WHERE m.document_id = {document.id} AND r.document_id = {document.id}
            RETURN n.name AS entity_name,
                n.label AS label,
                collect(DISTINCT {{
                    related_entity: m.name,
                    related_label: m.label,
                    relation: type(r)
                }}) AS related_entities
            LIMIT 1
        """.strip()

    if intent == "relationship_path" and len(matched_entities) >= 2:
        left = matched_entities[0]
        right = matched_entities[1]
        max_hops = question_analysis.get("filters", {}).get("max_hops", 3)

        return f"""
            MATCH (a:Entity)
            WHERE a.document_id = {document.id}
            AND toLower(a.name) = toLower("{_escape(left)}")

            MATCH (b:Entity)
            WHERE b.document_id = {document.id}
            AND toLower(b.name) = toLower("{_escape(right)}")
            AND id(a) <> id(b)

            MATCH p = shortestPath((a)-[*1..{int(max_hops)}]-(b))
            WHERE all(n IN nodes(p) WHERE n.document_id = {document.id})
            AND all(r IN relationships(p) WHERE r.document_id = {document.id})

            RETURN a.name AS source,
                a.label AS source_label,
                b.name AS target,
                b.label AS target_label,
                [node IN nodes(p) | {{graph_id: node.graph_id, name: node.name, label: node.label}}] AS path_nodes,
                [node IN nodes(p) | node.graph_id] AS path_node_ids,
                [i IN range(0, length(p) - 1) |
                    {{
                        source: nodes(p)[i].graph_id,
                        target: nodes(p)[i + 1].graph_id,
                        type: type(relationships(p)[i])
                    }}
                ] AS path_edges,
                [rel IN relationships(p) | type(rel)] AS path_relations,
                length(p) AS path_length
            LIMIT 1
        """.strip()

    if intent == "ranking_centrality":
        return f"""
            MATCH (n:Entity)
            WHERE n.document_id = {document.id}
            OPTIONAL MATCH (n)-[r]-(m:Entity)
            WHERE m.document_id = {document.id} AND r.document_id = {document.id}
            WITH n, count(DISTINCT r) AS degree
            RETURN n.name AS entity_name,
                n.label AS label,
                degree
            ORDER BY degree DESC, entity_name ASC
            LIMIT 10
        """.strip()

    if intent == "ranking_influence":
        return f"""
            MATCH (n:Entity)
            WHERE n.document_id = {document.id}
            OPTIONAL MATCH (n)-[r]-(m:Entity)
            WHERE m.document_id = {document.id} AND r.document_id = {document.id}
            WITH n, count(r) AS influence_score
            RETURN n.name AS entity_name,
                n.label AS label,
                influence_score
            ORDER BY influence_score DESC, entity_name ASC
            LIMIT 10
        """.strip()

    return None


def _escape(value: Any) -> str:
    """
    Escape a string for safe interpolation into a Cypher string literal.
    """
    return str(value or "").replace("\\", "\\\\").replace('"', '\\"')
