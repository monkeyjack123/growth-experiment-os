from __future__ import annotations

from dataclasses import dataclass
from typing import List, Mapping, Optional, Sequence


@dataclass(frozen=True)
class RankedExperiment:
    name: str
    score: float
    confidence_weighted_impact: float


def _normalize(value: float, minimum: float, maximum: float) -> float:
    if maximum <= minimum:
        return 0.0
    return (value - minimum) / (maximum - minimum)


def rank_experiments(
    experiments: Sequence[Mapping[str, float]],
    min_confidence: Optional[float] = None,
    max_effort: Optional[float] = None,
    min_reach: Optional[float] = None,
    min_impact: Optional[float] = None,
    min_score: Optional[float] = None,
    min_confidence_weighted_impact: Optional[float] = None,
    max_results: Optional[int] = None,
) -> List[RankedExperiment]:
    """Rank experiments by a confidence-adjusted RICE-like score.

    Required fields per experiment:
      - name
      - reach
      - impact
      - confidence   (must be in 0-1 range)
      - effort       (must be > 0)

    Optional args:
      - min_confidence (0-1): skip experiments below this confidence threshold.
      - max_effort (>0): skip experiments whose effort exceeds this threshold.
      - min_reach (>=0): skip experiments below this audience threshold.
      - min_impact: skip experiments below this minimum impact score.
      - min_score (>=0): skip experiments below this final computed score.
      - min_confidence_weighted_impact (>=0): skip experiments whose impact*confidence is below this floor.
      - max_results (>0 integer): return only the top N ranked experiments.

    Score formula:
      ((reach * impact * confidence) / effort) * (0.7 + 0.3 * normalized_confidence_impact)

    The extra multiplier lightly favors higher confidence-adjusted impact,
    while keeping output deterministic through a tie-break on name.
    """

    if not experiments:
        return []

    if min_confidence is not None and not 0 <= float(min_confidence) <= 1:
        raise ValueError("min_confidence must be within [0, 1]")
    if max_effort is not None and float(max_effort) <= 0:
        raise ValueError("max_effort must be > 0")
    if min_reach is not None and float(min_reach) < 0:
        raise ValueError("min_reach must be >= 0")
    if min_impact is not None and float(min_impact) < 0:
        raise ValueError("min_impact must be >= 0")
    if min_score is not None and float(min_score) < 0:
        raise ValueError("min_score must be >= 0")
    if min_confidence_weighted_impact is not None and float(min_confidence_weighted_impact) < 0:
        raise ValueError("min_confidence_weighted_impact must be >= 0")
    if max_results is not None:
        if int(max_results) != max_results or int(max_results) <= 0:
            raise ValueError("max_results must be a positive integer")

    validated: List[Mapping[str, float]] = []
    for exp in experiments:
        name = str(exp.get("name", "<unknown>"))
        confidence = float(exp["confidence"])
        effort = float(exp["effort"])
        reach = float(exp["reach"])
        impact = float(exp["impact"])

        if not 0 <= confidence <= 1:
            raise ValueError(f"confidence must be within [0, 1] for experiment '{name}'")
        if effort <= 0:
            raise ValueError(f"effort must be > 0 for experiment '{name}'")

        if min_confidence is not None and confidence < float(min_confidence):
            continue
        if max_effort is not None and effort > float(max_effort):
            continue
        if min_reach is not None and reach < float(min_reach):
            continue
        if min_impact is not None and impact < float(min_impact):
            continue

        if (
            min_confidence_weighted_impact is not None
            and (impact * confidence) < float(min_confidence_weighted_impact)
        ):
            continue

        validated.append(exp)

    if not validated:
        return []

    cwi_values = [float(exp["impact"]) * float(exp["confidence"]) for exp in validated]
    cwi_min = min(cwi_values)
    cwi_max = max(cwi_values)

    ranked: List[RankedExperiment] = []
    for exp in validated:
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

    if min_score is not None:
        ranked = [item for item in ranked if item.score >= float(min_score)]

    ordered = sorted(ranked, key=lambda item: (-item.score, item.name.lower()))
    if max_results is not None:
        return ordered[: int(max_results)]
    return ordered
