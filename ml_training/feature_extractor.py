import numpy as np


def dist(a, b):
    a = np.array(a, dtype=float)
    b = np.array(b, dtype=float)
    return float(np.linalg.norm(a - b))


def angle(a, b, c):
    a = np.array(a, dtype=float)
    b = np.array(b, dtype=float)
    c = np.array(c, dtype=float)

    ba = a - b
    bc = c - b

    norm_ba = np.linalg.norm(ba)
    norm_bc = np.linalg.norm(bc)

    if norm_ba == 0 or norm_bc == 0:
        return 0.0

    cos_angle = np.dot(ba, bc) / (norm_ba * norm_bc)
    cos_angle = np.clip(cos_angle, -1.0, 1.0)

    return float(np.arccos(cos_angle))


def finger_extended(tip, pip, mcp):
    return dist(tip, mcp) > dist(pip, mcp)


def extract_features(landmarks):
    lm = np.array(landmarks, dtype=float)

    if lm.shape != (21, 3):
        raise ValueError("Expected landmarks shape (21, 3)")

    wrist = lm[0]

    thumb_tip, thumb_ip, thumb_mcp = lm[4], lm[3], lm[2]
    index_tip, index_pip, index_mcp = lm[8], lm[6], lm[5]
    middle_tip, middle_pip, middle_mcp = lm[12], lm[10], lm[9]
    ring_tip, ring_pip, ring_mcp = lm[16], lm[14], lm[13]
    pinky_tip, pinky_pip, pinky_mcp = lm[20], lm[18], lm[17]

    # Normalize landmarks relative to wrist
    normalized = lm - wrist

    # Scale normalization using wrist → middle MCP distance
    scale = dist(wrist, middle_mcp)
    if scale > 1e-8:
        normalized = normalized / scale

    features = []

    # normalized coordinates
    features.extend(normalized.flatten())

    # wrist → fingertip distances
    features.extend([
        dist(wrist, thumb_tip) / scale if scale > 1e-8 else 0.0,
        dist(wrist, index_tip) / scale if scale > 1e-8 else 0.0,
        dist(wrist, middle_tip) / scale if scale > 1e-8 else 0.0,
        dist(wrist, ring_tip) / scale if scale > 1e-8 else 0.0,
        dist(wrist, pinky_tip) / scale if scale > 1e-8 else 0.0,
    ])

    # fingertip distances
    features.extend([
        dist(index_tip, middle_tip) / scale if scale > 1e-8 else 0.0,
        dist(middle_tip, ring_tip) / scale if scale > 1e-8 else 0.0,
        dist(ring_tip, pinky_tip) / scale if scale > 1e-8 else 0.0,
        dist(thumb_tip, index_tip) / scale if scale > 1e-8 else 0.0,
        dist(thumb_tip, middle_tip) / scale if scale > 1e-8 else 0.0,
        dist(thumb_tip, ring_tip) / scale if scale > 1e-8 else 0.0,
        dist(thumb_tip, pinky_tip) / scale if scale > 1e-8 else 0.0,
    ])

    # angles
    features.extend([
        angle(index_tip, index_pip, index_mcp),
        angle(middle_tip, middle_pip, middle_mcp),
        angle(ring_tip, ring_pip, ring_mcp),
        angle(pinky_tip, pinky_pip, pinky_mcp),
        angle(thumb_tip, thumb_ip, thumb_mcp),
    ])

    # finger states
    features.extend([
        int(finger_extended(index_tip, index_pip, index_mcp)),
        int(finger_extended(middle_tip, middle_pip, middle_mcp)),
        int(finger_extended(ring_tip, ring_pip, ring_mcp)),
        int(finger_extended(pinky_tip, pinky_pip, pinky_mcp)),
    ])

    return features