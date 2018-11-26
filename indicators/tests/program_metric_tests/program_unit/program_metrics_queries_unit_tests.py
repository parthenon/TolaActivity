""" Program metrics tests for the Home Page

    - program.metrics['indicator_count'] - total indicators for program
    - program.metrics['targets_defined'] - indicators with targets defined
    - program.metrics['reported_results'] - indicators with reported results
    - program.metrics['results_count'] - total results for all indicators in program
    - program.metrics['results_evidence'] - total results for all indicators in program which have evidence/tolatable
    """


import datetime
from indicators.queries import ProgramWithMetrics
from indicators.models import Indicator, PeriodicTarget
from indicators.views.views_indicators import generate_periodic_targets
from indicators.views.views_reports import IPTT_ReportView
from factories import (
    indicators_models as i_factories,
    workflow_models as w_factories
)
from workflow.models import Program
from django import test

def get_reporting_program(*annotations):
    if annotations[0] == 'metrics':
        annotations = ['targets', 'results', 'evidence']
    return ProgramWithMetrics.home_page.with_annotations(*annotations).get(pk=1)

class ProgramMetricsBase(test.TestCase):
    fixtures = ['one_year_program.yaml']

    def setUp(self):
        self.program = Program.objects.get(pk=1)
        self.indicators = []
        self.targets = []
        self.data = []
        self.documents = []

    def get_indicator(self, frequency=Indicator.LOP):
        indicator = i_factories.IndicatorFactory(
            target_frequency=frequency,
            program=self.program
        )
        self.indicators.append(indicator)
        return indicator

    def add_data(self, indicator=None, target=None):
        data = i_factories.CollectedDataFactory(
            indicator=indicator,
            periodic_target=target,
            date_collected=self.program.reporting_period_start+datetime.timedelta(days=3+2*len(self.data)),
            achieved=100
        )
        self.data.append(data)
        return data

    def get_target(self, indicator):
        target = i_factories.PeriodicTargetFactory(
            indicator=indicator,
            period="target {0}".format(len(self.targets)),
            target=100
        )
        self.targets.append(target)
        return target

    def add_evidence(self, data):
        documentation = w_factories.DocumentationFactory()
        data.evidence = documentation
        data.save()
        self.documents.append(documentation)


class TestIndicatorCounts(ProgramMetricsBase):
    def test_indicator_count_zero(self):
        """no indicators should return indicator count of 0"""
        program = get_reporting_program('count')
        self.assertEqual(program.indicator_count, 0)


# TARGETS DEFINED TESTS:

# pylint: disable=W0232
class TargetTestsMixin:
    """mixin containing test methods so tests won't fire on base class"""
    print_all=False

    def test_one_good(self):
        self.add_good_indicator()
        program_reporting = get_reporting_program('targets')
        self.assertEqual(program_reporting.metrics['targets_defined'], 1,
                         "One indicator with targets defined should be 1 good, got {0}".format(
                             program_reporting.metrics['targets_defined']))

    def test_two_good(self):
        self.add_good_indicator()
        self.add_good_indicator()
        program_reporting = get_reporting_program('targets')
        self.assertEqual(program_reporting.metrics['targets_defined'], 2,
                         "Two indicators with targets defined should be 2 good, got {0}".format(
                             program_reporting.metrics['targets_defined']))

    def test_alternate_good_indicators(self):
        if not hasattr(self, 'good_indicators'):
            self.skipTest('no alternate good indicator methods')
        for good_indicator_method in self.good_indicators:
            getattr(self, good_indicator_method)()
            program_reporting = get_reporting_program('targets')
            self.assertEqual(program_reporting.metrics['targets_defined'], 1,
                             "One indicator with targets defined should be 1 good, got {0}".format(
                                 program_reporting.metrics['targets_defined']))
            for indicator in self.indicators:
                indicator.delete()
            self.indicators = []
            for target in self.targets:
                target.delete()
            self.targets = []

    def test_one_bad_indicator(self):
        if not hasattr(self, 'bad_indicators'):
            self.skipTest('no bad indicator methods')
        for bad_indicator_method in self.bad_indicators:
            getattr(self, bad_indicator_method)()
            program_reporting = get_reporting_program('targets')
            self.assertEqual(
                program_reporting.metrics['targets_defined'], 0,
                "{case}: One indicator {0} should be 0 good, got {1}".format(
                    bad_indicator_method, program_reporting.metrics['targets_defined'], case=self.testcase))
            for indicator in self.indicators:
                indicator.delete()
            self.indicators = []
            for target in self.targets:
                target.delete()
            self.targets = []

    def test_bad_and_good(self):
        if not hasattr(self, 'bad_indicators'):
            self.skipTest('no bad indicator methods')
        self.add_good_indicator()
        expected_bad_count = 0
        for bad_indicator_method in self.bad_indicators:
            getattr(self, bad_indicator_method)()
            expected_bad_count += 1
        program_reporting = get_reporting_program('targets')
        self.assertEqual(
            program_reporting.metrics['targets_defined'], 1,
            "One good {0} bad indicators should be {1} good, got {2} with ct {3} and def {4}".format(
                expected_bad_count, 1, program_reporting.metrics['targets_defined'],
                program_reporting.indicator_count, program_reporting.targets_defined_count))

class TestLOPTargetsDefined(ProgramMetricsBase, TargetTestsMixin):
    testcase = "lop"
    bad_indicators = [
        'add_no_target_indicator'
    ]

    def add_good_indicator(self):
        indicator = self.get_indicator(Indicator.LOP)
        indicator.lop_target = 1000
        indicator.save()

    def add_no_target_indicator(self):
        indicator = self.get_indicator(Indicator.LOP)
        assert indicator.lop_target is None, "test relies on lop_target being default None"

class TestMidEndTargetsDefined(ProgramMetricsBase, TargetTestsMixin):
    testcase = "midend"
    print_all=True
    bad_indicators = [
        'add_no_midline_indicator',
        'add_no_endline_indicator',
        'add_no_targets_indicator',
    ]
    def add_good_indicator(self):
        indicator = self.get_indicator(Indicator.MID_END)
        target_mid = i_factories.PeriodicTargetFactory(
            indicator=indicator,
            period=PeriodicTarget.MIDLINE,
            target=400
        )
        target_end = i_factories.PeriodicTargetFactory(
            indicator=indicator,
            period=PeriodicTarget.ENDLINE,
            target=800
        )
        self.targets.extend([target_mid, target_end])

    def add_no_midline_indicator(self):
        indicator = self.get_indicator(Indicator.MID_END)
        target_end = i_factories.PeriodicTargetFactory(
            indicator=indicator,
            period=PeriodicTarget.ENDLINE,
            target=800
        )
        self.targets.append(target_end)

    def add_no_endline_indicator(self):
        indicator = self.get_indicator(Indicator.MID_END)
        target_mid = i_factories.PeriodicTargetFactory(
            indicator=indicator,
            period=PeriodicTarget.MIDLINE,
            target=800
        )
        self.targets.append(target_mid)

    def add_no_targets_indicator(self):
        self.get_indicator(Indicator.MID_END)

class TestEventTargetsDefined(ProgramMetricsBase, TargetTestsMixin):
    testcase = 'event'
    good_indicators = [
        'add_good_indicator_multiple_targets',
    ]
    bad_indicators = [
        'add_no_target_indicator',
    ]
    def add_good_indicator(self):
        indicator = self.get_indicator(Indicator.EVENT)
        target = i_factories.PeriodicTargetFactory(
            indicator=indicator,
            period="Event 1",
            target=400
        )
        self.targets.append(target)

    def add_good_indicator_multiple_targets(self):
        indicator = self.get_indicator(Indicator.EVENT)
        target_1 = i_factories.PeriodicTargetFactory(
            indicator=indicator,
            period="Event 1",
            target=400
        )
        target_2 = i_factories.PeriodicTargetFactory(
            indicator=indicator,
            period="Event 6",
            target=500
        )
        self.targets.extend([target_1, target_2])

    def add_no_target_indicator(self):
        self.get_indicator(Indicator.EVENT)

class TimeAwareTargetsMixin:
    testcase = 'timeaware'
    bad_indicators = [
        'add_indicator_missing_one_target',
    ]

    def generate_targets(self, indicator, skip=None):
        #pylint: disable=W0212
        target_frequency_num_periods = IPTT_ReportView._get_num_periods(
            self.program.reporting_period_start,
            self.program.reporting_period_end,
            self.frequency
        )
        if skip is not None:
            target_frequency_num_periods -= 1
        if target_frequency_num_periods == 0:
            return []
        generatedTargets = generate_periodic_targets(
            self.frequency, self.program.reporting_period_start,
            target_frequency_num_periods, '')
        to_return_targets = []
        for target in generatedTargets:
            to_return_targets.append(
                i_factories.PeriodicTargetFactory(
                    indicator=indicator,
                    period=target['period'],
                    start_date=target['start_date'],
                    end_date=target['end_date']
                )
            )
        return to_return_targets

    def add_good_indicator(self):
        indicator = self.get_indicator(self.frequency)
        targets = self.generate_targets(indicator)
        for target in targets:
            target.value = 400
            target.save()
            self.targets.append(target)

    def add_indicator_missing_one_target(self):
        indicator = self.get_indicator(self.frequency)
        targets = self.generate_targets(indicator, skip=1)
        for target in targets:
            target.value = 400
            target.save()
            self.targets.append(target)

class TestAnnualTargetsDefined(TargetTestsMixin, TimeAwareTargetsMixin, ProgramMetricsBase):
    testcase = 'annual'
    frequency = Indicator.ANNUAL

class TestSemiAnnualTargetCounts(TargetTestsMixin, TimeAwareTargetsMixin, ProgramMetricsBase):
    testcase = 'semiannual'
    frequency = Indicator.SEMI_ANNUAL

class TestTriAnnualTargetCounts(TargetTestsMixin, TimeAwareTargetsMixin, ProgramMetricsBase):
    testcase = 'triannual'
    frequency = Indicator.TRI_ANNUAL

class TestQuarterlyTargetCounts(TargetTestsMixin, TimeAwareTargetsMixin, ProgramMetricsBase):
    testcase = 'quarterly'
    frequency = Indicator.QUARTERLY

class TestMonthlyTargetCounts(TargetTestsMixin, TimeAwareTargetsMixin, ProgramMetricsBase):
    testcase = 'monthly'
    frequency = Indicator.MONTHLY

# REPORTED RESULTS TESTS:    

class TestProgramReportedResultsQueries(ProgramMetricsBase):
    def test_program_one_indicator_reported_results(self):
        for frequency in [Indicator.LOP, Indicator.EVENT, Indicator.SEMI_ANNUAL, Indicator.MONTHLY]:
            indicator = self.get_indicator(frequency=frequency)
            with self.assertNumQueries(2):
                program = get_reporting_program('results')
                self.assertEqual(
                    program.metrics['reported_results'], 0,
                    "One bare indicator should not be counted as 0 reported results, got {0}".format(
                        program.metrics['reported_results'])
                )
                self.assertEqual(
                    program.metrics['results_count'], 0,
                    "One bare indicator should not be counted as 0 results count, got {0}".format(
                        program.metrics['results_count'])
                )
            self.add_data(indicator)
            program = get_reporting_program('results')
            self.assertEqual(
                program.metrics['reported_results'], 1,
                "One indicator with 1 results should  be counted as 1 reported results, got {0}".format(
                    program.metrics['reported_results'])
            )
            self.assertEqual(
                program.metrics['results_count'], 1,
                "One indicator with one results should be counted as 1 results count, got {0}".format(
                    program.metrics['results_count'])
            )
            self.add_data(indicator)
            program = get_reporting_program('results')
            self.assertEqual(
                program.metrics['reported_results'], 1,
                "One indicator with 2 results should  be counted as 1 reported results, got {0}".format(
                    program.metrics['reported_results'])
            )
            self.assertEqual(
                program.metrics['results_count'], 2,
                "One indicator with 2 results should be counted as 2 results count, got {0}".format(
                    program.metrics['results_count'])
            )
            for datum in self.data:
                datum.delete()
            self.data = []
            for indicator in self.indicators:
                indicator.delete()
            self.indicators = []

    def test_multiple_indicators(self):
        for frequency, _ in Indicator.TARGET_FREQUENCIES:
            indicator = self.get_indicator(frequency=frequency)
            self.add_data(indicator)
            self.add_data(indicator)
        for frequency, _ in Indicator.TARGET_FREQUENCIES:
            indicator = self.get_indicator(frequency=frequency)
        program = get_reporting_program('results')
        self.assertEqual(
            program.metrics['reported_results'], len(Indicator.TARGET_FREQUENCIES),
            "one of each freq with data should count as {0} reported results, got {1}".format(
                len(Indicator.TARGET_FREQUENCIES), program.metrics['reported_results']
            )
        )
        self.assertEqual(
            program.metrics['results_count'], 2*len(Indicator.TARGET_FREQUENCIES),
            "one of each freq with data should count as {0} reported results, got {1}".format(
                2*len(Indicator.TARGET_FREQUENCIES), program.metrics['results_count']
            )
        )

# RESULTS BACKED UP TESTS:


class TestProgramWithEvidenceQueries(ProgramMetricsBase):
    def test_program_one_indicator_reported_results(self):
        for frequency in [Indicator.LOP, Indicator.EVENT, Indicator.MID_END, Indicator.QUARTERLY]:
            indicator = self.get_indicator(frequency=frequency)
            program = get_reporting_program('evidence')
            self.assertEqual(
                program.metrics['results_evidence'], 0,
                "One bare indicator should be counted as 0% evidence, got {0}".format(
                    program.metrics['results_evidence'])
            )
            data = self.add_data(indicator)
            self.add_evidence(data)
            program = get_reporting_program('evidence')
            self.assertEqual(
                program.metrics['results_evidence'], 1,
                "One indicator with 1 result and 1 evidence should be counted as 1 with evidence, got {0}".format(
                    program.metrics['results_evidence'])
            )
            for doc in self.documents:
                doc.delete()
            self.documents = []
            for datum in self.data:
                datum.delete()
            self.data = []
            for indicator in self.indicators:
                indicator.delete()
            self.indicators = []

    def test_multiple_indicators(self):
        for frequency, _ in Indicator.TARGET_FREQUENCIES:
            indicator = self.get_indicator(frequency=frequency)
            data = self.add_data(indicator)
            self.add_evidence(data)
        for frequency, _ in Indicator.TARGET_FREQUENCIES:
            indicator = self.get_indicator(frequency=frequency)
            data = self.add_data(indicator)
        program = get_reporting_program('evidence')
        self.assertEqual(
            program.metrics['results_evidence']*2, program.metrics['results_count'],
            "one of each freq with data should count as double evidence as count, got {0} ev and {1} results".format(
                program.metrics['results_evidence'], program.metrics['results_count']
            )
        )

    def test_multiple_data_points(self):
        for frequency, _ in Indicator.TARGET_FREQUENCIES:
            indicator = self.get_indicator(frequency=frequency)
            data = self.add_data(indicator)
            self.add_evidence(data)
            _ = self.add_data(indicator)
            _ = self.add_data(indicator)
        for frequency, _ in Indicator.TARGET_FREQUENCIES:
            indicator = self.get_indicator(frequency=frequency)
            data = self.add_data(indicator)
        program = get_reporting_program('evidence')
        self.assertEqual(
            program.metrics['results_evidence'], len(Indicator.TARGET_FREQUENCIES),
            "one of each freq with 1 ev/3 results, 1 of each freq with 0 ev/1res"
            " should count as 8 with evidence results, got {0}".format(
                program.metrics['results_evidence']
            )
        )


class TestIndicatorReportingEdgeCases(test.TestCase):
    fixtures = ['one_year_program.yaml']

    def setUp(self):
        self.program = Program.objects.get(pk=1)

    def get_indicator(self):
        return i_factories.IndicatorFactory(
            program=self.program,
            target_frequency=Indicator.LOP,
            lop_target=1000
        )

    def add_result(self, indicator):
        return i_factories.CollectedDataFactory(
            indicator=indicator,
            program=self.program,
            achieved=100,
            date_collected=self.program.reporting_period_start
        )

    def add_evidence(self, result):
        document = w_factories.DocumentationFactory()
        result.evidence = document
        result.save()

    def results_count_asserts(self, indicator_count, with_results_count, results_count):
        reporting_program = get_reporting_program('metrics')
        self.assertEqual(
            reporting_program.metrics['indicator_count'], indicator_count,
            "{0} indicator should show indicator_count as {0}, got {1}".format(
                indicator_count, reporting_program.metrics['indicator_count']
            )
        )
        self.assertEqual(
            reporting_program.metrics['reported_results'], with_results_count,
            "{0} with results should show reported_results as {0}, got {1}".format(
                with_results_count, reporting_program.metrics['reported_results']
                ))
        self.assertEqual(
            reporting_program.metrics['results_count'], results_count,
            "{0} results should show results_count as {0}, got {1}".format(
                results_count, reporting_program.metrics['results_count'])
        )

    def test_needs_evidence_counts(self):
        indicator = self.get_indicator()
        result = self.add_result(indicator)
        metrics = get_reporting_program('metrics').metrics
        self.assertEqual(
            metrics['results_count'], 1,
            "one indicator with 1 result should have 1 result count, got {0}".format(metrics['results_count']))
        self.assertEqual(
            metrics['results_evidence'], 0,
            "one indicator with 1 result and no evidence should have 0 evidence, got {0}".format(
                metrics['results_evidence']
            )
        )
        self.add_evidence(result)
        metrics = get_reporting_program('metrics').metrics
        self.assertEqual(
            metrics['results_count'], 1,
            "one indicator with 1 result should have 1 result count, got {0}".format(metrics['results_count']))
        self.assertEqual(
            metrics['results_evidence'], 1,
            "one indicator with 1 result and 1 evidence should have 1 evidence, got {0}".format(
                metrics['results_evidence']
            )
        )
        indicator2 = self.get_indicator()
        result2 = self.add_result(indicator2)
        indicator3 = self.get_indicator()
        result3 = self.add_result(indicator3)
        result4 = self.add_result(indicator3)
        self.add_evidence(result4)
        result5 = self.add_result(indicator3)
        self.add_evidence(result5)
        metrics = get_reporting_program('metrics').metrics
        self.assertEqual(
            metrics['results_count'], 5,
            "three indicators with 5 results should have 5 result count, got {0}".format(metrics['results_count']))
        self.assertEqual(
            metrics['results_evidence'], 3,
            "three indicators with 5 result and 3 evidence should have 3 evidence, got {0}".format(
                metrics['results_evidence']
            )
        )