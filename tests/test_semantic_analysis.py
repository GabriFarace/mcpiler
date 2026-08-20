from pathlib import Path
import json
import tempfile
import unittest

from mcpiler.semantic import (
    FakeSemanticAnalyzer,
    SemanticFailure,
    analyze_endpoint_contexts,
    validate_endpoint_semantics,
)
from mcpiler.structural import extract_endpoint_contexts


FIXTURE_ROOT = Path(__file__).parent.parent / "fixtures" / "order_management"


def _candidate() -> dict[str, object]:
    return {
        "purpose": {
            "text": "List orders.",
            "confidence": "medium",
            "evidence_refs": ["openapi.operation"],
        },
        "agent_description": {
            "text": "List available orders.",
            "confidence": "high",
            "evidence_refs": ["openapi.operation"],
        },
        "preconditions": [],
        "side_effects": [],
        "relevance": {
            "text": "The operation is user-facing.",
            "confidence": "high",
            "evidence_refs": ["openapi.operation"],
            "classification": "user-facing",
        },
        "semantic_risk_signals": [],
        "uncertainty_reasons": [],
        "analysis_provenance": {
            "analyzer_id": "fake-test",
            "provider_id": None,
            "model_id": None,
            "schema_version": "v1",
            "prompt_version": "fixture-test-v1",
        },
    }


class SemanticAnalysisTests(unittest.TestCase):
    def test_fixed_fake_analyzes_supported_contexts_and_skips_archive(self) -> None:
        structural_analysis = extract_endpoint_contexts(
            FIXTURE_ROOT / "openapi.json",
            FIXTURE_ROOT / "backend",
        )
        analyzer = FakeSemanticAnalyzer()

        analysis = analyze_endpoint_contexts(
            structural_analysis.endpoint_contexts,
            analyzer,
        )

        results = {record.context.operation_key: record.analysis for record in analysis.records}
        self.assertEqual(len(analysis.records), 8)
        self.assertEqual(
            [record.context.operation_key for record in analysis.records],
            [context.operation_key for context in structural_analysis.endpoint_contexts],
        )
        self.assertEqual(
            [record.context.operation_key for record in analysis.records if record.analysis.status == "succeeded"],
            [
                "DELETE /orders/{order_id}",
                "GET /internal/health",
                "GET /orders",
                "GET /orders/{order_id}",
                "PATCH /orders/{order_id}/address",
                "POST /orders",
                "POST /orders/{order_id}/refund",
            ],
        )
        self.assertEqual(results["POST /orders/{order_id}/archive"].status, "skipped")
        self.assertEqual(
            analyzer.calls,
            [
                "DELETE /orders/{order_id}",
                "GET /internal/health",
                "GET /orders",
                "GET /orders/{order_id}",
                "PATCH /orders/{order_id}/address",
                "POST /orders",
                "POST /orders/{order_id}/refund",
            ],
        )

        address = results["PATCH /orders/{order_id}/address"].semantics
        self.assertEqual(address.preconditions[0].confidence, "high")
        self.assertEqual(address.preconditions[0].evidence_refs, ("source.handler",))
        self.assertEqual(address.uncertainty_reasons, ())

    def test_fake_accepts_json_shaped_fixture_data_and_preserves_uncertainty(self) -> None:
        context = next(
            context
            for context in extract_endpoint_contexts(
                FIXTURE_ROOT / "openapi.json",
                FIXTURE_ROOT / "backend",
            ).endpoint_contexts
            if context.operation_key == "GET /orders"
        )
        candidate = _candidate()
        candidate["uncertainty_reasons"] = [
            "The supplied evidence does not show pagination limits."
        ]
        analyzer = FakeSemanticAnalyzer(overrides={context.operation_key: candidate})

        result = analyzer.analyze(context)

        self.assertEqual(result.status, "succeeded")
        self.assertEqual(result.semantics.purpose.confidence, "medium")
        self.assertEqual(
            result.semantics.purpose.evidence_refs,
            ("openapi.operation",),
        )
        self.assertEqual(
            result.semantics.uncertainty_reasons,
            ("The supplied evidence does not show pagination limits.",),
        )

    def test_shared_validator_rejects_invalid_schema_and_nonlocal_evidence(self) -> None:
        context = next(
            context
            for context in extract_endpoint_contexts(
                FIXTURE_ROOT / "openapi.json",
                FIXTURE_ROOT / "backend",
            ).endpoint_contexts
            if context.operation_key == "GET /orders"
        )
        cases = (
            (lambda candidate: candidate.pop("agent_description"), "invalid_semantic_output"),
            (
                lambda candidate: candidate.update({"unapproved": "field"}),
                "invalid_semantic_output",
            ),
            (
                lambda candidate: candidate["purpose"].update({"confidence": "certain"}),
                "invalid_semantic_output",
            ),
            (
                lambda candidate: candidate["purpose"].update(
                    {"evidence_refs": ["source.direct_call.99"]}
                ),
                "invalid_evidence_reference",
            ),
            (
                lambda candidate: candidate["purpose"].update({"evidence_refs": []}),
                "invalid_evidence_reference",
            ),
            (
                lambda candidate: candidate.update({"uncertainty_reasons": [""]}),
                "invalid_semantic_output",
            ),
        )

        for mutate, expected_category in cases:
            with self.subTest(expected_category=expected_category):
                candidate = _candidate()
                mutate(candidate)

                result = validate_endpoint_semantics(context, candidate)

                self.assertIsInstance(result, SemanticFailure)
                self.assertEqual(result.category, expected_category)

    def test_fake_injections_fail_only_the_targeted_endpoint(self) -> None:
        contexts = extract_endpoint_contexts(
            FIXTURE_ROOT / "openapi.json",
            FIXTURE_ROOT / "backend",
        ).endpoint_contexts
        invalid_evidence = _candidate()
        invalid_evidence["purpose"].update({"evidence_refs": ["source.direct_call.99"]})
        analyzer = FakeSemanticAnalyzer(
            overrides={
                "GET /orders": {"malformed": True},
                "GET /orders/{order_id}": invalid_evidence,
                "POST /orders": SemanticFailure("analyzer_failed"),
                "PATCH /orders/{order_id}/address": RuntimeError("sentinel secret"),
            }
        )

        analysis = analyze_endpoint_contexts(contexts, analyzer)
        records = {record.context.operation_key: record for record in analysis.records}

        self.assertEqual(records["GET /orders"].analysis.category, "invalid_semantic_output")
        self.assertEqual(
            records["GET /orders/{order_id}"].analysis.category,
            "invalid_evidence_reference",
        )
        self.assertEqual(records["POST /orders"].analysis.category, "analyzer_failed")
        address_failure = records["PATCH /orders/{order_id}/address"].analysis
        self.assertEqual(address_failure.category, "analyzer_failed")
        self.assertNotIn("sentinel secret", address_failure.message)
        self.assertEqual(
            records["POST /orders/{order_id}/archive"].analysis.status,
            "skipped",
        )
        self.assertEqual(records["DELETE /orders/{order_id}"].analysis.status, "succeeded")
        self.assertEqual(records["GET /internal/health"].analysis.status, "succeeded")
        self.assertEqual(records["POST /orders/{order_id}/refund"].analysis.status, "succeeded")
        self.assertTrue(
            all(
                records[context.operation_key].context is context
                for context in contexts
            )
        )

    def test_stage_skips_ambiguous_and_unsupported_contexts_but_analyzes_truncation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            openapi_path = root / "openapi.json"
            openapi_path.write_text(
                json.dumps(
                    {
                        "openapi": "3.1.0",
                        "paths": {
                            "/ambiguous": {"get": {"responses": {}}},
                            "/unsupported": {"put": {"responses": {}}},
                            "/truncated": {"get": {"responses": {}}},
                        },
                    }
                ),
                encoding="utf-8",
            )
            source_root = root / "backend"
            source_root.mkdir()
            (source_root / "app.py").write_text(
                "@app.get('/ambiguous')\n"
                "def first():\n"
                "    pass\n"
                "@app.get('/ambiguous')\n"
                "def second():\n"
                "    pass\n"
                "@app.put('/unsupported')\n"
                "def unsupported():\n"
                "    pass\n"
                "@app.get('/truncated')\n"
                "def truncated():\n"
                f"    payload = '{'x' * 4_100}'\n",
                encoding="utf-8",
            )
            contexts = extract_endpoint_contexts(openapi_path, source_root).endpoint_contexts
            analyzer = FakeSemanticAnalyzer(overrides={"GET /truncated": _candidate()})

            analysis = analyze_endpoint_contexts(contexts, analyzer)
            records = {record.context.operation_key: record for record in analysis.records}

        self.assertEqual(records["GET /ambiguous"].analysis.status, "skipped")
        self.assertEqual(records["PUT /unsupported"].analysis.status, "skipped")
        self.assertEqual(records["GET /truncated"].analysis.status, "succeeded")
        self.assertEqual(analyzer.calls, ["GET /truncated"])
        self.assertTrue(records["GET /truncated"].context.handler.source.truncated)
        self.assertEqual(
            [gap.code for gap in records["GET /truncated"].context.evidence_completeness.gaps],
            ["handler_source_truncated"],
        )


if __name__ == "__main__":
    unittest.main()
