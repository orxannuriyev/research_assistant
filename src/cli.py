"""Command-line parsing and execution for the Research Assistant."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from src.engine import ResearchEngine
from src.validation import normalize_sources, validate_question


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        prog="researcher",
        description="Research questions with cited sources.",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    ask_parser = subparsers.add_parser(
        "ask",
        help="Ask a research question.",
    )
    ask_parser.add_argument(
        "question",
        help="Research question to answer.",
    )
    ask_parser.add_argument(
        "--sources",
        default=None,
        help="Comma-separated sources: wiki, arxiv, web.",
    )
    ask_parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Bypass cached source results.",
    )

    return parser


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse and validate command-line arguments."""
    args = build_parser().parse_args(argv)

    if args.command == "ask":
        args.question = validate_question(args.question)
        args.sources = normalize_sources(args.sources)

    return args


def main(argv: Sequence[str] | None = None) -> None:
    """CLI entry point to execute research pipeline."""
    try:
        args = parse_args(argv)
        if args.command == "ask":
            engine = ResearchEngine()
            result = engine.research(
                question=args.question,
                sources=args.sources,
                use_cache=not args.no_cache,
            )
            print("\n=== RESEARCH ANSWER ===")
            print(result.get("answer"))
            print("\n=======================")
            print(f"Sources used: {', '.join(result.get('sources', []))}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()