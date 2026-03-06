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

    def test_rejects_non_positive_effort(self):
        experiments = [{"name": "Bad", "reach": 100, "impact": 1, "confidence": 1, "effort": 0}]

        with self.assertRaisesRegex(ValueError, "effort must be > 0"):
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


if __name__ == "__main__":
    unittest.main()
