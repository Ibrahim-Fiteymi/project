"""Single-image U-Net inference utility.

Run from the project root::

    python -m src.infer --image path/to/image.png

By default, predictions are written under ``outputs/inference/``. The
``make_overlay`` helper is also imported by the FastAPI backend, so this module
serves both as a CLI tool and a small library.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np
import segmentation_models_pytorch as smp
import torch

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

DEFAULT_CHECKPOINT = ROOT / "outputs" / "checkpoints" / "best_model.pth"
DEFAULT_OUTPUT_DIR = ROOT / "outputs" / "inference"
DEFAULT_IMAGE_SIZE = 256
DEFAULT_THRESHOLD = 0.7


def load_image(image_path: Path, image_size: int) -> tuple[np.ndarray, torch.Tensor]:
    image_bgr = cv2.imread(str(image_path))
    if image_bgr is None:
        raise ValueError(f"Failed to read image: {image_path}")

    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    resized_rgb = cv2.resize(image_rgb, (image_size, image_size))

    tensor = resized_rgb.astype(np.float32) / 255.0
    tensor = np.transpose(tensor, (2, 0, 1))
    tensor = torch.tensor(tensor, dtype=torch.float32).unsqueeze(0)
    return resized_rgb, tensor


def make_overlay(image_rgb: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Blend a binary mask over an RGB image as a translucent red layer."""
    color_mask = np.zeros_like(image_rgb)
    color_mask[mask > 0] = [255, 0, 0]
    return cv2.addWeighted(image_rgb, 0.7, color_mask, 0.3, 0)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run U-Net inference on a single image.")
    p.add_argument("--image", type=Path, required=True, help="Input image path.")
    p.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    p.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    p.add_argument("--image-size", type=int, default=DEFAULT_IMAGE_SIZE)
    p.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Device: {DEVICE}")

    model = smp.Unet(
        encoder_name="resnet18",
        encoder_weights=None,
        in_channels=3,
        classes=1,
    ).to(DEVICE)
    model.load_state_dict(torch.load(args.checkpoint, map_location=DEVICE))
    model.eval()

    image_rgb, image_tensor = load_image(args.image, args.image_size)
    image_tensor = image_tensor.to(DEVICE)

    with torch.no_grad():
        logits = model(image_tensor)
        probs = torch.sigmoid(logits).squeeze().cpu().numpy()

    pred_mask = (probs > args.threshold).astype(np.uint8) * 255
    overlay = make_overlay(image_rgb, pred_mask)

    base = args.image.stem
    cv2.imwrite(str(args.output_dir / f"{base}_input.png"), cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR))
    cv2.imwrite(str(args.output_dir / f"{base}_pred_mask.png"), pred_mask)
    cv2.imwrite(str(args.output_dir / f"{base}_overlay.png"), cv2.cvtColor(overlay, cv2.COLOR_RGB2BGR))

    print(f"Outputs written to: {args.output_dir}")


if __name__ == "__main__":
    main()
