import re
from typing import Any

from django.conf import settings
from gqlalchemy import Memgraph

from ..models import Document


def save_graph_to_database(document: Document, graph_data: dict[str, Any]) -> None:
    """
    Replace the current document's graph in Memgraph with the latest graph data.

    The normal behavior is document-scoped replacement: delete the existing graph
    for this document and then insert the regenerated nodes and edges.
    """
    memgraph = Memgraph(
        host=settings.MG_HOST,
        port=int(settings.MG_PORT),
    )

    if getattr(settings, "CLEAR_GRAPH_BEFORE_INSERT", False):
        clear_database(memgraph)

    _delete_existing_document_graph(memgraph, document.id)
    _create_nodes(memgraph, graph_data.get("nodes", []))
    _create_edges(memgraph, graph_data.get("edges", []))


def clear_database(memgraph: Memgraph) -> None:
    """
    Delete the entire graph from Memgraph.

    This is a destructive development/debug helper and should not be used as the
    normal persistence strategy for document reprocessing.
    """
    memgraph.execute("MATCH (n) DETACH DELETE n")


def _delete_existing_document_graph(memgraph: Memgraph, document_id: int) -> None:
    """
    Remove all nodes and attached edges for a single document.
    """
    query = """
    MATCH (n:Entity {document_id: $document_id})
    DETACH DELETE n
    """
    memgraph.execute(query, {"document_id": document_id})


def _create_nodes(memgraph: Memgraph, nodes: list[dict[str, Any]]) -> None:
    """
    Insert or update graph nodes for a document in Memgraph.

    A stable application-level identifier is stored as `graph_id` so QA results
    can be aligned with frontend Cytoscape node ids.
    """
    query = """
    MERGE (n:Entity {
        document_id: $document_id,
        name: $name,
        label: $label
    })
    SET n.chunk_id = $chunk_id,
        n.graph_id = $graph_id,
        n.start_index = $start_index,
        n.end_index = $end_index
    """

    for node in nodes:
        memgraph.execute(
            query,
            {
                "graph_id": node["id"],
                "document_id": node["document_id"],
                "name": node["name"],
                "label": node["label"],
                "chunk_id": node.get("chunk_id"),
                "start_index": node.get("start_index"),
                "end_index": node.get("end_index"),
            },
        )


def _create_edges(memgraph: Memgraph, edges: list[dict[str, Any]]) -> None:
    """
    Insert or update graph edges for a document in Memgraph.
    """
    for edge in edges:
        relation_type = _sanitize_relationship_type(edge["type"])

        query = f"""
        MATCH (source:Entity {{
            document_id: $document_id,
            name: $source_name,
            label: $source_label
        }})
        MATCH (target:Entity {{
            document_id: $document_id,
            name: $target_name,
            label: $target_label
        }})
        MERGE (source)-[r:{relation_type}]->(target)
        SET r.chunk_id = $chunk_id,
            r.start_index = $start_index,
            r.end_index = $end_index,
            r.document_id = $document_id
        """

        memgraph.execute(
            query,
            {
                "document_id": edge["document_id"],
                "source_name": edge["source_name"],
                "source_label": edge["source_label"],
                "target_name": edge["target_name"],
                "target_label": edge["target_label"],
                "chunk_id": edge.get("chunk_id"),
                "start_index": edge.get("start_index"),
                "end_index": edge.get("end_index"),
            },
        )


def _sanitize_relationship_type(value: str) -> str:
    """
    Convert an arbitrary relation label into a safe Cypher relationship type.
    """
    cleaned = re.sub(r"[^A-Za-z0-9_]", "_", value.strip().upper())
    cleaned = re.sub(r"_+", "_", cleaned)

    if not cleaned:
        return "RELATED_TO"

    if cleaned[0].isdigit():
        cleaned = f"REL_{cleaned}"

    return cleaned


def execute_read_query(query: str) -> list[dict[str, Any]]:
    """
    Execute a read-only query against Memgraph and return the fetched rows.
    """
    memgraph = Memgraph(
        host=settings.MG_HOST,
        port=int(settings.MG_PORT),
    )

    return list(memgraph.execute_and_fetch(query))
