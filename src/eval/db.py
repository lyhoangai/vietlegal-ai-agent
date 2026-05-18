"""src/eval/db.py — SQLite persistence for Ragas eval results."""
from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path

DB_PATH = "eval_results.db"
ROOT = Path(__file__).resolve().parents[2]
LATEST_RESULTS_PATH = ROOT / "docs" / "benchmarks" / "latest_results.json"


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS eval_results (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp         REAL,
                question          TEXT,
                answer            TEXT,
                context_precision REAL,
                answer_relevancy  REAL,
                faithfulness      REAL,
                answer_correctness REAL
            )
            """
        )


def save_result(question: str, answer: str, scores: dict):
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO eval_results VALUES (NULL,?,?,?,?,?,?,?)",
            (
                time.time(),
                question,
                answer,
                scores.get("context_precision", 0),
                scores.get("answer_relevancy", 0),
                scores.get("faithfulness", 0),
                scores.get("answer_correctness", 0),
            ),
        )


def _load_latest_benchmark_snapshot() -> dict:
    if not LATEST_RESULTS_PATH.exists():
        return {}

    with LATEST_RESULTS_PATH.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    full_results = data.get("modes", {}).get("full", [])
    cases = len(full_results)
    if cases == 0:
        return {}

    answer_cases = [row for row in full_results if row.get("expected_behavior") == "answer"]
    passed = sum(1 for row in full_results if row.get("passed"))
    source_hits = sum(1 for row in answer_cases if row.get("source_hit"))
    web_hits = sum(1 for row in full_results if row.get("web_used"))
    confidence_sum = sum(float(row.get("confidence") or 0) for row in full_results)
    phrase_match_sum = sum(float(row.get("phrase_match_rate") or 0) for row in answer_cases)

    return {
        "generated_at": data.get("generated_at", ""),
        "dataset_path": data.get("dataset_path", ""),
        "cases": cases,
        "pass_rate": round(passed / cases, 3),
        "citation_rate": round(source_hits / len(answer_cases), 3) if answer_cases else 0.0,
        "reference_match": round(phrase_match_sum / len(answer_cases), 3) if answer_cases else 0.0,
        "avg_confidence": round(confidence_sum / cases, 3),
        "web_usage_rate": round(web_hits / cases, 3),
        "source": "docs/benchmarks/latest_results.json",
    }


def get_avg_metrics() -> dict:
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            """
            SELECT
                AVG(context_precision),
                AVG(answer_relevancy),
                AVG(faithfulness),
                AVG(answer_correctness),
                COUNT(*)
            FROM eval_results
            """
        ).fetchone()

    return {
        "context_precision": round(row[0] or 0, 3),
        "answer_relevancy": round(row[1] or 0, 3),
        "faithfulness": round(row[2] or 0, 3),
        "answer_correctness": round(row[3] or 0, 3),
        "total_evaluations": row[4] or 0,
        "unit": "0.0 to 1.0",
        "benchmark_snapshot": _load_latest_benchmark_snapshot(),
    }
