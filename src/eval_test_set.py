"""Evaluate the trained U-Net on the held-out test split.

Reports per-image and aggregate Dice, IoU, and counting metrics (MAE, MSE)
under the project's selected operating point (THRESHOLD = 0.7, MIN_AREA = 5)
and the XML-based ground-truth counts. Writes:

    outputs/test_set_eval/test_set_results.csv
    outputs/test_set_eval/test_set_summary.txt
    outputs/test_set_eval/overlays/<image>_overlay.png
    outputs/test_set_eval/pred_masks/<image>_pred_mask.png

Usage::

    python -m src.eval_test_set
"""

from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
import segmentation_models_pytorch as smp
import torch
from torch.utils.data import DataLoader
from tqdm import tqdm

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

from src.batch_count_refined import (  # noqa: E402  (path setup above)
    count_nuclei_from_binary,
    save_overlay,
    tensor_to_uint8_image,
)
from src.dataset import NucleiDataset  # noqa: E402

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

TEST_CSV = ROOT / "data" / "splits" / "test.csv"
GT_COUNTS_CSV = ROOT / "outputs" / "ground_truth" / "ground_truth_counts.csv"
CHECKPOINT_PATH = ROOT / "outputs" / "checkpoints" / "best_model.pth"

OUTPUT_DIR = ROOT / "outputs" / "test_set_eval"
PRED_MASK_DIR = OUTPUT_DIR / "pred_masks"
OVERLAY_DIR = OUTPUT_DIR / "overlays"

IMAGE_SIZE = 256
THRESHOLD = 0.7
MIN_AREA = 5


def dice_iou(pred: torch.Tensor, target: torch.Tensor, smooth: float = 1.0) -> tuple[float, float]:
    """Return (dice, iou) for binary 0/1 tensors of identical shape."""
    pred_flat = pred.flatten()
    target_flat = target.flatten()

    intersection = (pred_flat * target_flat).sum().item()
    pred_sum = pred_flat.sum().item()
    target_sum = target_flat.sum().item()

    dice = (2.0 * intersection + smooth) / (pred_sum + target_sum + smooth)
    union = pred_sum + target_sum - intersection
    iou = (intersection + smooth) / (union + smooth)
    return dice, iou


def main() -> None:
    print(f"Using device: {DEVICE}")
    print(f"Threshold: {THRESHOLD}  MIN_AREA: {MIN_AREA}")

    if not TEST_CSV.exists():
        raise FileNotFoundError(TEST_CSV)
    if not GT_COUNTS_CSV.exists():
        raise FileNotFoundError(GT_COUNTS_CSV)
    if not CHECKPOINT_PATH.exists():
        raise FileNotFoundError(CHECKPOINT_PATH)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PRED_MASK_DIR.mkdir(parents=True, exist_ok=True)
    OVERLAY_DIR.mkdir(parents=True, exist_ok=True)

    gt_df = pd.read_csv(GT_COUNTS_CSV)
    gt_map = dict(zip(gt_df["image_name"], gt_df["ground_truth_count_xml"]))

    dataset = NucleiDataset(str(TEST_CSV), image_size=IMAGE_SIZE)
    loader = DataLoader(dataset, batch_size=1, shuffle=False, num_workers=0)

    model = smp.Unet(
        encoder_name="resnet18",
        encoder_weights=None,
        in_channels=3,
        classes=1,
    ).to(DEVICE)
    model.load_state_dict(torch.load(CHECKPOINT_PATH, map_location=DEVICE))
    model.eval()

    rows: list[dict] = []

    with torch.no_grad():
        for idx, (images, masks) in enumerate(tqdm(loader, desc="Test eval")):
            images = images.to(DEVICE)
            masks = masks.to(DEVICE)

            logits = model(images)
            probs = torch.sigmoid(logits)
            preds = (probs > THRESHOLD).float()

            dice, iou = dice_iou(preds, masks)

            pred_mask = preds[0, 0].cpu().numpy().astype("uint8")
            image_name = Path(dataset.df.iloc[idx]["image_path"]).stem

            if image_name not in gt_map:
                raise KeyError(f"No XML ground-truth count for {image_name}")

            pred_count = count_nuclei_from_binary(pred_mask, min_area=MIN_AREA)
            gt_count = int(gt_map[image_name])
            abs_err = abs(pred_count - gt_count)
            sq_err = (pred_count - gt_count) ** 2

            cv2.imwrite(str(PRED_MASK_DIR / f"{image_name}_pred_mask.png"), pred_mask * 255)
            save_overlay(
                tensor_to_uint8_image(images[0]),
                pred_mask,
                OVERLAY_DIR / f"{image_name}_overlay.png",
            )

            rows.append({
                "image_name": image_name,
                "dice": round(dice, 4),
                "iou": round(iou, 4),
                "predicted_count": pred_count,
                "ground_truth_count": gt_count,
                "absolute_error": abs_err,
                "squared_error": sq_err,
            })

    df = pd.DataFrame(rows)
    csv_path = OUTPUT_DIR / "test_set_results.csv"
    df.to_csv(csv_path, index=False)

    avg_dice = df["dice"].mean()
    avg_iou = df["iou"].mean()
    mae = df["absolute_error"].mean()
    mse = df["squared_error"].mean()

    summary = (
        "Test-set evaluation (XML ground-truth counts)\n"
        f"Threshold: {THRESHOLD}\n"
        f"MIN_AREA: {MIN_AREA}\n"
        f"Images: {len(df)}\n"
        f"Average Dice: {avg_dice:.4f}\n"
        f"Average IoU:  {avg_iou:.4f}\n"
        f"Average MAE:  {mae:.4f}\n"
        f"Average MSE:  {mse:.4f}\n"
    )
    (OUTPUT_DIR / "test_set_summary.txt").write_text(summary, encoding="utf-8")

    print(summary)
    print(f"CSV:    {csv_path}")
    print(f"Masks:  {PRED_MASK_DIR}")
    print(f"Overlays: {OVERLAY_DIR}")


if __name__ == "__main__":
    main()
