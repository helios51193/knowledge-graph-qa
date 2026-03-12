# Knowledge Graph QA System – Project Context

## Purpose of this Document

This document provides a complete description of the system architecture, modules, and data processing pipeline for the Knowledge Graph QA System.

The goal of this document is to ensure that a developer or autonomous agent can understand:

- the system architecture
- responsibilities of each module
- the document ingestion pipeline
- how the graph is generated
- how components interact

The document prioritizes **clarity and completeness over presentation**.

---

# System Overview

This project is a **knowledge graph question-answering platform** built with Django and Memgraph.

The system allows users to upload documents. These documents are processed into a **knowledge graph** by extracting entities and relationships from the text.

Users can then ask **natural language questions** about the graph. The system converts the question into a **Cypher query**, executes it against Memgraph, and returns a natural language answer.

The system demonstrates a **Graph-RAG architecture**, where structured graph data is used together with LLM reasoning.

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

## AI Layer

Planned LLM providers:

- GPT-4
- Llama 3
- Mistral

## Background Processing

- Celery
- Redis (broker)

---

# Project Structure

All Django apps are located inside the `apps` directory.
- apps/
  - auth_manager/
  - document_manager/

Each app encapsulates a specific domain of the system.

---

# Authentication System

The `auth_manager` application manages authentication.

Responsibilities:

- user login
- user logout
- session management
- authentication templates

Authentication logic is isolated so other apps remain independent.

---

# Template System

The system uses **Jinja templates** through `django-jinja`.

This replaces Django’s default template engine.

Benefits:

- more expressive template syntax
- better control over rendering
- easier component reuse

---

# Frontend Architecture

Frontend uses server-rendered templates enhanced with HTMX.

Technologies used:

- Tailwind CSS
- DaisyUI
- HTMX
- Alpine.js

Templates are organized as reusable components.

Example structure:

templates/
 - document_manager
    - base.jinja
    - dashboard.jinja 
    - components/
      - document_table.jinja
      - upload_modal.jinja

---

# Static Files

Compiled frontend assets are stored in a centralized static directory.

Example:
- static/
  - css/
    - styles.css

Tailwind compiles CSS into this directory.

---

# Document Manager

The `document_manager` app is responsible for handling uploaded documents and converting them into knowledge graphs.

Responsibilities include:

- document upload
- file storage
- document metadata management
- tracking processing state
- running background processing tasks
- generating graph-ready data
- storing intermediate graph structures

Documents are **scoped to users**, meaning each user only sees their own documents.

---

# Document Model

Each uploaded document is stored in the database.

Fields include:

- `user` — owner of the document
- `name` — document name
- `file` — uploaded file
- `llm_used` — LLM selected for extraction
- `status` — processing state
- `nodes` — number of nodes generated
- `edges` — number of edges generated
- `relations` — number of relation types
- `processing_time` — time taken for processing
- `error_message` — error message if processing fails
- `graph_data` — intermediate graph structure (JSON)
- `created_at` — upload timestamp

---

# Document Status Lifecycle

Documents move through several states during processing.

Possible values:
 - pending
 - processing
 - complete
 - error

Descriptions:

**pending**  
Document uploaded but not yet processed.

**processing**  
Celery worker is currently processing the document.

**complete**  
Graph generation finished successfully.

**error**  
Processing failed and an error message is stored.

---

# Processing Logs

Each stage of the processing pipeline produces log entries.

Logs are stored in a `ProcessingLog` model.

Each log entry contains:

- document reference
- processing stage
- message
- timestamp

Example stages:
  - START
  - TEXT_EXTRACTION
  - NORMALIZATION
  - CHUNKING
  - COMPLETE
  - ERROR


These logs provide traceability and debugging information for asynchronous tasks.

---

# Document Dashboard

The dashboard shows all documents belonging to the logged-in user.

Displayed information:

- document name
- number of nodes
- number of edges
- number of relations
- selected LLM
- processing status

The dashboard loads document data dynamically using HTMX.

Example:
hx-get={{document_manager:document_list}}
hx-trigger="load"


---

# Document Upload Flow

The upload process works as follows.
User opens upload modal
↓
User submits form
↓
Server stores file and metadata
↓
Dashboard refreshes document list
↓
User can start processing

Upload is handled using HTMX forms.

---

# Background Processing

Document processing is performed asynchronously using Celery.

Workflow:
User clicks Process
↓
Django view triggers Celery task
↓
Celery worker executes pipeline
↓
Graph representation generated
↓
Document status updated


This prevents long-running tasks from blocking HTTP requests.

---

# Document Processing Pipeline

Uploaded documents are processed through a structured pipeline.

Document Upload
↓
Text Extraction
↓
Text Normalization
↓
Text Chunking
↓
Chunk Metadata Generation
↓
Entity Extraction (LLM)
↓
Relationship Extraction (LLM)
↓
Graph Structure Generation
↓
Cypher Generation
↓
Insertion into Memgraph

Each stage is implemented as a **separate module**.

---

# Text Extraction

The text extraction stage converts files into raw text.

Currently supported formats:

 - pdf
 - txt
 - md

Extraction uses a **pluggable extractor system**.

Example extractors:

  - PdfExtractor
  - TxtExtractor
  - MarkdownExtractor

The correct extractor is selected automatically based on file extension.

---

# Text Normalization

Extracted text is cleaned before further processing.

Normalization performs:

- unicode normalization
- whitespace normalization
- removal of repeated blank lines
- correction of PDF line breaks

Example issue:

Artificial intelligence is transforming
the world.


Normalized result:


Artificial intelligence is transforming the world.


---

# Text Chunking

Normalized text is split into smaller segments called **chunks**.

Chunking is required because LLMs cannot process extremely long text.

Supported chunking strategies:

- word
- sentence
- paragraph

The chunking strategy is configurable via Django settings.

Example configuration:

DOCUMENT_CHUNKER = "word"
CHUNK_SIZE = 200
CHUNK_OVERLAP = 20

---

# Chunk Metadata

Each chunk includes metadata describing its origin.

Chunk structure:
chunk_id
document_id
text
start_index
end_index

Metadata enables:

- tracing extracted entities to source text
- debugging extraction results
- supporting future retrieval features

Chunks are passed to the LLM extraction stage.

---

# Graph Representation (Future Module)

Before inserting data into Memgraph, the extracted entities and relationships are converted into a graph representation.

Example structure:
`
{
  "nodes": [
    {"label": "Person", "name": "Alice"},
    {"label": "Company", "name": "OpenAI"}
  ],
  "edges": [
    {"source": "Alice", "target": "OpenAI", "type": "WORKS_AT"}
  ]
}
`
This intermediate structure is stored in the `graph_data` field.

---

# Graph Manager (Future Module)

The graph manager will handle all interaction with Memgraph.

Responsibilities:

- database connection
- Cypher query execution
- schema inspection
- graph updates

---

# QA Engine (Future Module)

The QA engine will handle natural language questions.

Responsibilities:

- convert user question into Cypher query
- execute query on graph database
- generate natural language response

---

# Long-Term Goals

The system is designed to demonstrate practical experience in:

- knowledge graph engineering
- graph database integration
- Graph-RAG architectures
- LLM pipeline design
- backend system architecture
- modular Django application design

The final system should function as a lightweight platform for building and querying knowledge graphs using natural language.