# growth-experiment-os

Experiment management system for growth teams

## Why this exists
This project helps teams launch products faster with measurable outcomes.

## MVP scope (v0.1)
- Core workflow
- API/CLI interface
- Example demo data
- Quickstart docs

## Roadmap
- v0.1: baseline MVP
- v0.2: integrations
- v0.3: collaboration + analytics improvements

## Getting started

### Run tests

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_*.py' -v
```

### Demo ranking snippet

```python
from growth_experiment_os import rank_experiments

experiments = [
  {"name": "Onboarding email", "reach": 800, "impact": 0.7, "confidence": 0.9, "effort": 2},
  {"name": "SEO refresh", "reach": 1000, "impact": 0.6, "confidence": 0.8, "effort": 4},
]

for item in rank_experiments(
    experiments,
    min_confidence=0.7,
    max_effort=3,
    min_reach=500,
    min_impact=0.5,
    min_score=150,
    min_base_score=180,
    min_confidence_weighted_impact=0.5,
    min_reach_per_effort=250,
    min_expected_lift=300,
    min_roi=120,
    max_risk=0.4,
    min_risk_adjusted_score=150,
    include_names=["Onboarding email", "SEO refresh"],
    exclude_names=["SEO refresh"],
    name_contains="onboarding",
    max_results=1,
    sort_by="risk_adjusted_score",
    confidence_boost_weight=0.3,
):
    print(item.name, item.score, item.expected_lift, item.reach_per_effort)
```

Use `min_confidence` to exclude low-confidence ideas, `max_effort` to keep only shippable low-lift experiments, `min_reach` to avoid tiny audiences, `min_impact` to cut low-upside ideas, `min_score` to enforce a minimum boosted-score bar, `min_base_score` to enforce a pure RICE-style floor before confidence boost, `min_confidence_weighted_impact` to block ideas that look big but carry weak confidence-adjusted upside, `min_reach_per_effort` to enforce efficiency, `min_expected_lift` to ensure a minimum absolute upside, `min_roi` to enforce expected lift per unit effort, `max_risk` to cap execution risk, `min_risk_adjusted_score` to require a minimum downside-aware score floor, `include_names`/`exclude_names` to quickly scope or block named experiments, `name_contains` to focus on a keyword slice without maintaining exact-name lists, `max_results` to cap output to the top N candidates for sprint planning, `sort_by` to rank by a specific metric (`score`, `base_score`, `expected_lift`, `reach_per_effort`, `confidence_weighted_impact`, `roi`, `risk_adjusted_score`, or `name`), and `confidence_boost_weight` to tune how strongly confidence-adjusted impact normalization affects final scoring (`0` = pure base score, `1` = full normalization influence). Ranked output includes `base_score`/`roi`, `expected_lift` (absolute upside), `reach_per_effort` (execution leverage), and `risk_adjusted_score` to factor downside into sequencing.

See `docs/prioritization.md` for full scoring and input contract details, including
clear validation errors for missing/non-numeric required fields and guardrails
that reject negative `reach`/`impact` inputs.

