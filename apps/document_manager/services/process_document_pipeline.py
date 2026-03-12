from .normalization.text_normalizer import normalize_document_text
from .logger import log_stage
from .extraction.text_extractor import extract_text
from .chunking.chunker import chunk_text
from .entity_extractor import extract_entities
from .relation_extractor import extract_relations
from .graph_builder import build_graph

def process_document_pipeline(document):
    
    text = extract_text(document)

    normalized_text = normalize_document_text(document, text)

    chunks = chunk_text(document, normalized_text)

    # entities = extract_entities(chunks, document.llm_used)
    # log_stage(document, "ENTITY_EXTRACTION", f"{len(entities)} entities extracted")
    # relations = extract_relations(chunks, document.llm_used)
    # log_stage(document, "RELATION_EXTRACTION", f"{len(relations)} relation observed")
    # graph = build_graph(entities, relations)
    # log_stage(document, "GRAPH_BUILDING", f"Graph Created")

    print(chunks)

    # res = {
    #     "graph": graph,
    #     "nodes": len(graph["nodes"]),
    #     "edges": len(graph["edges"]),
    #     "relations": len(set([e["type"] for e in graph["edges"]]))
    # }

    res = {}




    return res