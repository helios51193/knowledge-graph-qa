# Knowledge Graph QA System - Project Context

## Purpose of this Document

This document describes the current architecture, implemented modules, and near-term direction of the Knowledge Graph QA System.

The goal is to help a developer or autonomous agent understand:

- what the system does today
- how the main modules are organized
- how the ingestion pipeline works
- how graph data is stored and queried
- how the QA layer currently works
- what the main limitations and next steps are

This document reflects the project as it is currently implemented, while also noting important architectural intent where relevant.

---

# System Overview

This project is a Django-based knowledge graph question-answering platform built around a document ingestion pipeline and a Memgraph-backed query layer.

Users can:

- sign up and log in
- upload documents
- process documents asynchronously
- extract entities and relationships from document text
- generate a graph representation from that extracted data
- store the graph both in Django and in Memgraph
- ask natural language questions about a processed document

The overall architecture follows a Graph-RAG style workflow:

Document  
-> Text processing  
-> Entity and relation extraction  
-> Graph generation  
-> Graph storage  
-> Natural language question answering via Cypher + LLM

---

# Technology Stack

## Backend

- Python
- Django

## Frontend

- Jinja templates via `django-jinja`
- HTMX
- Alpine.js
- Tailwind CSS
- DaisyUI

## Graph Database

- Memgraph
- Cypher query language
- `gqlalchemy` for database interaction

## AI Layer

Currently supported LLM choices in the app:

- GPT-4 style OpenAI-backed extraction / QA
- Local Llama via Ollama

## Background Processing

- Celery
- Redis as broker/result backend

---

# Project Structure

All Django apps are under `apps/`.

Primary apps:

- `apps/auth_manager`
- `apps/document_manager`

The main implementation currently lives in `document_manager`, which contains:

- views and routes
- upload and processing flow
- ingestion pipeline services
- graph building
- graph database integration
- QA engine

Service modules are organized by responsibility, including:

- `services/extraction`
- `services/normalization`
- `services/chunking`
- `services/entity_extraction`
- `services/relation_extraction`
- `services/graph_building`
- `services/qa`

---

# Authentication System

The `auth_manager` app handles authentication.

Responsibilities:

- user signup
- user login
- user logout
- session-backed authentication views and templates

The project uses a custom user model based on email login.

---

# Document Manager

The `document_manager` app is the core application.

Responsibilities include:

- document upload
- document ownership and storage
- process-state tracking
- asynchronous ingestion
- graph generation
- graph persistence
- question answering over the generated graph

Documents are scoped to users, so each user sees only their own uploaded documents in the application layer.

---

# Document Model

Each uploaded document is stored in the database.

Important fields include:

- `user` - owner of the document
- `name` - document name
- `file` - uploaded file
- `llm_used` - chosen LLM option
- `status` - pending / processing / complete / error
- `nodes` - total number of graph nodes generated
- `edges` - total number of graph edges generated
- `relations` - count of distinct relation types
- `processing_time` - total processing time in seconds
- `error_message` - failure message if processing fails
- `graph_data` - JSON representation of the generated graph
- `created_at` - upload timestamp

The `graph_data` field acts as the Django-side serialized version of the document graph.

---

# Processing Log Model

Pipeline progress is tracked using `ProcessingLog`.

Each log entry stores:

- document reference
- pipeline stage
- message
- timestamp

Typical stages include:

- START
- TEXT_EXTRACTION
- NORMALIZATION
- CHUNKING
- ENTITY_EXTRACTION
- RELATION_EXTRACTION
- GRAPH_BUILDING
- GRAPH_DATABASE
- COMPLETE
- ERROR

These logs help debug asynchronous document processing.

---

# Frontend Architecture

The frontend is server-rendered and HTMX-enhanced.

Current UI responsibilities include:

- document dashboard
- upload modal
- document table refresh
- process trigger
- QA form and answer display

The dashboard is the main working surface for the user. It currently supports:

- listing uploaded documents
- processing documents
- asking questions against a selected document graph

---

# Current User Flow

## Upload Flow

The upload flow works as follows:

User opens upload modal  
-> User submits document form  
-> Django stores file and metadata  
-> Dashboard refreshes document list

## Processing Flow

The processing flow works as follows:

User clicks Process  
-> Django marks document as processing  
-> Celery task starts  
-> Text is extracted and normalized  
-> Text is chunked  
-> Entities are extracted  
-> Relations are extracted  
-> Graph is built  
-> Graph is saved to `graph_data`  
-> Counts are updated on the `Document` model  
-> Graph is inserted into Memgraph  
-> Document status becomes complete

## QA Flow

The QA flow works as follows:

User selects a document id and asks a question  
-> QA engine builds graph schema context from `graph_data`  
-> LLM generates a read-only Cypher query  
-> Cypher is validated for safety  
-> Query is executed against Memgraph  
-> If execution fails, a repair prompt is used to generate corrected Cypher  
-> Result rows are converted into a natural-language answer  
-> Answer is rendered back into the dashboard

---

# Document Processing Pipeline

The current pipeline is:

Document Upload  
-> Text Extraction  
-> Text Normalization  
-> Text Chunking  
-> Entity Extraction  
-> Relation Extraction  
-> Graph Building  
-> Save Graph Data to Django  
-> Insert Graph into Memgraph

This pipeline is implemented as a set of service modules.

---

# Text Extraction

The system supports extracting text from:

- pdf
- txt
- md

Extraction is implemented through a factory-based extractor system.

Current extractor pattern:

- base extractor interface
- extension-based factory selection
- extractor implementation per file type

This keeps extraction modular and easy to extend.

---

# Text Normalization

Extracted text is normalized before chunking.

Normalization currently includes:

- Unicode normalization
- whitespace cleanup
- blank-line cleanup
- fixing common PDF line-break artifacts

The goal is to make chunking and extraction more stable.

---

# Text Chunking

Normalized text is split into chunks before extraction.

Currently implemented chunking strategies:

- word
- sentence
- paragraph

The strategy is controlled through Django settings.

Chunk objects include:

- `chunk_id`
- `document_id`
- `text`
- `start_index`
- `end_index`

This metadata is carried forward into extraction results.

---

# Entity Extraction

Entity extraction is implemented using a factory-based design.

Current extractor options:

- heuristic extractor
- LLM extractor

## Heuristic Entity Extraction

The heuristic extractor uses hand-written rules and pattern matching.

Characteristics:

- fast
- cheap
- easy to debug
- domain-sensitive
- less flexible across very different document styles

## LLM Entity Extraction

The LLM extractor supports:

- OpenAI-backed extraction
- local Llama extraction through Ollama

The LLM extractor:

- prompts the model for structured JSON
- parses JSON safely
- normalizes extracted entities
- deduplicates repeated entities

Entity output is normalized into a consistent internal structure including:

- `label`
- `name`
- `document_id`
- `chunk_id`
- `start_index`
- `end_index`
- `source_text`

---

# Relation Extraction

Relation extraction follows the same pattern as entity extraction.

Current extractor options:

- heuristic extractor
- LLM extractor

## Heuristic Relation Extraction

The heuristic relation extractor uses explicit phrase-based rules.

Characteristics:

- simple baseline
- easy to reason about
- best suited for predictable text
- weaker across highly varied domains

## LLM Relation Extraction

The LLM relation extractor supports:

- OpenAI-backed relation extraction
- local Llama relation extraction through Ollama

The LLM is given:

- the chunk text
- the entities already identified in that chunk

It returns structured JSON relations, which are then normalized into a consistent relation shape.

Relation output includes:

- `source`
- `source_label`
- `target`
- `target_label`
- `type`
- `document_id`
- `chunk_id`
- `start_index`
- `end_index`
- `source_text`

---

# Graph Building

After extraction, entities and relations are converted into an in-memory graph representation.

The graph builder currently:

- deduplicates nodes
- deduplicates edges
- assigns a stable node id shape
- produces node and edge collections
- computes graph counts

The resulting graph structure looks like:

```json
{
  "nodes": [
    {
      "id": "3:Location:Whisperwood",
      "name": "Whisperwood",
      "label": "Location",
      "document_id": 3
    }
  ],
  "edges": [
    {
      "source": "3:Character:Elarin",
      "target": "3:Location:Whisperwood",
      "source_name": "Elarin",
      "target_name": "Whisperwood",
      "type": "LIVES_IN",
      "document_id": 3
    }
  ],
  "counts": {
    "nodes": 10,
    "edges": 14,
    "relation_types": 4
  }
}
