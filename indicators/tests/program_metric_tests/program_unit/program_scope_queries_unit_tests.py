"""Unittests for Program Scope rollups (for Home Page)

  3.2. What percentage of indicators?
  4. Which indicators are ABOVE the 15% variance range?
  4.1. How many indicators?
  4.2. What percentage of indicators?
  5. Which indicators are BELOW the 15% variance range?
  5.1. How many indicators?
  5.2. What percentage of indicators?
"""

import unittest
import datetime
from indicators.models import Indicator, PeriodicTarget
from indicators.queries import ProgramWithMetrics
from factories import (
    workflow_models as w_factories,
    indicators_models as i_factories
    )
from django import test

class TestProgramReportingingCounts (test.TransactionTestCase):
    def setUp(self):
        self.program = w_factories.ProgramFactory(
            reporting_period_start=datetime.date.today()-datetime.timedelta(days=365),
            reporting_period_end=datetime.date.today()-datetime.timedelta(days=1)
        )
        self.indicators = []
        self.data = []
        self.targets = []
        self.indicators.extend(self.get_on_target_indicators())
        self.indicators.extend(self.get_undertarget_indicators())
        self.indicators.extend(self.get_overtarget_indicators())
        self.indicators.extend(self.get_nonreporting_indicators())
        with self.assertNumQueries(3):
            self.reporting_program = ProgramWithMetrics.home_page.with_annotations('scope').get(pk=self.program.id)

    def tearDown(self):
        for datum in self.data:
            datum.delete()
        for target in self.targets:
            target.delete()
        for indicator in self.indicators:
            indicator.delete()
        self.program.delete()

    def get_base_indicator(self):
        return i_factories.IndicatorFactory(
            program=self.program
        )

    def get_base_data(self, indicator, target=None):
        data = i_factories.CollectedDataFactory(
            indicator=indicator,
            periodic_target=target,
            date_collected=self.program.reporting_period_start + datetime.timedelta(days=10)
        )
        return data

    def get_on_target_indicators(self):
        # lop indicator on target to lop target value
        lop_indicator = self.get_base_indicator()
        lop_indicator.target_frequency = Indicator.LOP
        lop_indicator.lop_target = 10000
        lop_indicator.is_cumulative = False
        lop_indicator.unit_of_measure_type = Indicator.NUMBER
        lop_indicator.save()
        lop_data = self.get_base_data(lop_indicator)
        lop_data.achieved = 10000
        lop_data.save()
        self.data.append(lop_data)
        # semi annual indicator with target and valid data
        time_indicator = self.get_base_indicator()
        time_indicator.target_frequency = Indicator.SEMI_ANNUAL
        time_indicator.is_cumulative = True
        time_indicator.unit_of_measure_type = Indicator.NUMBER
        time_indicator.save()
        start_date = self.program.reporting_period_start
        mid_date = datetime.date(
            start_date.year + 1 if start_date.month > 6 else start_date.year,
            start_date.month - 6 if start_date.month > 6 else start_date.month + 6,
            start_date.day)
        time_target_1 = i_factories.PeriodicTargetFactory(
            indicator=time_indicator,
            target=400,
            start_date=start_date,
            end_date=mid_date - datetime.timedelta(days=1)
        )
        time_target_2 = i_factories.PeriodicTargetFactory(
            indicator=time_indicator,
            target=600,
            start_date=mid_date,
            end_date=self.program.reporting_period_end
        )
        self.targets.extend([time_target_1, time_target_2])
        data_1 = i_factories.CollectedDataFactory(
            indicator=time_indicator,
            periodic_target=time_target_1,
            date_collected=time_target_1.start_date + datetime.timedelta(days=2),
            achieved=200
        )
        data_2 = i_factories.CollectedDataFactory(
            indicator=time_indicator,
            periodic_target=time_target_2,
            date_collected=time_target_2.start_date + datetime.timedelta(days=2),
            achieved=600
        )
        self.data.extend([data_1, data_2])
        return [lop_indicator, time_indicator]

    def get_undertarget_indicators(self):
        # event indicator (percent) with less than 85% of the target % hit
        event_indicator = self.get_base_indicator()
        event_indicator.target_frequency = Indicator.EVENT
        event_indicator.is_cumulative = False
        event_indicator.unit_of_measure_type = Indicator.PERCENTAGE
        event_indicator.save()
        event_target = i_factories.PeriodicTargetFactory(
            indicator=event_indicator,
            target=75,
            customsort=0,
            period="event 1"
        )
        self.targets.append(event_target)
        event_data = self.get_base_data(indicator=event_indicator, target=event_target)
        event_data.achieved = 60
        event_data.save()
        self.data.append(event_data)
        return [event_indicator]

    def get_overtarget_indicators(self):
        # lop indicator with 120/100 data
        lop_indicator = self.get_base_indicator()
        lop_indicator.target_frequency = Indicator.LOP
        lop_indicator.is_cumulative = False
        lop_indicator.lop_target = 100
        lop_indicator.save()
        lop_data = self.get_base_data(lop_indicator)
        lop_data.achieved = 120
        lop_data.save()
        self.data.append(lop_data)
        # negative direction of change so under data should show as over target
        neg_indicator = self.get_base_indicator()
        neg_indicator.target_frequency = Indicator.LOP
        neg_indicator.direction_of_change = Indicator.DIRECTION_OF_CHANGE_NEGATIVE
        neg_indicator.lop_target = 800
        neg_indicator.save()
        neg_data = self.get_base_data(neg_indicator)
        neg_data.achieved = 600
        neg_data.save()
        self.data.append(neg_data)
        # mid end indicator _cumulative_ should check against end target only
        midend_indicator = self.get_base_indicator()
        midend_indicator.target_frequency = Indicator.MID_END
        midend_indicator.is_cumulative = True
        midend_indicator.save()
        mid_target = i_factories.PeriodicTargetFactory(
            indicator=midend_indicator,
            period=PeriodicTarget.MIDLINE,
            customsort=0,
            target=500
        )
        end_target = i_factories.PeriodicTargetFactory(
            indicator=midend_indicator,
            period=PeriodicTarget.ENDLINE,
            customsort=1,
            target=800
        )
        self.targets.extend([mid_target, end_target])
        mid_data_1 = self.get_base_data(midend_indicator, mid_target)
        mid_data_1.achieved = 200
        mid_data_1.save()
        mid_data_2 = self.get_base_data(midend_indicator, mid_target)
        mid_data_2.achieved = 200
        mid_data_2.save()
        mid_data_3 = self.get_base_data(midend_indicator, end_target)
        mid_data_3.achieved = 250
        mid_data_3.save()
        mid_data_4 = self.get_base_data(midend_indicator, end_target)
        mid_data_4.achieved = 250
        mid_data_4.save()
        self.data.extend([mid_data_1, mid_data_2, mid_data_3, mid_data_4])
        return [lop_indicator, neg_indicator, midend_indicator]

    def get_nonreporting_indicators(self):
        event_indicator = self.get_base_indicator()
        event_indicator.target_frequency = Indicator.EVENT
        event_indicator.save()
        event_target = i_factories.PeriodicTargetFactory(
            indicator=event_indicator,
            target=400,
            customsort=0,
            period="event 1"
        )
        self.targets.append(event_target)
        return [event_indicator]


    def test_percentages(self):
        with self.assertNumQueries(1):
            percentages = self.reporting_program.scope_counts
            self.assertEqual(
                percentages['low'], 1,
                "expected 1 undertarget for 1/7, got {0}".format(percentages['low'])
            )
            self.assertEqual(
                percentages['on_scope'], 2,
                "expected 2 ontarget for 2/7, got {0}".format(percentages['on_scope'])
            )
            self.assertEqual(
                percentages['high'], 3,
                "expected 3 overtarget for 3/7, got {0}".format(percentages['high'])
            )

    def test_queries(self):
        expected = {
            'low': 1,
            'on_scope': 2,
            'high': 3,
            'nonreporting_count': 1,
            'indicator_count': 7
        }
        with self.assertNumQueries(4):
            program = ProgramWithMetrics.home_page.with_annotations(
                'scope', 'targets', 'results', 'evidence'
            ).get(pk=self.program.id)
            scope_counts = program.scope_counts
            metrics = program.metrics
        for key, expected_value in expected.items():
            with self.assertNumQueries(0):
                self.assertEqual(
                    expected_value, scope_counts[key],
                    "expected {0} to be {1}, but got {2} (counts: {3} and metrics {4})".format(
                        key, expected_value, scope_counts[key], scope_counts, metrics
                    )
                )
        self.assertIn('results_count', metrics.keys())


class TestTargetsActualsOverUnderCorrect(test.TestCase):
    def setUp(self):
        self.program = w_factories.ProgramFactory(
            reporting_period_start=datetime.date(2016, 10, 1),
            reporting_period_end=datetime.date(2017, 9, 30)
        )
        self.indicator = i_factories.IndicatorFactory(
            program=self.program
        )
        self.targets = []
        self.data = []

    def tearDown(self):
        for datum in self.data:
            datum.delete()
        for target in self.targets:
            target.delete()
        self.indicator.delete()
        self.program.delete()

    def test_midend_target_sums_midend_with_both_data(self):
        self.indicator.target_frequency = Indicator.MID_END
        self.indicator.save()
        mid_target = i_factories.PeriodicTargetFactory(
            indicator=self.indicator,
            target=500,
            period=PeriodicTarget.MIDLINE,
            customsort=0
        )
        end_target = i_factories.PeriodicTargetFactory(
            indicator=self.indicator,
            target=800,
            period=PeriodicTarget.ENDLINE,
            customsort=1
        )
        self.targets.extend([mid_target, end_target])
        mid_data = i_factories.CollectedDataFactory(
            indicator=self.indicator,
            periodic_target=mid_target,
            achieved=350,
            date_collected=self.program.reporting_period_start + datetime.timedelta(days=1)
        )
        end_data = i_factories.CollectedDataFactory(
            indicator=self.indicator,
            periodic_target=end_target,
            achieved=950,
            date_collected=self.program.reporting_period_start + datetime.timedelta(days=10)
        )
        self.data.extend([mid_data, end_data])
        program = ProgramWithMetrics.home_page.with_annotations('scope').get(pk=self.program.id)
        self.assertEqual(
            program.scope_counts['on_scope'], 1,
            "should show overunder as 0 (in range), got {0}".format(program.scope_counts)
        )
        self.indicator.is_cumulative = True
        self.indicator.save()
        program = ProgramWithMetrics.home_page.with_annotations('scope').get(pk=self.program.id)
        # both have data, set to cumulative, so should show latest (endline) target:
        self.assertEqual(
            program.scope_counts['high'], 1,
            "should show overunder as 1 (over range), got {0}".format(program.scope_counts)
        )
        self.indicator.direction_of_change = Indicator.DIRECTION_OF_CHANGE_NEGATIVE
        self.indicator.save()
        program = ProgramWithMetrics.home_page.with_annotations('scope').get(pk=self.program.id)
        self.assertEqual(
            program.scope_counts['low'], 1,
            "should show overunder as -1 (under range - negative DOC), got {0}".format(program.scope_counts)
        )

    def test_midend_doesnt_sum_if_no_endline_data(self):
        self.indicator.target_frequency = Indicator.MID_END
        self.indicator.save()
        mid_target = i_factories.PeriodicTargetFactory(
            indicator=self.indicator,
            target=500,
            period=PeriodicTarget.MIDLINE,
            customsort=0
        )
        end_target = i_factories.PeriodicTargetFactory(
            indicator=self.indicator,
            target=800,
            period=PeriodicTarget.ENDLINE,
            customsort=1
        )
        self.targets.extend([mid_target, end_target])
        mid_data = i_factories.CollectedDataFactory(
            indicator=self.indicator,
            periodic_target=mid_target,
            achieved=350,
            date_collected=self.program.reporting_period_start + datetime.timedelta(days=1)
        )
        self.data.append(mid_data)
        program = ProgramWithMetrics.home_page.with_annotations('scope').get(pk=self.program.id)
        self.assertEqual(
            program.scope_counts['low'], 1,
            "should show under (350/500), got {0}".format(program.scope_counts)
        )
        self.indicator.direction_of_change = Indicator.DIRECTION_OF_CHANGE_NEGATIVE
        self.indicator.save()
        program = ProgramWithMetrics.home_page.with_annotations('scope').get(pk=self.program.id)
        self.assertEqual(
            program.scope_counts['high'], 1,
            "should show over (350/500), got {0}".format(program.scope_counts)
        )

