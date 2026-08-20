"""Thin command-line adapter for fake or explicitly selected live compilation."""

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
    parser.add_argument("--analyzer", choices=("fake", "live"), default="fake")
    arguments = parser.parse_args(argv)

    if arguments.analyzer == "live":
        try:
            from .live import LangChainOpenAISemanticAnalyzer, LiveAnalyzerInitializationError

            analyzer = LangChainOpenAISemanticAnalyzer.from_environment()
        except Exception as error:
            category = getattr(error, "category", "analyzer_initialization_failed")
            message = (
                str(error)
                if category == "analyzer_initialization_failed"
                else "The live semantic analyzer could not be initialized."
            )
            print(
                f"compilation failed [{category}]: {message}",
                file=sys.stderr,
            )
            return 1
    else:
        analyzer = FakeSemanticAnalyzer()

    try:
        result = compile_interface(
            CompileRequest(
                openapi_path=arguments.openapi,
                source_root=arguments.source_root,
                output_dir=arguments.output_dir,
                analyzer=analyzer,
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
