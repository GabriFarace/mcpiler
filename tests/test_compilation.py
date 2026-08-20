import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
import json
import tempfile

from mcpiler.compiler import (
    CompilationError,
    CompileRequest,
    complete_semantic_ir,
    compile_interface,
    effective_risk,
    operational_risk_floor,
)
from mcpiler.__main__ import main
from mcpiler.semantic import (
    EndpointSemanticRecord,
    FakeSemanticAnalyzer,
    RelevanceClaim,
    SemanticAnalysis,
    SemanticFailure,
    SemanticRiskSignal,
    SemanticSuccess,
    analyze_endpoint_contexts,
)
from mcpiler.structural import StructuralAnalysis, extract_endpoint_contexts


FIXTURE_ROOT = Path(__file__).parent.parent / "fixtures" / "order_management"


class RiskPolicyTests(unittest.TestCase):
    def test_operational_risk_floor_uses_the_fixed_method_mapping(self) -> None:
        expected = {
            "GET": "low",
            "POST": "medium",
            "PATCH": "medium",
            "DELETE": "high",
            "PUT": "unknown",
            "HEAD": "unknown",
            "OPTIONS": "unknown",
            "TRACE": "unknown",
        }

        self.assertEqual(
            {method: operational_risk_floor(method) for method in expected},
            expected,
        )

    def test_effective_risk_preserves_or_raises_deterministic_caution(self) -> None:
        medium_signal = SemanticRiskSignal(
            text="The operation changes external state.",
            confidence="high",
            evidence_refs=("source.handler",),
            category="external-side-effect",
            severity="medium",
        )
        high_signal = SemanticRiskSignal(
            text="The operation initiates a financial action.",
            confidence="high",
            evidence_refs=("source.handler",),
            category="financial",
            severity="high",
        )

        cases = (
            ("low", (), "low"),
            ("low", (medium_signal,), "medium"),
            ("medium", (medium_signal,), "medium"),
            ("medium", (high_signal,), "high"),
            ("high", (), "high"),
            ("high", (medium_signal,), "high"),
            ("unknown", (), "unknown"),
            ("unknown", (high_signal,), "unknown"),
        )
        for floor, signals, expected in cases:
            with self.subTest(floor=floor, expected=expected):
                self.assertEqual(effective_risk(floor, signals), expected)


class SemanticIrCompletionTests(unittest.TestCase):
    def test_fixed_fixture_completes_all_operations_with_ordered_policy(self) -> None:
        structural = extract_endpoint_contexts(
            FIXTURE_ROOT / "openapi.json",
            FIXTURE_ROOT / "backend",
        )
        analyzer = FakeSemanticAnalyzer()
        semantic = analyze_endpoint_contexts(structural.endpoint_contexts, analyzer)

        semantic_ir = complete_semantic_ir(structural, semantic)

        records = {
            record.context.operation_key: record for record in semantic_ir.operations
        }
        self.assertEqual(len(records), 8)
        self.assertEqual(
            {
                outcome: sum(
                    record.recommendation.outcome == outcome
                    for record in semantic_ir.operations
                )
                for outcome in ("expose", "hide", "requires-review")
            },
            {"expose": 4, "hide": 1, "requires-review": 3},
        )
        self.assertEqual(
            records["POST /orders/{order_id}/archive"].recommendation.rule_id,
            "CURATION_REVIEW_BLOCKER",
        )
        self.assertEqual(
            records["DELETE /orders/{order_id}"].risk.operational_floor,
            "high",
        )
        self.assertEqual(
            records["DELETE /orders/{order_id}"].risk.effective_risk,
            "high",
        )
        self.assertEqual(
            records["DELETE /orders/{order_id}"].recommendation.rule_id,
            "CURATION_REVIEW_RISK",
        )
        self.assertEqual(
            records["POST /orders/{order_id}/refund"].risk.operational_floor,
            "medium",
        )
        self.assertEqual(
            records["POST /orders/{order_id}/refund"].risk.effective_risk,
            "high",
        )
        self.assertEqual(
            records["GET /internal/health"].risk.effective_risk,
            "low",
        )
        self.assertEqual(
            records["GET /internal/health"].recommendation.rule_id,
            "CURATION_HIDE_INTERNAL",
        )
        self.assertEqual(analyzer.calls, [
            "DELETE /orders/{order_id}",
            "GET /internal/health",
            "GET /orders",
            "GET /orders/{order_id}",
            "PATCH /orders/{order_id}/address",
            "POST /orders",
            "POST /orders/{order_id}/refund",
        ])

    def test_blockers_and_material_uncertainty_precede_lower_policy_rules(self) -> None:
        structural = extract_endpoint_contexts(
            FIXTURE_ROOT / "openapi.json",
            FIXTURE_ROOT / "backend",
        )
        baseline_semantic = analyze_endpoint_contexts(
            structural.endpoint_contexts,
            FakeSemanticAnalyzer(),
        )
        succeeded = {
            record.context.operation_key: record.analysis.semantics
            for record in baseline_semantic.records
            if record.analysis.status == "succeeded"
        }
        low_internal = succeeded["GET /internal/health"].model_copy(
            update={
                "relevance": succeeded["GET /internal/health"].relevance.model_copy(
                    update={"confidence": "low"}
                )
            }
        )
        uncertain_create = succeeded["POST /orders"].model_copy(
            update={"uncertainty_reasons": ("The available evidence is ambiguous.",)}
        )
        low_high_refund = succeeded["POST /orders/{order_id}/refund"].model_copy(
            update={
                "semantic_risk_signals": (
                    succeeded["POST /orders/{order_id}/refund"]
                    .semantic_risk_signals[0]
                    .model_copy(update={"confidence": "low"}),
                )
            }
        )
        low_purpose = succeeded["GET /orders"].model_copy(
            update={
                "purpose": succeeded["GET /orders"].purpose.model_copy(
                    update={"confidence": "low"}
                )
            }
        )
        analyzer = FakeSemanticAnalyzer(
            overrides={
                "DELETE /orders/{order_id}": SemanticFailure("analyzer_failed"),
                "GET /internal/health": low_internal,
                "GET /orders": low_purpose,
                "POST /orders": uncertain_create,
                "POST /orders/{order_id}/refund": low_high_refund,
            }
        )

        completed = complete_semantic_ir(
            structural,
            analyze_endpoint_contexts(structural.endpoint_contexts, analyzer),
        )
        rules = {
            record.context.operation_key: record.recommendation.rule_id
            for record in completed.operations
        }

        self.assertEqual(
            rules["DELETE /orders/{order_id}"], "CURATION_REVIEW_BLOCKER"
        )
        self.assertEqual(
            rules["GET /internal/health"],
            "CURATION_REVIEW_MATERIAL_UNCERTAINTY",
        )
        self.assertEqual(
            rules["GET /orders"], "CURATION_REVIEW_MATERIAL_UNCERTAINTY"
        )
        self.assertEqual(
            rules["POST /orders"], "CURATION_REVIEW_MATERIAL_UNCERTAINTY"
        )
        self.assertEqual(
            rules["POST /orders/{order_id}/refund"],
            "CURATION_REVIEW_MATERIAL_UNCERTAINTY",
        )

    def test_unknown_relevance_and_unhandled_states_fail_conservatively(self) -> None:
        structural = extract_endpoint_contexts(
            FIXTURE_ROOT / "openapi.json",
            FIXTURE_ROOT / "backend",
        )
        context = next(
            context
            for context in structural.endpoint_contexts
            if context.operation_key == "GET /orders"
        )
        succeeded = FakeSemanticAnalyzer().analyze(context)
        unknown = succeeded.semantics.model_copy(
            update={
                "relevance": succeeded.semantics.relevance.model_copy(
                    update={"classification": "unknown"}
                )
            }
        )
        unknown_ir = complete_semantic_ir(
            StructuralAnalysis(structural.handler_source_limit, (context,)),
            SemanticAnalysis((EndpointSemanticRecord(context, SemanticSuccess(unknown)),)),
        )
        self.assertEqual(
            unknown_ir.operations[0].recommendation.rule_id,
            "CURATION_REVIEW_MATERIAL_UNCERTAINTY",
        )

        future_relevance = RelevanceClaim.model_construct(
            text="A future relevance classification.",
            confidence="high",
            evidence_refs=("openapi.operation",),
            classification="future",
        )
        future = succeeded.semantics.model_copy(
            update={"relevance": future_relevance}
        )
        future_ir = complete_semantic_ir(
            StructuralAnalysis(structural.handler_source_limit, (context,)),
            SemanticAnalysis((EndpointSemanticRecord(context, SemanticSuccess(future)),)),
        )
        self.assertEqual(
            future_ir.operations[0].recommendation.rule_id,
            "CURATION_REVIEW_UNHANDLED",
        )


class CompilationAcceptanceTests(unittest.TestCase):
    def test_fake_backed_compile_writes_the_golden_consistent_artifact_set(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            first_output = Path(temporary_directory) / "first"
            second_output = Path(temporary_directory) / "second"
            first_analyzer = FakeSemanticAnalyzer()

            result = compile_interface(
                CompileRequest(
                    openapi_path=FIXTURE_ROOT / "openapi.json",
                    source_root=FIXTURE_ROOT / "backend",
                    output_dir=first_output,
                    analyzer=first_analyzer,
                )
            )
            compile_interface(
                CompileRequest(
                    openapi_path=FIXTURE_ROOT / "openapi.json",
                    source_root=FIXTURE_ROOT / "backend",
                    output_dir=second_output,
                    analyzer=FakeSemanticAnalyzer(),
                )
            )

            semantic_ir = json.loads(
                (first_output / "semantic_ir.json").read_text(encoding="utf-8")
            )
            manifest = json.loads(
                (first_output / "manifest.json").read_text(encoding="utf-8")
            )
            baseline = json.loads(
                (first_output / "baseline_manifest.json").read_text(encoding="utf-8")
            )
            report = (first_output / "risk_report.md").read_text(encoding="utf-8")

            self.assertEqual(result.status, "degraded")
            self.assertEqual(
                result.recommendation_counts,
                {"expose": 4, "hide": 1, "requires-review": 3},
            )
            self.assertEqual(result.degraded_endpoint_count, 1)
            self.assertEqual(len(semantic_ir["operations"]), 8)
            self.assertEqual(len(manifest["tools"]), 4)
            self.assertEqual(len(baseline["tools"]), 8)
            self.assertEqual(semantic_ir["run"]["handler_source_limit"], 4_000)
            self.assertEqual(
                semantic_ir["run"]["analyzer_provenance"][0]["analyzer_id"],
                "fake-semantic-analyzer",
            )

            outcomes = {
                operation["context"]["operation_key"]: operation["recommendation"][
                    "outcome"
                ]
                for operation in semantic_ir["operations"]
            }
            proposed_keys = [
                tool["_meta"]["mcpiler"]["source_operation"]["operation_key"]
                for tool in manifest["tools"]
            ]
            baseline_keys = [
                tool["_meta"]["mcpiler"]["source_operation"]["operation_key"]
                for tool in baseline["tools"]
            ]
            all_keys = [
                operation["context"]["operation_key"]
                for operation in semantic_ir["operations"]
            ]
            self.assertEqual(
                proposed_keys,
                [key for key in all_keys if outcomes[key] == "expose"],
            )
            self.assertEqual(baseline_keys, all_keys)
            self.assertTrue(all(report.count(f"`{key}`") == 1 for key in all_keys))
            archive = next(
                operation
                for operation in semantic_ir["operations"]
                if operation["context"]["operation_key"]
                == "POST /orders/{order_id}/archive"
            )
            self.assertEqual(archive["context"]["source_match"]["status"], "unmatched")
            self.assertEqual(archive["analysis"]["status"], "skipped")
            self.assertEqual(
                archive["recommendation"]["rule_id"], "CURATION_REVIEW_BLOCKER"
            )
            refund = next(
                operation
                for operation in semantic_ir["operations"]
                if operation["context"]["operation_key"]
                == "POST /orders/{order_id}/refund"
            )
            self.assertEqual(
                refund["analysis"]["semantics"]["semantic_risk_signals"][0][
                    "confidence"
                ],
                "high",
            )
            self.assertEqual(
                refund["risk"]["reasons"][1]["code"],
                "semantic_signal_escalation",
            )
            self.assertEqual(
                [tool["name"] for tool in manifest["tools"]],
                [
                    "list_orders",
                    "get_order",
                    "update_order_address",
                    "create_order",
                ],
            )
            self.assertNotIn("relevance", baseline["tools"][0]["_meta"]["mcpiler"])
            self.assertEqual(
                set(manifest["tools"][0]),
                {"name", "description", "inputSchema", "outputSchema", "_meta"},
            )
            self.assertNotIn("annotations", manifest["tools"][0])
            self.assertIn("human review", report)
            self.assertIn("not a deployable MCP server", report)
            self.assertIn("effective_risk_high [source.handler]", report)
            self.assertEqual(len(first_analyzer.calls), 7)

            for artifact_name in (
                "semantic_ir.json",
                "manifest.json",
                "baseline_manifest.json",
                "risk_report.md",
            ):
                self.assertEqual(
                    (first_output / artifact_name).read_bytes(),
                    (second_output / artifact_name).read_bytes(),
                )

    def test_endpoint_semantic_failures_remain_visible_and_isolated(self) -> None:
        structural = extract_endpoint_contexts(
            FIXTURE_ROOT / "openapi.json",
            FIXTURE_ROOT / "backend",
        )
        get_orders = next(
            context
            for context in structural.endpoint_contexts
            if context.operation_key == "GET /orders/{order_id}"
        )
        invalid_reference = FakeSemanticAnalyzer().analyze(get_orders).semantics.model_dump(
            mode="json"
        )
        invalid_reference["purpose"]["evidence_refs"] = ["source.missing"]
        analyzer = FakeSemanticAnalyzer(
            overrides={
                "GET /orders": {"malformed": True},
                "GET /orders/{order_id}": invalid_reference,
                "POST /orders": RuntimeError("must not escape"),
            }
        )

        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "artifacts"
            result = compile_interface(
                CompileRequest(
                    FIXTURE_ROOT / "openapi.json",
                    FIXTURE_ROOT / "backend",
                    output,
                    analyzer,
                )
            )
            semantic_ir = json.loads(
                (output / "semantic_ir.json").read_text(encoding="utf-8")
            )
            baseline = json.loads(
                (output / "baseline_manifest.json").read_text(encoding="utf-8")
            )
            report = (output / "risk_report.md").read_text(encoding="utf-8")

        records = {
            operation["context"]["operation_key"]: operation
            for operation in semantic_ir["operations"]
        }
        self.assertEqual(
            records["GET /orders"]["analysis"]["category"],
            "invalid_semantic_output",
        )
        self.assertEqual(
            records["GET /orders/{order_id}"]["analysis"]["category"],
            "invalid_evidence_reference",
        )
        self.assertEqual(
            records["POST /orders"]["analysis"]["category"], "analyzer_failed"
        )
        self.assertTrue(
            all(
                records[key]["recommendation"]["rule_id"]
                == "CURATION_REVIEW_BLOCKER"
                for key in (
                    "GET /orders",
                    "GET /orders/{order_id}",
                    "POST /orders",
                )
            )
        )
        self.assertEqual(result.status, "degraded")
        self.assertEqual(result.degraded_endpoint_count, 4)
        self.assertEqual(len(baseline["tools"]), 8)
        self.assertNotIn("must not escape", json.dumps(semantic_ir))
        self.assertTrue(
            all(report.count(f"`{key}`") == 1 for key in records)
        )

    def test_duplicate_operation_ids_use_stable_method_path_fallback_names(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source_root = root / "backend"
            source_root.mkdir()
            (source_root / "app.py").write_text(
                "@app.get('/orders')\n"
                "def list_orders():\n"
                "    return []\n"
                "@app.get('/orders/{order_id}')\n"
                "def get_order(order_id: str):\n"
                "    return {}\n",
                encoding="utf-8",
            )
            openapi_path = root / "openapi.json"
            openapi_path.write_text(
                json.dumps(
                    {
                        "openapi": "3.1.0",
                        "paths": {
                            "/orders": {
                                "get": {
                                    "operationId": "duplicate",
                                    "responses": {},
                                }
                            },
                            "/orders/{order_id}": {
                                "get": {
                                    "operationId": "duplicate",
                                    "parameters": [
                                        {
                                            "name": "order_id",
                                            "in": "path",
                                            "required": True,
                                            "schema": {"type": "string"},
                                        }
                                    ],
                                    "responses": {},
                                }
                            },
                        },
                    }
                ),
                encoding="utf-8",
            )
            output = root / "artifacts"

            compile_interface(
                CompileRequest(
                    openapi_path,
                    source_root,
                    output,
                    FakeSemanticAnalyzer(),
                )
            )
            proposed = json.loads(
                (output / "manifest.json").read_text(encoding="utf-8")
            )
            baseline = json.loads(
                (output / "baseline_manifest.json").read_text(encoding="utf-8")
            )

        expected = ["get_orders", "get_orders_by_order_id"]
        self.assertEqual([tool["name"] for tool in proposed["tools"]], expected)
        self.assertEqual([tool["name"] for tool in baseline["tools"]], expected)

    def test_ir_invariant_failure_is_global_before_artifact_publication(self) -> None:
        structural = extract_endpoint_contexts(
            FIXTURE_ROOT / "openapi.json",
            FIXTURE_ROOT / "backend",
        )
        semantic = analyze_endpoint_contexts(
            structural.endpoint_contexts,
            FakeSemanticAnalyzer(),
        )
        incomplete_semantic = SemanticAnalysis(semantic.records[:-1])

        with self.assertRaises(CompilationError) as raised:
            complete_semantic_ir(structural, incomplete_semantic)

        self.assertEqual(raised.exception.category, "invariant_failed")

    def test_global_input_and_artifact_write_failures_are_clear(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            output = root / "artifacts"
            with self.assertRaises(CompilationError) as missing_input:
                compile_interface(
                    CompileRequest(
                        root / "missing.json",
                        FIXTURE_ROOT / "backend",
                        output,
                        FakeSemanticAnalyzer(),
                    )
                )
            self.assertEqual(missing_input.exception.category, "openapi_unreadable")
            self.assertFalse(output.exists())

            output.write_text("not a directory", encoding="utf-8")
            with self.assertRaises(CompilationError) as write_failure:
                compile_interface(
                    CompileRequest(
                        FIXTURE_ROOT / "openapi.json",
                        FIXTURE_ROOT / "backend",
                        output,
                        FakeSemanticAnalyzer(),
                    )
                )
            self.assertEqual(write_failure.exception.category, "artifact_write_failed")
            self.assertEqual(output.read_text(encoding="utf-8"), "not a directory")

    def test_serialization_failure_is_global_and_publishes_no_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source_root = root / "backend"
            source_root.mkdir()
            (source_root / "app.py").write_text(
                "@app.get('/orders')\n"
                "def list_orders():\n"
                "    return []\n",
                encoding="utf-8",
            )
            openapi_path = root / "openapi.json"
            openapi_path.write_text(
                '{"openapi":"3.1.0","paths":{"/orders":{"get":'
                '{"operationId":"list_orders","responses":{"200":'
                '{"content":{"application/json":{"schema":'
                '{"type":"number","default":NaN}}}}}}}}}',
                encoding="utf-8",
            )
            output = root / "artifacts"

            with self.assertRaises(CompilationError) as raised:
                compile_interface(
                    CompileRequest(
                        openapi_path,
                        source_root,
                        output,
                        FakeSemanticAnalyzer(),
                    )
                )

            self.assertEqual(raised.exception.category, "serialization_failed")
            self.assertFalse(output.exists())


class CliTests(unittest.TestCase):
    def test_cli_reports_success_degraded_success_and_global_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source_root = root / "backend"
            source_root.mkdir()
            (source_root / "app.py").write_text(
                "@app.get('/orders')\n"
                "def list_orders():\n"
                "    return []\n",
                encoding="utf-8",
            )
            openapi_path = root / "openapi.json"
            openapi_path.write_text(
                json.dumps(
                    {
                        "openapi": "3.1.0",
                        "paths": {
                            "/orders": {
                                "get": {
                                    "operationId": "list_orders",
                                    "responses": {},
                                }
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )

            success_out = StringIO()
            with redirect_stdout(success_out):
                success_exit = main(
                    [
                        "--openapi",
                        str(openapi_path),
                        "--source-root",
                        str(source_root),
                        "--output-dir",
                        str(root / "success"),
                    ]
                )
            self.assertEqual(success_exit, 0)
            self.assertIn("status=success", success_out.getvalue())
            self.assertIn("expose=1", success_out.getvalue())

            degraded_out = StringIO()
            with redirect_stdout(degraded_out):
                degraded_exit = main(
                    [
                        "--openapi",
                        str(FIXTURE_ROOT / "openapi.json"),
                        "--source-root",
                        str(FIXTURE_ROOT / "backend"),
                        "--output-dir",
                        str(root / "degraded"),
                    ]
                )
            self.assertEqual(degraded_exit, 0)
            self.assertIn("status=degraded", degraded_out.getvalue())
            self.assertIn("degraded=1", degraded_out.getvalue())

            failure_err = StringIO()
            with redirect_stderr(failure_err):
                failure_exit = main(
                    [
                        "--openapi",
                        str(root / "missing.json"),
                        "--source-root",
                        str(source_root),
                        "--output-dir",
                        str(root / "failure"),
                    ]
                )
            self.assertEqual(failure_exit, 1)
            self.assertIn("openapi_unreadable", failure_err.getvalue())


if __name__ == "__main__":
    unittest.main()
