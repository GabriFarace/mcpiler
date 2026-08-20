"""Deterministic risk, curation, and artifact compilation."""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, fields, is_dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Literal

from pydantic import BaseModel

from .semantic import (
    AnalysisProvenance,
    EndpointSemanticRecord,
    EndpointSemantics,
    SemanticAnalysis,
    SemanticAnalyzer,
    SemanticClaim,
    SemanticRiskSignal,
    SemanticStageResult,
    SemanticSuccess,
    analyze_endpoint_contexts,
    semantic_claims,
)
from .structural import (
    EndpointContext,
    FrozenJsonObject,
    MediaSchema,
    OpenApiOperation,
    StructuralAnalysis,
    StructuralInputError,
    StructuralInputErrorCategory,
    extract_endpoint_contexts,
)


type RiskLevel = Literal["low", "medium", "high", "unknown"]
type Recommendation = Literal["expose", "hide", "requires-review"]
type CurationRuleId = Literal[
    "CURATION_REVIEW_BLOCKER",
    "CURATION_REVIEW_MATERIAL_UNCERTAINTY",
    "CURATION_REVIEW_RISK",
    "CURATION_HIDE_INTERNAL",
    "CURATION_EXPOSE_USER_FACING",
    "CURATION_REVIEW_UNHANDLED",
]
type CompilationStatus = Literal["success", "degraded"]
type CompilationErrorCategory = StructuralInputErrorCategory | Literal[
    "invariant_failed",
    "serialization_failed",
    "artifact_write_failed",
]

_NOTICE = (
    "Candidate MCP interface decision aids requiring human review; not a deployable "
    "MCP server, authorization result, publication approval, or security guarantee."
)
_ARTIFACT_NAMES = (
    "semantic_ir.json",
    "manifest.json",
    "baseline_manifest.json",
    "risk_report.md",
)

_OPERATIONAL_RISK_FLOORS: dict[str, RiskLevel] = {
    "GET": "low",
    "POST": "medium",
    "PATCH": "medium",
    "DELETE": "high",
}


@dataclass(frozen=True, slots=True)
class PolicyReason:
    code: str
    message: str
    evidence_refs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class RiskAssessment:
    operational_floor: RiskLevel
    effective_risk: RiskLevel
    reasons: tuple[PolicyReason, ...]


@dataclass(frozen=True, slots=True)
class CurationDecision:
    outcome: Recommendation
    rule_id: CurationRuleId
    reasons: tuple[PolicyReason, ...]


@dataclass(frozen=True, slots=True)
class SemanticIrOperation:
    context: EndpointContext
    analysis: SemanticStageResult
    risk: RiskAssessment
    recommendation: CurationDecision


@dataclass(frozen=True, slots=True)
class SemanticIrRun:
    compiler_version: str
    policy_version: str
    handler_source_limit: int
    analyzer_provenance: tuple[AnalysisProvenance, ...]


@dataclass(frozen=True, slots=True)
class SemanticIr:
    schema_version: str
    run: SemanticIrRun
    operations: tuple[SemanticIrOperation, ...]


@dataclass(frozen=True, slots=True)
class CompileRequest:
    openapi_path: Path
    source_root: Path
    output_dir: Path
    analyzer: SemanticAnalyzer


@dataclass(frozen=True, slots=True)
class CompilationResult:
    status: CompilationStatus
    artifact_paths: Mapping[str, Path]
    recommendation_counts: Mapping[Recommendation, int]
    degraded_endpoint_count: int


class CompilationError(Exception):
    """A stable global failure that prevents a successful artifact set."""

    def __init__(self, category: CompilationErrorCategory, message: str) -> None:
        super().__init__(message)
        self.category = category


def operational_risk_floor(method: str) -> RiskLevel:
    """Return the fixed likelihood-of-state-change floor for an HTTP method."""
    return _OPERATIONAL_RISK_FLOORS.get(method.upper(), "unknown")


def effective_risk(
    floor: RiskLevel,
    signals: tuple[SemanticRiskSignal, ...],
) -> RiskLevel:
    """Combine a fixed floor with validated signals without lowering caution."""
    if floor == "unknown":
        return "unknown"
    levels: dict[RiskLevel, int] = {"low": 0, "medium": 1, "high": 2, "unknown": 3}
    signal_levels = (signal.severity for signal in signals)
    return max((floor, *signal_levels), key=levels.__getitem__)


def complete_semantic_ir(
    structural: StructuralAnalysis,
    semantic: SemanticAnalysis,
) -> SemanticIr:
    """Complete authoritative endpoint records with deterministic policy output."""
    semantic_contexts = tuple(record.context for record in semantic.records)
    if semantic_contexts != structural.endpoint_contexts:
        raise CompilationError(
            "invariant_failed",
            "Semantic records do not cover the structural endpoint contexts exactly.",
        )
    operations = tuple(_complete_operation(record) for record in semantic.records)
    provenances = {
        record.analysis.semantics.analysis_provenance
        for record in semantic.records
        if isinstance(record.analysis, SemanticSuccess)
    }
    analyzer_provenance = tuple(
        sorted(
            provenances,
            key=lambda item: (
                item.analyzer_id,
                item.provider_id or "",
                item.model_id or "",
                item.schema_version,
                item.prompt_version,
            ),
        )
    )
    return SemanticIr(
        schema_version="mcpiler.semantic-ir.v1",
        run=SemanticIrRun(
            compiler_version="0.1.0",
            policy_version="t03-v1",
            handler_source_limit=structural.handler_source_limit,
            analyzer_provenance=analyzer_provenance,
        ),
        operations=operations,
    )


def compile_interface(request: CompileRequest) -> CompilationResult:
    """Run the offline compiler and publish one internally consistent artifact set."""
    try:
        structural = extract_endpoint_contexts(request.openapi_path, request.source_root)
    except StructuralInputError as error:
        raise CompilationError(error.category, str(error)) from error
    semantic = analyze_endpoint_contexts(structural.endpoint_contexts, request.analyzer)
    semantic_ir = complete_semantic_ir(structural, semantic)
    artifacts = _render_artifacts(semantic_ir)
    validate_artifact_invariants(semantic_ir, artifacts)
    artifact_paths = _write_artifacts(request.output_dir, artifacts)

    counts = {
        outcome: sum(
            operation.recommendation.outcome == outcome
            for operation in semantic_ir.operations
        )
        for outcome in ("expose", "hide", "requires-review")
    }
    degraded_count = sum(
        operation.context.evidence_completeness.status == "incomplete"
        or operation.analysis.status != "succeeded"
        for operation in semantic_ir.operations
    )
    return CompilationResult(
        status="degraded" if degraded_count else "success",
        artifact_paths=artifact_paths,
        recommendation_counts=counts,
        degraded_endpoint_count=degraded_count,
    )


def _complete_operation(record: EndpointSemanticRecord) -> SemanticIrOperation:
    context = record.context
    signals = (
        record.analysis.semantics.semantic_risk_signals
        if isinstance(record.analysis, SemanticSuccess)
        else ()
    )
    floor = operational_risk_floor(context.openapi_operation.method)
    effective = effective_risk(floor, signals)
    risk = RiskAssessment(
        operational_floor=floor,
        effective_risk=effective,
        reasons=_risk_reasons(floor, effective, signals),
    )
    return SemanticIrOperation(
        context=context,
        analysis=record.analysis,
        risk=risk,
        recommendation=_curation_decision(record, risk),
    )


def _risk_reasons(
    floor: RiskLevel,
    effective: RiskLevel,
    signals: tuple[SemanticRiskSignal, ...],
) -> tuple[PolicyReason, ...]:
    reasons = [
        PolicyReason(
            code="http_method_floor",
            message=f"The HTTP method establishes a {floor} operational/action floor.",
            evidence_refs=("openapi.operation",),
        )
    ]
    if effective != floor:
        reasons.append(
            PolicyReason(
                code="semantic_signal_escalation",
                message=(
                    "Validated semantic risk evidence raised the effective risk "
                    f"to {effective}."
                ),
                evidence_refs=_evidence_refs(
                    signal for signal in signals if signal.severity == effective
                ),
            )
        )
    return tuple(reasons)


def _curation_decision(
    record: EndpointSemanticRecord,
    risk: RiskAssessment,
) -> CurationDecision:
    blocker_reasons = _blocker_reasons(record)
    if blocker_reasons:
        return CurationDecision(
            outcome="requires-review",
            rule_id="CURATION_REVIEW_BLOCKER",
            reasons=blocker_reasons,
        )

    if not isinstance(record.analysis, SemanticSuccess):
        return CurationDecision(
            outcome="requires-review",
            rule_id="CURATION_REVIEW_UNHANDLED",
            reasons=(_unhandled_reason(),),
        )
    semantics = record.analysis.semantics
    uncertainty_reasons = _material_uncertainty_reasons(semantics)
    if uncertainty_reasons:
        return CurationDecision(
            outcome="requires-review",
            rule_id="CURATION_REVIEW_MATERIAL_UNCERTAINTY",
            reasons=uncertainty_reasons,
        )

    if risk.effective_risk in {"high", "unknown"}:
        evidence_refs = (
            ("openapi.operation",)
            if risk.operational_floor in {"high", "unknown"}
            else _evidence_refs(
                signal
                for signal in semantics.semantic_risk_signals
                if signal.severity == "high"
            )
        )
        return CurationDecision(
            outcome="requires-review",
            rule_id="CURATION_REVIEW_RISK",
            reasons=(
                PolicyReason(
                    code=f"effective_risk_{risk.effective_risk}",
                    message=(
                        f"The effective operational/action risk is {risk.effective_risk}."
                    ),
                    evidence_refs=evidence_refs,
                ),
            ),
        )

    if semantics.relevance.classification == "internal/infrastructure":
        return CurationDecision(
            outcome="hide",
            rule_id="CURATION_HIDE_INTERNAL",
            reasons=(
                PolicyReason(
                    code="supported_internal_operation",
                    message="Supported evidence classifies the operation as internal/infrastructure.",
                    evidence_refs=tuple(sorted(set(semantics.relevance.evidence_refs))),
                ),
            ),
        )

    if semantics.relevance.classification == "user-facing":
        return CurationDecision(
            outcome="expose",
            rule_id="CURATION_EXPOSE_USER_FACING",
            reasons=(
                PolicyReason(
                    code="supported_user_facing_operation",
                    message="Supported evidence classifies the operation as user-facing.",
                    evidence_refs=tuple(sorted(set(semantics.relevance.evidence_refs))),
                ),
            ),
        )

    return CurationDecision(
        outcome="requires-review",
        rule_id="CURATION_REVIEW_UNHANDLED",
        reasons=(_unhandled_reason(),),
    )


def _blocker_reasons(record: EndpointSemanticRecord) -> tuple[PolicyReason, ...]:
    context = record.context
    reasons: list[PolicyReason] = []
    if context.source_match.status != "matched":
        reasons.append(
            PolicyReason(
                code=f"source_match_{context.source_match.status}",
                message=(
                    "The operation does not have one supported, unique source match."
                ),
            )
        )
    for gap in context.evidence_completeness.gaps:
        reasons.append(
            PolicyReason(
                code=f"evidence_gap_{gap.code}",
                message=gap.message,
            )
        )
    if record.analysis.status == "failed":
        reasons.append(
            PolicyReason(
                code=f"semantic_{record.analysis.category}",
                message=record.analysis.message,
            )
        )
    elif record.analysis.status == "skipped" and context.source_match.status == "matched":
        reasons.append(
            PolicyReason(
                code="semantic_analysis_skipped",
                message="Semantic analysis was skipped for the operation.",
            )
        )
    return tuple(reasons)


def _material_uncertainty_reasons(
    semantics: EndpointSemantics,
) -> tuple[PolicyReason, ...]:
    claims = semantic_claims(semantics)
    low_confidence_claims = tuple(claim for claim in claims if claim.confidence == "low")
    reasons: list[PolicyReason] = []
    if low_confidence_claims:
        reasons.append(
            PolicyReason(
                code="low_confidence_semantic_claim",
                message="At least one semantic claim has low confidence.",
                evidence_refs=_evidence_refs(low_confidence_claims),
            )
        )
    if semantics.uncertainty_reasons:
        reasons.append(
            PolicyReason(
                code="explicit_semantic_uncertainty",
                message="The semantic analysis reports explicit uncertainty.",
            )
        )
    if semantics.relevance.classification == "unknown":
        reasons.append(
            PolicyReason(
                code="unknown_relevance",
                message="The operation relevance is unknown.",
                evidence_refs=tuple(sorted(set(semantics.relevance.evidence_refs))),
            )
        )
    return tuple(reasons)


def _evidence_refs(claims: Iterable[SemanticClaim]) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                evidence_ref
                for claim in claims
                for evidence_ref in claim.evidence_refs
            }
        )
    )


def _unhandled_reason() -> PolicyReason:
    return PolicyReason(
        code="unhandled_policy_state",
        message="The operation reached an unhandled conservative policy state.",
    )


def _render_artifacts(semantic_ir: SemanticIr) -> dict[str, str]:
    names = _tool_names(semantic_ir.operations)
    proposed_tools = [
        _proposed_tool(operation, names[operation.context.operation_key])
        for operation in semantic_ir.operations
        if operation.recommendation.outcome == "expose"
    ]
    baseline_tools = [
        _baseline_tool(operation, names[operation.context.operation_key])
        for operation in semantic_ir.operations
    ]
    documents: dict[str, object] = {
        "semantic_ir.json": _semantic_ir_document(semantic_ir),
        "manifest.json": {
            "tools": proposed_tools,
            "_meta": {
                "mcpiler": {
                    "schema_version": "mcpiler.manifest.v1",
                    "notice": _NOTICE,
                }
            },
        },
        "baseline_manifest.json": {
            "tools": baseline_tools,
            "_meta": {
                "mcpiler": {
                    "schema_version": "mcpiler.baseline-manifest.v1",
                    "notice": _NOTICE,
                }
            },
        },
    }
    try:
        rendered = {
            name: json.dumps(
                document,
                indent=2,
                sort_keys=True,
                ensure_ascii=False,
                allow_nan=False,
            )
            + "\n"
            for name, document in documents.items()
        }
        rendered["risk_report.md"] = _render_risk_report(semantic_ir)
    except (TypeError, ValueError) as error:
        raise CompilationError(
            "serialization_failed",
            "The review artifacts could not be serialized.",
        ) from error
    return rendered


def _proposed_tool(operation: SemanticIrOperation, name: str) -> dict[str, object]:
    if not isinstance(operation.analysis, SemanticSuccess):
        raise CompilationError(
            "invariant_failed",
            "An exposed operation does not have successful semantic analysis.",
        )
    semantics = operation.analysis.semantics
    tool = _base_tool(
        operation.context.openapi_operation,
        name,
        semantics.agent_description.text,
    )
    tool["_meta"] = {
        "mcpiler": {
            "source_operation": _source_operation_identity(operation.context),
            "purpose": _json_value(semantics.purpose),
            "preconditions": _json_value(semantics.preconditions),
            "side_effects": _json_value(semantics.side_effects),
            "relevance": _json_value(semantics.relevance),
            "semantic_risk_signals": _json_value(semantics.semantic_risk_signals),
            "risk": _json_value(operation.risk),
            "recommendation": _json_value(operation.recommendation),
            "analysis_provenance": _json_value(semantics.analysis_provenance),
        }
    }
    return tool


def _baseline_tool(operation: SemanticIrOperation, name: str) -> dict[str, object]:
    openapi_operation = operation.context.openapi_operation
    tool = _base_tool(
        openapi_operation,
        name,
        _openapi_description(openapi_operation),
    )
    tool["_meta"] = {
        "mcpiler": {
            "source_operation": _source_operation_identity(operation.context),
        }
    }
    return tool


def _base_tool(
    operation: OpenApiOperation,
    name: str,
    description: str,
) -> dict[str, object]:
    tool: dict[str, object] = {
        "name": name,
        "description": description,
        "inputSchema": _input_schema(operation),
    }
    output_schema = _output_schema(operation)
    if output_schema is not None:
        tool["outputSchema"] = output_schema
    return tool


def _input_schema(operation: OpenApiOperation) -> dict[str, object]:
    properties: dict[str, object] = {}
    required: list[str] = []
    for parameter in operation.parameters:
        schema = dict(_json_value(parameter.schema)) if parameter.schema is not None else {}
        if parameter.description and "description" not in schema:
            schema["description"] = parameter.description
        properties[parameter.name] = schema
        if parameter.required:
            required.append(parameter.name)
    if operation.request_body is not None and operation.request_body.schemas:
        body_schema = _preferred_media_schema(operation.request_body.schemas)
        properties["body"] = _json_value(body_schema)
        if operation.request_body.required:
            required.append("body")

    schema: dict[str, object] = {
        "type": "object",
        "properties": properties,
        "additionalProperties": False,
    }
    if required:
        schema["required"] = required
    return schema


def _output_schema(operation: OpenApiOperation) -> object | None:
    for response in operation.responses:
        if response.status_code.startswith("2") and response.schemas:
            return _json_value(_preferred_media_schema(response.schemas))
    return None


def _preferred_media_schema(schemas: tuple[MediaSchema, ...]) -> FrozenJsonObject:
    selected = next(
        (item for item in schemas if item.media_type == "application/json"),
        schemas[0],
    )
    return selected.schema


def _openapi_description(operation: OpenApiOperation) -> str:
    values = tuple(
        value for value in (operation.summary, operation.description) if value
    )
    if not values:
        return f"{operation.method} {operation.path}"
    if len(values) == 2 and values[0].rstrip(".") == values[1].rstrip("."):
        return values[0]
    return "\n\n".join(values)


def _source_operation_identity(context: EndpointContext) -> dict[str, object]:
    operation = context.openapi_operation
    return {
        "operation_key": context.operation_key,
        "method": operation.method,
        "path": operation.path,
        "operation_id": operation.operation_id,
    }


def _tool_names(
    operations: tuple[SemanticIrOperation, ...],
) -> dict[str, str]:
    operation_id_counts: dict[str, int] = {}
    for record in operations:
        operation_id = record.context.openapi_operation.operation_id
        if operation_id and _valid_tool_name(operation_id):
            operation_id_counts[operation_id] = operation_id_counts.get(operation_id, 0) + 1

    reserved_names = {
        operation_id
        for operation_id, count in operation_id_counts.items()
        if count == 1
    }
    assigned: dict[str, str] = {}
    used: set[str] = set()
    for record in operations:
        context = record.context
        operation_id = context.openapi_operation.operation_id
        if (
            operation_id
            and _valid_tool_name(operation_id)
            and operation_id_counts[operation_id] == 1
        ):
            name = operation_id
        else:
            name = _fallback_tool_name(context)
        if not operation_id or operation_id_counts.get(operation_id) != 1:
            name = _available_fallback_name(
                name,
                context.operation_key,
                used | reserved_names,
            )
        elif name in used:
            raise CompilationError(
                "invariant_failed",
                "A unique OpenAPI operation ID could not be preserved as a tool name.",
            )
        assigned[context.operation_key] = name
        used.add(name)
    return assigned


def _available_fallback_name(
    base_name: str,
    operation_key: str,
    unavailable: set[str],
) -> str:
    if base_name not in unavailable:
        return base_name
    digest = hashlib.sha256(operation_key.encode("utf-8")).hexdigest()[:8]
    candidate = f"{base_name}_{digest}"
    suffix = 2
    while candidate in unavailable:
        candidate = f"{base_name}_{digest}_{suffix}"
        suffix += 1
    return candidate


def _valid_tool_name(value: str) -> bool:
    return re.fullmatch(r"[A-Za-z0-9_-]+", value) is not None


def _fallback_tool_name(context: EndpointContext) -> str:
    segments: list[str] = [context.openapi_operation.method.lower()]
    for raw_segment in context.openapi_operation.path.strip("/").split("/"):
        if not raw_segment:
            segments.append("root")
        elif raw_segment.startswith("{") and raw_segment.endswith("}"):
            segments.extend(("by", _name_token(raw_segment[1:-1])))
        else:
            segments.append(_name_token(raw_segment))
    return "_".join(segments)


def _name_token(value: str) -> str:
    token = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_").lower()
    return token or "value"


def _render_risk_report(semantic_ir: SemanticIr) -> str:
    counts = {
        outcome: sum(
            operation.recommendation.outcome == outcome
            for operation in semantic_ir.operations
        )
        for outcome in ("expose", "hide", "requires-review")
    }
    lines = [
        "# MCPiler Risk and Curation Report",
        "",
        _NOTICE,
        "",
        (
            "Operational/action floors estimate likely state change only; they are "
            "not confidentiality, authorization, business-impact, or security classifications."
        ),
        "",
        (
            f"Naive baseline: {len(semantic_ir.operations)} tools. Curated candidate: "
            f"{counts['expose']} tools. Recommendations: {counts['expose']} expose, "
            f"{counts['requires-review']} requires-review, {counts['hide']} hide."
        ),
        "",
        "| Operation | Baseline | Evidence | Semantic | Relevance | Floor | Signals | Effective | Recommendation | Policy | Gaps |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for operation in semantic_ir.operations:
        semantics = (
            operation.analysis.semantics
            if isinstance(operation.analysis, SemanticSuccess)
            else None
        )
        relevance = semantics.relevance.classification if semantics else "unknown"
        signals = (
            "; ".join(
                f"{signal.category}:{signal.severity} ({signal.confidence}) [{', '.join(signal.evidence_refs)}]"
                for signal in semantics.semantic_risk_signals
            )
            if semantics and semantics.semantic_risk_signals
            else "none"
        )
        evidence = (
            f"{operation.context.source_match.status}/"
            f"{operation.context.evidence_completeness.status}"
        )
        policy_reasons = ", ".join(
            reason.code
            + (
                f" [{', '.join(reason.evidence_refs)}]"
                if reason.evidence_refs
                else ""
            )
            + f": {reason.message}"
            for reason in operation.recommendation.reasons
        )
        policy = f"{operation.recommendation.rule_id}: {policy_reasons}"
        gaps = (
            "; ".join(gap.code for gap in operation.context.evidence_completeness.gaps)
            or "none"
        )
        values = (
            f"`{operation.context.operation_key}`",
            "yes",
            evidence,
            operation.analysis.status,
            relevance,
            operation.risk.operational_floor,
            signals,
            operation.risk.effective_risk,
            operation.recommendation.outcome,
            policy,
            gaps,
        )
        lines.append("| " + " | ".join(_markdown_cell(value) for value in values) + " |")
    return "\n".join(lines) + "\n"


def _markdown_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "<br>")


def _json_value(value: object) -> object:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, tuple | list):
        return [_json_value(item) for item in value]
    return value


def validate_artifact_invariants(
    semantic_ir: SemanticIr,
    artifacts: Mapping[str, str],
) -> None:
    """Reject rendered projections that drift from their authoritative Semantic IR."""
    keys = [operation.context.operation_key for operation in semantic_ir.operations]
    if keys != sorted(keys) or len(keys) != len(set(keys)):
        raise CompilationError(
            "invariant_failed",
            "Semantic IR operations are not unique and canonically ordered.",
        )
    try:
        semantic_ir_document = json.loads(artifacts["semantic_ir.json"])
        manifest = json.loads(artifacts["manifest.json"])
        baseline = json.loads(artifacts["baseline_manifest.json"])
        proposed_records = [
            (
                tool["_meta"]["mcpiler"]["source_operation"]["operation_key"],
                tool["name"],
            )
            for tool in manifest["tools"]
        ]
        baseline_records = [
            (
                tool["_meta"]["mcpiler"]["source_operation"]["operation_key"],
                tool["name"],
            )
            for tool in baseline["tools"]
        ]
    except (KeyError, TypeError, json.JSONDecodeError) as error:
        raise CompilationError(
            "invariant_failed",
            "The rendered artifact set is incomplete or invalid.",
        ) from error
    proposed_keys = [key for key, _ in proposed_records]
    baseline_keys = [key for key, _ in baseline_records]
    exposed_keys = [
        operation.context.operation_key
        for operation in semantic_ir.operations
        if operation.recommendation.outcome == "expose"
    ]
    proposed_names = [name for _, name in proposed_records]
    baseline_names = [name for _, name in baseline_records]
    baseline_name_by_key = dict(baseline_records)
    report = artifacts.get("risk_report.md", "")
    if (
        semantic_ir_document != _semantic_ir_document(semantic_ir)
        or proposed_keys != exposed_keys
        or baseline_keys != keys
        or len(proposed_names) != len(set(proposed_names))
        or len(baseline_names) != len(set(baseline_names))
        or any(
            baseline_name_by_key.get(key) != name
            for key, name in proposed_records
        )
        or any(report.count(f"`{key}`") != 1 for key in keys)
    ):
        raise CompilationError(
            "invariant_failed",
            "The rendered artifacts do not cover the authoritative Semantic IR consistently.",
        )


def _semantic_ir_document(semantic_ir: SemanticIr) -> dict[str, object]:
    return {
        "schema_version": semantic_ir.schema_version,
        "notice": _NOTICE,
        "run": _json_value(semantic_ir.run),
        "operations": _json_value(semantic_ir.operations),
    }


def _write_artifacts(
    output_dir: Path,
    artifacts: Mapping[str, str],
) -> dict[str, Path]:
    staged: list[tuple[Path, Path]] = []
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        for name in _ARTIFACT_NAMES:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=output_dir,
                prefix=f".{name}.",
                delete=False,
            ) as temporary_file:
                temporary_file.write(artifacts[name])
                temporary_path = Path(temporary_file.name)
            staged.append((temporary_path, output_dir / name))
        for temporary_path, final_path in staged:
            os.replace(temporary_path, final_path)
    except (KeyError, OSError, UnicodeError) as error:
        for temporary_path, _ in staged:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass
        raise CompilationError(
            "artifact_write_failed",
            "The complete review artifact set could not be written.",
        ) from error
    return {name: output_dir / name for name in _ARTIFACT_NAMES}
