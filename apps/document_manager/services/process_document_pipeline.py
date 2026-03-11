from .logger import log_stage

from .text_extractor import extract_text
from .chunker import chunk_text
from .entity_extractor import extract_entities
from .relation_extractor import extract_relations
from .graph_builder import build_graph

def process_document_pipeline(document):
    
    file_path = document.file.path
    log_stage(document, "TEXT_EXTRACTION", "Starting text extraction")
    text = extract_text(file_path)
    log_stage(document, "TEXT_EXTRACTION", "Text extraction finished")
    chunks = chunk_text(text)
    log_stage(document, "CHUNKING", f"{len(chunks)} chunks created")
    entities = extract_entities(chunks, document.llm_used)
    log_stage(document, "ENTITY_EXTRACTION", f"{len(entities)} entities extracted")
    relations = extract_relations(chunks, document.llm_used)
    log_stage(document, "RELATION_EXTRACTION", f"{len(relations)} relation observed")
    graph = build_graph(entities, relations)
    log_stage(document, "GRAPH_BUILDING", f"Graph Created")

    return {
        "graph": graph,
        "nodes": len(graph["nodes"]),
        "edges": len(graph["edges"]),
        "relations": len(set([e["type"] for e in graph["edges"]]))
    }