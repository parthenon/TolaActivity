"""For a given queryset of programs (1..n) queryset should provide an "all_targets_defined" count and "program_count"
   without unnecessary queries"""

import datetime
from indicators.queries import ProgramWithMetrics
from indicators.models import Indicator
from factories import (
    indicators_models as i_factories,
    workflow_models as w_factories
)
from django import test

def get_program():
    return w_factories.ProgramFactory(
        reporting_period_start=datetime.date(2015, 1, 1),
        reporting_period_end=datetime.date(2016, 12, 31)
    )

def get_one_target_defined_indicator(program):
    indicator = i_factories.IndicatorFactory(
        program=program,
        target_frequency=Indicator.ANNUAL
    )
    i_factories.PeriodicTargetFactory(
        indicator=indicator,
        start_date=datetime.date(2015, 1, 1),
        end_date=datetime.date(2015, 12, 31),
        target=100
    )
    return indicator

def get_all_targets_defined_indicator(program):
    indicator = get_one_target_defined_indicator(program)
    i_factories.PeriodicTargetFactory(
        indicator=indicator,
        start_date=datetime.date(2016, 1, 1),
        end_date=datetime.date(2016, 12, 31),
        target=100
    )
    return indicator

def get_data(indicator):
    return i_factories.ResultFactory(
        indicator=indicator,
        achieved=100,
        date_collected=datetime.date(2016, 10, 1)
    )

def get_evidence(data):
    data.evidence_url = 'http://test_evidence_url'
    data.save()

class TestTwoProgramsBothDefined(test.TestCase):
    def setUp(self):
        program1 = get_program()
        get_all_targets_defined_indicator(program1)
        program2 = get_program()
        get_all_targets_defined_indicator(program2)
        self.program_ids = (program1.id, program2.id)

    def test_programs_each_report_all_defined(self):
        for program_id in self.program_ids:
            annotated = ProgramWithMetrics.home_page.with_annotations().get(pk=program_id)
            self.assertEqual(
                annotated.metrics['indicator_count'],
                annotated.metrics['targets_defined']
            )
            self.assertTrue(annotated.all_targets_defined_for_all_indicators)

    def test_programs_qs_reports_all_defined_counts(self):
        program_qs = ProgramWithMetrics.home_page.with_annotations().filter(pk__in=self.program_ids)
        self.assertEqual(
            program_qs.program_count,
            program_qs.all_targets_defined_for_all_indicators_count
        )

    def test_query_counts(self):
        with self.assertNumQueries(3):
            program_qs = ProgramWithMetrics.home_page.with_annotations().filter(pk__in=self.program_ids)
            self.assertIsNotNone(program_qs.program_count)
            self.assertIsNotNone(program_qs.all_targets_defined_for_all_indicators_count)

class TestTwoProgramsOneDefined(test.TestCase):
    def setUp(self):
        program1 = get_program()
        get_all_targets_defined_indicator(program1)
        program2 = get_program()
        get_one_target_defined_indicator(program2)
        self.program_ids = (program1.id, program2.id)

    def test_programs_qs_reports_all_defined_counts(self):
        program_qs = ProgramWithMetrics.home_page.with_annotations().filter(pk__in=self.program_ids)
        self.assertEqual(
            program_qs.program_count,
            program_qs.all_targets_defined_for_all_indicators_count*2
        )

    def test_query_counts(self):
        with self.assertNumQueries(3):
            program_qs = ProgramWithMetrics.home_page.with_annotations().filter(pk__in=self.program_ids)
            self.assertIsNotNone(program_qs.program_count)
            self.assertIsNotNone(program_qs.all_targets_defined_for_all_indicators_count)

class TestTwoProgramsFiveIndicatorsThreeReportedResults(test.TestCase):
    def setUp(self):
        program1 = get_program()
        ind1 = get_all_targets_defined_indicator(program1)
        get_data(ind1)
        get_data(ind1)
        get_data(ind1)
        get_data(ind1)
        ind2 = get_all_targets_defined_indicator(program1)
        get_data(ind2)
        get_all_targets_defined_indicator(program1)
        program2 = get_program()
        ind4 = get_all_targets_defined_indicator(program2)
        get_data(ind4)
        get_all_targets_defined_indicator(program2)
        self.program_ids = (program1.id, program2.id)

    def test_program_qs_reports_results_count(self):
        program_qs = ProgramWithMetrics.home_page.with_annotations().filter(pk__in=self.program_ids)
        self.assertEqual(program_qs.program_count, 2)
        self.assertEqual(program_qs.indicators_count, 5)
        self.assertEqual(program_qs.indicators_with_results_count, 3)

    def test_query_counts(self):
        with self.assertNumQueries(3):
            program_qs = ProgramWithMetrics.home_page.with_annotations().filter(pk__in=self.program_ids)
            self.assertIsNotNone(program_qs.program_count)
            self.assertIsNotNone(program_qs.indicators_count)
            self.assertIsNotNone(program_qs.indicators_with_results_count)

class TestTwoProgramsFiveIndicatorsEightResultsFiveEvidence(test.TestCase):
    def setUp(self):
        program1 = get_program()
        ind1 = get_all_targets_defined_indicator(program1)
        get_data(ind1)
        data1 = get_data(ind1)
        get_evidence(data1)
        ind2 = get_all_targets_defined_indicator(program1)
        data2 = get_data(ind2)
        get_evidence(data2)
        data3 = get_data(ind2)
        get_evidence(data3)
        get_all_targets_defined_indicator(program1)
        program2 = get_program()
        ind4 = get_all_targets_defined_indicator(program2)
        get_data(ind4)
        data4 = get_data(ind4)
        get_evidence(data4)
        data5 = get_data(ind4)
        get_evidence(data5)
        ind5 = get_all_targets_defined_indicator(program2)
        get_data(ind5)
        self.program_ids = (program1.id, program2.id)

    def test_program_qs_results_count(self):
        program_qs = ProgramWithMetrics.home_page.with_annotations().filter(pk__in=self.program_ids)
        self.assertEqual(program_qs.program_count, 2)
        self.assertEqual(program_qs.results_count, 8)
        self.assertEqual(program_qs.results_with_evidence_count, 5)

    def test_query_counts(self):
        with self.assertNumQueries(3):
            program_qs = ProgramWithMetrics.home_page.with_annotations().filter(pk__in=self.program_ids)
            self.assertIsNotNone(program_qs.program_count)
            self.assertIsNotNone(program_qs.results_count)
            self.assertIsNotNone(program_qs.results_with_evidence_count)

class TestMultipleProgramsStressTestQSCounts(test.TestCase):
    def setUp(self):
        self.program_ids = []
        for _ in range(10):
            program = get_program()
            for _ in range(10):
                ind = get_all_targets_defined_indicator(program)
                get_data(ind)
                get_evidence(get_data(ind))
            self.program_ids.append(program.id)

    def test_query_counts(self):
        with self.assertNumQueries(3):
            program_qs = ProgramWithMetrics.home_page.with_annotations().filter(pk__in=self.program_ids)
            self.assertIsNotNone(program_qs.program_count)
            self.assertIsNotNone(program_qs.all_targets_defined_for_all_indicators_count)
            self.assertIsNotNone(program_qs.indicators_count)
            self.assertIsNotNone(program_qs.indicators_with_results_count)
            self.assertIsNotNone(program_qs.results_count)
            self.assertIsNotNone(program_qs.results_with_evidence_count)
