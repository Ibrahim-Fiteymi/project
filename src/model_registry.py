"""Lightweight model registry for the U-Net checkpoints.

Every training run creates a versioned checkpoint of the form::

    outputs/checkpoints/unet_resnet18_<timestamp>_<run_id>.pth

…and an entry is appended to ``outputs/checkpoints/registry.json`` capturing
the hyperparameters, metric snapshot, and the path to the weights. A
``best_model.pth`` symlink/copy continues to point at the highest-val-Dice
run so the existing inference paths keep working unchanged.

This module is deliberately stdlib-only — no MLflow / DVC dependency — to keep
the academic submission self-contained.
"""

from __future__ import annotations

import json
import shutil
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class RunRecord:
    run_id: str
    created_at: str
    encoder: str
    epochs: int
    batch_size: int
    image_size: int
    learning_rate: float
    threshold: float
    min_area: int
    metrics: dict[str, float] = field(default_factory=dict)
    weights_path: str = ""
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ModelRegistry:
    """File-backed registry stored at ``<output_dir>/registry.json``."""

    def __init__(self, output_dir: Path) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.output_dir / "registry.json"
        if not self.path.exists():
            self.path.write_text(json.dumps({"runs": []}, indent=2), encoding="utf-8")

    def _load(self) -> dict[str, Any]:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {"runs": []}

    def _save(self, payload: dict[str, Any]) -> None:
        self.path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    def runs(self) -> list[RunRecord]:
        data = self._load()
        return [RunRecord(**r) for r in data.get("runs", [])]

    def add(self, record: RunRecord) -> None:
        data = self._load()
        data.setdefault("runs", []).append(record.to_dict())
        self._save(data)

    def best_run(self, metric: str = "val_dice") -> Optional[RunRecord]:
        runs = [r for r in self.runs() if metric in r.metrics]
        if not runs:
            return None
        return max(runs, key=lambda r: r.metrics[metric])


def make_run_id() -> str:
    """``<UTC timestamp>_<random suffix>`` — sortable and unique."""
    return f"{time.strftime('%Y%m%dT%H%M%S', time.gmtime())}_{uuid.uuid4().hex[:6]}"


def register_run(
    output_dir: Path,
    weights_src: Path,
    *,
    encoder: str,
    epochs: int,
    batch_size: int,
    image_size: int,
    learning_rate: float,
    threshold: float,
    min_area: int,
    metrics: dict[str, float],
    notes: str = "",
) -> RunRecord:
    """Copy the weights to a versioned filename, append to the registry, refresh ``best_model.pth``."""
    run_id = make_run_id()
    versioned = Path(output_dir) / f"unet_{encoder}_{run_id}.pth"
    shutil.copy2(weights_src, versioned)

    record = RunRecord(
        run_id=run_id,
        created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        encoder=encoder,
        epochs=epochs,
        batch_size=batch_size,
        image_size=image_size,
        learning_rate=learning_rate,
        threshold=threshold,
        min_area=min_area,
        metrics=metrics,
        weights_path=str(versioned.relative_to(output_dir.parent.parent)),
        notes=notes,
    )

    registry = ModelRegistry(output_dir)
    registry.add(record)

    best = registry.best_run("val_dice")
    if best and best.run_id == run_id:
        best_target = output_dir / "best_model.pth"
        shutil.copy2(versioned, best_target)

    return record
