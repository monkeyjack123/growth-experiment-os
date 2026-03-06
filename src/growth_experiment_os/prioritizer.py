from __future__ import annotations

from dataclasses import dataclass
from typing import List, Mapping, Optional, Sequence, Set


@dataclass(frozen=True)
class RankedExperiment:
    name: str
    score: float
    base_score: float
    confidence_weighted_impact: float
    expected_lift: float
    reach_per_effort: float
    roi: float


def _normalize(value: float, minimum: float, maximum: float) -> float:
    if maximum <= minimum:
        return 0.0
    return (value - minimum) / (maximum - minimum)


def _as_float(exp: Mapping[str, float], field: str, name: str) -> float:
    if field not in exp:
        raise ValueError(f"missing required field '{field}' for experiment '{name}'")

    raw = exp[field]
    try:
        return float(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"field '{field}' must be numeric for experiment '{name}'"
        ) from exc


def rank_experiments(
    experiments: Sequence[Mapping[str, float]],
    min_confidence: Optional[float] = None,
    max_effort: Optional[float] = None,
    min_reach: Optional[float] = None,
    min_impact: Optional[float] = None,
    min_score: Optional[float] = None,
    min_base_score: Optional[float] = None,
    min_confidence_weighted_impact: Optional[float] = None,
    min_reach_per_effort: Optional[float] = None,
    min_expected_lift: Optional[float] = None,
    min_roi: Optional[float] = None,
    max_results: Optional[int] = None,
    include_names: Optional[Sequence[str]] = None,
    exclude_names: Optional[Sequence[str]] = None,
    sort_by: str = "score",
) -> List[RankedExperiment]:
    """Rank experiments by a confidence-adjusted RICE-like score.

    Required fields per experiment:
      - name
      - reach        (must be >= 0)
      - impact       (must be >= 0)
      - confidence   (must be in 0-1 range)
      - effort       (must be > 0)

    Optional args:
      - min_confidence (0-1): skip experiments below this confidence threshold.
      - max_effort (>0): skip experiments whose effort exceeds this threshold.
      - min_reach (>=0): skip experiments below this audience threshold.
      - min_impact: skip experiments below this minimum impact score.
      - min_score (>=0): skip experiments below this final computed score.
      - min_base_score (>=0): skip experiments below the unboosted base score ((reach*impact*confidence)/effort).
      - min_confidence_weighted_impact (>=0): skip experiments whose impact*confidence is below this floor.
      - min_reach_per_effort (>=0): skip experiments whose reach/effort efficiency is below this floor.
      - min_expected_lift (>=0): skip experiments whose expected lift (reach*impact*confidence) is below this floor.
      - min_roi (>=0): skip experiments whose expected_lift/effort is below this floor.
      - max_results (>0 integer): return only the top N ranked experiments.
      - include_names (list[str]): keep only experiments whose names match this allow-list (case-insensitive, trimmed).
      - exclude_names (list[str]): skip experiments whose names match this deny-list (case-insensitive, trimmed).
      - sort_by (str): ranking metric. One of: score, base_score, expected_lift,
        reach_per_effort, confidence_weighted_impact, roi.

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
    if min_base_score is not None and float(min_base_score) < 0:
        raise ValueError("min_base_score must be >= 0")
    if min_confidence_weighted_impact is not None and float(min_confidence_weighted_impact) < 0:
        raise ValueError("min_confidence_weighted_impact must be >= 0")
    if min_reach_per_effort is not None and float(min_reach_per_effort) < 0:
        raise ValueError("min_reach_per_effort must be >= 0")
    if min_expected_lift is not None and float(min_expected_lift) < 0:
        raise ValueError("min_expected_lift must be >= 0")
    if min_roi is not None and float(min_roi) < 0:
        raise ValueError("min_roi must be >= 0")
    if max_results is not None:
        if int(max_results) != max_results or int(max_results) <= 0:
            raise ValueError("max_results must be a positive integer")

    sort_key = str(sort_by).strip().lower()
    allowed_sort_keys = {
        "score",
        "base_score",
        "expected_lift",
        "reach_per_effort",
        "confidence_weighted_impact",
        "roi",
    }
    if sort_key not in allowed_sort_keys:
        raise ValueError(
            "sort_by must be one of: score, base_score, expected_lift, reach_per_effort, confidence_weighted_impact, roi"
        )

    include_set: Optional[Set[str]] = None
    if include_names is not None:
        include_set = {str(name).strip().lower() for name in include_names if str(name).strip()}
        if not include_set:
            raise ValueError("include_names must contain at least one non-empty name")

    exclude_set: Optional[Set[str]] = None
    if exclude_names is not None:
        exclude_set = {str(name).strip().lower() for name in exclude_names if str(name).strip()}
        if not exclude_set:
            raise ValueError("exclude_names must contain at least one non-empty name")

    validated: List[Mapping[str, float]] = []
    for exp in experiments:
        name = str(exp.get("name", "<unknown>"))
        confidence = _as_float(exp, "confidence", name)
        effort = _as_float(exp, "effort", name)
        reach = _as_float(exp, "reach", name)
        impact = _as_float(exp, "impact", name)

        if not 0 <= confidence <= 1:
            raise ValueError(f"confidence must be within [0, 1] for experiment '{name}'")
        if reach < 0:
            raise ValueError(f"reach must be >= 0 for experiment '{name}'")
        if impact < 0:
            raise ValueError(f"impact must be >= 0 for experiment '{name}'")
        if effort <= 0:
            raise ValueError(f"effort must be > 0 for experiment '{name}'")

        normalized_name = name.strip().lower()
        if include_set is not None and normalized_name not in include_set:
            continue
        if exclude_set is not None and normalized_name in exclude_set:
            continue

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

        if min_reach_per_effort is not None and (reach / effort) < float(min_reach_per_effort):
            continue

        expected_lift = reach * impact * confidence
        base_score = expected_lift / effort

        if min_expected_lift is not None and expected_lift < float(min_expected_lift):
            continue

        if min_roi is not None and base_score < float(min_roi):
            continue

        if min_base_score is not None and base_score < float(min_base_score):
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
        expected_lift = reach * impact * confidence
        reach_per_effort = reach / effort
        base_score = expected_lift / effort
        confidence_boost = 0.7 + 0.3 * _normalize(confidence_weighted_impact, cwi_min, cwi_max)
        score = base_score * confidence_boost

        ranked.append(
            RankedExperiment(
                name=name,
                score=round(score, 4),
                base_score=round(base_score, 4),
                confidence_weighted_impact=round(confidence_weighted_impact, 4),
                expected_lift=round(expected_lift, 4),
                reach_per_effort=round(reach_per_effort, 4),
                roi=round(base_score, 4),
            )
        )

    if min_score is not None:
        ranked = [item for item in ranked if item.score >= float(min_score)]

    ordered = sorted(ranked, key=lambda item: (-getattr(item, sort_key), item.name.lower()))
    if max_results is not None:
        return ordered[: int(max_results)]
    return ordered
