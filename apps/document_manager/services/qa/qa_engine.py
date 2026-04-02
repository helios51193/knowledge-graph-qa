import json
import re

import requests
from django.conf import settings
from openai import OpenAI
from .question_intents import analyze_question
from .intent_queries import build_intent_cypher

from ..graph_database import execute_read_query


READ_ONLY_PREFIXES = ("MATCH", "OPTIONAL MATCH", "WITH", "RETURN", "CALL")


class QAEngine:

    def answer_question(self, document, question):
        
        schema = self._build_graph_schema(document)
        question_analysis = analyze_question(question, document.graph_data or {})

        cypher = build_intent_cypher(document, question_analysis)

        if not cypher:
            question_analysis["fallback_used"] = True
            question_analysis["strategy"] = "llm_cypher_generation"
            cypher = self._generate_cypher(document, question, schema)

        self._validate_read_only_query(cypher)

        try:
            rows = execute_read_query(cypher)
        except Exception as exc:
            cypher = self._repair_cypher_on_error(
                document=document,
                question=question,
                schema=schema,
                bad_cypher=cypher,
                error_message=str(exc),
            )
            self._validate_read_only_query(cypher)
            rows = execute_read_query(cypher)

        answer = self._generate_answer(
            document=document,
            question=question,
            cypher=cypher,
            rows=rows,
            schema=schema,
            question_analysis=question_analysis,
        )

        highlight = self._build_highlight_payload(document, rows)
        provenance = self._build_provenance_payload(document, highlight)

        return {
            "question": question,
            "cypher": cypher,
            "rows": rows,
            "answer": answer,
            "highlight":highlight,
            "provenance":provenance,
            "question_analysis": question_analysis,
        }
    
    def _build_highlight_payload(self, document, rows):
        graph_data = document.graph_data or {}
        nodes = graph_data.get("nodes", [])
        edges = graph_data.get("edges", [])

        node_id_by_name = {
            node["name"].strip().lower(): node["id"]
            for node in nodes
            if node.get("name") and node.get("id")
        }

        edge_ids = set()
        node_ids = set()
        highlighted_names = set()
        highlighted_relation_types = set()

        for row in rows:
            # Path-specific direct highlighting
            for node_id in row.get("path_node_ids", []):
                if node_id:
                    node_ids.add(node_id)

            for edge in row.get("path_edges", []):
                source = edge.get("source")
                target = edge.get("target")
                rel_type = edge.get("type")

                if source and target and rel_type:
                    edge_ids.add(f"{source}-{rel_type}-{target}")

            # Generic fallback highlighting
            self._collect_highlight_values(
                value=row,
                highlighted_names=highlighted_names,
                highlighted_relation_types=highlighted_relation_types,
            )

        for name in highlighted_names:
            node_id = node_id_by_name.get(name.lower())
            if node_id:
                node_ids.add(node_id)

        for edge in edges:
            edge_id = f'{edge["source"]}-{edge["type"]}-{edge["target"]}'

            source_selected = edge["source"] in node_ids
            target_selected = edge["target"] in node_ids
            relation_selected = edge["type"] in highlighted_relation_types

            if edge_id in edge_ids:
                continue

            if (source_selected and target_selected) or relation_selected:
                edge_ids.add(edge_id)

        return {
            "node_ids": sorted(node_ids),
            "edge_ids": sorted(edge_ids),
            "focus": True,
        }
    
    def _collect_highlight_values(self, value, highlighted_names, highlighted_relation_types):
        if isinstance(value, dict):
            for key, inner_value in value.items():
                key_lower = str(key).lower()

                if isinstance(inner_value, str):
                    cleaned = inner_value.strip()

                    if key_lower in {
                        "name",
                        "entity_name",
                        "entity",
                        "related_entity",
                        "source",
                        "target",
                    }:
                        highlighted_names.add(cleaned)

                    elif key_lower in {
                        "relation",
                        "relation_type",
                        "type",
                    }:
                        highlighted_relation_types.add(cleaned.upper())

                else:
                    self._collect_highlight_values(
                        inner_value,
                        highlighted_names,
                        highlighted_relation_types,
                    )

        elif isinstance(value, list):
            for item in value:
                self._collect_highlight_values(
                    item,
                    highlighted_names,
                    highlighted_relation_types,
                )

    def _build_provenance_payload(self, document, highlight):
        graph_data = document.graph_data or {}
        nodes = graph_data.get("nodes", [])
        edges = graph_data.get("edges", [])

        node_map = {node["id"]: node for node in nodes if node.get("id")}
        edge_map = {
            f'{edge["source"]}-{edge["type"]}-{edge["target"]}': edge
            for edge in edges
            if edge.get("source") and edge.get("type") and edge.get("target")
        }

        evidence = []

        for node_id in highlight.get("node_ids", []):
            node = node_map.get(node_id)
            if not node:
                continue

            provenance = node.get("provenance") or {}
            source_text = (provenance.get("source_text") or "").strip()

            if not source_text:
                continue

            evidence.append({
                "kind": "node",
                "title": f'{node.get("name")} ({node.get("label")})',
                "chunk_id": provenance.get("chunk_id"),
                "start_index": provenance.get("start_index"),
                "end_index": provenance.get("end_index"),
                "source_text": source_text,
                "snippet": self._build_text_snippet(
                            source_text=source_text,
                            terms=[node.get("name", "")],
                ),
            })

        for edge_id in highlight.get("edge_ids", []):
            edge = edge_map.get(edge_id)
            if not edge:
                continue

            provenance = edge.get("provenance") or {}
            source_text = (provenance.get("source_text") or "").strip()

            if not source_text:
                continue

            evidence.append({
                "kind": "edge",
                "title": f'{edge.get("source_name")} -[{edge.get("type")}]-> {edge.get("target_name")}',
                "chunk_id": provenance.get("chunk_id"),
                "start_index": provenance.get("start_index"),
                "end_index": provenance.get("end_index"),
                "source_text": source_text,
                "snippet": self._build_text_snippet(
                source_text=source_text,
                terms=[
                    edge.get("source_name", ""),
                    edge.get("target_name", ""),
                    edge.get("type", ""),
                ],
            ),

            })

        unique_evidence = []
        seen = set()

        for item in evidence:
            key = (
                item["kind"],
                item["title"],
                item["chunk_id"],
                item["source_text"],
            )
            if key in seen:
                continue
            seen.add(key)
            unique_evidence.append(item)

        return unique_evidence[:6]

    def _build_text_snippet(self, source_text, terms, window=140):
        text = (source_text or "").strip()
        if not text:
            return ""

        lower_text = text.lower()

        match_index = -1
        match_term = ""

        for term in terms:
            cleaned_term = (term or "").strip()
            if not cleaned_term:
                continue

            idx = lower_text.find(cleaned_term.lower())
            if idx != -1:
                match_index = idx
                match_term = cleaned_term
                break

        if match_index == -1:
            if len(text) <= window:
                return text
            return text[:window].rstrip() + "..."

        start = max(0, match_index - window // 2)
        end = min(len(text), match_index + len(match_term) + window // 2)

        snippet = text[start:end].strip()

        if start > 0:
            snippet = "..." + snippet
        if end < len(text):
            snippet = snippet + "..."

        return snippet

    def _build_graph_schema(self, document):
        graph_data = document.graph_data or {}

        nodes = graph_data.get("nodes", [])
        edges = graph_data.get("edges", [])

        node_labels = sorted({node.get("label", "Entity") for node in nodes})
        relation_types = sorted({edge.get("type", "RELATED_TO") for edge in edges})
        sample_entity_names = sorted({
            node.get("name", "")
            for node in nodes
            if node.get("name")
        })[:25]

        return {
            "document_id": document.id,
            "node_label": "Entity",
            "node_properties": ["document_id", "name", "label"],
            "relationship_types": relation_types,
            "entity_labels": node_labels,
            "sample_entity_names": sample_entity_names,
        }

    def _generate_cypher(self, document, question, schema):
        prompt = self._build_cypher_prompt(document, question, schema)

        if document.llm_used == "gpt4":
            response_text = self._ask_openai(
                prompt,
                model=getattr(settings, "OPENAI_QA_MODEL", "gpt-4o-mini"),
            )
        elif document.llm_used == "llama3":
            response_text = self._ask_ollama(
                prompt,
                model=getattr(settings, "OLLAMA_QA_MODEL", "llama3"),
            )
        else:
            raise ValueError(f"Unsupported LLM for QA: {document.llm_used}")

        return self._extract_cypher(response_text)

    def _repair_cypher_on_error(self, document, question, schema, bad_cypher, error_message):
        prompt = self._build_cypher_repair_prompt(
            document=document,
            question=question,
            schema=schema,
            bad_cypher=bad_cypher,
            error_message=error_message,
        )

        if document.llm_used == "gpt4":
            response_text = self._ask_openai(
                prompt,
                model=getattr(settings, "OPENAI_QA_MODEL", "gpt-4o-mini"),
            )
        elif document.llm_used == "llama3":
            response_text = self._ask_ollama(
                prompt,
                model=getattr(settings, "OLLAMA_QA_MODEL", "llama3"),
            )
        else:
            raise ValueError(f"Unsupported LLM for QA: {document.llm_used}")

        return self._extract_cypher(response_text)

    def _generate_answer(self, document, question, cypher, rows, schema, question_analysis):
        
        if rows:
            if len(rows) == 1 and len(rows[0]) == 1:
                return str(next(iter(rows[0].values())))

            if all(len(row) == 1 for row in rows):
                values = []
                for row in rows:
                    values.extend(row.values())
                return ", ".join(str(value) for value in values)
        
        question_analysis_json = json.dumps(question_analysis, ensure_ascii=True)
        
        prompt = self._build_answer_prompt(question, cypher, rows, schema, question_analysis_json)

        if document.llm_used == "gpt4":
            return self._ask_openai(
                prompt,
                model=getattr(settings, "OPENAI_QA_MODEL", "gpt-4o-mini"),
            )
        elif document.llm_used == "llama3":
            return self._ask_ollama(
                prompt,
                model=getattr(settings, "OLLAMA_QA_MODEL", "llama3"),
            )

        raise ValueError(f"Unsupported LLM for QA: {document.llm_used}")

    def _build_cypher_prompt(self, document, question, schema):
        schema_json = json.dumps(schema, ensure_ascii=True)

        return f"""
        You generate Cypher queries for Memgraph.

        Return ONLY the Cypher query.
        Do not include markdown.
        Do not include explanation.
        Do not include comments.

        Actual graph schema for this document:
        {schema_json}

        Graph conventions:
        - All nodes use label :Entity
        - Node properties include: document_id, name, label
        - Relationship property includes: document_id
        - Restrict every query to document_id = {document.id}
        - Use actual relationship types from the schema above
        - Use actual entity labels from the schema above

        Read-only constraints:
        - The query must be READ ONLY
        - Use only MATCH, OPTIONAL MATCH, WHERE, WITH, RETURN, ORDER BY, LIMIT
        - Never use CREATE, MERGE, DELETE, DETACH DELETE, SET, REMOVE, DROP, LOAD CSV, FOREACH

        Cypher usage rules:
        - Prefer case-insensitive matching for names:
        toLower(n.name) = toLower("Whisperwood")
        - Do not use relationships(node)
        - The relationships() function expects a path, not a node
        - To inspect connected entities, use pattern matching:
        MATCH (n:Entity)-[r]-(m:Entity)
        - Always scope connected nodes and relationships to the same document_id
        - If the question asks "what is X" or "who is X", identify the entity and return its name and label
        - If the question asks "what is in X", "who is in X", "what is there in X", "what is connected to X", or "tell me about X", prefer traversing neighboring nodes and relationships
        - If the question asks for categories or lists, return DISTINCT values
        - Use aliases in RETURN for readability

        Intent examples:

        Question: What is Whisperwood?
        Cypher:
        MATCH (n:Entity)
        WHERE n.document_id = {document.id}
        AND toLower(n.name) = toLower("Whisperwood")
        RETURN n.name AS entity_name, n.label AS label

        Question: What is in Whisperwood?
        Cypher:
        MATCH (n:Entity)
        WHERE n.document_id = {document.id}
        AND toLower(n.name) = toLower("Whisperwood")
        OPTIONAL MATCH (n)-[r]-(m:Entity)
        WHERE m.document_id = {document.id} AND r.document_id = {document.id}
        RETURN n.name AS entity_name,
            n.label AS label,
            collect(DISTINCT {{
                related_entity: m.name,
                related_label: m.label,
                relation: type(r)
            }}) AS related_entities

        Question: What relationship types exist in this document?
        Cypher:
        MATCH ()-[r]->()
        WHERE r.document_id = {document.id}
        RETURN DISTINCT type(r) AS relation_type
        ORDER BY relation_type

        Question: List all locations.
        Cypher:
        MATCH (n:Entity)
        WHERE n.document_id = {document.id}
        AND n.label = "Location"
        RETURN DISTINCT n.name AS location
        ORDER BY location

        User question:
        {question}
        """.strip()

    def _build_cypher_repair_prompt(self, document, question, schema, bad_cypher, error_message):
        schema_json = json.dumps(schema, ensure_ascii=True)

        return f"""
    You are repairing a Cypher query for Memgraph.

    Return ONLY the corrected Cypher query.
    Do not include markdown.
    Do not include explanation.
    Do not include comments.

    User question:
    {question}

    Document id constraint:
    {document.id}

    Actual graph schema:
    {schema_json}

    The previous query was:
    {bad_cypher}

    It failed with this error:
    {error_message}

    Repair rules:
    - Keep the query READ ONLY
    - Use only MATCH, OPTIONAL MATCH, WHERE, WITH, RETURN, ORDER BY, LIMIT
    - Never use CREATE, MERGE, DELETE, DETACH DELETE, SET, REMOVE, DROP, LOAD CSV, FOREACH
    - Scope the query to document_id = {document.id}
    - Prefer case-insensitive matching for entity names using toLower(...)
    - Do not use relationships(node)
    - If the query needs connected entities, use pattern matching like:
    MATCH (n:Entity)-[r]-(m:Entity)

    Return only the corrected Cypher query.
    """.strip()

    def _build_answer_prompt(self, question, cypher, rows, schema, question_analysis_json):
        rows_json = json.dumps(rows, ensure_ascii=True)
        schema_json = json.dumps(schema, ensure_ascii=True)
        style = getattr(settings, "QA_ANSWER_STYLE", "natural")
        return f"""
        Answer the user's question using the query result below.

        Style rules:
        - Sound {style}.
        - Write like a helpful human assistant, not like a database engine.
        - Keep the answer grounded in the query result.
        - Do not invent facts that are not supported by the rows.
        - If the result is small, you may phrase it smoothly in one or two sentences.
        - If the result contains related entities, summarize them in a natural way.
        - If rows are non-empty, answer from the rows directly.
        - Do NOT say "The graph does not contain enough information to answer confidently" when rows are non-empty.
        - Only use the fallback if rows are truly empty.
        - If rows are empty, say that the graph for this document does not currently contain enough matching information.

        User question:
        {question}

        Graph schema:
        {schema_json}

        Cypher used:
        {cypher}

        Question analysis:
        {question_analysis_json}

        Query result rows:
        {rows_json}
        """.strip()

    def _ask_openai(self, prompt, model):
        client = OpenAI(api_key=settings.OPEN_AI_KEY)

        response = client.chat.completions.create(
            model=model,
            temperature=getattr(settings, "QA_LLM_TEMPERATURE", 0),
            messages=[
                {
                    "role": "system",
                    "content": "You are a graph question answering assistant."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return response.choices[0].message.content.strip()

    def _ask_ollama(self, prompt, model):
        response = requests.post(
            f"http://{settings.OLLAMA_HOST}:{settings.OLLAMA_PORT}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": getattr(settings, "QA_LLM_TEMPERATURE", 0)
                }
            },
            timeout=getattr(settings, "QA_LLM_TIMEOUT", 90),
        )

        response.raise_for_status()
        data = response.json()
        return data.get("response", "").strip()

    def _extract_cypher(self, response_text):
        text = response_text.strip()

        if text.startswith("```"):
            text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
            text = re.sub(r"\s*```$", "", text)

        return text.strip()

    def _validate_read_only_query(self, cypher):
        upper = cypher.upper()

        forbidden = [
            "CREATE ",
            "MERGE ",
            "DELETE ",
            "DETACH DELETE ",
            "SET ",
            "REMOVE ",
            "DROP ",
            "LOAD CSV ",
            "FOREACH ",
        ]

        for token in forbidden:
            if token in upper:
                raise ValueError(f"Unsafe Cypher generated: contains '{token.strip()}'")

        if not upper.startswith(READ_ONLY_PREFIXES):
            raise ValueError("Generated Cypher is not read-only.")

        if "DOCUMENT_ID" not in upper:
            raise ValueError("Generated Cypher is not scoped to a document.")
