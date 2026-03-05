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
):
    print(item)
```

Use `min_confidence` to exclude low-confidence ideas, `max_effort` to keep only shippable low-lift experiments, and `min_reach` to avoid ideas with tiny audiences.

See `docs/prioritization.md` for full scoring and input contract details.

