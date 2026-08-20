import os
from pathlib import Path
import unittest
from unittest.mock import patch

from langchain_core.callbacks.manager import CallbackManager
from langchain_core.tracers.context import tracing_v2_callback_var
from langsmith.run_helpers import get_tracing_context

from mcpiler.live import LangChainOpenAISemanticAnalyzer, LiveAnalyzerSettings
from mcpiler.semantic import FakeSemanticAnalyzer
from mcpiler.structural import extract_endpoint_contexts


FIXTURE_ROOT = Path(__file__).parent.parent / "fixtures" / "order_management"


class _TracingProbeStructuredModel:
    def __init__(self, parsed: object) -> None:
        self.parsed = parsed
        self.tracing_enabled: object = "not-invoked"
        self.callback_handlers: list[object] | None = None

    def invoke(self, messages: object, **options: object) -> dict[str, object]:
        self.tracing_enabled = get_tracing_context()["enabled"]
        self.callback_handlers = CallbackManager.configure([], []).handlers
        return {"parsed": self.parsed, "parsing_error": None}


class _ChatModelProbe:
    def __init__(self) -> None:
        self.output_schema: type[object] | None = None

    def with_structured_output(
        self,
        schema: type[object],
        **options: object,
    ) -> object:
        self.output_schema = schema
        return object()


class LiveSemanticAnalyzerTests(unittest.TestCase):
    def test_analyze_disables_ambient_langsmith_tracing(self) -> None:
        context = next(
            context
            for context in extract_endpoint_contexts(
                FIXTURE_ROOT / "openapi.json",
                FIXTURE_ROOT / "backend",
            ).endpoint_contexts
            if context.operation_key == "GET /orders"
        )
        parsed = FakeSemanticAnalyzer().analyze(context).semantics
        structured_model = _TracingProbeStructuredModel(parsed)
        analyzer = LangChainOpenAISemanticAnalyzer(
            LiveAnalyzerSettings("secret", "model", None, 30.0, 1),
            structured_model,
        )

        with patch.dict(os.environ, {"LANGSMITH_TRACING": "true"}):
            result = analyzer.analyze(context)

        self.assertEqual(result.status, "succeeded")
        self.assertIs(structured_model.tracing_enabled, False)
        self.assertEqual(structured_model.callback_handlers, [])

    def test_analyze_detaches_an_inherited_langchain_tracer(self) -> None:
        context = next(
            context
            for context in extract_endpoint_contexts(
                FIXTURE_ROOT / "openapi.json",
                FIXTURE_ROOT / "backend",
            ).endpoint_contexts
            if context.operation_key == "GET /orders"
        )
        parsed = FakeSemanticAnalyzer().analyze(context).semantics
        structured_model = _TracingProbeStructuredModel(parsed)
        analyzer = LangChainOpenAISemanticAnalyzer(
            LiveAnalyzerSettings("secret", "model", None, 30.0, 1),
            structured_model,
        )
        ambient_tracer = object()
        token = tracing_v2_callback_var.set(ambient_tracer)
        try:
            result = analyzer.analyze(context)
        finally:
            tracing_v2_callback_var.reset(token)

        self.assertEqual(result.status, "succeeded")
        self.assertNotIn(ambient_tracer, structured_model.callback_handlers)

    def test_provider_output_excludes_adapter_owned_provenance(self) -> None:
        chat_model = _ChatModelProbe()
        environment = {
            "MCPILER_LIVE_MODEL": "model",
            "MCPILER_LIVE_API_KEY": "secret",
        }

        with patch.dict(os.environ, environment, clear=True), patch(
            "mcpiler.live.ChatOpenAI",
            return_value=chat_model,
        ):
            LangChainOpenAISemanticAnalyzer.from_environment()

        properties = chat_model.output_schema.model_json_schema()["properties"]
        self.assertEqual(
            set(properties),
            {
                "purpose",
                "agent_description",
                "preconditions",
                "side_effects",
                "relevance",
                "semantic_risk_signals",
                "uncertainty_reasons",
            },
        )

    def test_example_environment_has_runnable_nonsecret_defaults(self) -> None:
        values = dict(
            line.split("=", 1)
            for line in (Path(__file__).parent.parent / ".env.example")
            .read_text(encoding="utf-8")
            .splitlines()
            if line and not line.startswith("#")
        )
        values["MCPILER_LIVE_MODEL"] = "local-model"

        settings = LiveAnalyzerSettings.from_environment(values)

        self.assertEqual(settings.base_url, "http://127.0.0.1:1234/v1")
        self.assertEqual(settings.api_key, "lm-studio")
        self.assertEqual(settings.timeout_seconds, 30.0)
        self.assertEqual(settings.max_retries, 1)
        self.assertEqual(values["LANGSMITH_TRACING"], "false")


if __name__ == "__main__":
    unittest.main()
