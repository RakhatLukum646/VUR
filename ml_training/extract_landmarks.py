import os
import cv2
import csv
import mediapipe as mp

from feature_extractor import extract_features

DATASET_PATH = "../datasets/asl_alphabet/asl_alphabet_train/asl_alphabet_train"
OUTPUT_CSV = "data/asl_landmarks.csv"

SKIP_CLASSES = {"j", "z", "del", "space", "nothing"}

mp_hands = mp.solutions.hands


def extract_landmarks(image, hands):
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    if not results.multi_hand_landmarks:
        return None

    hand = results.multi_hand_landmarks[0]

    landmarks = []
    for lm in hand.landmark:
        landmarks.append([lm.x, lm.y, lm.z])

    return landmarks


def main():
    os.makedirs("data", exist_ok=True)

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = None

        with mp_hands.Hands(
            static_image_mode=True,
            max_num_hands=1,
            min_detection_confidence=0.5
        ) as hands:

            for label in os.listdir(DATASET_PATH):
                class_dir = os.path.join(DATASET_PATH, label)

                if not os.path.isdir(class_dir):
                    continue

                if label.lower() in SKIP_CLASSES:
                    print(f"Skipping {label}")
                    continue

                print(f"Processing {label}")

                for img_name in os.listdir(class_dir):
                    img_path = os.path.join(class_dir, img_name)

                    img = cv2.imread(img_path)
                    if img is None:
                        continue

                    img = cv2.resize(img, (256, 256))

                    landmarks = extract_landmarks(img, hands)
                    if landmarks is None:
                        continue

                    features = extract_features(landmarks)

                    if writer is None:
                        header = [f"f{i}" for i in range(len(features))] + ["label"]
                        writer = csv.writer(f)
                        writer.writerow(header)

                    writer.writerow(features + [label])

    print(f"CSV created: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()