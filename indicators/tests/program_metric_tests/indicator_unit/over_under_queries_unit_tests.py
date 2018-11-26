""" Scope over_under reporting for the Program Page indicators list

over_under business rules:
    - 1 = more than 15% over (under in case of negative DOC)
    - 0 = within 15% of target
    - -1 = more than 15% under (over in case of negative DOC)
    - None = nonreporting (coincides with reporting=False)"""


import datetime
from indicators.models import Indicator, PeriodicTarget
from indicators.queries import MetricsIndicator
from factories import (
    workflow_models as w_factories,
    indicators_models as i_factories
    )
from django import test

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
        indicator = MetricsIndicator.objects.with_annotations('scope').get(pk=self.indicator.id)
        # both have data, defaults to non_cumulative, so should show sum of both targets:
        self.assertEqual(
            indicator.lop_target_sum, 1300,
            "should sum both targets 500 and 800 to get 1300, got {0}".format(indicator.lop_target_sum)
        )
        # both have data and targets, defaults to non_cumulative, should show sum of both data:
        self.assertEqual(
            indicator.lop_actual_sum, 1300,
            "should sum both data 350 and 950 to get 1300, got {0}".format(indicator.lop_actual_sum)
        )
        self.assertEqual(
            indicator.over_under, 0,
            "should show overunder as 0 (in range), got {0}".format(indicator.over_under)
        )
        self.indicator.is_cumulative = True
        self.indicator.save()
        indicator = MetricsIndicator.objects.with_annotations('scope').get(pk=self.indicator.id)
        # both have data, set to cumulative, so should show latest (endline) target:
        self.assertEqual(
            indicator.lop_target_sum, 800,
            "should show latest target (800), got {0}".format(indicator.lop_target_sum)
        )
        # both have data and targets, defaults to non_cumulative, should show sum of both data:
        self.assertEqual(
            indicator.lop_actual_sum, 1300,
            "should show all data (1300), got {0}".format(indicator.lop_actual_sum)
        )
        self.assertEqual(
            indicator.over_under, 1,
            "should show overunder as 1 (over range), got {0}".format(indicator.over_under)
        )
        self.indicator.direction_of_change = Indicator.DIRECTION_OF_CHANGE_NEGATIVE
        self.indicator.save()
        indicator = MetricsIndicator.objects.with_annotations('scope').get(pk=self.indicator.id)
        self.assertEqual(
            indicator.over_under, -1,
            "should show overunder as -1 (under range - negative DOC), got {0}".format(indicator.over_under)
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
        indicator = MetricsIndicator.objects.with_annotations('scope').get(pk=self.indicator.id)
        # both have data, defaults to non_cumulative, so should show sum of both targets:
        self.assertEqual(
            indicator.lop_target_sum, 500,
            "should not sum targets (no data for endline) expecting 500, got {0}".format(indicator.lop_target_sum)
        )
        self.assertEqual(
            indicator.lop_actual_sum, 350,
            "should show only data, 350 got {0}".format(indicator.lop_actual_sum)
        )
        self.assertEqual(
            indicator.over_under, -1,
            "should show under (350/500), got {0}".format(indicator.over_under)
        )
        self.indicator.direction_of_change = Indicator.DIRECTION_OF_CHANGE_NEGATIVE
        self.indicator.save()
        indicator = MetricsIndicator.objects.with_annotations('scope').get(pk=self.indicator.id)
        self.assertEqual(
            indicator.over_under, 1,
            "should show over (350/500), got {0}".format(indicator.over_under)
        )
        self.indicator.is_cumulative = True
        self.indicator.save()
        indicator = MetricsIndicator.objects.with_annotations('scope').get(pk=self.indicator.id)
        self.assertEqual(
            indicator.lop_target_sum, 500,
            "should not take endline target (no data`) expecting 500, got {0}".format(indicator.lop_target_sum)
        )


    def test_event_sums_all_targets_using_customsort(self):
        self.indicator.target_frequency = Indicator.EVENT
        self.indicator.save()
        target_1 = i_factories.PeriodicTargetFactory(
            indicator=self.indicator,
            target=500,
            period="event 1",
            customsort=0
        )
        target_2 = i_factories.PeriodicTargetFactory(
            indicator=self.indicator,
            target=800,
            period="event 2",
            customsort=1
        )
        self.targets.extend([target_1, target_2])
        data_1 = i_factories.CollectedDataFactory(
            indicator=self.indicator,
            periodic_target=target_1,
            achieved=350,
            date_collected=self.program.reporting_period_start + datetime.timedelta(days=1)
        )
        self.data.append(data_1)
        indicator = MetricsIndicator.objects.with_annotations('scope').get(pk=self.indicator.id)
        # both have data, defaults to non_cumulative, so should show sum of both targets:
        self.assertEqual(
            indicator.lop_target_sum, 500,
            "should not sum targets (no data for second target) expecting 500, got {0}".format(
                indicator.lop_target_sum)
        )
        self.assertEqual(
            indicator.lop_actual_sum, 350,
            "should show only data, 350 got {0}".format(indicator.lop_actual_sum)
        )
        self.assertEqual(
            indicator.over_under, -1,
            "should show under (350/500), got {0}".format(indicator.over_under)
        )
        data_2 = i_factories.CollectedDataFactory(
            indicator=self.indicator,
            periodic_target=target_2,
            achieved=950,
            date_collected=self.program.reporting_period_start + datetime.timedelta(days=20)
        )
        self.data.append(data_2)
        indicator = MetricsIndicator.objects.with_annotations('scope').get(pk=self.indicator.id)
        self.assertEqual(
            indicator.lop_target_sum, 1300,
            "expected sum of targets (both have data) 1300, got {0}".format(indicator.lop_target_sum)
        )
        self.assertEqual(
            indicator.lop_actual_sum, 1300,
            "expecting sum of data 1300, got {0}".format(indicator.lop_actual_sum)
        )
        self.assertEqual(
            indicator.over_under, 0,
            "should show on target (over under 0, 1300/1300), got {0}".format(indicator.over_under)
        )
        self.indicator.is_cumulative = True
        self.indicator.save()
        indicator = MetricsIndicator.objects.with_annotations('scope').get(pk=self.indicator.id)
        self.assertEqual(
            indicator.lop_target_sum, 800,
            "expected most recent target for non-cumulative indicator 800, got {0}".format(indicator.lop_target_sum)
        )
