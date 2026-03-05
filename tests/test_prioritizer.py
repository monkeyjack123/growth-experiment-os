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

    def test_rejects_non_positive_effort(self):
        experiments = [{"name": "Bad", "reach": 100, "impact": 1, "confidence": 1, "effort": 0}]

        with self.assertRaisesRegex(ValueError, "effort must be > 0"):
            rank_experiments(experiments)


if __name__ == "__main__":
    unittest.main()
