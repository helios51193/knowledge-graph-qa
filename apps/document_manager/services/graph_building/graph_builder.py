def build_graph(entities, relations):
    node_index = {}
    edge_index = set()
    nodes = []
    edges = []

    for entity in entities:
        entity_name = entity.get("canonical_name", entity["name"])
        key = (
            entity["document_id"],
            entity_name.strip().lower(),
            entity["label"].strip(),
        )

        if key in node_index:
            continue

        node = {
            "id": f'{entity["document_id"]}:{entity["label"]}:{entity_name}',
            "name": entity["name"],
            "label": entity["label"],
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

        source_node = _find_node(nodes, relation["document_id"], relation["source"])
        target_node = _find_node(nodes, relation["document_id"], relation["target"])

        if source_node is None or target_node is None:
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


def _find_node(nodes, document_id, name):
    normalized_name = name.strip().lower()

    for node in nodes:
        if (
            node["document_id"] == document_id
            and node["name"].strip().lower() == normalized_name
        ):
            return node

    return None