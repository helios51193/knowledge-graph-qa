def build_graph(entities, relations):

    nodes = []
    edges = []

    for entity in entities:
        nodes.append(entity)

    for rel in relations:
        edges.append(rel)

    return {
        "nodes": nodes,
        "edges": edges
    }