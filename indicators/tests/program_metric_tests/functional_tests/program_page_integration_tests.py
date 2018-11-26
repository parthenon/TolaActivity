"""Integration tests for the Program Page (indicator data for one program with rollup metrics available)"""

import datetime
import unittest
import time
import json
from indicators.models import Indicator, PeriodicTarget, CollectedData
from workflow.models import Documentation, Program
from indicators.queries import ProgramWithMetrics
from factories import (
    workflow_models as w_factories,
    indicators_models as i_factories
)
from django import test

class ProgramPageQueryTests(test.TestCase):
    fixtures = ['one_program_home_page.yaml']

    def test_scope_counts_and_metric_counts(self):
        with self.assertNumQueries(2):
            program = ProgramWithMetrics.program_page.get(pk=1)
            indicators = program.annotated_indicators
            indicator_count = len(indicators)
            nonreporting = len([i for i in indicators if not i.reporting])
            low = len([i for i in indicators if i.reporting and i.over_under == -1])
            on_scope = len([i for i in indicators if i.reporting and i.over_under == 0])
            high = len([i for i in indicators if i.reporting and i.over_under == 1])
            targets_defined = len([i for i in indicators if i.all_targets_defined])
            reported_results = len([i for i in indicators if i.has_reported_results])
            results_count = sum([i.results_count for i in indicators])
            results_evidence = sum([i.results_with_evidence_count for i in indicators])
        self.assertEqual(nonreporting, 7)
        self.assertEqual(low, 5)
        self.assertEqual(on_scope, 3)
        self.assertEqual(high, 4)
        self.assertEqual(indicator_count, 19)
        self.assertEqual(targets_defined, 15)
        self.assertEqual(reported_results, 12)
        self.assertEqual(results_count, 22)
        self.assertEqual(results_evidence, 2)



def do_add_indicator(program):
    indicator = i_factories.IndicatorFactory(program=program)
    return indicator

def do_add_defined_target(indicator):
    indicator.target_frequency = Indicator.MID_END
    mid_target = i_factories.PeriodicTargetFactory(
        indicator=indicator,
        period=PeriodicTarget.MIDLINE,
        target=1000
    )
    end_target = i_factories.PeriodicTargetFactory(
        indicator=indicator,
        period=PeriodicTarget.ENDLINE,
        target=400
    )
    indicator.save()
    return (mid_target, end_target)

def do_add_reported_result(indicator, collect_date, program):
    return i_factories.CollectedDataFactory(
        indicator=indicator,
        date_collected=collect_date,
        achieved=140,
        program=program
    )

def do_add_evidence(result, program):
    doc = w_factories.DocumentationFactory(program=program)
    result.evidence = doc
    result.save()


class ProgramWithMetricsQueryCountsBase(test.TestCase):
    skip_all = False
    do_print = False
    country = None
    program_start_date = datetime.date.today()-datetime.timedelta(days=730)
    program_end_date = datetime.date.today()-datetime.timedelta(days=1)
    collect_date = datetime.date.today()-datetime.timedelta(days=400)

    def setUp(self):
        if self.skip_all:
            raise unittest.SkipTest('skip')

    @classmethod
    def setUpTestData(cls):
        cls.country = w_factories.CountryFactory()
        cls.user = w_factories.TolaUserFactory()
        cls.user.countries.add(cls.country)
        for case in cls.expected_cases:
            program = w_factories.ProgramFactory(
                reporting_period_start=cls.program_start_date,
                reporting_period_end=cls.program_end_date,
                funding_status='Funded',
                name=case['name']
            )
            program.country.add(cls.country)
            for c in range(case['indicator_count']):
                data_count = 0
                indicator = do_add_indicator(program)
                if c < case['targets_defined']:
                    do_add_defined_target(indicator)
                if c < case['reported_results']:
                    collect_date = cls.collect_date + datetime.timedelta(days=data_count)
                    data_count += 1
                    result = do_add_reported_result(indicator, collect_date, program)
                    if c < case['results_evidence']:
                        do_add_evidence(result, program)

#pylint: disable=W0232
class QueryTestsMixin:
    def test_program_queryset_returns_one(self):
        program_qs = ProgramWithMetrics.program_page.all()
        self.assertEqual(program_qs.count(), len(self.expected_cases),
                         "{0} programs created, {1} returned, {2}".format(
                             len(self.expected_cases), program_qs.count(), [x.name for x in program_qs]))

    def test_program_queryset_metric_counts(self):
        for expected in self.expected_cases:
            program = ProgramWithMetrics.program_page.filter(name=expected['name']).first()
            if self.do_print:
                print "targets defined count: {0}".format(program.targets_defined_count)
                for indicator in program.annotated_indicators.all():
                    print "indicator: {0} and defined_targets {1} and targets {2}".format(
                        indicator,
                        indicator.defined_targets,
                        [x.target for x in PeriodicTarget.objects.filter(indicator_id=indicator.pk).all()])
                    print "indicator: {0} and reported_results {1} and results {2}".format(
                        indicator,
                        indicator.reported_results,
                        [x.achieved for x in CollectedData.objects.filter(indicator_id=indicator.pk).all()])
                    print "indicator: {0} and evidence count {1} and documents {2}".format(
                        indicator,
                        indicator.evidence_count,
                        [x for x in Documentation.objects.filter(collecteddata__indicator_id=indicator.pk).all()])
                print "metrics: {0}".format(program.metrics)
            metrics = program.metrics
            for key in ['targets_defined', 'reported_results', 'results_evidence', 'indicator_count']:
                self.assertIn(
                    key, metrics.keys(), "program.metrics should have {0}, got {1}".format(key, metrics.keys()))
                self.assertEqual(metrics[key], expected[key], "expected {0} for {1}, got {2} {3}".format(
                    expected[key], key, metrics, expected))

    def test_program_queryset_takes_one_query(self):
        for expected in self.expected_cases:
            with self.assertNumQueries(2):
                metrics = ProgramWithMetrics.program_page.filter(name=expected['name']).first().metrics
                count = metrics['indicator_count']
                defined_targets = metrics['targets_defined']
                assert count == expected['indicator_count'] # to ensure queryset is evaluated
                

    def test_program_view_returns_correct_program_data(self):
        client = test.Client()
        client.force_login(self.user.user)
        for c, expected in enumerate(self.expected_cases):
            program = Program.objects.filter(name=expected['name']).first()
            response = client.get('/program/{program_id}/0/0/'.format(program_id=program.id))
            self.assertEqual(response.status_code, 200)
            program_response_metrics = response.context['program'].metrics
            for key in ['targets_defined', 'reported_results', 'results_evidence', 'indicator_count']:
                self.assertIn(
                    key, program_response_metrics.keys(), "program.metrics should have {0}, got {1}".format(
                        key, program_response_metrics.keys()))
                self.assertEqual(program_response_metrics[key], expected[key],
                                 "expected {0} for {1}, got {2}".format(
                                     expected[key], key, program_response_metrics[key]))

    def test_program_ajax_update_returns_correct_program_data(self):
        client = test.Client()
        client.force_login(self.user.user)
        for expected in self.expected_cases:
            program = Program.objects.filter(name=expected['name']).first()
            response = client.get('/program/{program_id}/metrics/'.format(program_id=program.id),
                                  HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            self.assertEqual(response.status_code, 200)
            json_metrics = json.loads(response.content)['metrics']
            for key in ['targets_defined', 'reported_results', 'results_evidence', 'indicator_count']:
                self.assertIn(
                    key, json_metrics.keys(), "json metrics should have {0}, got {1}".format(
                        key, json_metrics.keys()))
                self.assertEqual(json_metrics[key], expected[key],
                                 "expected {0} for {1}, got {2}".format(
                                     expected[key], key, json_metrics[key]))

class TestOneBareProgram(ProgramWithMetricsQueryCountsBase, QueryTestsMixin):
    skip_all = False
    expected_cases = [
        {
            'indicator_count': 0,
            'targets_defined': 0,
            'reported_results': 0,
            'results_evidence': 0,
            'name': 'Bare 1'
        }
    ]

class TestOneProgramWithIndicators(ProgramWithMetricsQueryCountsBase, QueryTestsMixin):
    expected_cases = [
        {
            'indicator_count': 5,
            'targets_defined': 0,
            'reported_results': 0,
            'results_evidence': 0,
            'name': 'Bare Indicators 1'
        }
    ]

class TestFourProgramsWithIndicators(ProgramWithMetricsQueryCountsBase, QueryTestsMixin):
    expected_cases = [
        {
            'indicator_count': 5,
            'targets_defined': 0,
            'reported_results': 0,
            'results_evidence': 0,
            'name': 'Bare Indicators 1'
        },
        {
            'indicator_count': 3,
            'targets_defined': 0,
            'reported_results': 0,
            'results_evidence': 0,
            'name': 'Bare Indicators 2'
        },
        {
            'indicator_count': 9,
            'targets_defined': 0,
            'reported_results': 0,
            'results_evidence': 0,
            'name': 'Bare Indicators 3'
        },
        {
            'indicator_count': 1,
            'targets_defined': 0,
            'reported_results': 0,
            'results_evidence': 0,
            'name': 'Bare Indicators 4'
        }
    ]

class TestOneProgramWithTargetsDefined(ProgramWithMetricsQueryCountsBase, QueryTestsMixin):
    expected_cases = [
        {
            'indicator_count': 5,
            'targets_defined': 3,
            'reported_results': 0,
            'results_evidence': 0,
            'name': 'Target Indicators 1'
        }
    ]

class TestThreeProgramsWithTargetsDefined(ProgramWithMetricsQueryCountsBase, QueryTestsMixin):
    expected_cases = [
        {
            'indicator_count': 4,
            'targets_defined': 3,
            'reported_results': 0,
            'results_evidence': 0,
            'name': 'Target Indicators 1'
        },
        {
            'indicator_count': 2,
            'targets_defined': 2,
            'reported_results': 0,
            'results_evidence': 0,
            'name': 'Target Indicators 2'
        },
        {
            'indicator_count': 5,
            'targets_defined': 1,
            'reported_results': 0,
            'results_evidence': 0,
            'name': 'Target Indicators 3'
        }
    ]

class TestOneProgramWithResultsReported(ProgramWithMetricsQueryCountsBase, QueryTestsMixin):
    expected_cases = [
        {
            'indicator_count': 5,
            'targets_defined': 0,
            'reported_results': 2,
            'results_evidence': 0,
            'name': 'Results Indicators 1'
        }
    ]

class TestMultipleProgramsWithResultsReported(ProgramWithMetricsQueryCountsBase, QueryTestsMixin):
    expected_cases = [
        {
            'indicator_count': 5,
            'targets_defined': 0,
            'reported_results': 2,
            'results_evidence': 0,
            'name': 'Results Indicators 1'
        },
        {
            'indicator_count': 1,
            'targets_defined': 0,
            'reported_results': 1,
            'results_evidence': 0,
            'name': 'Results Indicators 2'
        },
        {
            'indicator_count': 6,
            'targets_defined': 0,
            'reported_results': 5,
            'results_evidence': 0,
            'name': 'Results Indicators 3'
        }
    ]

class TestOneProgramWithEvidenceReported(ProgramWithMetricsQueryCountsBase, QueryTestsMixin):
    expected_cases = [
        {
            'indicator_count': 5,
            'targets_defined': 0,
            'reported_results': 2,
            'results_evidence': 1,
            'name': 'Evidence Indicators 1'
        }
    ]

class TestMultipleProgramsWithEvidenceReported(ProgramWithMetricsQueryCountsBase, QueryTestsMixin):
    expected_cases = [
        {
            'indicator_count': 3,
            'targets_defined': 0,
            'reported_results': 2,
            'results_evidence': 2,
            'name': 'Evidence Indicators 1'
        },
        {
            'indicator_count': 4,
            'targets_defined': 0,
            'reported_results': 2,
            'results_evidence': 1,
            'name': 'Evidence Indicators 2'
        },
        {
            'indicator_count': 6,
            'targets_defined': 0,
            'reported_results': 3,
            'results_evidence': 3,
            'name': 'Evidence Indicators 3'
        }
    ]

class TestProgramsWithMixedTargetTypesAndResultsAndEvdience(ProgramWithMetricsQueryCountsBase, QueryTestsMixin):
    expected_cases = [
        {
            'indicator_count': 2,
            'targets_defined': 1,
            'reported_results': 2,
            'results_evidence': 2,
            'name': 'test name 1'
        },
        {
            'indicator_count': 4,
            'targets_defined': 4,
            'reported_results': 3,
            'results_evidence': 3,
            'name': 'test name 2'
        },
        {
            'indicator_count': 3,
            'targets_defined': 1,
            'reported_results': 3,
            'results_evidence': 1,
            'name': 'test name 3'
        }
    ]
