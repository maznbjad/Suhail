from __future__ import annotations

from dataclasses import dataclass
from statistics import mean, pstdev
from typing import Iterable


@dataclass(frozen=True)
class Prediction:
    center: int
    low: int
    high: int
    confidence: str
    attempts: int


def _clamp(value: float, minimum: float = 0, maximum: float = 100) -> float:
    return max(minimum, min(maximum, value))


def weighted_qudrat(quant: float, verbal: float, academic_track: str) -> float:
    if academic_track == "literary":
        return quant * 0.30 + verbal * 0.70
    return quant * 0.50 + verbal * 0.50


def weighted_tahsili(subject_scores: dict[str, float], academic_track: str | None = None) -> float:
    """Compute the common Tahsili readiness score.

    academic_track is accepted for backwards compatibility but intentionally ignored;
    the scientific/literary distinction belongs to Qudrat only.
    """
    weights = {"رياضيات": 0.25, "فيزياء": 0.25, "كيمياء": 0.25, "أحياء": 0.25}
    present = [(float(subject_scores.get(subject, 0)), weight) for subject, weight in weights.items()]
    return sum(score * weight for score, weight in present)


def predict(scores: Iterable[float], average_seconds: Iterable[float] = ()) -> Prediction | None:
    values = [float(v) for v in scores]
    if not values:
        return None
    weights = list(range(1, len(values) + 1))
    weighted = sum(score * weight for score, weight in zip(values, weights)) / sum(weights)
    times = [float(v) for v in average_seconds]
    if times:
        avg_time = mean(times)
        if avg_time <= 50:
            weighted += 1.5
        elif avg_time > 75:
            weighted -= 2
    attempts = len(values)
    stability = pstdev(values[-8:]) if attempts > 1 else 15
    width = 3 if attempts >= 8 and stability < 8 else 5 if attempts >= 4 else 7
    center = round(_clamp(weighted))
    confidence = "مرتفعة" if width == 3 else "متوسطة" if width == 5 else "أولية"
    return Prediction(center=center, low=round(_clamp(center - width)), high=round(_clamp(center + width)), confidence=confidence, attempts=attempts)
