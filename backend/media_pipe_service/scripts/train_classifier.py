"""
Train an MLP gesture classifier from a CSV of MediaPipe landmarks.

Usage
-----
    cd backend/media_pipe_service
    python scripts/train_classifier.py [--data data/landmarks.csv] [--out data/gesture_model.pkl]

CSV format (header required):
    label,x0,y0,z0,x1,y1,z1,...,x20,y20,z20

You can collect training data with scripts/record_training_data.py.

Public datasets
---------------
The Kaggle "ASL Alphabet" dataset provides per-letter images.
Run them through MediaPipe to extract landmarks and save in the format above,
or use https://www.kaggle.com/datasets/grassknoted/asl-alphabet and
the extract_kaggle_landmarks.py helper (see below).
"""

import argparse
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, LabelEncoder

DATA_DIR = Path(__file__).parent.parent / "data"
DEFAULT_CSV = DATA_DIR / "landmarks.csv"
DEFAULT_OUT = DATA_DIR / "gesture_model.pkl"


def load_data(csv_path: Path):
    df = pd.read_csv(csv_path)
    if "label" not in df.columns:
        sys.exit("CSV must have a 'label' column.")

    expected_feature_cols = 63  # 21 landmarks × 3 (x, y, z)
    feature_cols = [c for c in df.columns if c != "label"]

    if len(feature_cols) < expected_feature_cols:
        # Try 2-coord format (21 × 2 = 42)
        if len(feature_cols) < 42:
            sys.exit(f"Expected >= 42 feature columns, got {len(feature_cols)}.")

    X = df[feature_cols].values.astype(float)
    y = df["label"].astype(str).values
    return X, y


def train(csv_path: Path, out_path: Path):
    print(f"Loading data from {csv_path} ...")
    X, y = load_data(csv_path)

    classes = sorted(set(y))
    print(f"  Samples: {len(X)}   Classes ({len(classes)}): {classes}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.15, random_state=42, stratify=y
    )

    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("mlp", MLPClassifier(
            hidden_layer_sizes=(256, 128, 64),
            activation="relu",
            max_iter=500,
            early_stopping=True,
            validation_fraction=0.1,
            random_state=42,
            verbose=False,
        )),
    ])

    print("Training MLP ...")
    pipeline.fit(X_train, y_train)

    acc = pipeline.score(X_test, y_test)
    print(f"  Test accuracy: {acc * 100:.1f}%")

    bundle = {"pipeline": pipeline, "classes": classes}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "wb") as f:
        pickle.dump(bundle, f)
    print(f"  Model saved to {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train gesture MLP classifier")
    parser.add_argument("--data", default=str(DEFAULT_CSV))
    parser.add_argument("--out",  default=str(DEFAULT_OUT))
    args = parser.parse_args()

    train(Path(args.data), Path(args.out))
