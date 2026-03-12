# Experiment Prioritization (MVP)

`rank_experiments` provides deterministic, confidence-adjusted ranking for growth experiments.
It returns scored records with both `confidence_weighted_impact` and `expected_lift`
so planning and reporting can use normalized ranking + absolute upside.

## Input contract

Each experiment must include:

- `name` (string)
- `reach` (number, must be >= 0)
- `impact` (number, must be >= 0)
- `confidence` (number, must be within `0..1`)
- `effort` (number, must be > 0)

If required fields are missing or contain non-numeric values, the function raises
`ValueError` with the experiment name and offending field for faster triage in CI/logs.

Optional ranking filters:

- `min_confidence` (number in `0..1`) — excludes items below this threshold before scoring
- `min_effort` (number `> 0`) — excludes items with effort smaller than this threshold
- `max_effort` (number `> 0`) — excludes items with effort greater than this threshold
- `min_reach` (number `>= 0`) — excludes items with reach smaller than this threshold
- `min_impact` (number `>= 0`) — excludes items with impact smaller than this threshold
- `min_score` (number `>= 0`) — excludes items with final score lower than this threshold
- `min_base_score` (number `>= 0`) — excludes items where base score `(reach * impact * confidence) / effort` falls below this floor
- `min_confidence_weighted_impact` (number `>= 0`) — excludes items where `impact * confidence` falls below this floor
- `min_reach_per_effort` (number `>= 0`) — excludes items where `reach / effort` falls below this floor
- `min_expected_lift` (number `>= 0`) — excludes items where `reach * impact * confidence` falls below this floor
- `min_roi` (number `>= 0`) — excludes items where `(reach * impact * confidence) / effort` falls below this floor
- `max_risk` (number in `0..1`) — excludes items whose `risk` is above this threshold (`risk` defaults to `0` when omitted)
- `min_risk_adjusted_score` (number `>= 0`) — excludes items whose `risk_adjusted_score` is below this threshold
- `max_results` (positive integer) — returns only the top N items after ranking
- `include_names` (list of strings) — keeps only experiments whose names match this allow-list (case-insensitive, trimmed)
- `exclude_names` (list of strings) — excludes experiments whose names match this deny-list (case-insensitive, trimmed)
- `name_contains` (non-empty string) — keeps only experiments whose name includes this case-insensitive substring (after trim)
- `include_owners` (list of strings) — keeps only experiments whose `owner` metadata matches this allow-list (case-insensitive, trimmed)
- `exclude_owners` (list of strings) — excludes experiments whose `owner` metadata matches this deny-list (case-insensitive, trimmed)
- `include_channels` (list of strings) — keeps only experiments whose `channel` metadata matches this allow-list (case-insensitive, trimmed)
- `exclude_channels` (list of strings) — excludes experiments whose `channel` metadata matches this deny-list (case-insensitive, trimmed)
- `sort_by` (string, default `score`) — ranking metric. One of: `score`, `base_score`, `expected_lift`, `reach_per_effort`, `confidence_weighted_impact`, `roi`, `risk_adjusted_score`, `name`
- `confidence_boost_weight` (number in `0..1`, default `0.3`) — controls how strongly confidence-weighted impact normalization influences the final score. `0` uses pure base score, `1` uses only normalized confidence-weighted impact scaling
- `channel_score_multipliers` (mapping `channel -> number > 0`) — optional per-channel execution-capacity weight applied after confidence boosting (channel match is case-insensitive + trimmed)
- `owner_score_multipliers` (mapping `owner -> number > 0`) — optional per-owner bandwidth weight applied after channel multipliers (owner match is case-insensitive + trimmed)

## Scoring

Base score:

`reach * impact * confidence / effort`

Then a configurable confidence-weighted impact multiplier is applied:

`base_score * ((1 - confidence_boost_weight) + confidence_boost_weight * normalized(impact * confidence)) * channel_multiplier * owner_multiplier`

This keeps RICE-like behavior while preferring higher-confidence opportunities.
`channel_multiplier` defaults to `1.0` when no multiplier is provided for an experiment's channel.
`owner_multiplier` defaults to `1.0` when no multiplier is provided for an experiment's owner.

## Output fields

Each ranked item contains:

- `name`
- `owner` (optional owner metadata copied from input for routing)
- `channel` (optional execution channel metadata copied from input for routing)
- `score` (final confidence-adjusted prioritization score)
- `base_score` (unboosted score: `(reach * impact * confidence) / effort`)
- `roi` (alias of `base_score` for planning/reporting readability)
- `confidence_weighted_impact` (`impact * confidence`)
- `expected_lift` (`reach * impact * confidence`, absolute upside before effort penalty)
- `reach_per_effort` (`reach / effort`, operational leverage for execution planning)
- `risk` (`0..1`, optional input, defaults to `0`)
- `risk_adjusted_score` (`score * (1 - risk)`, useful when sequencing with downside constraints)

## Determinism

- Sort order: selected `sort_by` metric descending (defaults to `score`)
- Tie-break: experiment name (case-insensitive, ascending)

This ensures stable ordering for dashboards and CI snapshots.
