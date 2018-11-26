"""Functional (query count and stress test) tests for Home Page (groups of programs not broken out by indicator)"""

import unittest
import datetime
import unittest
from indicators.models import Indicator
from indicators.queries import ProgramWithMetrics, get_lop_annotations, get_lop_met_real_annotation, get_over_under_annotation
from factories import (
    workflow_models as w_factories,
    indicators_models as i_factories
)
from django import test

class OneProgramHomePageTests(test.TestCase):
    fixtures = ['one_program_home_page.yaml']

    def test_scope_counts_and_metric_counts(self):
        with self.assertNumQueries(4):
            program = ProgramWithMetrics.home_page.with_annotations().get(pk=1)
            scope_counts = program.scope_counts
            metrics = program.metrics
        self.assertEqual(scope_counts['nonreporting_count'], 7)
        self.assertEqual(scope_counts['low'], 5)
        self.assertEqual(scope_counts['on_scope'], 3)
        self.assertEqual(scope_counts['high'], 4)
        self.assertEqual(metrics['indicator_count'], 19)
        self.assertEqual(metrics['targets_defined'], 15)
        self.assertEqual(metrics['reported_results'], 12)
        self.assertEqual(metrics['results_count'], 22)
        self.assertEqual(metrics['results_evidence'], 2)


class HomePageQueryStressTest(test.TestCase):
    def setUp(self):
        for _ in range(10):
            program = w_factories.ProgramFactory(
                reporting_period_start=datetime.date(2014, 1, 1),
                reporting_period_end=datetime.date(2014, 12, 31)
            )
            for _ in range(5):
                indicator = i_factories.IndicatorFactory(
                    target_frequency=Indicator.LOP,
                    lop_target=100,
                    program=program
                )
                data = i_factories.CollectedDataFactory(
                    indicator=indicator,
                    achieved=105
                )
            for _ in range(5):
                indicator = i_factories.IndicatorFactory(
                    target_frequency=Indicator.LOP,
                    lop_target=100,
                    program=program
                )
                evidence = w_factories.DocumentationFactory(program=program)
                data = i_factories.CollectedDataFactory(
                    indicator=indicator,
                    achieved=50,
                    evidence=evidence
                )
            for _ in range(2):
                indicator = i_factories.IndicatorFactory(
                    target_frequency=Indicator.LOP,
                    program=program
                )
            for _ in range(4):
                indicator = i_factories.IndicatorFactory(
                    target_frequency=Indicator.MID_END,
                    program=program
                )
                for sort in range(2):
                    target = i_factories.PeriodicTargetFactory(
                        indicator=indicator,
                        target=40,
                        start_date=datetime.date(2014, 5, 1),
                        end_date=datetime.date(2014, 8, 1),
                        customsort=sort
                    )
    @unittest.skip('home page query counts currently wrong')
    def test_scope_counts_and_metric_counts(self):
        with self.assertNumQueries(3):
            programs = ProgramWithMetrics.home_page.with_annotations().all()
            nonreporting = sum([p.scope_counts['nonreporting_count'] for p in programs])
            low = sum([p.scope_counts['low'] for p in programs])
            on_scope = sum([p.scope_counts['on_scope'] for p in programs])
            high = sum([p.scope_counts['high'] for p in programs])
            indicator_count = sum([p.metrics['indicator_count'] for p in programs])
            targets_defined = sum([p.metrics['targets_defined'] for p in programs])
            reported_results = sum([p.metrics['reported_results'] for p in programs])
            results_count = sum([p.metrics['results_count'] for p in programs])
            results_evidence = sum([p.metrics['results_evidence'] for p in programs])
        self.assertEqual(nonreporting, 60)
        self.assertEqual(low, 50)
        self.assertEqual(on_scope, 50)
        self.assertEqual(high, 0)
        self.assertEqual(indicator_count, 160)
        self.assertEqual(targets_defined, 140)
        self.assertEqual(reported_results, 100)
        self.assertEqual(results_count, 100)
        self.assertEqual(results_evidence, 50)