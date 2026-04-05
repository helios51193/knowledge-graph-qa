from typing import Any


def build_graph(
    entities: list[dict[str, Any]],
    relations: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Build a serialized graph structure from resolved entities and relations.

    The resulting graph is suitable for:
    - storing in `Document.graph_data`
    - rendering in the QA graph viewer
    - persisting into Memgraph
    """
    node_index: dict[tuple[int, str, str], dict[str, Any]] = {}
    edge_index: set[tuple[int, str, str, str]] = set()
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []

    for entity in entities:
        entity_name = entity.get("canonical_name", entity["name"])
        entity_label = entity.get("canonical_label", entity["label"])
        key = (
            entity["document_id"],
            entity_name.strip().lower(),
            entity_label.strip(),
        )

        if key in node_index:
            continue

        node = {
            "id": f'{entity["document_id"]}:{entity_label}:{entity_name}',
            "name": entity_name,
            "original_name": entity["name"],
            "aliases": entity.get("aliases", [entity["name"]]),
            "label": entity_label,
            "label_counts": entity.get("label_counts", {}),
            "document_id": entity["document_id"],
            "chunk_id": entity.get("chunk_id"),
            "start_index": entity.get("start_index"),
            "end_index": entity.get("end_index"),
            "provenance": {
                "chunk_id": entity.get("chunk_id"),
                "start_index": entity.get("start_index"),
                "end_index": entity.get("end_index"),
                "source_text": entity.get("source_text", ""),
            },
        }

        node_index[key] = node
        nodes.append(node)

    for relation in relations:
        edge_key = (
            relation["document_id"],
            relation["source"].strip().lower(),
            relation["target"].strip().lower(),
            relation["type"].strip().upper(),
        )

        if edge_key in edge_index:
            continue

        source_node = _find_node(
            nodes,
            relation["document_id"],
            relation["source"],
            relation.get("source_label"),
        )
        target_node = _find_node(
            nodes,
            relation["document_id"],
            relation["target"],
            relation.get("target_label"),
        )

        if source_node is None or target_node is None:
            continue

        # Skip self-loop edges created by identical resolved endpoints.
        if source_node["id"] == target_node["id"]:
            continue

        edge = {
            "id": f'{source_node["id"]}-{relation["type"].strip().upper()}-{target_node["id"]}',
            "source": source_node["id"],
            "target": target_node["id"],
            "source_name": relation["source"],
            "target_name": relation["target"],
            "source_label": relation.get("source_label", "Entity"),
            "target_label": relation.get("target_label", "Entity"),
            "type": relation["type"].strip().upper(),
            "document_id": relation["document_id"],
            "chunk_id": relation.get("chunk_id"),
            "start_index": relation.get("start_index"),
            "end_index": relation.get("end_index"),
            "provenance": {
                "chunk_id": relation.get("chunk_id"),
                "start_index": relation.get("start_index"),
                "end_index": relation.get("end_index"),
                "source_text": relation.get("source_text", ""),
            },
        }

        edge_index.add(edge_key)
        edges.append(edge)

    return {
        "nodes": nodes,
        "edges": edges,
        "counts": {
            "nodes": len(nodes),
            "edges": len(edges),
            "relation_types": len({edge["type"] for edge in edges}),
        },
    }


def _find_node(
    nodes: list[dict[str, Any]],
    document_id: int,
    name: str,
    label: str | None = None,
) -> dict[str, Any] | None:
    """
    Find a graph node by document, normalized name, and optional label.
    """
    normalized_name = name.strip().lower()
    normalized_label = label.strip() if label else None

    for node in nodes:
        if node["document_id"] != document_id:
            continue

        if node["name"].strip().lower() != normalized_name:
            continue

        if normalized_label and node["label"].strip() != normalized_label:
            continue

        return node

    return None
