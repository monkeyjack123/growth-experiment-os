from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Mapping, Sequence


@dataclass(frozen=True)
class RankedExperiment:
    name: str
    score: float
    confidence_weighted_impact: float


def _normalize(value: float, minimum: float, maximum: float) -> float:
    if maximum <= minimum:
        return 0.0
    return (value - minimum) / (maximum - minimum)


def rank_experiments(experiments: Sequence[Mapping[str, float]]) -> List[RankedExperiment]:
    """Rank experiments by a confidence-adjusted RICE-like score.

    Required fields per experiment:
      - name
      - reach
      - impact
      - confidence   (0-1 range expected)
      - effort       (must be > 0)

    Score formula:
      ((reach * impact * confidence) / effort) * (0.7 + 0.3 * normalized_confidence_impact)

    The extra multiplier lightly favors higher confidence-adjusted impact,
    while keeping output deterministic through a tie-break on name.
    """

    if not experiments:
        return []

    for exp in experiments:
        if exp.get("effort", 0) <= 0:
            raise ValueError(f"effort must be > 0 for experiment '{exp.get('name', '<unknown>')}'")

    cwi_values = [float(exp["impact"]) * float(exp["confidence"]) for exp in experiments]
    cwi_min = min(cwi_values)
    cwi_max = max(cwi_values)

    ranked: List[RankedExperiment] = []
    for exp in experiments:
        name = str(exp["name"])
        reach = float(exp["reach"])
        impact = float(exp["impact"])
        confidence = float(exp["confidence"])
        effort = float(exp["effort"])

        confidence_weighted_impact = impact * confidence
        confidence_boost = 0.7 + 0.3 * _normalize(confidence_weighted_impact, cwi_min, cwi_max)
        score = (reach * impact * confidence / effort) * confidence_boost

        ranked.append(
            RankedExperiment(
                name=name,
                score=round(score, 4),
                confidence_weighted_impact=round(confidence_weighted_impact, 4),
            )
        )

    return sorted(ranked, key=lambda item: (-item.score, item.name.lower()))
