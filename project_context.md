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

A dedicated Django app called `document_manager` manages documents uploaded to the platform.

Each uploaded document represents a dataset that will later be converted into a knowledge graph.

Documents are **user scoped**, meaning each user can only access and manage their own documents.

---

## Responsibilities

The `document_manager` app is responsible for:

* storing uploaded documents
* tracking metadata about generated graphs
* displaying document dashboards
* providing document upload functionality

---

# Document Model

Each uploaded document is stored in the database.

Documents are linked to users through a ForeignKey relationship.

Fields include:

* user — owner of the document
* name — document name
* file — uploaded document file
* nodes — number of nodes created in the graph
* edges — number of edges created in the graph
* relations — number of unique relation types
* llm_used — LLM used for extraction
* processing_time — time taken to generate the graph
* status — processing status (pending / processing / completed)
* created_at — upload timestamp

This metadata helps track the graph creation process for each document.

---

# Document Dashboard

The first screen of the platform is a **Document Dashboard**.

This page displays all documents uploaded by the currently logged-in user.

The dashboard shows metadata about the knowledge graphs generated from each document.

Displayed columns include:

* document name
* number of nodes
* number of edges
* number of relations
* LLM used
* processing time

Documents are filtered by the currently authenticated user to ensure user isolation.

---

# Upload Document Feature

Users can upload documents from the dashboard.

The dashboard includes an **Upload Document** button.

Clicking the button opens a modal containing the upload form.

---

# Document Upload Form

The upload form collects the following information:

* document name
* file to upload
* LLM model used

Inputs follow the project's UI conventions using DaisyUI classes:

```
input input-bordered w-full
select select-bordered w-full
file-input file-input-bordered w-full
```

These classes ensure consistent styling with the login form and other platform components.

---

# Upload Modal

The upload form appears inside a modal window.

The modal allows users to upload documents without leaving the dashboard page.

This approach improves the user experience and keeps the interface responsive.

---

# Document Processing Pipeline (Planned)

After a document is uploaded, the system will process it to generate a knowledge graph.

The planned processing pipeline:

Document Upload
↓
Text Chunking
↓
Entity Extraction (LLM)
↓
Relationship Extraction (LLM)
↓
Cypher Generation
↓
Graph Storage in Memgraph

Graph generation tasks will run asynchronously using Celery workers.

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
