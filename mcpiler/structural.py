"""Deterministic OpenAPI and bounded Python source evidence extraction."""

import ast
from collections.abc import Mapping
from dataclasses import dataclass
import json
from pathlib import Path
from types import MappingProxyType
from typing import Literal


type JsonValue = None | bool | int | float | str | list[JsonValue] | dict[str, JsonValue]
type JsonObject = dict[str, JsonValue]
type FrozenJsonValue = (
    None
    | bool
    | int
    | float
    | str
    | tuple[FrozenJsonValue, ...]
    | Mapping[str, FrozenJsonValue]
)
type FrozenJsonObject = Mapping[str, FrozenJsonValue]
type SourceMatchStatus = Literal["matched", "unmatched", "ambiguous", "unsupported"]
type EvidenceOrigin = Literal["openapi", "source"]
type CompletenessStatus = Literal["complete", "incomplete"]
type StructuralInputErrorCategory = Literal[
    "openapi_unreadable",
    "openapi_invalid_json",
    "openapi_invalid_structure",
    "source_root_unreadable",
    "source_syntax_error",
]

HANDLER_SOURCE_LIMIT = 4_000
_OPENAPI_METHODS = frozenset(
    {"delete", "get", "head", "options", "patch", "post", "put", "trace"}
)
_SUPPORTED_ROUTE_METHODS = frozenset({"delete", "get", "patch", "post"})


class StructuralInputError(Exception):
    """A stable global input failure that prevents structural analysis."""

    def __init__(self, category: StructuralInputErrorCategory, message: str) -> None:
        super().__init__(message)
        self.category = category


@dataclass(frozen=True, slots=True)
class MediaSchema:
    media_type: str
    schema: FrozenJsonObject


@dataclass(frozen=True, slots=True)
class OpenApiParameter:
    name: str
    location: str
    required: bool
    description: str | None
    schema: FrozenJsonObject | None


@dataclass(frozen=True, slots=True)
class RequestBodyEvidence:
    required: bool
    schemas: tuple[MediaSchema, ...]


@dataclass(frozen=True, slots=True)
class ResponseEvidence:
    status_code: str
    schemas: tuple[MediaSchema, ...]


@dataclass(frozen=True, slots=True)
class OpenApiOperation:
    method: str
    path: str
    operation_id: str | None
    summary: str | None
    description: str | None
    parameters: tuple[OpenApiParameter, ...]
    request_body: RequestBodyEvidence | None
    responses: tuple[ResponseEvidence, ...]


@dataclass(frozen=True, slots=True)
class BoundedText:
    text: str
    original_char_count: int
    truncated: bool


@dataclass(frozen=True, slots=True)
class SourceLocation:
    relative_path: str
    start_line: int
    end_line: int


@dataclass(frozen=True, slots=True)
class SourceMatch:
    status: SourceMatchStatus
    reason_codes: tuple[str, ...]
    candidate_locations: tuple[SourceLocation, ...]


@dataclass(frozen=True, slots=True)
class HandlerEvidence:
    name: str
    relative_path: str
    start_line: int
    end_line: int
    signature: str
    docstring: BoundedText | None
    source: BoundedText
    direct_call_names: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class OpenApiProvenance:
    json_pointer: str


@dataclass(frozen=True, slots=True)
class SourceProvenance:
    relative_path: str
    start_line: int
    end_line: int


type EvidenceProvenance = OpenApiProvenance | SourceProvenance


@dataclass(frozen=True, slots=True)
class EvidenceRecord:
    id: str
    origin: EvidenceOrigin
    kind: str
    value: FrozenJsonValue
    provenance: EvidenceProvenance

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _freeze_json(self.value))


@dataclass(frozen=True, slots=True)
class EvidenceGap:
    code: str
    message: str


@dataclass(frozen=True, slots=True)
class EvidenceCompleteness:
    status: CompletenessStatus
    gaps: tuple[EvidenceGap, ...]


@dataclass(frozen=True, slots=True)
class EndpointContext:
    operation_key: str
    openapi_operation: OpenApiOperation
    source_match: SourceMatch
    handler: HandlerEvidence | None
    evidence: tuple[EvidenceRecord, ...]
    evidence_completeness: EvidenceCompleteness


@dataclass(frozen=True, slots=True)
class StructuralAnalysis:
    handler_source_limit: int
    endpoint_contexts: tuple[EndpointContext, ...]


@dataclass(frozen=True, slots=True)
class _OpenApiRecord:
    operation: OpenApiOperation
    json_pointer: str


@dataclass(frozen=True, slots=True)
class _Route:
    method: str
    path: str
    supported: bool
    handler_node: ast.FunctionDef | ast.AsyncFunctionDef
    source: str
    relative_path: str
    decorator_location: SourceLocation


def extract_endpoint_contexts(
    openapi_path: Path,
    source_root: Path,
) -> StructuralAnalysis:
    """Build canonically ordered endpoint contexts without executing target code."""
    document = _load_openapi(openapi_path)
    try:
        operations = _openapi_operations(document)
    except (AttributeError, KeyError, TypeError, ValueError) as error:
        raise StructuralInputError(
            "openapi_invalid_structure",
            "The OpenAPI document does not contain structurally usable operations.",
        ) from error
    routes = _literal_routes(source_root)

    contexts = tuple(
        sorted(
            (_endpoint_context(record, routes) for record in operations),
            key=lambda context: context.operation_key,
        )
    )
    return StructuralAnalysis(
        handler_source_limit=HANDLER_SOURCE_LIMIT,
        endpoint_contexts=contexts,
    )


def _load_openapi(openapi_path: Path) -> JsonObject:
    try:
        raw_document = openapi_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise StructuralInputError(
            "openapi_unreadable",
            "The OpenAPI document is not readable.",
        ) from error
    try:
        document = json.loads(raw_document)
    except json.JSONDecodeError as error:
        raise StructuralInputError(
            "openapi_invalid_json",
            "The OpenAPI document is not valid JSON.",
        ) from error
    if not isinstance(document, dict) or not isinstance(document.get("paths"), dict):
        raise StructuralInputError(
            "openapi_invalid_structure",
            "The OpenAPI document must be an object containing a paths object.",
        )
    return document


def _endpoint_context(
    record: _OpenApiRecord,
    routes: dict[str, tuple[_Route, ...]],
) -> EndpointContext:
    operation = record.operation
    operation_key = f"{operation.method} {operation.path}"
    candidates = routes.get(operation_key, ())
    locations = tuple(candidate.decorator_location for candidate in candidates)

    if len(candidates) > 1:
        source_match = SourceMatch(
            status="ambiguous",
            reason_codes=("multiple_literal_route_matches",),
            candidate_locations=locations,
        )
        handler = None
    elif len(candidates) == 1 and not candidates[0].supported:
        source_match = SourceMatch(
            status="unsupported",
            reason_codes=("unsupported_http_method_decorator",),
            candidate_locations=locations,
        )
        handler = None
    elif len(candidates) == 1:
        source_match = SourceMatch(
            status="matched",
            reason_codes=(),
            candidate_locations=locations,
        )
        handler = _handler_evidence(candidates[0])
    else:
        source_match = SourceMatch(
            status="unmatched",
            reason_codes=("no_literal_route_match",),
            candidate_locations=(),
        )
        handler = None

    evidence = _openapi_evidence(operation, record.json_pointer) + _source_evidence(
        candidates, handler
    )
    completeness = _evidence_completeness(source_match, handler)
    return EndpointContext(
        operation_key=operation_key,
        openapi_operation=operation,
        source_match=source_match,
        handler=handler,
        evidence=evidence,
        evidence_completeness=completeness,
    )


def _openapi_operations(document: object) -> tuple[_OpenApiRecord, ...]:
    paths = document["paths"]
    operations: list[_OpenApiRecord] = []
    for raw_path, path_item in paths.items():
        path = _normalize_path(raw_path)
        for raw_method, raw_operation in path_item.items():
            method = raw_method.lower()
            if method not in _OPENAPI_METHODS:
                continue
            operation = _object(raw_operation)
            operations.append(
                _OpenApiRecord(
                    operation=OpenApiOperation(
                        method=method.upper(),
                        path=path,
                        operation_id=_optional_string(operation.get("operationId")),
                        summary=_optional_string(operation.get("summary")),
                        description=_optional_string(operation.get("description")),
                        parameters=_parameters(operation),
                        request_body=_request_body(operation),
                        responses=_responses(operation),
                    ),
                    json_pointer=(
                        f"#/paths/{_pointer_segment(raw_path)}/{method}"
                    ),
                )
            )
    return tuple(operations)


def _parameters(operation: JsonObject) -> tuple[OpenApiParameter, ...]:
    raw_parameters = operation.get("parameters", [])
    if not isinstance(raw_parameters, list):
        raise ValueError("parameters must be an array")
    parameters: list[OpenApiParameter] = []
    for raw_parameter_value in raw_parameters:
        raw_parameter = _object(raw_parameter_value)
        parameters.append(
            OpenApiParameter(
                name=_required_string(raw_parameter.get("name")),
                location=_required_string(raw_parameter.get("in")),
                required=_boolean(raw_parameter.get("required", False)),
                description=_optional_string(raw_parameter.get("description")),
                schema=_optional_frozen_object(raw_parameter.get("schema")),
            )
        )
    return tuple(parameters)


def _request_body(operation: JsonObject) -> RequestBodyEvidence | None:
    raw_body = operation.get("requestBody")
    if raw_body is None:
        return None
    body = _object(raw_body)
    return RequestBodyEvidence(
        required=_boolean(body.get("required", False)),
        schemas=_media_schemas(_object(body.get("content", {}))),
    )


def _responses(operation: JsonObject) -> tuple[ResponseEvidence, ...]:
    raw_responses = _object(operation.get("responses", {}))
    responses: list[ResponseEvidence] = []
    for status_code, raw_response_value in sorted(raw_responses.items()):
        raw_response = _object(raw_response_value)
        responses.append(
            ResponseEvidence(
                status_code=status_code,
                schemas=_media_schemas(_object(raw_response.get("content", {}))),
            )
        )
    return tuple(responses)


def _media_schemas(content: JsonObject) -> tuple[MediaSchema, ...]:
    schemas: list[MediaSchema] = []
    for media_type, media_value in sorted(content.items()):
        media = _object(media_value)
        schema = media.get("schema")
        if schema is not None:
            schemas.append(
                MediaSchema(
                    media_type=media_type,
                    schema=_freeze_object(_object(schema)),
                )
            )
    return tuple(schemas)


def _object(value: JsonValue) -> JsonObject:
    if not isinstance(value, dict):
        raise ValueError("expected an object")
    return value


def _optional_frozen_object(value: JsonValue) -> FrozenJsonObject | None:
    if value is None:
        return None
    return _freeze_object(_object(value))


def _required_string(value: JsonValue) -> str:
    if not isinstance(value, str):
        raise ValueError("expected a string")
    return value


def _optional_string(value: JsonValue) -> str | None:
    if value is None:
        return None
    return _required_string(value)


def _boolean(value: JsonValue) -> bool:
    if not isinstance(value, bool):
        raise ValueError("expected a boolean")
    return value


def _freeze_object(value: JsonObject) -> FrozenJsonObject:
    frozen = _freeze_json(value)
    if not isinstance(frozen, Mapping):
        raise TypeError("expected a frozen object")
    return frozen


def _freeze_json(value: object) -> FrozenJsonValue:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Mapping):
        return MappingProxyType(
            {str(key): _freeze_json(item) for key, item in value.items()}
        )
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_json(item) for item in value)
    raise TypeError("evidence contains a non-JSON value")


def _literal_routes(source_root: Path) -> dict[str, tuple[_Route, ...]]:
    if not source_root.is_dir():
        raise StructuralInputError(
            "source_root_unreadable",
            "The Python source root is not a readable directory.",
        )
    routes: dict[str, list[_Route]] = {}
    try:
        source_paths = sorted(source_root.rglob("*.py"))
    except OSError as error:
        raise StructuralInputError(
            "source_root_unreadable",
            "The Python source root could not be inspected.",
        ) from error
    for source_path in source_paths:
        try:
            source = source_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            raise StructuralInputError(
                "source_root_unreadable",
                "A Python source file is not readable.",
            ) from error
        try:
            tree = ast.parse(source, filename=str(source_path))
        except SyntaxError as error:
            relative_path = source_path.relative_to(source_root).as_posix()
            raise StructuralInputError(
                "source_syntax_error",
                f"Python syntax could not be parsed in {relative_path}:{error.lineno}.",
            ) from error
        relative_path = source_path.relative_to(source_root).as_posix()
        for node in tree.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for decorator in node.decorator_list:
                route = _literal_route(decorator, node, source, relative_path)
                if route is None:
                    continue
                key = f"{route.method} {route.path}"
                routes.setdefault(key, []).append(route)
    return {key: tuple(value) for key, value in routes.items()}


def _literal_route(
    decorator: ast.expr,
    handler_node: ast.FunctionDef | ast.AsyncFunctionDef,
    source: str,
    relative_path: str,
) -> _Route | None:
    if not isinstance(decorator, ast.Call) or not isinstance(decorator.func, ast.Attribute):
        return None
    method = decorator.func.attr.lower()
    if method not in _OPENAPI_METHODS or not decorator.args:
        return None
    path_argument = decorator.args[0]
    if not isinstance(path_argument, ast.Constant) or not isinstance(path_argument.value, str):
        return None
    return _Route(
        method=method.upper(),
        path=_normalize_path(path_argument.value),
        supported=method in _SUPPORTED_ROUTE_METHODS,
        handler_node=handler_node,
        source=source,
        relative_path=relative_path,
        decorator_location=SourceLocation(
            relative_path=relative_path,
            start_line=decorator.lineno,
            end_line=decorator.end_lineno or decorator.lineno,
        ),
    )


def _handler_evidence(route: _Route) -> HandlerEvidence:
    node = route.handler_node
    raw_source = ast.get_source_segment(route.source, node) or ""
    raw_docstring = ast.get_docstring(node, clean=False)
    return HandlerEvidence(
        name=node.name,
        relative_path=route.relative_path,
        start_line=node.lineno,
        end_line=node.end_lineno or node.lineno,
        signature=_signature(node),
        docstring=_bounded(raw_docstring) if raw_docstring is not None else None,
        source=_bounded(raw_source),
        direct_call_names=_direct_call_names(node),
    )


def _signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
    returns = f" -> {ast.unparse(node.returns)}" if node.returns is not None else ""
    return f"{prefix} {node.name}({ast.unparse(node.args)}){returns}"


class _DirectCallCollector(ast.NodeVisitor):
    def __init__(self) -> None:
        self.names: list[str] = []

    def visit_Call(self, node: ast.Call) -> None:
        name = _call_name(node.func)
        if name is not None and name not in self.names:
            self.names.append(name)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        return

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        return

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        return

    def visit_Lambda(self, node: ast.Lambda) -> None:
        return


def _direct_call_names(node: ast.FunctionDef | ast.AsyncFunctionDef) -> tuple[str, ...]:
    collector = _DirectCallCollector()
    for statement in node.body:
        collector.visit(statement)
    return tuple(collector.names)


def _call_name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _call_name(node.value)
        if parent is not None:
            return f"{parent}.{node.attr}"
    return None


def _bounded(value: str) -> BoundedText:
    return BoundedText(
        text=value[:HANDLER_SOURCE_LIMIT],
        original_char_count=len(value),
        truncated=len(value) > HANDLER_SOURCE_LIMIT,
    )


def _openapi_evidence(
    operation: OpenApiOperation,
    pointer: str,
) -> tuple[EvidenceRecord, ...]:
    evidence: list[EvidenceRecord] = [
        EvidenceRecord(
            id="openapi.operation",
            origin="openapi",
            kind="openapi.operation",
            value={
                "method": operation.method,
                "path": operation.path,
                "operation_id": operation.operation_id,
                "summary": operation.summary,
                "description": operation.description,
            },
            provenance=OpenApiProvenance(json_pointer=pointer),
        )
    ]
    for index, parameter in enumerate(operation.parameters):
        evidence.append(
            EvidenceRecord(
                id=f"openapi.parameter.{index}",
                origin="openapi",
                kind="openapi.parameter",
                value={
                    "name": parameter.name,
                    "location": parameter.location,
                    "required": parameter.required,
                    "description": parameter.description,
                    "schema": parameter.schema,
                },
                provenance=OpenApiProvenance(
                    json_pointer=f"{pointer}/parameters/{index}"
                ),
            )
        )
    if operation.request_body is not None:
        for index, media_schema in enumerate(operation.request_body.schemas):
            evidence.append(
                EvidenceRecord(
                    id=f"openapi.request_body_schema.{index}",
                    origin="openapi",
                    kind="openapi.request_body_schema",
                    value={
                        "required": operation.request_body.required,
                        "media_type": media_schema.media_type,
                        "schema": media_schema.schema,
                    },
                    provenance=OpenApiProvenance(
                        json_pointer=(
                            f"{pointer}/requestBody/content/"
                            f"{_pointer_segment(media_schema.media_type)}/schema"
                        )
                    ),
                )
            )
    response_index = 0
    for response in operation.responses:
        for media_schema in response.schemas:
            evidence.append(
                EvidenceRecord(
                    id=f"openapi.response_schema.{response_index}",
                    origin="openapi",
                    kind="openapi.response_schema",
                    value={
                        "status_code": response.status_code,
                        "media_type": media_schema.media_type,
                        "schema": media_schema.schema,
                    },
                    provenance=OpenApiProvenance(
                        json_pointer=(
                            f"{pointer}/responses/{_pointer_segment(response.status_code)}/content/"
                            f"{_pointer_segment(media_schema.media_type)}/schema"
                        )
                    ),
                )
            )
            response_index += 1
    return tuple(evidence)


def _source_evidence(
    candidates: tuple[_Route, ...],
    handler: HandlerEvidence | None,
) -> tuple[EvidenceRecord, ...]:
    evidence: list[EvidenceRecord] = []
    for index, candidate in enumerate(candidates):
        location = candidate.decorator_location
        evidence.append(
            EvidenceRecord(
                id=f"source.route.{index}",
                origin="source",
                kind="source.route",
                value={"method": candidate.method, "path": candidate.path},
                provenance=_source_provenance(location),
            )
        )
    if handler is None:
        return tuple(evidence)

    handler_provenance = SourceProvenance(
        relative_path=handler.relative_path,
        start_line=handler.start_line,
        end_line=handler.end_line,
    )
    evidence.extend(
        [
            EvidenceRecord(
                id="source.signature",
                origin="source",
                kind="source.signature",
                value=handler.signature,
                provenance=handler_provenance,
            ),
            EvidenceRecord(
                id="source.handler",
                origin="source",
                kind="source.handler",
                value=handler.source.text,
                provenance=handler_provenance,
            ),
        ]
    )
    if handler.docstring is not None:
        evidence.append(
            EvidenceRecord(
                id="source.docstring",
                origin="source",
                kind="source.docstring",
                value=handler.docstring.text,
                provenance=handler_provenance,
            )
        )
    for index, call_name in enumerate(handler.direct_call_names):
        evidence.append(
            EvidenceRecord(
                id=f"source.direct_call.{index}",
                origin="source",
                kind="source.direct_call",
                value=call_name,
                provenance=handler_provenance,
            )
        )
    return tuple(evidence)


def _source_provenance(location: SourceLocation) -> SourceProvenance:
    return SourceProvenance(
        relative_path=location.relative_path,
        start_line=location.start_line,
        end_line=location.end_line,
    )


def _evidence_completeness(
    source_match: SourceMatch,
    handler: HandlerEvidence | None,
) -> EvidenceCompleteness:
    gaps: list[EvidenceGap] = []
    if source_match.status == "unmatched":
        gaps.append(EvidenceGap("source_unmatched", "No exact literal route match."))
    elif source_match.status == "ambiguous":
        gaps.append(EvidenceGap("source_ambiguous", "Multiple exact literal route matches."))
    elif source_match.status == "unsupported":
        gaps.append(EvidenceGap("source_unsupported", "The exact route form is unsupported."))
    if handler is not None and handler.source.truncated:
        gaps.append(EvidenceGap("handler_source_truncated", "Handler source exceeded 4000 characters."))
    if handler is not None and handler.docstring is not None and handler.docstring.truncated:
        gaps.append(EvidenceGap("handler_docstring_truncated", "Handler docstring exceeded 4000 characters."))
    return EvidenceCompleteness(
        status="incomplete" if gaps else "complete",
        gaps=tuple(gaps),
    )


def _pointer_segment(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def _normalize_path(path: str) -> str:
    normalized = path if path.startswith("/") else f"/{path}"
    if normalized != "/":
        normalized = normalized.rstrip("/")
    return normalized
