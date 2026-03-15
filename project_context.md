# Knowledge Graph QA System - Target Architecture

## Purpose of this Document

This document describes the intended target architecture, planned modules, and desired data processing pipeline for the Knowledge Graph QA System.

The goal of this document is to ensure that a developer or autonomous agent can understand:

- the intended system architecture
- the responsibilities of each module
- the desired document ingestion pipeline
- how the graph should be generated
- how components are expected to interact

The document prioritizes **clarity and completeness over presentation**.

This is primarily a **target-state design document**, not a guarantee that every module or workflow described here is already implemented in code.

---

# System Overview

This project is intended to become a **knowledge graph question-answering platform** built with Django and Memgraph.

The system is designed to allow users to upload documents. These documents will be processed into a **knowledge graph** by extracting entities and relationships from the text.

Users will then be able to ask **natural language questions** about the graph. The system will convert the question into a **Cypher query**, execute it against Memgraph, and return a natural language answer.

The system is intended to demonstrate a **Graph-RAG architecture**, where structured graph data is used together with LLM reasoning.

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

The `auth_manager` application is intended to manage authentication.

Responsibilities:

- user login
- user logout
- session management
- authentication templates

Authentication logic is intended to remain isolated so other apps can stay independent.

---

# Template System

The system is designed to use **Jinja templates** through `django-jinja` as the primary template layer.

Jinja is intended to be the main rendering approach, even if Django's default template engine may still remain enabled for compatibility where needed.

Benefits:

- more expressive template syntax
- better control over rendering
- easier component reuse

---

# Frontend Architecture

The frontend is intended to use server-rendered templates enhanced with HTMX.

Technologies used:

- Tailwind CSS
- DaisyUI
- HTMX
- Alpine.js

Templates should be organized as reusable components.

Example structure:

templates/
- document_manager/
- base.jinja
- dashboard.jinja
- components/
- document_table.jinja
- upload_modal.jinja

---

# Static Files

Compiled frontend assets are expected to be stored in a centralized static directory.

Example:

- static/
- css/
- styles.css

Tailwind is expected to compile CSS into this directory.

---

# Document Manager

The `document_manager` app is intended to handle uploaded documents and convert them into knowledge graphs.

Responsibilities include:

- document upload
- file storage
- document metadata management
- tracking processing state
- running background processing tasks
- generating graph-ready data
- storing intermediate graph structures

Documents should be **scoped to users**, meaning each user only sees their own documents.

---

# Document Model

Each uploaded document is expected to be stored in the database.

Fields include:

- `user` - owner of the document
- `name` - document name
- `file` - uploaded file
- `llm_used` - LLM selected for extraction
- `status` - processing state
- `nodes` - number of nodes generated
- `edges` - number of edges generated
- `relations` - number of relation types
- `processing_time` - time taken for processing
- `error_message` - error message if processing fails
- `graph_data` - intermediate graph structure (JSON)
- `created_at` - upload timestamp

---

# Document Status Lifecycle

Documents are expected to move through several states during processing.

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

Each stage of the processing pipeline should produce log entries.

Logs are expected to be stored in a `ProcessingLog` model.

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

These logs are intended to provide traceability and debugging information for asynchronous tasks.

---

# Document Dashboard

The dashboard should show all documents belonging to the logged-in user.

Displayed information:

- document name
- number of nodes
- number of edges
- number of relations
- selected LLM
- processing status

The dashboard is intended to load document data dynamically using HTMX.

Example intent:

```html
hx-get="{{ url('document_manager:document_table') }}"
hx-trigger="load"
```

---

# Document Upload Flow

The intended upload process works as follows:

User opens upload modal  
-> User submits form  
-> Server stores file and metadata  
-> Dashboard refreshes document list  
-> User can start processing

Upload should be handled using HTMX forms.

---

# Background Processing

Document processing is intended to be performed asynchronously using Celery.

Workflow:

User clicks Process  
-> Django view triggers Celery task  
-> Celery worker executes pipeline  
-> Graph representation generated  
-> Document status updated

This design prevents long-running tasks from blocking HTTP requests.

---

# Document Processing Pipeline

Uploaded documents are intended to be processed through a structured pipeline.

Document Upload  
-> Text Extraction  
-> Text Normalization  
-> Text Chunking  
-> Chunk Metadata Generation  
-> Entity Extraction (LLM)  
-> Relationship Extraction (LLM)  
-> Graph Structure Generation  
-> Cypher Generation  
-> Insertion into Memgraph

Each stage should ideally be implemented as a **separate module** to keep the pipeline maintainable and extensible.

---

# Text Extraction

The text extraction stage should convert files into raw text.

Currently intended formats:

- pdf
- txt
- md

Extraction should use a **pluggable extractor system**.

Example extractors:

- PdfExtractor
- TxtExtractor
- MarkdownExtractor

The correct extractor should be selected automatically based on file extension.

---

# Text Normalization

Extracted text should be cleaned before further processing.

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

Normalized text should be split into smaller segments called **chunks**.

Chunking is required because LLMs cannot reliably process extremely long text in a single pass.

Supported chunking strategies:

- word
- sentence
- paragraph

The chunking strategy should be configurable via Django settings.

Example configuration:

```python
DOCUMENT_CHUNKER = "word"
CHUNK_SIZE = 200
CHUNK_OVERLAP = 20
```

---

# Chunk Metadata

Each chunk should include metadata describing its origin.

Chunk structure:

- chunk_id
- document_id
- text
- start_index
- end_index

This metadata enables:

- tracing extracted entities to source text
- debugging extraction results
- supporting future retrieval features

Chunks are then intended to be passed to the LLM extraction stage.

---

# Graph Representation

Before inserting data into Memgraph, the extracted entities and relationships should be converted into a graph representation.

Example structure:

```json
{
  "nodes": [
    {"label": "Person", "name": "Alice"},
    {"label": "Company", "name": "OpenAI"}
  ],
  "edges": [
    {"source": "Alice", "target": "OpenAI", "type": "WORKS_AT"}
  ]
}
```

This intermediate structure is intended to be stored in the `graph_data` field.

---

# Graph Manager

The graph manager is intended to handle all interaction with Memgraph.

Responsibilities:

- database connection
- Cypher query execution
- schema inspection
- graph updates

---

# QA Engine

The QA engine is intended to handle natural language questions.

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
