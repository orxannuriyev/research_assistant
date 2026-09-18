"""Generate offline JSON artefacts for all sample research questions."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from demo_ai import _OfflineLLM, fetch_all_sources_offline
from ai import synthesize


async def main() -> None:
    root = ROOT
    questions = json.loads((root / "data" / "research_questions.json").read_text())[
        "questions"
    ]
    output_dir = root / "artefacts"
    output_dir.mkdir(exist_ok=True)

    for question in questions:
        sources = await fetch_all_sources_offline(question["text"])
        answer = synthesize(question["text"], sources, llm=_OfflineLLM())
        output = {
            "id": question["id"],
            "question": question["text"],
            "difficulty": question["difficulty"],
            "answer": answer.to_dict(),
            "source_count": len(sources),
            "mode": "offline",
        }
        (output_dir / f"{question['id']}.json").write_text(
            json.dumps(output, indent=2),
            encoding="utf-8",
        )


if __name__ == "__main__":
    asyncio.run(main())