from __future__ import annotations

from dataclasses import dataclass
from typing import List, Mapping, Optional, Sequence, Set


@dataclass(frozen=True)
class RankedExperiment:
    name: str
    owner: Optional[str]
    channel: Optional[str]
    score: float
    base_score: float
    confidence_weighted_impact: float
    expected_lift: float
    reach_per_effort: float
    roi: float
    risk: float
    risk_adjusted_score: float


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
    max_risk: Optional[float] = None,
    min_risk_adjusted_score: Optional[float] = None,
    max_results: Optional[int] = None,
    include_names: Optional[Sequence[str]] = None,
    exclude_names: Optional[Sequence[str]] = None,
    name_contains: Optional[str] = None,
    include_owners: Optional[Sequence[str]] = None,
    exclude_owners: Optional[Sequence[str]] = None,
    sort_by: str = "score",
    confidence_boost_weight: float = 0.3,
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
      - max_risk (0-1): skip experiments whose risk exceeds this threshold. If an experiment has no risk field, risk defaults to 0.
      - min_risk_adjusted_score (>=0): skip experiments below this final risk-adjusted score floor.
      - max_results (>0 integer): return only the top N ranked experiments.
      - include_names (list[str]): keep only experiments whose names match this allow-list (case-insensitive, trimmed).
      - exclude_names (list[str]): skip experiments whose names match this deny-list (case-insensitive, trimmed).
      - name_contains (str): keep only experiments whose names include this case-insensitive substring.
      - include_owners (list[str]): keep only experiments assigned to owners in this allow-list (case-insensitive, trimmed).
      - exclude_owners (list[str]): skip experiments assigned to owners in this deny-list (case-insensitive, trimmed).
      - sort_by (str): ranking metric. One of: score, base_score, expected_lift,
        reach_per_effort, confidence_weighted_impact, roi, risk_adjusted_score, name.
      - confidence_boost_weight (0-1): how strongly to weight the confidence-adjusted
        impact normalization boost in the final score. 0 disables the boost; 1 makes
        score fully driven by normalized confidence-adjusted impact.

    Score formula:
      base_score * ((1 - confidence_boost_weight) + confidence_boost_weight * normalized_confidence_impact)

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
    if max_risk is not None and not 0 <= float(max_risk) <= 1:
        raise ValueError("max_risk must be within [0, 1]")
    if min_risk_adjusted_score is not None and float(min_risk_adjusted_score) < 0:
        raise ValueError("min_risk_adjusted_score must be >= 0")
    if max_results is not None:
        if int(max_results) != max_results or int(max_results) <= 0:
            raise ValueError("max_results must be a positive integer")
    if not 0 <= float(confidence_boost_weight) <= 1:
        raise ValueError("confidence_boost_weight must be within [0, 1]")

    sort_key = str(sort_by).strip().lower()
    allowed_sort_keys = {
        "score",
        "base_score",
        "expected_lift",
        "reach_per_effort",
        "confidence_weighted_impact",
        "roi",
        "risk_adjusted_score",
        "name",
    }
    if sort_key not in allowed_sort_keys:
        raise ValueError(
            "sort_by must be one of: score, base_score, expected_lift, reach_per_effort, confidence_weighted_impact, roi, risk_adjusted_score, name"
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

    name_query: Optional[str] = None
    if name_contains is not None:
        name_query = str(name_contains).strip().lower()
        if not name_query:
            raise ValueError("name_contains must be a non-empty string")

    include_owner_set: Optional[Set[str]] = None
    if include_owners is not None:
        include_owner_set = {
            str(owner).strip().lower() for owner in include_owners if str(owner).strip()
        }
        if not include_owner_set:
            raise ValueError("include_owners must contain at least one non-empty owner")

    exclude_owner_set: Optional[Set[str]] = None
    if exclude_owners is not None:
        exclude_owner_set = {
            str(owner).strip().lower() for owner in exclude_owners if str(owner).strip()
        }
        if not exclude_owner_set:
            raise ValueError("exclude_owners must contain at least one non-empty owner")

    validated: List[Mapping[str, float]] = []
    for exp in experiments:
        name = str(exp.get("name", "<unknown>"))
        confidence = _as_float(exp, "confidence", name)
        effort = _as_float(exp, "effort", name)
        reach = _as_float(exp, "reach", name)
        impact = _as_float(exp, "impact", name)
        try:
            risk = float(exp.get("risk", 0.0))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"field 'risk' must be numeric for experiment '{name}'") from exc

        if not 0 <= confidence <= 1:
            raise ValueError(f"confidence must be within [0, 1] for experiment '{name}'")
        if reach < 0:
            raise ValueError(f"reach must be >= 0 for experiment '{name}'")
        if impact < 0:
            raise ValueError(f"impact must be >= 0 for experiment '{name}'")
        if effort <= 0:
            raise ValueError(f"effort must be > 0 for experiment '{name}'")
        if not 0 <= risk <= 1:
            raise ValueError(f"risk must be within [0, 1] for experiment '{name}'")

        normalized_name = name.strip().lower()
        normalized_owner = str(exp.get("owner", "")).strip().lower()
        if include_set is not None and normalized_name not in include_set:
            continue
        if exclude_set is not None and normalized_name in exclude_set:
            continue
        if name_query is not None and name_query not in normalized_name:
            continue
        if include_owner_set is not None and normalized_owner not in include_owner_set:
            continue
        if exclude_owner_set is not None and normalized_owner in exclude_owner_set:
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

        if max_risk is not None and risk > float(max_risk):
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
        risk = float(exp.get("risk", 0.0))

        confidence_weighted_impact = impact * confidence
        expected_lift = reach * impact * confidence
        reach_per_effort = reach / effort
        base_score = expected_lift / effort
        normalized_cwi = _normalize(confidence_weighted_impact, cwi_min, cwi_max)
        confidence_boost = (1 - float(confidence_boost_weight)) + float(confidence_boost_weight) * normalized_cwi
        score = base_score * confidence_boost
        risk_adjusted_score = score * (1 - risk)

        ranked.append(
            RankedExperiment(
                name=name,
                owner=str(exp.get("owner")).strip() if exp.get("owner") is not None else None,
                channel=str(exp.get("channel")).strip() if exp.get("channel") is not None else None,
                score=round(score, 4),
                base_score=round(base_score, 4),
                confidence_weighted_impact=round(confidence_weighted_impact, 4),
                expected_lift=round(expected_lift, 4),
                reach_per_effort=round(reach_per_effort, 4),
                roi=round(base_score, 4),
                risk=round(risk, 4),
                risk_adjusted_score=round(risk_adjusted_score, 4),
            )
        )

    if min_score is not None:
        ranked = [item for item in ranked if item.score >= float(min_score)]

    if min_risk_adjusted_score is not None:
        ranked = [
            item
            for item in ranked
            if item.risk_adjusted_score >= float(min_risk_adjusted_score)
        ]

    if sort_key == "name":
        ordered = sorted(ranked, key=lambda item: item.name.lower())
    else:
        ordered = sorted(ranked, key=lambda item: (-getattr(item, sort_key), item.name.lower()))
    if max_results is not None:
        return ordered[: int(max_results)]
    return ordered
