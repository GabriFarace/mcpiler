"""Thin command-line adapter for deterministic fixture compilation."""

import argparse
from collections.abc import Sequence
from pathlib import Path
import sys

from .compiler import CompilationError, CompileRequest, compile_interface
from .semantic import FakeSemanticAnalyzer


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compile candidate MCP review artifacts.")
    parser.add_argument("--openapi", required=True, type=Path)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    arguments = parser.parse_args(argv)

    try:
        result = compile_interface(
            CompileRequest(
                openapi_path=arguments.openapi,
                source_root=arguments.source_root,
                output_dir=arguments.output_dir,
                analyzer=FakeSemanticAnalyzer(),
            )
        )
    except CompilationError as error:
        print(f"compilation failed [{error.category}]: {error}", file=sys.stderr)
        return 1

    counts = result.recommendation_counts
    print(
        f"status={result.status} expose={counts['expose']} hide={counts['hide']} "
        f"requires-review={counts['requires-review']} "
        f"degraded={result.degraded_endpoint_count}"
    )
    for name, path in result.artifact_paths.items():
        print(f"{name}={path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
