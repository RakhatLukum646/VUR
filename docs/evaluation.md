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

## Human Evaluation Protocol

For a stronger product-grade report, add a short human evaluation pass:

1. Recruit at least 5 participants with varied lighting, distance, and device quality.
2. Ask each participant to complete the same fixed set of signs and short phrases.
3. Record:
   - recognition success rate
   - first-attempt success rate
   - average time to successful translation
   - common failure categories such as framing, lighting, or ambiguous gesture shape
4. Capture qualitative feedback on clarity of the on-screen guidance.

Recommended summary table:
- participant/device
- phrase set
- successful translations / total
- average retries
- comments

## Privacy and Limitations

- Camera frames are used for live processing and should not be retained beyond the active session unless explicit consent is added.
- Current recognition coverage is limited to the supported sign inventory in the classifier, so unsupported gestures should be documented as out of scope.
- The system can be sensitive to framing, hand size in frame, lighting quality, and signer variation.
- If the evaluation dataset uses only one or two signers, report that as a generalization risk.

## Current Baseline

Without a populated landmark dataset, classifier metrics cannot be generated yet.
The translation benchmark can still be run in fallback mode to produce a
sanity-check baseline and should be rerun with `GEMINI_API_KEY` configured for
the final defense report.
