"""Endpoint-local semantic analysis contracts and validation."""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from .structural import EndpointContext


type Confidence = Literal["high", "medium", "low"]
type Relevance = Literal["user-facing", "internal/infrastructure", "unknown"]
type RiskCategory = Literal[
    "financial",
    "destructive",
    "sensitive-data",
    "privileged",
    "external-side-effect",
    "other",
]
type RiskSeverity = Literal["medium", "high"]
type FailureCategory = Literal[
    "analyzer_failed",
    "invalid_semantic_output",
    "invalid_evidence_reference",
]

_FAILURE_MESSAGES: dict[FailureCategory, str] = {
    "analyzer_failed": "The semantic analyzer did not return an analysis.",
    "invalid_semantic_output": "The semantic output did not match the required schema.",
    "invalid_evidence_reference": (
        "The semantic output referenced evidence outside the endpoint context."
    ),
}


class _StrictSemanticModel(BaseModel):
    """Strict immutable semantic data, accepting JSON arrays as collections."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    @field_validator("*", mode="before")
    @classmethod
    def normalize_json_arrays(cls, value: object) -> object:
        return tuple(value) if isinstance(value, list) else value


class SemanticClaim(_StrictSemanticModel):
    text: str = Field(min_length=1)
    confidence: Confidence
    evidence_refs: tuple[str, ...] = Field(min_length=1)


class RelevanceClaim(SemanticClaim):
    classification: Relevance


class SemanticRiskSignal(SemanticClaim):
    category: RiskCategory
    severity: RiskSeverity


class AnalysisProvenance(_StrictSemanticModel):
    analyzer_id: str = Field(min_length=1)
    provider_id: str | None
    model_id: str | None
    schema_version: str = Field(min_length=1)
    prompt_version: str = Field(min_length=1)


class EndpointSemantics(_StrictSemanticModel):
    purpose: SemanticClaim
    agent_description: SemanticClaim
    preconditions: tuple[SemanticClaim, ...]
    side_effects: tuple[SemanticClaim, ...]
    relevance: RelevanceClaim
    semantic_risk_signals: tuple[SemanticRiskSignal, ...]
    uncertainty_reasons: tuple[str, ...]
    analysis_provenance: AnalysisProvenance

    @field_validator("uncertainty_reasons")
    @classmethod
    def require_explicit_uncertainty_reasons(
        cls,
        reasons: tuple[str, ...],
    ) -> tuple[str, ...]:
        if any(not reason.strip() for reason in reasons):
            raise ValueError("uncertainty reasons must not be blank")
        return reasons


@dataclass(frozen=True, slots=True)
class SemanticSuccess:
    semantics: EndpointSemantics
    status: Literal["succeeded"] = field(default="succeeded", init=False)


@dataclass(frozen=True, slots=True)
class SemanticFailure:
    category: FailureCategory
    status: Literal["failed"] = field(default="failed", init=False)
    message: str = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "message", _FAILURE_MESSAGES[self.category])


@dataclass(frozen=True, slots=True)
class SemanticSkipped:
    source_match_status: Literal["unmatched", "ambiguous", "unsupported"]
    reason_codes: tuple[str, ...]
    status: Literal["skipped"] = field(default="skipped", init=False)


type SemanticAnalyzerResult = SemanticSuccess | SemanticFailure
type SemanticStageResult = SemanticSuccess | SemanticFailure | SemanticSkipped


class SemanticAnalyzer(Protocol):
    """Analyze one context; source and OpenAPI text are untrusted data, never instructions.

    A future textual adapter must delimit any serialized context as untrusted data,
    provide no tools or code execution, and must not log raw prompts or responses.
    """

    def analyze(self, context: EndpointContext) -> SemanticAnalyzerResult:
        """Return a validated analysis or a sanitized endpoint-local failure."""


@dataclass(frozen=True, slots=True)
class EndpointSemanticRecord:
    context: EndpointContext
    analysis: SemanticStageResult


@dataclass(frozen=True, slots=True)
class SemanticAnalysis:
    records: tuple[EndpointSemanticRecord, ...]


def validate_endpoint_semantics(
    context: EndpointContext,
    candidate: object,
) -> SemanticAnalyzerResult:
    """Validate model-shaped data and require references from this context only."""
    try:
        semantics = (
            candidate
            if isinstance(candidate, EndpointSemantics)
            else EndpointSemantics.model_validate(candidate)
        )
    except ValidationError as error:
        return SemanticFailure(_validation_failure_category(error))

    evidence_ids = {evidence.id for evidence in context.evidence}
    if any(
        evidence_ref not in evidence_ids
        for claim in semantic_claims(semantics)
        for evidence_ref in claim.evidence_refs
    ):
        return SemanticFailure("invalid_evidence_reference")
    return SemanticSuccess(semantics)


def analyze_endpoint_contexts(
    contexts: Iterable[EndpointContext],
    analyzer: SemanticAnalyzer,
) -> SemanticAnalysis:
    """Analyze supported contexts while retaining every original structural context."""
    records: list[EndpointSemanticRecord] = []
    for context in contexts:
        if context.source_match.status != "matched":
            records.append(
                EndpointSemanticRecord(
                    context=context,
                    analysis=SemanticSkipped(
                        source_match_status=context.source_match.status,
                        reason_codes=context.source_match.reason_codes,
                    ),
                )
            )
            continue

        try:
            result: object = analyzer.analyze(context)
        except Exception:
            analysis: SemanticStageResult = SemanticFailure("analyzer_failed")
        else:
            if isinstance(result, SemanticFailure):
                analysis = result
            elif isinstance(result, SemanticSuccess):
                analysis = validate_endpoint_semantics(context, result.semantics)
            else:
                analysis = validate_endpoint_semantics(context, result)
        records.append(EndpointSemanticRecord(context=context, analysis=analysis))
    return SemanticAnalysis(records=tuple(records))


def _validation_failure_category(error: ValidationError) -> FailureCategory:
    errors = error.errors()
    if errors and all("evidence_refs" in issue["loc"] for issue in errors):
        return "invalid_evidence_reference"
    return "invalid_semantic_output"


def semantic_claims(semantics: EndpointSemantics) -> tuple[SemanticClaim, ...]:
    """Return every evidence-linked claim in authoritative schema order."""
    return (
        semantics.purpose,
        semantics.agent_description,
        *semantics.preconditions,
        *semantics.side_effects,
        semantics.relevance,
        *semantics.semantic_risk_signals,
    )


@dataclass(slots=True)
class FakeSemanticAnalyzer:
    """Deterministic fixed-fixture analyzer used by normal tests only."""

    overrides: Mapping[str, object | SemanticFailure | Exception] = field(
        default_factory=dict
    )
    calls: list[str] = field(default_factory=list)

    def analyze(self, context: EndpointContext) -> SemanticAnalyzerResult:
        self.calls.append(context.operation_key)
        override = self.overrides.get(context.operation_key, _NO_OVERRIDE)
        if isinstance(override, Exception):
            raise override
        if isinstance(override, SemanticFailure):
            return override
        candidate = (
            override
            if override is not _NO_OVERRIDE
            else _FIXTURE_CANDIDATES.get(context.operation_key)
        )
        if candidate is None:
            return SemanticFailure("analyzer_failed")
        return validate_endpoint_semantics(context, candidate)


def _claim(text: str, evidence_refs: list[str]) -> dict[str, object]:
    return {"text": text, "confidence": "high", "evidence_refs": evidence_refs}


def _fixture_candidate(
    purpose: str,
    description: str,
    relevance: Relevance,
    *,
    preconditions: list[dict[str, object]] | None = None,
    side_effects: list[dict[str, object]] | None = None,
    signals: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    return {
        "purpose": _claim(purpose, ["openapi.operation"]),
        "agent_description": _claim(description, ["openapi.operation"]),
        "preconditions": preconditions or [],
        "side_effects": side_effects or [],
        "relevance": {
            **_claim(f"This is a {relevance} operation.", ["openapi.operation"]),
            "classification": relevance,
        },
        "semantic_risk_signals": signals or [],
        "uncertainty_reasons": [],
        "analysis_provenance": {
            "analyzer_id": "fake-semantic-analyzer",
            "provider_id": None,
            "model_id": None,
            "schema_version": "v1",
            "prompt_version": "fixture-v1",
        },
    }


_FIXTURE_CANDIDATES: dict[str, dict[str, object]] = {
    "GET /orders": _fixture_candidate(
        "List orders.", "List available orders for a user.", "user-facing"
    ),
    "GET /orders/{order_id}": _fixture_candidate(
        "Retrieve an order.", "Retrieve one order by identifier.", "user-facing"
    ),
    "POST /orders": _fixture_candidate(
        "Create an order.", "Create a new order for a customer.", "user-facing"
    ),
    "PATCH /orders/{order_id}/address": _fixture_candidate(
        "Update an order address.",
        "Update an order delivery address before shipment.",
        "user-facing",
        preconditions=[
            _claim("The order must not already be shipped.", ["source.handler"])
        ],
    ),
    "POST /orders/{order_id}/refund": _fixture_candidate(
        "Refund an order.", "Issue a refund for an eligible order.", "user-facing",
        side_effects=[_claim("The handler issues a refund.", ["source.handler"])],
        signals=[
            {
                **_claim("The handler initiates a financial refund.", ["source.handler"]),
                "category": "financial",
                "severity": "high",
            }
        ],
    ),
    "DELETE /orders/{order_id}": _fixture_candidate(
        "Delete an order.", "Delete an order by identifier.", "user-facing",
        side_effects=[_claim("The handler deletes an order.", ["source.handler"])],
        signals=[
            {
                **_claim("The handler deletes an order.", ["source.handler"]),
                "category": "destructive",
                "severity": "high",
            }
        ],
    ),
    "GET /internal/health": _fixture_candidate(
        "Read service health.",
        "Read the internal service health status.",
        "internal/infrastructure",
    ),
}

_NO_OVERRIDE = object()
