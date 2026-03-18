"""
Evaluate the gesture classifier on a labeled landmark CSV.

The script reports:
- overall accuracy
- classified accuracy (excluding abstentions / low-confidence None results)
- per-class precision/recall/F1
- confusion matrix CSV
- per-sample inference latency statistics

Expected CSV format:
    label,x0,y0,z0,x1,y1,z1,...,x20,y20,z20

42-feature rows (x/y only) are also supported and will be padded with z=0.
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
import time
from pathlib import Path

from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

SERVICE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SERVICE_ROOT))

from app.models.gesture_classifier import GestureClassifier

REPORTS_DIR = SERVICE_ROOT / "reports"


def _load_samples(csv_path: Path) -> tuple[list[list[list[float]]], list[str]]:
    samples: list[list[list[float]]] = []
    labels: list[str] = []

    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if "label" not in reader.fieldnames:
            raise ValueError("CSV must include a 'label' column.")

        for row in reader:
            label = str(row["label"]).strip()
            features = [
                float(value)
                for key, value in row.items()
                if key != "label" and value is not None and value != ""
            ]

            if len(features) not in (42, 63):
                raise ValueError(
                    f"Unsupported feature width {len(features)}. "
                    "Expected 42 or 63 numeric columns."
                )

            if len(features) == 42:
                landmarks = [
                    [features[idx], features[idx + 1], 0.0]
                    for idx in range(0, len(features), 2)
                ]
            else:
                landmarks = [
                    features[idx : idx + 3]
                    for idx in range(0, len(features), 3)
                ]

            samples.append(landmarks)
            labels.append(label)

    if not samples:
        raise ValueError("No samples found in dataset.")

    return samples, labels


def _p95(values: list[float]) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    ordered = sorted(values)
    index = round(0.95 * (len(ordered) - 1))
    return ordered[index]


def evaluate(csv_path: Path, out_dir: Path) -> dict:
    samples, labels = _load_samples(csv_path)
    classifier = GestureClassifier()

    predictions: list[str] = []
    latencies_ms: list[float] = []

    for landmarks in samples:
        started = time.perf_counter()
        sign, _confidence = classifier.classify(landmarks)
        latencies_ms.append((time.perf_counter() - started) * 1000)
        predictions.append(sign or "UNCLASSIFIED")

    classified_pairs = [
        (truth, predicted)
        for truth, predicted in zip(labels, predictions)
        if predicted != "UNCLASSIFIED"
    ]

    report = {
        "dataset": str(csv_path),
        "sample_count": len(samples),
        "classifier_mode": "mlp" if classifier._ml.is_available else "heuristic",
        "overall_accuracy": accuracy_score(labels, predictions),
        "classified_accuracy": (
            accuracy_score(
                [truth for truth, _predicted in classified_pairs],
                [predicted for _truth, predicted in classified_pairs],
            )
            if classified_pairs
            else 0.0
        ),
        "abstention_rate": predictions.count("UNCLASSIFIED") / len(predictions),
        "latency_ms": {
            "mean": statistics.fmean(latencies_ms),
            "median": statistics.median(latencies_ms),
            "p95": _p95(latencies_ms),
            "max": max(latencies_ms),
        },
        "classification_report": classification_report(
            labels,
            predictions,
            output_dict=True,
            zero_division=0,
        ),
    }

    label_order = sorted(set(labels) | set(predictions))
    matrix = confusion_matrix(labels, predictions, labels=label_order)

    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / "classifier_metrics.json"
    matrix_path = out_dir / "confusion_matrix.csv"
    predictions_path = out_dir / "predictions.csv"

    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    with matrix_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["label"] + label_order)
        for label, row in zip(label_order, matrix):
            writer.writerow([label] + row.tolist())

    with predictions_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["expected", "predicted"])
        writer.writerows(zip(labels, predictions))

    return {
        "report_path": str(report_path),
        "confusion_matrix_path": str(matrix_path),
        "predictions_path": str(predictions_path),
        **report,
    }


def main():
    parser = argparse.ArgumentParser(description="Evaluate gesture classifier")
    parser.add_argument(
        "--data",
        default=str(Path(__file__).resolve().parent.parent / "data" / "landmarks.csv"),
        help="Path to labeled landmark CSV",
    )
    parser.add_argument(
        "--out-dir",
        default=str(REPORTS_DIR),
        help="Directory for JSON/CSV outputs",
    )
    args = parser.parse_args()

    result = evaluate(Path(args.data), Path(args.out_dir))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
