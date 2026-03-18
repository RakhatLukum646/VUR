# Evaluation Workflow

This repository includes two reproducible evaluation entry points:

1. `backend/media_pipe_service/scripts/evaluate_classifier.py`
2. `backend/llm_service/scripts/benchmark_translation.py`

## 1. Classifier Evaluation

Input:
- `data/landmarks.csv`
- expected columns: `label,x0,y0,z0,...,x20,y20,z20`
- 42-column `x/y` datasets are also accepted

Command:

```bash
cd backend/media_pipe_service
source venv/bin/activate
python scripts/evaluate_classifier.py --data data/landmarks.csv --out-dir reports
```

Outputs:
- `reports/classifier_metrics.json`
- `reports/confusion_matrix.csv`
- `reports/predictions.csv`

Recommended thesis metrics:
- overall accuracy
- classified accuracy
- abstention rate
- precision / recall / F1 by class
- per-sample latency mean / median / p95

## 2. Translation Benchmark

Input:
- `evaluation/translation_cases.json`
- each case declares `sign_sequence`, `language`, and `expected_keywords`

Command:

```bash
cd backend/llm_service
source venv/bin/activate
python scripts/benchmark_translation.py --cases evaluation/translation_cases.json --out reports/translation_benchmark.json
```

Outputs:
- `reports/translation_benchmark.json`

Reported metrics:
- average / median / p95 latency
- per-case translations
- keyword-match score
- pass rate
- whether fallback mode was used

## Recommended Defense Evidence

For a diploma defense, include these generated artifacts in the appendix:
- one classifier report from the final landmark dataset
- one confusion matrix from the final model
- one translation benchmark report with Gemini enabled
- a short note on hardware and runtime environment
- 3 to 5 representative failure cases with explanation

## Current Baseline

Without a populated landmark dataset, classifier metrics cannot be generated yet.
The translation benchmark can still be run in fallback mode to produce a
sanity-check baseline and should be rerun with `GEMINI_API_KEY` configured for
the final defense report.
