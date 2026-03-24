from pprint import pprint
from .chunking.chunk import Chunk
from .chunking.factory import get_chunker
from .normalization.text_normalizer import normalize_document_text
from .logger import log_stage
from .coreference.coreference_resolver import resolve_coreferences
from .extraction.text_extractor import extract_text
from .chunking.chunker import chunk_text
from .entity_extraction.entity_extractor import extract_entities
from .relation_extraction.relation_extractor import extract_relations
from .graph_building.graph_builder import build_graph
from .normalization.entity_resolver import (
    apply_entity_resolution_to_relations,
    resolve_entities,
)
from ..models import Document

def process_document_pipeline(document:Document):
    
   text = extract_text(document)

   normalized_text = normalize_document_text(document, text)
   
   original_chunks = chunk_text(document, normalized_text)
   
   coreference_result = resolve_coreferences(document, normalized_text)
   relation_chunks = _build_relation_chunks(
        document=document,
        original_chunks=original_chunks,
        resolved_text=coreference_result["resolved_text"],
    )

   entities = extract_entities(original_chunks, document.llm_used, document=document)
    
   relations = extract_relations(relation_chunks, entities, llm=document.llm_used, document=document)

   log_stage(document, "ENTITY_RESOLUTION", "Starting entity normalization")

   resolved_entities, canonical_map, label_summary = resolve_entities(entities)
   resolved_relations = apply_entity_resolution_to_relations(relations, canonical_map)

   log_stage(document, "ENTITY_RESOLUTION", "Entity normalization completed")
    
   graph = build_graph(resolved_entities, resolved_relations)

   res = {
       "chunks":original_chunks,
       "entities":resolved_entities,
       "relation":resolved_relations,
       "graph":graph,
       "coreference":coreference_result,
       "label_summary": label_summary,
    }

   return res

def _build_relation_chunks(document, original_chunks, resolved_text):
    chunker = get_chunker()
    resolved_chunks = chunker.chunk(resolved_text, document.id)

    if len(original_chunks) != len(resolved_chunks):
        log_stage(
            document,
            "COREFERENCE",
            "Resolved text changed chunk boundaries; falling back to original chunks for relation extraction",
        )
        return original_chunks

    relation_chunks = []

    for original_chunk, resolved_chunk in zip(original_chunks, resolved_chunks):
        relation_chunks.append(
            Chunk(
                chunk_id=original_chunk.chunk_id,
                document_id=original_chunk.document_id,
                text=original_chunk.text,
                start_index=original_chunk.start_index,
                end_index=original_chunk.end_index,
                analysis_text=resolved_chunk.text,
            )
        )

    return relation_chunks