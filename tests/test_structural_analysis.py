from pathlib import Path
import json
import tempfile
import unittest

from mcpiler.structural import StructuralInputError, extract_endpoint_contexts


FIXTURE_ROOT = Path(__file__).parent.parent / "fixtures" / "order_management"


class StructuralAnalysisTests(unittest.TestCase):
    def test_fixed_fixture_enumerates_eight_operations_and_matches_seven_handlers(self) -> None:
        analysis = extract_endpoint_contexts(
            FIXTURE_ROOT / "openapi.json",
            FIXTURE_ROOT / "backend",
        )

        self.assertEqual(
            [context.operation_key for context in analysis.endpoint_contexts],
            [
                "DELETE /orders/{order_id}",
                "GET /internal/health",
                "GET /orders",
                "GET /orders/{order_id}",
                "PATCH /orders/{order_id}/address",
                "POST /orders",
                "POST /orders/{order_id}/archive",
                "POST /orders/{order_id}/refund",
            ],
        )
        self.assertEqual(
            [context.source_match.status for context in analysis.endpoint_contexts].count("matched"),
            7,
        )

        archive = next(
            context
            for context in analysis.endpoint_contexts
            if context.operation_key == "POST /orders/{order_id}/archive"
        )
        self.assertEqual(archive.source_match.status, "unmatched")
        self.assertIsNone(archive.handler)

    def test_contexts_expose_openapi_handler_evidence_and_completeness(self) -> None:
        analysis = extract_endpoint_contexts(
            FIXTURE_ROOT / "openapi.json",
            FIXTURE_ROOT / "backend",
        )
        contexts = {context.operation_key: context for context in analysis.endpoint_contexts}

        self.assertEqual(analysis.handler_source_limit, 4_000)

        create = contexts["POST /orders"]
        self.assertEqual(create.openapi_operation.operation_id, "create_order")
        self.assertEqual(create.openapi_operation.summary, "Create order")
        self.assertEqual(
            create.openapi_operation.description,
            "Creates an order for a customer.",
        )
        self.assertTrue(create.openapi_operation.request_body.required)
        self.assertEqual(
            create.openapi_operation.request_body.schemas[0].media_type,
            "application/json",
        )
        self.assertEqual(create.openapi_operation.responses[0].status_code, "201")

        address = contexts["PATCH /orders/{order_id}/address"]
        self.assertEqual(address.source_match.status, "matched")
        self.assertEqual(address.source_match.reason_codes, ())
        self.assertEqual(len(address.source_match.candidate_locations), 1)
        self.assertEqual(address.handler.name, "update_order_address")
        self.assertEqual(address.handler.relative_path, "app.py")
        self.assertGreater(address.handler.start_line, 0)
        self.assertGreaterEqual(address.handler.end_line, address.handler.start_line)
        self.assertEqual(
            address.handler.signature,
            "def update_order_address(order_id: str, address: dict=Body(...)) -> dict",
        )
        self.assertEqual(
            address.handler.docstring.text,
            "Update the delivery address before the order ships.",
        )
        self.assertIn('order["status"] == "shipped"', address.handler.source.text)
        self.assertEqual(
            address.handler.direct_call_names,
            (
                "order_store.get_order",
                "HTTPException",
                "order_store.update_address",
            ),
        )
        self.assertEqual(address.evidence_completeness.status, "complete")
        self.assertEqual(address.evidence_completeness.gaps, ())
        self.assertTrue(
            {
                "openapi.operation",
                "openapi.parameter",
                "openapi.request_body_schema",
                "openapi.response_schema",
                "source.route",
                "source.signature",
                "source.docstring",
                "source.handler",
                "source.direct_call",
            }.issubset({evidence.kind for evidence in address.evidence})
        )

        archive = contexts["POST /orders/{order_id}/archive"]
        self.assertEqual(archive.evidence_completeness.status, "incomplete")
        self.assertEqual(archive.evidence_completeness.gaps[0].code, "source_unmatched")

    def test_invalid_global_inputs_report_stable_failure_categories(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source_root = root / "backend"
            source_root.mkdir()
            (source_root / "app.py").write_text("value = 1\n", encoding="utf-8")

            invalid_json = root / "invalid.json"
            invalid_json.write_text("{not json", encoding="utf-8")
            invalid_structure = root / "invalid-structure.json"
            invalid_structure.write_text("[]", encoding="utf-8")
            invalid_operation = root / "invalid-operation.json"
            invalid_operation.write_text(
                '{"openapi":"3.1.0","paths":{"/health":{"get":{"operationId":7}}}}',
                encoding="utf-8",
            )
            valid_openapi = root / "openapi.json"
            valid_openapi.write_text(
                '{"openapi":"3.1.0","paths":{"/health":{"get":{"responses":{}}}}}',
                encoding="utf-8",
            )
            invalid_source = root / "invalid-source"
            invalid_source.mkdir()
            (invalid_source / "app.py").write_text("def broken(:\n", encoding="utf-8")

            cases = (
                (root / "missing.json", source_root, "openapi_unreadable"),
                (invalid_json, source_root, "openapi_invalid_json"),
                (invalid_structure, source_root, "openapi_invalid_structure"),
                (invalid_operation, source_root, "openapi_invalid_structure"),
                (valid_openapi, root / "missing-source", "source_root_unreadable"),
                (valid_openapi, invalid_source, "source_syntax_error"),
            )
            for openapi_path, candidate_source_root, expected_category in cases:
                with self.subTest(expected_category=expected_category):
                    with self.assertRaises(StructuralInputError) as raised:
                        extract_endpoint_contexts(openapi_path, candidate_source_root)
                    self.assertEqual(raised.exception.category, expected_category)

    def test_source_evidence_is_bounded_shallow_and_never_executed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            openapi_path = root / "openapi.json"
            openapi_path.write_text(
                json.dumps(
                    {
                        "openapi": "3.1.0",
                        "paths": {
                            "/oversized": {
                                "get": {
                                    "operationId": "oversized",
                                    "responses": {},
                                }
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )
            source_root = root / "backend"
            source_root.mkdir()
            padding = "x" * 4_200
            (source_root / "app.py").write_text(
                "raise RuntimeError('target backend must not execute')\n"
                "@app.get('/oversized')\n"
                "def oversized():\n"
                "    \"\"\"A bounded handler.\"\"\"\n"
                "    visible()\n"
                "    registry['dynamic']()\n"
                "    callback = lambda: hidden_lambda()\n"
                "    def nested():\n"
                "        hidden()\n"
                f"    payload = '{padding}'\n"
                "    return adapter.run(payload)\n",
                encoding="utf-8",
            )

            analysis = extract_endpoint_contexts(openapi_path, source_root)
            context = analysis.endpoint_contexts[0]

            self.assertEqual(context.source_match.status, "matched")
            self.assertEqual(len(context.handler.source.text), 4_000)
            self.assertGreater(context.handler.source.original_char_count, 4_000)
            self.assertTrue(context.handler.source.truncated)
            self.assertEqual(
                context.handler.direct_call_names,
                ("visible", "adapter.run"),
            )
            self.assertEqual(context.evidence_completeness.status, "incomplete")
            self.assertEqual(
                [gap.code for gap in context.evidence_completeness.gaps],
                ["handler_source_truncated"],
            )
            handler_evidence = next(
                evidence for evidence in context.evidence if evidence.kind == "source.handler"
            )
            self.assertEqual(handler_evidence.value, context.handler.source.text)

    def test_route_matching_is_exact_normalized_and_conservative(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            openapi_path = root / "openapi.json"
            openapi_path.write_text(
                json.dumps(
                    {
                        "openapi": "3.1.0",
                        "paths": {
                            "/normalized": {"get": {"responses": {}}},
                            "/ambiguous": {"get": {"responses": {}}},
                            "/unsupported": {"put": {"responses": {}}},
                            "/dynamic": {"get": {"responses": {}}},
                        },
                    }
                ),
                encoding="utf-8",
            )
            source_root = root / "backend"
            source_root.mkdir()
            (source_root / "app.py").write_text(
                "@app.get('normalized/')\n"
                "def normalized():\n"
                "    pass\n"
                "@app.get('/ambiguous')\n"
                "def first():\n"
                "    pass\n"
                "@app.get('/ambiguous/')\n"
                "def second():\n"
                "    pass\n"
                "@app.put('/unsupported')\n"
                "def unsupported():\n"
                "    pass\n"
                "dynamic_path = '/dynamic'\n"
                "@app.get(dynamic_path)\n"
                "def dynamic():\n"
                "    pass\n",
                encoding="utf-8",
            )

            analysis = extract_endpoint_contexts(openapi_path, source_root)
            statuses = {
                context.operation_key: context.source_match.status
                for context in analysis.endpoint_contexts
            }

            self.assertEqual(statuses["GET /normalized"], "matched")
            self.assertEqual(statuses["GET /ambiguous"], "ambiguous")
            self.assertEqual(statuses["PUT /unsupported"], "unsupported")
            self.assertEqual(statuses["GET /dynamic"], "unmatched")

    def test_identical_inputs_produce_stable_contexts_and_evidence_ids(self) -> None:
        first = extract_endpoint_contexts(
            FIXTURE_ROOT / "openapi.json",
            FIXTURE_ROOT / "backend",
        )
        second = extract_endpoint_contexts(
            FIXTURE_ROOT / "openapi.json",
            FIXTURE_ROOT / "backend",
        )

        self.assertEqual(first, second)
        for context in first.endpoint_contexts:
            evidence_ids = [evidence.id for evidence in context.evidence]
            self.assertEqual(len(evidence_ids), len(set(evidence_ids)))


if __name__ == "__main__":
    unittest.main()
