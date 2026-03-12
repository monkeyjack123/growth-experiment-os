import unittest

from growth_experiment_os import rank_experiments


class PrioritizerTests(unittest.TestCase):
    def test_ranks_highest_scoring_experiment_first(self):
        experiments = [
            {"name": "SEO refresh", "reach": 1000, "impact": 0.6, "confidence": 0.8, "effort": 4},
            {"name": "Onboarding email", "reach": 800, "impact": 0.7, "confidence": 0.9, "effort": 2},
            {"name": "Referral CTA", "reach": 600, "impact": 0.9, "confidence": 0.6, "effort": 2.5},
        ]

        ranked = rank_experiments(experiments)

        self.assertEqual(ranked[0].name, "Onboarding email")
        self.assertGreater(ranked[0].score, ranked[1].score)

    def test_returns_empty_for_empty_input(self):
        self.assertEqual(rank_experiments([]), [])

    def test_includes_expected_lift_in_ranked_output(self):
        experiments = [
            {"name": "Onboarding email", "reach": 800, "impact": 0.7, "confidence": 0.9, "effort": 2},
        ]

        ranked = rank_experiments(experiments)

        self.assertEqual(len(ranked), 1)
        self.assertAlmostEqual(ranked[0].expected_lift, 504.0)

    def test_includes_reach_per_effort_in_ranked_output(self):
        experiments = [
            {"name": "Onboarding email", "reach": 800, "impact": 0.7, "confidence": 0.9, "effort": 2},
        ]

        ranked = rank_experiments(experiments)

        self.assertEqual(len(ranked), 1)
        self.assertAlmostEqual(ranked[0].reach_per_effort, 400.0)

    def test_includes_base_score_and_roi_in_ranked_output(self):
        experiments = [
            {"name": "Onboarding email", "reach": 800, "impact": 0.7, "confidence": 0.9, "effort": 2},
        ]

        ranked = rank_experiments(experiments)

        self.assertEqual(len(ranked), 1)
        self.assertAlmostEqual(ranked[0].base_score, 252.0)
        self.assertAlmostEqual(ranked[0].roi, 252.0)

    def test_rejects_negative_reach(self):
        experiments = [{"name": "Bad reach", "reach": -1, "impact": 1, "confidence": 0.8, "effort": 1}]

        with self.assertRaisesRegex(ValueError, "reach must be >= 0"):
            rank_experiments(experiments)

    def test_rejects_negative_impact(self):
        experiments = [{"name": "Bad impact", "reach": 10, "impact": -0.1, "confidence": 0.8, "effort": 1}]

        with self.assertRaisesRegex(ValueError, "impact must be >= 0"):
            rank_experiments(experiments)

    def test_rejects_non_positive_effort(self):
        experiments = [{"name": "Bad", "reach": 100, "impact": 1, "confidence": 1, "effort": 0}]

        with self.assertRaisesRegex(ValueError, "effort must be > 0"):
            rank_experiments(experiments)

    def test_rejects_missing_required_field_with_clear_error(self):
        experiments = [{"name": "Missing effort", "reach": 100, "impact": 1, "confidence": 0.8}]

        with self.assertRaisesRegex(ValueError, "missing required field 'effort'"):
            rank_experiments(experiments)

    def test_rejects_non_numeric_required_field_with_clear_error(self):
        experiments = [{"name": "Bad reach", "reach": "many", "impact": 1, "confidence": 0.8, "effort": 1}]

        with self.assertRaisesRegex(ValueError, "field 'reach' must be numeric"):
            rank_experiments(experiments)

    def test_rejects_confidence_outside_unit_interval(self):
        experiments = [{"name": "Overconfident", "reach": 100, "impact": 1, "confidence": 1.2, "effort": 2}]

        with self.assertRaisesRegex(ValueError, "confidence must be within \[0, 1\]"):
            rank_experiments(experiments)

    def test_filters_by_min_confidence_threshold(self):
        experiments = [
            {"name": "Bold bet", "reach": 2000, "impact": 1.0, "confidence": 0.4, "effort": 2},
            {"name": "Safer win", "reach": 900, "impact": 0.8, "confidence": 0.85, "effort": 2},
        ]

        ranked = rank_experiments(experiments, min_confidence=0.6)

        self.assertEqual(len(ranked), 1)
        self.assertEqual(ranked[0].name, "Safer win")

    def test_filters_by_max_effort_threshold(self):
        experiments = [
            {"name": "Heavy lift", "reach": 1500, "impact": 0.9, "confidence": 0.8, "effort": 8},
            {"name": "Quick win", "reach": 700, "impact": 0.7, "confidence": 0.9, "effort": 2},
        ]

        ranked = rank_experiments(experiments, max_effort=3)

        self.assertEqual(len(ranked), 1)
        self.assertEqual(ranked[0].name, "Quick win")

    def test_filters_by_min_effort_threshold(self):
        experiments = [
            {"name": "Quick tweak", "reach": 700, "impact": 0.8, "confidence": 0.9, "effort": 1},
            {"name": "Deeper build", "reach": 1000, "impact": 0.9, "confidence": 0.8, "effort": 5},
        ]

        ranked = rank_experiments(experiments, min_effort=2)

        self.assertEqual(len(ranked), 1)
        self.assertEqual(ranked[0].name, "Deeper build")

    def test_rejects_invalid_min_effort(self):
        experiments = [{"name": "One", "reach": 100, "impact": 1, "confidence": 0.8, "effort": 1}]

        with self.assertRaisesRegex(ValueError, "min_effort must be > 0"):
            rank_experiments(experiments, min_effort=0)

    def test_rejects_min_effort_above_max_effort(self):
        experiments = [{"name": "One", "reach": 100, "impact": 1, "confidence": 0.8, "effort": 1}]

        with self.assertRaisesRegex(ValueError, "min_effort must be <= max_effort"):
            rank_experiments(experiments, min_effort=3, max_effort=2)

    def test_rejects_invalid_min_confidence(self):
        experiments = [{"name": "One", "reach": 100, "impact": 1, "confidence": 0.8, "effort": 1}]

        with self.assertRaisesRegex(ValueError, "min_confidence must be within \[0, 1\]"):
            rank_experiments(experiments, min_confidence=1.1)

    def test_rejects_invalid_max_effort(self):
        experiments = [{"name": "One", "reach": 100, "impact": 1, "confidence": 0.8, "effort": 1}]

        with self.assertRaisesRegex(ValueError, "max_effort must be > 0"):
            rank_experiments(experiments, max_effort=0)

    def test_filters_by_min_reach_threshold(self):
        experiments = [
            {"name": "Tiny reach", "reach": 120, "impact": 1.0, "confidence": 0.95, "effort": 1},
            {"name": "Broad audience", "reach": 1200, "impact": 0.7, "confidence": 0.8, "effort": 3},
        ]

        ranked = rank_experiments(experiments, min_reach=500)

        self.assertEqual(len(ranked), 1)
        self.assertEqual(ranked[0].name, "Broad audience")

    def test_rejects_invalid_min_reach(self):
        experiments = [{"name": "One", "reach": 100, "impact": 1, "confidence": 0.8, "effort": 1}]

        with self.assertRaisesRegex(ValueError, "min_reach must be >= 0"):
            rank_experiments(experiments, min_reach=-1)

    def test_filters_by_min_impact_threshold(self):
        experiments = [
            {"name": "Low impact noise", "reach": 5000, "impact": 0.2, "confidence": 0.95, "effort": 1},
            {"name": "High impact bet", "reach": 900, "impact": 0.8, "confidence": 0.8, "effort": 2},
        ]

        ranked = rank_experiments(experiments, min_impact=0.5)

        self.assertEqual(len(ranked), 1)
        self.assertEqual(ranked[0].name, "High impact bet")

    def test_rejects_invalid_min_impact(self):
        experiments = [{"name": "One", "reach": 100, "impact": 1, "confidence": 0.8, "effort": 1}]

        with self.assertRaisesRegex(ValueError, "min_impact must be >= 0"):
            rank_experiments(experiments, min_impact=-0.1)

    def test_filters_by_min_score_threshold(self):
        experiments = [
            {"name": "Longshot", "reach": 300, "impact": 0.3, "confidence": 0.6, "effort": 3},
            {"name": "Quick win", "reach": 700, "impact": 0.8, "confidence": 0.9, "effort": 2},
        ]

        ranked = rank_experiments(experiments, min_score=100)

        self.assertEqual(len(ranked), 1)
        self.assertEqual(ranked[0].name, "Quick win")

    def test_rejects_invalid_min_score(self):
        experiments = [{"name": "One", "reach": 100, "impact": 1, "confidence": 0.8, "effort": 1}]

        with self.assertRaisesRegex(ValueError, "min_score must be >= 0"):
            rank_experiments(experiments, min_score=-1)

    def test_filters_by_min_base_score(self):
        experiments = [
            {"name": "Low base", "reach": 300, "impact": 0.4, "confidence": 0.6, "effort": 3},
            {"name": "High base", "reach": 1200, "impact": 0.7, "confidence": 0.8, "effort": 2},
        ]

        ranked = rank_experiments(experiments, min_base_score=200)

        self.assertEqual(len(ranked), 1)
        self.assertEqual(ranked[0].name, "High base")

    def test_rejects_invalid_min_base_score(self):
        experiments = [{"name": "One", "reach": 100, "impact": 1, "confidence": 0.8, "effort": 1}]

        with self.assertRaisesRegex(ValueError, "min_base_score must be >= 0"):
            rank_experiments(experiments, min_base_score=-1)

    def test_filters_by_min_confidence_weighted_impact(self):
        experiments = [
            {"name": "Big reach low confidence", "reach": 3000, "impact": 0.9, "confidence": 0.3, "effort": 2},
            {"name": "Solid bet", "reach": 900, "impact": 0.8, "confidence": 0.8, "effort": 2},
        ]

        ranked = rank_experiments(experiments, min_confidence_weighted_impact=0.5)

        self.assertEqual(len(ranked), 1)
        self.assertEqual(ranked[0].name, "Solid bet")

    def test_rejects_invalid_min_confidence_weighted_impact(self):
        experiments = [{"name": "One", "reach": 100, "impact": 1, "confidence": 0.8, "effort": 1}]

        with self.assertRaisesRegex(ValueError, "min_confidence_weighted_impact must be >= 0"):
            rank_experiments(experiments, min_confidence_weighted_impact=-0.1)

    def test_filters_by_min_reach_per_effort(self):
        experiments = [
            {"name": "High leverage", "reach": 1200, "impact": 0.6, "confidence": 0.8, "effort": 2},
            {"name": "Low leverage", "reach": 300, "impact": 0.9, "confidence": 0.8, "effort": 3},
        ]

        ranked = rank_experiments(experiments, min_reach_per_effort=400)

        self.assertEqual(len(ranked), 1)
        self.assertEqual(ranked[0].name, "High leverage")

    def test_rejects_invalid_min_reach_per_effort(self):
        experiments = [{"name": "One", "reach": 100, "impact": 1, "confidence": 0.8, "effort": 1}]

        with self.assertRaisesRegex(ValueError, "min_reach_per_effort must be >= 0"):
            rank_experiments(experiments, min_reach_per_effort=-1)

    def test_filters_by_min_expected_lift(self):
        experiments = [
            {"name": "Niche tweak", "reach": 80, "impact": 0.9, "confidence": 0.9, "effort": 0.5},
            {"name": "Lifecycle campaign", "reach": 1000, "impact": 0.4, "confidence": 0.8, "effort": 4},
        ]

        ranked = rank_experiments(experiments, min_expected_lift=200)

        self.assertEqual(len(ranked), 1)
        self.assertEqual(ranked[0].name, "Lifecycle campaign")

    def test_rejects_invalid_min_expected_lift(self):
        experiments = [{"name": "One", "reach": 100, "impact": 1, "confidence": 0.8, "effort": 1}]

        with self.assertRaisesRegex(ValueError, "min_expected_lift must be >= 0"):
            rank_experiments(experiments, min_expected_lift=-1)

    def test_filters_by_min_roi(self):
        experiments = [
            {"name": "Tiny niche", "reach": 120, "impact": 0.4, "confidence": 0.8, "effort": 4},
            {"name": "Lifecycle win", "reach": 900, "impact": 0.5, "confidence": 0.8, "effort": 2},
        ]

        ranked = rank_experiments(experiments, min_roi=100)

        self.assertEqual(len(ranked), 1)
        self.assertEqual(ranked[0].name, "Lifecycle win")

    def test_rejects_invalid_min_roi(self):
        experiments = [{"name": "One", "reach": 100, "impact": 1, "confidence": 0.8, "effort": 1}]

        with self.assertRaisesRegex(ValueError, "min_roi must be >= 0"):
            rank_experiments(experiments, min_roi=-1)

    def test_limits_results_with_max_results(self):
        experiments = [
            {"name": "A", "reach": 1000, "impact": 0.8, "confidence": 0.9, "effort": 2},
            {"name": "B", "reach": 900, "impact": 0.7, "confidence": 0.9, "effort": 2},
            {"name": "C", "reach": 800, "impact": 0.6, "confidence": 0.9, "effort": 2},
        ]

        ranked = rank_experiments(experiments, max_results=2)

        self.assertEqual(len(ranked), 2)
        self.assertEqual([item.name for item in ranked], ["A", "B"])

    def test_rejects_invalid_max_results(self):
        experiments = [{"name": "One", "reach": 100, "impact": 1, "confidence": 0.8, "effort": 1}]

        with self.assertRaisesRegex(ValueError, "max_results must be a positive integer"):
            rank_experiments(experiments, max_results=0)

        with self.assertRaisesRegex(ValueError, "max_results must be a positive integer"):
            rank_experiments(experiments, max_results=1.5)

    def test_filters_by_include_names_case_insensitive(self):
        experiments = [
            {"name": "Onboarding Email", "reach": 800, "impact": 0.7, "confidence": 0.9, "effort": 2},
            {"name": "SEO refresh", "reach": 1000, "impact": 0.6, "confidence": 0.8, "effort": 4},
        ]

        ranked = rank_experiments(experiments, include_names=[" onboarding email "])

        self.assertEqual(len(ranked), 1)
        self.assertEqual(ranked[0].name, "Onboarding Email")

    def test_filters_by_exclude_names_case_insensitive(self):
        experiments = [
            {"name": "Onboarding Email", "reach": 800, "impact": 0.7, "confidence": 0.9, "effort": 2},
            {"name": "SEO refresh", "reach": 1000, "impact": 0.6, "confidence": 0.8, "effort": 4},
        ]

        ranked = rank_experiments(experiments, exclude_names=["seo refresh"])

        self.assertEqual(len(ranked), 1)
        self.assertEqual(ranked[0].name, "Onboarding Email")

    def test_rejects_empty_include_or_exclude_name_sets(self):
        experiments = [{"name": "One", "reach": 100, "impact": 1, "confidence": 0.8, "effort": 1}]

        with self.assertRaisesRegex(ValueError, "include_names must contain at least one non-empty name"):
            rank_experiments(experiments, include_names=["   "])

        with self.assertRaisesRegex(ValueError, "exclude_names must contain at least one non-empty name"):
            rank_experiments(experiments, exclude_names=[""])

    def test_filters_by_name_contains_case_insensitive(self):
        experiments = [
            {"name": "Pricing page CTA", "reach": 1000, "impact": 0.7, "confidence": 0.8, "effort": 2},
            {"name": "Onboarding email", "reach": 800, "impact": 0.9, "confidence": 0.9, "effort": 2},
            {"name": "Homepage pricing copy", "reach": 700, "impact": 0.6, "confidence": 0.8, "effort": 2},
        ]

        ranked = rank_experiments(experiments, name_contains=" PRICING ")

        self.assertEqual([item.name for item in ranked], ["Pricing page CTA", "Homepage pricing copy"])

    def test_rejects_empty_name_contains(self):
        experiments = [{"name": "One", "reach": 100, "impact": 1, "confidence": 0.8, "effort": 1}]

        with self.assertRaisesRegex(ValueError, "name_contains must be a non-empty string"):
            rank_experiments(experiments, name_contains="   ")

    def test_sorts_by_expected_lift_when_requested(self):
        experiments = [
            {"name": "Low effort", "reach": 500, "impact": 0.6, "confidence": 0.9, "effort": 1},
            {"name": "High lift", "reach": 1300, "impact": 0.5, "confidence": 0.8, "effort": 4},
        ]

        ranked = rank_experiments(experiments, sort_by="expected_lift")

        self.assertEqual([item.name for item in ranked], ["High lift", "Low effort"])

    def test_filters_by_max_risk(self):
        experiments = [
            {"name": "Safer", "reach": 600, "impact": 0.7, "confidence": 0.9, "effort": 2, "risk": 0.2},
            {"name": "Risky", "reach": 1200, "impact": 0.9, "confidence": 0.8, "effort": 2, "risk": 0.8},
        ]

        ranked = rank_experiments(experiments, max_risk=0.5)

        self.assertEqual(len(ranked), 1)
        self.assertEqual(ranked[0].name, "Safer")

    def test_sorts_by_risk_adjusted_score_when_requested(self):
        experiments = [
            {"name": "High score high risk", "reach": 1000, "impact": 0.8, "confidence": 0.9, "effort": 2, "risk": 0.8},
            {"name": "Solid safer", "reach": 850, "impact": 0.75, "confidence": 0.9, "effort": 2, "risk": 0.1},
        ]

        ranked = rank_experiments(experiments, sort_by="risk_adjusted_score")

        self.assertEqual(ranked[0].name, "Solid safer")
        self.assertGreater(ranked[0].risk_adjusted_score, ranked[1].risk_adjusted_score)

    def test_defaults_missing_risk_to_zero(self):
        experiments = [
            {"name": "No risk field", "reach": 500, "impact": 0.7, "confidence": 0.8, "effort": 2},
        ]

        ranked = rank_experiments(experiments)

        self.assertEqual(ranked[0].risk, 0.0)
        self.assertEqual(ranked[0].risk_adjusted_score, ranked[0].score)

    def test_rejects_invalid_risk_inputs(self):
        experiments = [{"name": "Bad risk", "reach": 500, "impact": 0.7, "confidence": 0.8, "effort": 2, "risk": 1.2}]

        with self.assertRaisesRegex(ValueError, "risk must be within \[0, 1\]"):
            rank_experiments(experiments)

        with self.assertRaisesRegex(ValueError, "max_risk must be within \[0, 1\]"):
            rank_experiments(experiments=[{"name": "Good", "reach": 100, "impact": 1, "confidence": 0.8, "effort": 1}], max_risk=-0.1)

    def test_filters_by_min_risk_adjusted_score(self):
        experiments = [
            {"name": "High risk", "reach": 1200, "impact": 0.9, "confidence": 0.8, "effort": 2, "risk": 0.8},
            {"name": "Balanced", "reach": 900, "impact": 0.7, "confidence": 0.9, "effort": 2, "risk": 0.1},
        ]

        ranked = rank_experiments(experiments, min_risk_adjusted_score=150)

        self.assertEqual(len(ranked), 1)
        self.assertEqual(ranked[0].name, "Balanced")

    def test_rejects_invalid_min_risk_adjusted_score(self):
        experiments = [{"name": "One", "reach": 100, "impact": 1, "confidence": 0.8, "effort": 1}]

        with self.assertRaisesRegex(ValueError, "min_risk_adjusted_score must be >= 0"):
            rank_experiments(experiments, min_risk_adjusted_score=-1)

    def test_applies_confidence_boost_weight_zero_as_plain_base_score(self):
        experiments = [
            {"name": "A", "reach": 1000, "impact": 0.5, "confidence": 0.8, "effort": 2},
            {"name": "B", "reach": 800, "impact": 0.6, "confidence": 0.9, "effort": 2},
        ]

        ranked = rank_experiments(experiments, confidence_boost_weight=0)

        for item in ranked:
            self.assertAlmostEqual(item.score, item.base_score)

    def test_applies_confidence_boost_weight_one_for_full_normalized_boost(self):
        experiments = [
            {"name": "Lower CWI", "reach": 1000, "impact": 0.5, "confidence": 0.8, "effort": 2},
            {"name": "Higher CWI", "reach": 800, "impact": 0.6, "confidence": 0.9, "effort": 2},
        ]

        ranked = rank_experiments(experiments, confidence_boost_weight=1)
        by_name = {item.name: item for item in ranked}

        self.assertAlmostEqual(by_name["Lower CWI"].score, 0.0)
        self.assertAlmostEqual(by_name["Higher CWI"].score, by_name["Higher CWI"].base_score)

    def test_rejects_invalid_confidence_boost_weight(self):
        experiments = [{"name": "One", "reach": 100, "impact": 1, "confidence": 0.8, "effort": 1}]

        with self.assertRaisesRegex(ValueError, "confidence_boost_weight must be within \[0, 1\]"):
            rank_experiments(experiments, confidence_boost_weight=-0.1)

        with self.assertRaisesRegex(ValueError, "confidence_boost_weight must be within \[0, 1\]"):
            rank_experiments(experiments, confidence_boost_weight=1.1)

    def test_sorts_by_name_alphabetically_when_requested(self):
        experiments = [
            {"name": "Zulu", "reach": 100, "impact": 1, "confidence": 0.8, "effort": 1},
            {"name": "alpha", "reach": 100, "impact": 1, "confidence": 0.8, "effort": 1},
            {"name": "Bravo", "reach": 100, "impact": 1, "confidence": 0.8, "effort": 1},
        ]

        ranked = rank_experiments(experiments, sort_by="name")

        self.assertEqual([item.name for item in ranked], ["alpha", "Bravo", "Zulu"])

    def test_includes_owner_and_channel_metadata_when_present(self):
        experiments = [
            {
                "name": "Lifecycle email",
                "owner": "Growth Team",
                "channel": "email",
                "reach": 800,
                "impact": 0.7,
                "confidence": 0.9,
                "effort": 2,
            }
        ]

        ranked = rank_experiments(experiments)

        self.assertEqual(ranked[0].owner, "Growth Team")
        self.assertEqual(ranked[0].channel, "email")

    def test_filters_by_include_owners(self):
        experiments = [
            {"name": "Email lifecycle", "owner": "Growth", "reach": 900, "impact": 0.7, "confidence": 0.9, "effort": 2},
            {"name": "Pricing page", "owner": "Product", "reach": 950, "impact": 0.8, "confidence": 0.8, "effort": 2},
        ]

        ranked = rank_experiments(experiments, include_owners=[" growth "])

        self.assertEqual(len(ranked), 1)
        self.assertEqual(ranked[0].name, "Email lifecycle")

    def test_filters_by_exclude_owners(self):
        experiments = [
            {"name": "Email lifecycle", "owner": "Growth", "reach": 900, "impact": 0.7, "confidence": 0.9, "effort": 2},
            {"name": "Pricing page", "owner": "Product", "reach": 950, "impact": 0.8, "confidence": 0.8, "effort": 2},
        ]

        ranked = rank_experiments(experiments, exclude_owners=["product"])

        self.assertEqual(len(ranked), 1)
        self.assertEqual(ranked[0].name, "Email lifecycle")

    def test_rejects_empty_owner_filters(self):
        experiments = [{"name": "One", "reach": 100, "impact": 1, "confidence": 0.8, "effort": 1}]

        with self.assertRaisesRegex(ValueError, "include_owners must contain at least one non-empty owner"):
            rank_experiments(experiments, include_owners=["  "])

        with self.assertRaisesRegex(ValueError, "exclude_owners must contain at least one non-empty owner"):
            rank_experiments(experiments, exclude_owners=[""])

    def test_filters_by_include_channels(self):
        experiments = [
            {"name": "Email lifecycle", "channel": "email", "reach": 900, "impact": 0.7, "confidence": 0.9, "effort": 2},
            {"name": "Pricing page", "channel": "web", "reach": 950, "impact": 0.8, "confidence": 0.8, "effort": 2},
        ]

        ranked = rank_experiments(experiments, include_channels=[" email "])

        self.assertEqual(len(ranked), 1)
        self.assertEqual(ranked[0].name, "Email lifecycle")

    def test_filters_by_exclude_channels(self):
        experiments = [
            {"name": "Email lifecycle", "channel": "email", "reach": 900, "impact": 0.7, "confidence": 0.9, "effort": 2},
            {"name": "Pricing page", "channel": "web", "reach": 950, "impact": 0.8, "confidence": 0.8, "effort": 2},
        ]

        ranked = rank_experiments(experiments, exclude_channels=["web"])

        self.assertEqual(len(ranked), 1)
        self.assertEqual(ranked[0].name, "Email lifecycle")

    def test_rejects_empty_channel_filters(self):
        experiments = [{"name": "One", "reach": 100, "impact": 1, "confidence": 0.8, "effort": 1}]

        with self.assertRaisesRegex(ValueError, "include_channels must contain at least one non-empty channel"):
            rank_experiments(experiments, include_channels=["  "])

        with self.assertRaisesRegex(ValueError, "exclude_channels must contain at least one non-empty channel"):
            rank_experiments(experiments, exclude_channels=[""])

    def test_rejects_invalid_sort_by(self):
        experiments = [{"name": "One", "reach": 100, "impact": 1, "confidence": 0.8, "effort": 1}]

        with self.assertRaisesRegex(ValueError, "sort_by must be one of"):
            rank_experiments(experiments, sort_by="unknown_metric")


if __name__ == "__main__":
    unittest.main()
