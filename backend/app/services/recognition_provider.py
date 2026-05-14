from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class ProviderCandidate:
    food_name: str
    normalized_food_name: str
    confidence_score: Decimal
    portion_default: Decimal
    portion_unit: str
    food_type: str | None = None


class RecognitionProvider(Protocol):
    def recognize_meal_image(self, *, filename: str | None, image_path: Path) -> list[ProviderCandidate]: ...