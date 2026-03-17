"""
Collect MediaPipe landmark data for a single sign class using the webcam.

Usage
-----
    cd backend/media_pipe_service
    python scripts/record_training_data.py --label A --samples 200

The script opens the webcam, shows the video feed with landmark overlay,
and records `--samples` frames where a hand is detected.
Appends rows to data/landmarks.csv.

Run once per sign. After collecting all signs, train with:
    python scripts/train_classifier.py
"""

import argparse
import csv
import sys
import time
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np

DATA_DIR = Path(__file__).parent.parent / "data"
CSV_PATH = DATA_DIR / "landmarks.csv"

# MediaPipe hand connections for visualization
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils


def normalize_landmarks(landmarks_raw):
    """Wrist-relative, unit-scaled — same as HandDetector.normalize_landmarks."""
    lm = np.array([[l.x, l.y, l.z] for l in landmarks_raw])
    wrist = lm[0]
    scale = np.linalg.norm(lm[9] - wrist)
    if scale == 0:
        scale = 1.0
    return ((lm - wrist) / scale).tolist()


def collect(label: str, target_samples: int):
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    write_header = not CSV_PATH.exists()
    csv_file = open(CSV_PATH, "a", newline="")
    writer = csv.writer(csv_file)
    if write_header:
        header = ["label"] + [f"{c}{i}" for i in range(21) for c in ("x", "y", "z")]
        writer.writerow(header)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        sys.exit("Cannot open webcam.")

    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    collected = 0
    print(f"\nCollecting {target_samples} samples for '{label}'.")
    print("Press SPACE to start recording, Q to quit.\n")

    recording = False

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(frame_rgb)

        display = frame.copy()
        hand_detected = False

        if results.multi_hand_landmarks:
            hand_detected = True
            for hl in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(display, hl, mp_hands.HAND_CONNECTIONS)

            if recording:
                lm_raw = results.multi_hand_landmarks[0].landmark
                normed = normalize_landmarks(lm_raw)
                row = [label] + [coord for point in normed for coord in point]
                writer.writerow(row)
                collected += 1

        status = f"Label: {label} | Collected: {collected}/{target_samples}"
        color = (0, 200, 0) if recording and hand_detected else (100, 100, 255)
        cv2.putText(display, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        if not recording:
            cv2.putText(display, "Press SPACE to start", (10, 65),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
        elif not hand_detected:
            cv2.putText(display, "No hand — show your hand!", (10, 65),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 80, 255), 2)

        cv2.imshow("Data Collection", display)

        key = cv2.waitKey(1) & 0xFF
        if key == ord(' '):
            recording = not recording
            print("Recording:", "ON" if recording else "OFF")
        elif key == ord('q'):
            break

        if collected >= target_samples:
            print(f"Done! Collected {collected} samples for '{label}'.")
            break

    cap.release()
    hands.close()
    cv2.destroyAllWindows()
    csv_file.close()
    print(f"Saved to {CSV_PATH}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Record landmark training data")
    parser.add_argument("--label",   required=True, help="Sign label, e.g. A")
    parser.add_argument("--samples", type=int, default=200)
    args = parser.parse_args()
    collect(args.label, args.samples)
