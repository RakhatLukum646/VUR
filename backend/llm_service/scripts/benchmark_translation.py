"""
Benchmark translation latency and keyword-based quality.

The benchmark runs the full SentenceBuilder pipeline on curated cases and
produces a JSON report with:
- average / median / p95 latency
- per-case translations
- keyword match scores
- overall pass rate

This provides a reproducible baseline even when Gemini is unavailable; rerun it
with GEMINI_API_KEY configured to capture production-quality numbers.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import sys
import time
from pathlib import Path
from uuid import uuid4

SERVICE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SERVICE_ROOT))

from app.processors.sentence_builder import SentenceBuilder

DEFAULT_CASES = SERVICE_ROOT / "evaluation" / "translation_cases.json"
DEFAULT_REPORT = SERVICE_ROOT / "reports" / "translation_benchmark.json"


def _normalize(text: str) -> str:
    return " ".join(text.lower().split())


def _p95(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = round(0.95 * (len(ordered) - 1))
    return ordered[index]


async def benchmark(cases_path: Path, report_path: Path, reuse_session: bool) -> dict:
    cases = json.loads(cases_path.read_text(encoding="utf-8"))
    builder = SentenceBuilder()
    session_id = f"benchmark-{uuid4()}" if reuse_session else None

    results = []
    latencies_ms: list[float] = []
    total_keyword_score = 0.0

    for case in cases:
        active_session_id = session_id or f"case-{uuid4()}"

        started = time.perf_counter()
        response = await builder.process(
            sign_sequence=case["sign_sequence"],
            session_id=active_session_id,
            language=case.get("language", "ru"),
        )
        elapsed_ms = (time.perf_counter() - started) * 1000
        latencies_ms.append(elapsed_ms)

        translation = response["translation"]
        normalized = _normalize(translation)
        expected_keywords = [_normalize(keyword) for keyword in case.get("expected_keywords", [])]
        matched_keywords = [
            keyword for keyword in expected_keywords if keyword in normalized
        ]
        keyword_score = (
            len(matched_keywords) / len(expected_keywords)
            if expected_keywords
            else 1.0
        )
        total_keyword_score += keyword_score

        results.append(
            {
                "id": case["id"],
                "language": case.get("language", "ru"),
                "sign_sequence": case["sign_sequence"],
                "translation": translation,
                "fallback": response.get("fallback", False),
                "latency_ms": round(elapsed_ms, 3),
                "expected_keywords": expected_keywords,
                "matched_keywords": matched_keywords,
                "keyword_score": round(keyword_score, 3),
            }
        )

    report = {
        "cases": len(results),
        "reuse_session": reuse_session,
        "average_keyword_score": round(total_keyword_score / len(results), 3),
        "pass_rate": round(
            sum(1 for result in results if result["keyword_score"] == 1.0) / len(results),
            3,
        ),
        "latency_ms": {
            "mean": round(statistics.fmean(latencies_ms), 3),
            "median": round(statistics.median(latencies_ms), 3),
            "p95": round(_p95(latencies_ms), 3),
            "max": round(max(latencies_ms), 3),
        },
        "results": results,
    }

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description="Benchmark translation latency and quality")
    parser.add_argument("--cases", default=str(DEFAULT_CASES), help="Path to benchmark cases JSON")
    parser.add_argument("--out", default=str(DEFAULT_REPORT), help="Path for JSON report")
    parser.add_argument(
        "--reuse-session",
        action="store_true",
        help="Reuse one session across all cases to measure contextual flow",
    )
    args = parser.parse_args()

    report = asyncio.run(
        benchmark(
            cases_path=Path(args.cases),
            report_path=Path(args.out),
            reuse_session=args.reuse_session,
        )
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
