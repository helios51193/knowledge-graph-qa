from apps.llm.factory import get_llm
from apps.graph.memgraph_client import MemgraphClient

def process_document(document):
    document.status = "processing"
    document.save()

    llm = get_llm()
    kg_data = llm.extract_knowledge_graph(document.extracted_text)

    client = MemgraphClient()

    for entity in kg_data["entities"]:
        client.execute(
            """
            MERGE (e:Entity {name: $name, document_id: $doc_id})
            SET e.type = $type
            """,
            {
                "name": entity["name"],
                "type": entity["type"],
                "doc_id": document.id
            }
        )

    for rel in kg_data["relationships"]:
        client.execute(
            """
            MATCH (a:Entity {name: $source, document_id: $doc_id})
            MATCH (b:Entity {name: $target, document_id: $doc_id})
            MERGE (a)-[:RELATIONSHIP {type: $relation, document_id: $doc_id}]->(b)
            """,
            {
                "source": rel["source"],
                "target": rel["target"],
                "relation": rel["relation"],
                "doc_id": document.id
            }
        )

    document.status = "completed"
    document.save()