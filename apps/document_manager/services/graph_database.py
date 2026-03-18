import re

from django.conf import settings
from gqlalchemy import Memgraph

def save_graph_to_database(document, graph_data):
    memgraph = Memgraph(
        host=settings.MG_HOST,
        port=int(settings.MG_PORT),
    )

    if getattr(settings, "CLEAR_GRAPH_BEFORE_INSERT", False):
        print("Clearing Database")
        clear_database(memgraph)

    _delete_existing_document_graph(memgraph, document.id)
    _create_nodes(memgraph, graph_data.get("nodes", []))
    _create_edges(memgraph, graph_data.get("edges", []))


def clear_database(memgraph):
    memgraph.execute("MATCH (n) DETACH DELETE n")

def _delete_existing_document_graph(memgraph, document_id):
    query = """
    MATCH (n:Entity {document_id: $document_id})
    DETACH DELETE n
    """
    memgraph.execute(query, {"document_id": document_id})

def _create_nodes(memgraph, nodes):
    query = """
    MERGE (n:Entity {
        document_id: $document_id,
        name: $name,
        label: $label
    })
    SET n.chunk_id = $chunk_id,
        n.start_index = $start_index,
        n.end_index = $end_index
    """

    for node in nodes:
        memgraph.execute(
            query,
            {
                "document_id": node["document_id"],
                "name": node["name"],
                "label": node["label"],
                "chunk_id": node.get("chunk_id"),
                "start_index": node.get("start_index"),
                "end_index": node.get("end_index"),
            },
        )

def _create_edges(memgraph, edges):
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

def _sanitize_relationship_type(value):
    cleaned = re.sub(r"[^A-Za-z0-9_]", "_", value.strip().upper())
    cleaned = re.sub(r"_+", "_", cleaned)

    if not cleaned:
        return "RELATED_TO"

    if cleaned[0].isdigit():
        cleaned = f"REL_{cleaned}"

    return cleaned

def execute_read_query(query):
    memgraph = Memgraph(
        host=settings.MG_HOST,
        port=int(settings.MG_PORT),
    )

    return list(memgraph.execute_and_fetch(query))
