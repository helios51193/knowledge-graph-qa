# Knowledge Graph QA System - Project Context

## Purpose of this Document

This document describes the current architecture, implemented modules, UI structure, and near-term direction of the Knowledge Graph QA System.

The goal is to help a developer or autonomous agent understand:

- what the system does today
- how the main Django apps and service layers are organized
- how document ingestion works end to end
- how graph data is stored and queried
- how the QA layer currently operates
- how the current UI is structured
- what the most important limitations and next steps are

This document reflects the project as it is currently implemented.

---

# System Overview

This project is a Django-based knowledge graph question-answering platform built around:

- document ingestion
- entity and relation extraction
- graph generation
- graph persistence in Django and Memgraph
- natural language question answering over the generated graph

Users can:

- sign up and log in
- upload documents
- process documents asynchronously
- generate a graph from unstructured text
- store that graph in both `graph_data` and Memgraph
- open a dedicated QA page for a processed document
- ask natural language questions against that document graph
- view the graph in a visual panel while querying it

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
- Cytoscape.js for graph visualization

## Graph Database

- Memgraph
- Cypher query language
- `gqlalchemy` for database interaction

## AI Layer

Currently supported LLM choices in the app:

- OpenAI-backed GPT-style extraction and QA
- local Llama via Ollama

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

- routes and views
- upload and processing flow
- ingestion pipeline services
- graph building
- graph database integration
- QA engine
- UI templates for dashboard and QA

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
- graph-aware QA UI

Documents are scoped to users at the application layer, so each user sees only their own uploaded documents.

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

The `graph_data` field acts as the Django-side serialized version of the document graph and is also used to drive the graph viewer on the QA page.

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

Current UI surfaces include:

- dashboard
- upload modal
- document table
- dedicated QA page

## Dashboard

The dashboard currently supports:

- listing uploaded documents
- showing node/edge/relation counts
- showing process status
- starting document processing
- deleting documents
- opening a dedicated QA page for a selected document

## Dedicated QA Page

The QA experience now lives on a dedicated page per document.

Current layout:

- left panel: chat-style QA thread
- right panel: graph viewer

The left side is the primary interaction surface for:

- entering questions
- showing answer messages
- showing generated Cypher
- showing raw query results when needed

The right side currently renders the document graph visually using Cytoscape.js.

This creates a stronger document-specific QA experience than placing QA directly on the dashboard.

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

The QA flow currently works as follows:

User opens the QA page for a document  
-> User asks a natural language question  
-> QA engine builds graph schema context from `graph_data`  
-> LLM generates a read-only Cypher query  
-> Cypher is validated for safety  
-> Query is executed against Memgraph  
-> If execution fails, a repair prompt generates corrected Cypher  
-> Result rows are converted into a natural-language answer  
-> The answer is appended to the chat thread  
-> The graph remains visible in the adjacent graph panel

---

# Document Processing Pipeline

The current ingestion pipeline is:

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
      "source": "3:Person:Elarin",
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
```

This structure is stored in `document.graph_data`.

---

# Graph Persistence

Graph data is persisted in two places.

## Django Database

The serialized graph is stored in `Document.graph_data`.

Additional summary values are also stored:

- `nodes`
- `edges`
- `relations`

This gives the app a quick summary view of processing results and also supplies the data needed for the graph viewer.

## Memgraph

The graph is also inserted into Memgraph.

Current graph conventions in Memgraph:

- all nodes use label `:Entity`
- semantic type is stored in node property `label`
- relationships use typed edges such as `WORKS_AT`, `LIVES_IN`, `ALLY_OF`, etc.
- both nodes and edges are scoped using `document_id`

The graph insertion service can also clear the graph database before insertion if configured to do so, though that behavior is primarily useful during development and should be used carefully.

---

# Graph Database Layer

The graph database service handles Memgraph interaction.

Current responsibilities:

- create Memgraph connection
- optionally clear database
- delete existing graph for a single document
- create nodes
- create edges
- execute read queries for QA

This service is the bridge between the ingestion pipeline and the QA layer.

---

# QA Engine

The QA engine is implemented and working.

It is responsible for:

- building a schema summary from the document graph
- generating a Cypher query from a natural language question
- validating that the generated query is read-only
- executing the query against Memgraph
- repairing Cypher if execution fails
- generating a natural-language answer from result rows

## QA Design Principles

The QA layer currently follows these rules:

- every query must be scoped to one document
- only read-only Cypher is allowed
- dangerous Cypher operations are blocked
- prompts use actual graph schema instead of hardcoded domain assumptions
- name matching prefers case-insensitive Cypher patterns
- answer generation is phrased naturally but remains grounded in the graph result

## Cypher Repair

If generated Cypher fails to execute, the system performs a repair step.

The repair flow is:

Original question  
-> Generated Cypher  
-> Memgraph error  
-> Repair prompt with bad query + error message  
-> Corrected Cypher  
-> Query execution retry

This improves robustness against common LLM query mistakes.

---

# Graph Viewer

The dedicated QA page now includes a graph viewer built with Cytoscape.js.

Current capabilities:

- render nodes and edges from `document.graph_data`
- color nodes by entity type
- display relation labels on edges
- reset the graph view with a dedicated button
- show a legend for the current entity color mapping

Current state:

- graph rendering is implemented
- the graph and chat interface are visible side by side
- graph highlighting based on QA results is not yet implemented

The graph panel is intended to become the visual companion to the QA thread, eventually highlighting the relevant subgraph used to answer a question.

---

# Prompting Strategy

The system currently uses LLMs in three major places:

- entity extraction
- relation extraction
- QA query generation and answer generation

Prompting is designed to be:

- structured
- JSON-oriented where extraction is involved
- read-only and safety-constrained where Cypher is involved
- grounded in graph schema where QA is involved

The QA prompt has been made more generic so it can work with non-business domains such as fantasy, narrative, or mixed-content documents.

---

# Testing Direction

The project is beginning to add test coverage around the end-to-end pipeline.

The intended testing strategy is:

- use Django `TestCase` for application-level testing
- use real Django models and uploaded files in tests
- mock external boundaries such as Memgraph writes and LLM calls
- cover both ingestion flow and QA flow

Current testing priorities include:

- pipeline completion and document field updates
- processing log creation
- graph generation correctness
- QA query generation and repair behavior

---

# Current Strengths

The project now has a working vertical slice across ingestion, graph creation, QA, and UI.

Implemented strengths include:

- modular pipeline design
- pluggable extractor/factory pattern
- support for heuristic and LLM extraction
- graph serialization into Django
- Memgraph insertion
- natural-language question answering over the graph
- Cypher safety validation
- Cypher repair on query execution failure
- more natural answer tone while remaining grounded
- dedicated document QA page
- integrated graph visualization using Cytoscape.js

---

# Current Limitations

Important current limitations include:

- extraction quality still depends heavily on document style and chunk quality
- heuristic extraction remains brittle across very different domains
- LLM extraction may still produce incomplete or imperfect graph structure
- QA may return shallow answers if the graph itself is sparse
- graph highlighting from QA results is not yet implemented
- query repair currently handles execution errors, but not yet weak or empty-result recovery
- graph clearing behavior should be used carefully in multi-document scenarios
- tests are still being expanded and stabilized

---

# Near-Term Next Steps

Likely next improvements are:

- graph highlighting based on QA results
- empty-but-suspicious QA result recovery
- better QA thread persistence
- stronger automated test coverage
- safer multi-document graph coexistence
- improved extraction prompts and normalization
- confidence scoring or better answer provenance
- hybrid extraction strategies where useful

---

# Long-Term Goals

The long-term goal is to build a lightweight but capable platform for:

- ingesting unstructured documents
- transforming them into knowledge graphs
- storing and querying those graphs efficiently
- answering natural language questions over graph structure
- visually exploring the graph while asking questions
- demonstrating practical Graph-RAG architecture patterns

The project is also intended to serve as a hands-on system for learning and demonstrating:

- knowledge graph engineering
- graph database integration
- LLM pipeline design
- prompt engineering for structured extraction
- question answering over symbolic graph data
- graph-aware application UI design
- modular Django application architecture
