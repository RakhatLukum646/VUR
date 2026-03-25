"""ResNet18-based ASL sign language classifier.

Model:        huzaifanasirrr/realtime-sign-language-translator (HuggingFace)
Architecture: ResNet18 backbone + custom head → 26 ASL letters (A-Z)
Input:        224×224 RGB numpy array (hand crop from frame)
Output:       (letter, confidence) or None if below threshold / not loaded

Usage::
    clf = ResNetClassifier()
    clf.load()                          # auto-downloads from HuggingFace
    clf.load("/path/to/best_model.pth") # or load from local cache
    result = clf.predict(hand_crop_rgb) # → ("A", 0.96) or None
"""

import logging
from pathlib import Path
from typing import Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

_HF_REPO_ID = "huzaifanasirrr/realtime-sign-language-translator"
_HF_FILENAME = "best_model.pth"

# ImageNet normalisation constants used during training
_IMAGENET_MEAN = [0.485, 0.456, 0.406]
_IMAGENET_STD = [0.229, 0.224, 0.225]


class ResNetClassifier:
    """
    Wraps the pre-trained ResNet18 ASL gesture classifier.

    Torch and torchvision are imported lazily so the class is importable even
    when those packages are not yet installed (useful during test collection).
    """

    def __init__(
        self,
        confidence_threshold: float = 0.6,
        device: str = "cpu",
    ):
        self._model = None
        self.confidence_threshold = confidence_threshold
        self.device = device
        self._transform = None  # built lazily on first preprocess call

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    def load(self, model_path: Optional[str] = None) -> None:
        """Load model weights.

        Args:
            model_path: Local path to ``best_model.pth``.  When omitted the
                        model is downloaded from HuggingFace automatically.
        """
        import torch

        if model_path is None:
            model_path = self._download_from_huggingface()

        path = Path(model_path)
        if not path.exists():
            raise FileNotFoundError(f"Model file not found: {path}")

        try:
            checkpoint = torch.load(str(path), map_location=self.device, weights_only=False)

            # The checkpoint may be a full model object, a bare state dict,
            # or a training checkpoint with nested keys.
            if isinstance(checkpoint, dict):
                state_dict = checkpoint.get("model_state_dict", checkpoint)
                # Strip wrapper prefix (e.g. keys like "model.conv1.weight")
                prefix = next(iter(state_dict)).split(".")[0] + "."
                if all(k.startswith(prefix) for k in state_dict):
                    state_dict = {k[len(prefix):]: v for k, v in state_dict.items()}
                model = self._build_model()
                model.load_state_dict(state_dict)
            else:
                model = checkpoint

            model.eval()

            # JIT-trace for faster CPU inference (avoids Python overhead per call).
            dummy = torch.zeros(1, 3, 224, 224, device=self.device)
            with torch.inference_mode():
                self._model = torch.jit.trace(model, dummy)

            logger.info(
                "resnet_classifier_loaded path=%s device=%s jit=traced", path, self.device
            )
        except FileNotFoundError:
            raise
        except Exception as exc:
            logger.error(
                "resnet_classifier_load_failed path=%s error=%s", path, exc
            )
            raise

    def predict(self, image: np.ndarray) -> Optional[Tuple[str, float]]:
        """Predict the ASL letter shown in a hand-crop image.

        Args:
            image: RGB uint8 (or float32) numpy array, any spatial size.

        Returns:
            ``(letter, confidence)`` when confidence ≥ threshold, else ``None``.
        """
        if not self.is_loaded:
            return None

        import torch

        tensor = self._preprocess(image)
        with torch.inference_mode():
            logits = self._model(tensor)
            probs = torch.softmax(logits, dim=1)
            confidence_t, idx_t = torch.max(probs, dim=1)

        confidence = float(confidence_t.item())
        idx = int(idx_t.item())

        if confidence < self.confidence_threshold:
            return None

        letter = self._index_to_letter(idx)
        return letter, confidence

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _preprocess(self, image: np.ndarray):
        """Convert a numpy RGB image to a normalised (1, 3, 224, 224) tensor."""
        from PIL import Image

        pil_image = Image.fromarray(image.astype(np.uint8))
        return self._get_transform()(pil_image).unsqueeze(0)

    def _get_transform(self):
        if self._transform is None:
            self._transform = self._build_transform()
        return self._transform

    def _build_transform(self):
        from torchvision import transforms

        return transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=_IMAGENET_MEAN, std=_IMAGENET_STD),
        ])

    def _index_to_letter(self, idx: int) -> str:
        """Map class index 0–25 to uppercase ASCII letter A–Z."""
        if not (0 <= idx <= 25):
            raise ValueError(f"Class index {idx} out of range [0, 25]")
        return chr(65 + idx)

    def _build_model(self):
        """Reconstruct the ResNet18 + custom head used during training."""
        import torch.nn as nn
        from torchvision import models

        backbone = models.resnet18(weights=None)
        backbone.fc = nn.Sequential(
            nn.Dropout(0.5),
            nn.Linear(512, 512),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(512, 26),
        )
        return backbone.to(self.device)

    def _download_from_huggingface(self) -> str:
        try:
            from huggingface_hub import hf_hub_download
        except ImportError as exc:
            raise ImportError(
                "huggingface_hub is required to auto-download the model. "
                "Install it: pip install huggingface_hub"
            ) from exc

        logger.info(
            "resnet_downloading repo=%s filename=%s", _HF_REPO_ID, _HF_FILENAME
        )
        path = hf_hub_download(repo_id=_HF_REPO_ID, filename=_HF_FILENAME)
        logger.info("resnet_downloaded path=%s", path)
        return path
