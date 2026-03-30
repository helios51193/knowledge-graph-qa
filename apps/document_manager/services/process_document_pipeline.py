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
from .logger import log_stage, update_progress
from .normalization.entity_resolver import (
    apply_entity_resolution_to_relations,
    resolve_entities,
)
from ..models import Document

def process_document_pipeline(document:Document):
    
   text = extract_text(document)
   update_progress(document, 10)

   normalized_text = normalize_document_text(document, text)
   update_progress(document, 20)
   
   original_chunks = chunk_text(document, normalized_text)
   update_progress(document, 30)
   
   coreference_result = resolve_coreferences(document, normalized_text)
   analysis_chunks = _build_relation_chunks(
        document=document,
        original_chunks=original_chunks,
        resolved_text=coreference_result["resolved_text"],
    )
   relation_chunks = _build_adjacent_relation_windows(analysis_chunks)
   update_progress(document, 45)

   entities = extract_entities(original_chunks, document.llm_used, document=document)
   update_progress(document, 60)

   relations = extract_relations(relation_chunks, entities, llm=document.llm_used, document=document)
   update_progress(document, 75)

   log_stage(document, "ENTITY_RESOLUTION", "Starting entity normalization")

   resolved_entities, canonical_map, label_summary = resolve_entities(entities)
   resolved_relations = apply_entity_resolution_to_relations(relations, canonical_map)

   log_stage(document, "ENTITY_RESOLUTION", "Entity normalization completed")
   update_progress(document, 85)
    
   graph = build_graph(resolved_entities, resolved_relations)
   update_progress(document, 90)

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

def _build_adjacent_relation_windows(chunks):
    if not chunks:
        return []

    windows = []

    for idx, chunk in enumerate(chunks):
        next_chunk = chunks[idx + 1] if idx + 1 < len(chunks) else None

        if next_chunk is None:
            windows.append(chunk)
            continue

        combined_text = f"{chunk.text} {next_chunk.text}".strip()

        combined_analysis_text = " ".join(
            part for part in [
                chunk.analysis_text or chunk.text,
                next_chunk.analysis_text or next_chunk.text,
            ]
            if part
        ).strip()

        windows.append(
            Chunk(
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                text=combined_text,
                start_index=chunk.start_index,
                end_index=next_chunk.end_index,
                analysis_text=combined_analysis_text,
                source_chunk_ids=[chunk.chunk_id, next_chunk.chunk_id],
            )
        )

    return windows