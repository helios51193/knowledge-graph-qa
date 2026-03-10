# Knowledge Graph QA System – Project Context

## Overview

This project is a knowledge graph question-answering platform built using Django and Memgraph.

Users can upload documents to the platform. Each document is processed to extract entities and relationships, which are then stored as a knowledge graph.

Users can ask natural language questions about the knowledge graph. A Large Language Model (LLM) converts the question into a Cypher query, executes it on the graph database, and generates a natural language response.

The system demonstrates a **Graph-RAG architecture** combining knowledge graphs with LLM reasoning.

---

# Technology Stack

## Backend

* Django
* Python

## Frontend

* Jinja templates via `django-jinja`
* Tailwind CSS
* DaisyUI
* HTMX
* Alpine.js

## Graph Database

* Memgraph
* Cypher query language

## AI Layer (Planned)

* LLM integration (OpenAI or Ollama)

## Async Processing (Planned)

* Celery

---

# Project Structure

All Django applications are placed inside an `apps/` directory to keep the project modular.

Example structure:

```
apps/
    auth_manager/
    document_manager/
```

Each application is responsible for a specific domain of the platform.

---

# Authentication System

Authentication is handled through a dedicated Django app called `auth_manager`.

## Responsibilities

The `auth_manager` app manages user authentication features including:

* user login
* user logout
* session management
* authentication templates

The app isolates authentication logic from the rest of the system to maintain modular architecture.

---

## Login Form

The login form is implemented using Django forms and styled using Tailwind and DaisyUI.

Form fields:

* email
* password

Inputs use consistent UI classes:

```
input input-bordered w-full
```

This styling pattern is reused throughout the platform for consistency.

---

# Template Engine

The project uses **Jinja templates** via the `django-jinja` package instead of Django’s default template engine.

This allows a more flexible templating syntax and better control over template rendering.

---

# Styling

Frontend styling uses:

* Tailwind CSS
* DaisyUI

Tailwind integration is handled using `django-tailwind`.

DaisyUI provides pre-built UI components such as:

* inputs
* buttons
* tables
* modals
* forms

---

# Static Files

A centralized static directory is used for compiled assets.

Example structure:

```
static/
    css/
        generated.css
```

Tailwind builds its compiled CSS into this directory.

---

# Document Manager

The `document_manager` app is responsible for managing documents uploaded by users and preparing them for knowledge graph generation.

Each uploaded document represents a dataset that can be converted into a knowledge graph and inserted into Memgraph.

The app handles:

* document upload
* document storage
* processing status tracking
* triggering graph extraction
* background processing using Celery
* storing intermediate graph representations

Documents are scoped to users so each user only sees and manages their own documents.

---

# Document Model

Each document is stored in the database and linked to a user.

The model tracks both metadata and graph generation status.

Fields include:

* user — owner of the document
* name — document name
* file — uploaded document file
* llm_used — LLM used for graph extraction
* status — processing status of the document
* nodes — number of nodes generated
* edges — number of edges generated
* relations — number of relation types generated
* processing_time — time taken to process the document
* error_message — error message if processing fails
* graph_data — intermediate graph representation stored as JSON
* created_at — upload timestamp

---

# LLM Selection

Documents require an LLM to process the text and extract entities and relationships.

Available LLM choices currently include:

* Llama 3
* Mistral
* GPT-4

A placeholder option **“Select LLM”** is displayed in the upload form.

---

# Document Status Lifecycle

Each document moves through a processing lifecycle.

Possible states include:

pending
The document has been uploaded but not yet processed.

processing
A background task is currently generating the knowledge graph.

complete
The graph was successfully generated.

error
Processing failed and an error message is recorded.

---

# Document Dashboard

The dashboard displays all documents belonging to the currently logged-in user.

Information shown for each document includes:

* document name
* number of nodes
* number of edges
* number of relations
* selected LLM
* processing status

The dashboard is implemented using **Jinja templates with HTMX components**.

---

# Frontend Architecture

Templates follow a component-based structure.

```
templates/
    base.jinja
    dashboard.jinja

    document_manager/
        components/
            document_table.jinja
            upload_modal.jinja
```

### base.jinja

Provides the global layout including:

* navigation bar
* static CSS
* HTMX initialization
* CSRF header injection

---

### dashboard.jinja

Extends the base template and loads dashboard components.

The document table is loaded dynamically using HTMX.

```
hx-get="/documents/table"
hx-trigger="load"
```

This ensures the dashboard always displays fresh data.

---

### document_table.jinja

Displays all documents in a table format.

Columns include:

* document name
* node count
* edge count
* relation count
* LLM used
* processing status
* actions

Status indicators are rendered using DaisyUI badges and progress components.

---

### upload_modal.jinja

The upload modal allows users to upload new documents without leaving the dashboard.

The form includes:

* document name
* file upload
* LLM selection

Submission is handled using HTMX.

---

# Upload Flow

The document upload flow works as follows.

User opens upload modal
↓
User submits upload form
↓
Server saves document metadata
↓
Server sends HX trigger events
↓
Dashboard refreshes document table
↓
Modal closes automatically

HTMX triggers are used to keep components loosely coupled.

---

# Document Actions

Each document row includes an **Actions column**.

Two operations are available.

### Process

Starts graph generation for the document.

When clicked:

* the document status changes to **processing**
* a Celery task is started
* the dashboard refreshes automatically

---

### Delete

Deletes the document and removes it from the dashboard.

---

# Background Processing with Celery

Document processing runs asynchronously using Celery.

The workflow is:

User clicks Process
↓
Django view triggers Celery task
↓
Celery worker processes the document
↓
Graph representation is generated
↓
Document status updated in database

The Celery worker automatically discovers tasks defined in the application.

---

# Graph Representation Storage

Before inserting data into Memgraph, documents are converted into a graph-friendly structure.

The intermediate representation is stored in the `graph_data` field.

Example structure:

```
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

This structure can later be converted into Cypher queries.

---

# Future Processing Pipeline

The document processing pipeline will eventually include:

Document Upload
↓
Text extraction
↓
Text chunking
↓
Entity extraction using LLM
↓
Relationship extraction using LLM
↓
Graph structure generation
↓
Cypher generation
↓
Insertion into Memgraph

---

# Design Goals

The document manager is designed to support:

* asynchronous document processing
* modular graph generation pipelines
* scalable graph ingestion
* user-scoped datasets

The system will eventually serve as the ingestion layer for the knowledge graph QA engine.


---

# Future Modules

The following modules will be implemented later in the project.

## Graph Manager

Responsible for interaction with the graph database.

Responsibilities include:

* Memgraph connection
* Cypher query execution
* graph schema inspection

---

## QA Engine

Handles the natural language question answering pipeline.

Responsibilities include:

* converting user questions into Cypher queries
* executing graph queries
* generating natural language responses

---

# Long-Term Goals

This project aims to demonstrate practical experience in:

* knowledge graph engineering
* graph database integration
* Graph-RAG architecture
* LLM prompt engineering
* backend system design
* modular Django architecture

The final system should function as a lightweight platform for building and querying knowledge graphs using natural language.
