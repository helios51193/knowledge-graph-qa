import shutil
import tempfile
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from apps.auth_manager.models import User
from apps.document_manager.models import Document, ProcessingLog
from apps.document_manager.tasks import process_document
from apps.document_manager.services.qa.qa_engine import QAEngine


@override_settings(
    MEDIA_ROOT=tempfile.mkdtemp(),
    ENTITY_EXTRACTOR="heuristic",
    RELATION_EXTRACTOR="heuristic",
    DOCUMENT_CHUNKER="sentence",
)
class DocumentPipelineE2ETests(TestCase):

    @classmethod
    def tearDownClass(cls):
        media_root = getattr(cls, "media_root", None)
        super().tearDownClass()

    def setUp(self):
        self._media_root = tempfile.mkdtemp()
        self.override_media = override_settings(MEDIA_ROOT=self._media_root)
        self.override_media.enable()

        self.user = User.objects.create_user(
            email="tester@example.com",
            password="testpass123"
        )

    def tearDown(self):
        self.override_media.disable()
        shutil.rmtree(self._media_root, ignore_errors=True)

    def _create_text_document(self, text, name="story.txt", llm_used="gpt4"):
        uploaded_file = SimpleUploadedFile(
            name=name,
            content=text.encode("utf-8"),
            content_type="text/plain",
        )

        return Document.objects.create(
            user=self.user,
            name="Test Story",
            file=uploaded_file,
            llm_used=llm_used,
        )

    @patch("apps.document_manager.tasks.save_graph_to_database")
    def test_process_document_updates_document_fields_and_graph_data(self, mock_save_graph):
        text = (
            "Elarin lives in Whisperwood. "
            "Elarin works at Moonkeep. "
            "Moonkeep is based in Whisperwood."
        )

        document = self._create_text_document(text=text)

        process_document(document.id)

        document.refresh_from_db()

        self.assertEqual(document.status, Document.STATUS_COMPLETE)
        self.assertEqual(document.error_message, "")
        self.assertIsNotNone(document.processing_time)
        self.assertIsNotNone(document.graph_data)

        self.assertIn("nodes", document.graph_data)
        self.assertIn("edges", document.graph_data)
        self.assertIn("counts", document.graph_data)

        self.assertGreater(document.nodes, 0)
        self.assertGreaterEqual(document.edges, 0)
        self.assertGreaterEqual(document.relations, 0)

        self.assertEqual(document.nodes, document.graph_data["counts"]["nodes"])
        self.assertEqual(document.edges, document.graph_data["counts"]["edges"])
        self.assertEqual(document.relations, document.graph_data["counts"]["relation_types"])

        mock_save_graph.assert_called_once()

    @patch("apps.document_manager.tasks.save_graph_to_database")
    def test_process_document_creates_processing_logs(self, mock_save_graph):
        text = "Elarin lives in Whisperwood."

        document = self._create_text_document(text=text)

        process_document(document.id)

        stages = list(
            ProcessingLog.objects.filter(document=document)
            .values_list("stage", flat=True)
        )

        self.assertIn("START", stages)
        self.assertIn("TEXT_EXTRACTION", stages)
        self.assertIn("NORMALIZATION", stages)
        self.assertIn("CHUNKING", stages)
        self.assertIn("ENTITY_EXTRACTION", stages)
        self.assertIn("RELATION_EXTRACTION", stages)
        self.assertIn("GRAPH_BUILDING", stages)
        self.assertIn("COMPLETE", stages)

    @patch("apps.document_manager.tasks.save_graph_to_database")
    def test_process_document_extracts_expected_entities_into_graph(self, mock_save_graph):
        text = "Elarin lives in Whisperwood. Moonkeep is based in Whisperwood."

        document = self._create_text_document(text=text)

        process_document(document.id)
        document.refresh_from_db()

        node_names = {node["name"] for node in document.graph_data["nodes"]}

        self.assertIn("Elarin", node_names)
        self.assertIn("Whisperwood", node_names)
        self.assertIn("Moonkeep", node_names)

    @patch("apps.document_manager.tasks.save_graph_to_database")
    def test_process_document_creates_expected_relation_types(self, mock_save_graph):
        text = "Elarin lives in Whisperwood. Moonkeep is based in Whisperwood."

        document = self._create_text_document(text=text)

        process_document(document.id)
        document.refresh_from_db()

        relation_types = {edge["type"] for edge in document.graph_data["edges"]}

        self.assertIn("LIVES_IN", relation_types)
        self.assertIn("LIVES_IN", relation_types)


class QAEngineTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="qa@example.com",
            password="testpass123"
        )

        self.document = Document.objects.create(
            user=self.user,
            name="QA Graph",
            llm_used="gpt4",
            file=SimpleUploadedFile(
                "qa.txt",
                b"placeholder text",
                content_type="text/plain",
            ),
            graph_data={
                "nodes": [
                    {
                        "id": "1:Location:Whisperwood",
                        "name": "Whisperwood",
                        "label": "Location",
                        "document_id": 1,
                    },
                    {
                        "id": "1:Person:Elarin",
                        "name": "Elarin",
                        "label": "Person",
                        "document_id": 1,
                    },
                ],
                "edges": [
                    {
                        "source": "1:Person:Elarin",
                        "target": "1:Location:Whisperwood",
                        "source_name": "Elarin",
                        "target_name": "Whisperwood",
                        "source_label": "Person",
                        "target_label": "Location",
                        "type": "LIVES_IN",
                        "document_id": 1,
                    }
                ],
                "counts": {
                    "nodes": 2,
                    "edges": 1,
                    "relation_types": 1,
                },
            },
        )

    @patch("apps.document_manager.services.qa.qa_engine.execute_read_query")
    @patch.object(QAEngine, "_ask_openai")
    def test_qa_engine_answers_simple_identity_question(self, mock_ask_openai, mock_execute_read_query):
        mock_ask_openai.side_effect = [
            'MATCH (n:Entity) WHERE n.document_id = 1 AND toLower(n.name) = toLower("Whisperwood") RETURN n.name AS entity_name, n.label AS label',
            "Whisperwood is a location in the graph."
        ]
        mock_execute_read_query.return_value = [
            {"entity_name": "Whisperwood", "label": "Location"}
        ]

        engine = QAEngine()
        result = engine.answer_question(self.document, "What is Whisperwood?")

        self.assertIn("MATCH", result["cypher"])
        self.assertEqual(result["rows"][0]["label"], "Location")
        self.assertIn("Whisperwood", result["answer"])

    @patch("apps.document_manager.services.qa.qa_engine.execute_read_query")
    @patch.object(QAEngine, "_ask_openai")
    def test_qa_engine_repairs_cypher_after_query_error(self, mock_ask_openai, mock_execute_read_query):
        bad_query = (
            'MATCH (n:Entity) WHERE n.document_id = 1 '
            'AND toLower(n.name) = toLower("Whisperwood") '
            'RETURN relationships(n)'
        )

        repaired_query = (
            'MATCH (n:Entity) '
            'WHERE n.document_id = 1 AND toLower(n.name) = toLower("Whisperwood") '
            'OPTIONAL MATCH (n)-[r]-(m:Entity) '
            'WHERE m.document_id = 1 AND r.document_id = 1 '
            'RETURN n.name AS entity_name, collect(DISTINCT {related_entity: m.name, relation: type(r)}) AS related_entities'
        )

        mock_ask_openai.side_effect = [
            bad_query,
            repaired_query,
            "Whisperwood is a location, and Elarin is connected to it through a LIVES_IN relationship."
        ]

        mock_execute_read_query.side_effect = [
            Exception("'relationships' argument at position 1 must be either 'null' or 'path'."),
            [
                {
                    "entity_name": "Whisperwood",
                    "related_entities": [
                        {"related_entity": "Elarin", "relation": "LIVES_IN"}
                    ],
                }
            ],
        ]

        engine = QAEngine()
        result = engine.answer_question(self.document, "What is in Whisperwood?")

        self.assertEqual(mock_execute_read_query.call_count, 2)
        self.assertEqual(result["cypher"], repaired_query)
        self.assertIn("Whisperwood", result["answer"])

