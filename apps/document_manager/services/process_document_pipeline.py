from pprint import pprint

from .normalization.text_normalizer import normalize_document_text
from .logger import log_stage
from .extraction.text_extractor import extract_text
from .chunking.chunker import chunk_text
from .entity_extraction.entity_extractor import extract_entities
from .relation_extraction.relation_extractor import extract_relations
from .graph_building.graph_builder import build_graph
from ..models import Document

def process_document_pipeline(document:Document):
    
    text = extract_text(document)

    normalized_text = normalize_document_text(document, text)

    chunks = chunk_text(document, normalized_text)

    entities = extract_entities(chunks, document.llm_used, document=document)
    
    relations = extract_relations(chunks, entities, llm=document.llm_used, document=document)
    
    
    graph = build_graph(entities, relations)

    res = {
       "chunks":chunks,
       "entities":entities,
       "relation":relations,
       "graph":graph
    }

    return res