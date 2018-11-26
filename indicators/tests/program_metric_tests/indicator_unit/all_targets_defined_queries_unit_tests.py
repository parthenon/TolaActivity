""" All Targets Defined Unit Tests for annotated indicators in Program Page indicator list

Requirements for "True":
    - Indicator has target frequency
    - if LOP, indicator has lop_target
    - if MID_END, indicator has both MID and END periodic_target and also target values for both
    - if EVENT, indicator has at least one periodic_target and all have target values
    - if time aware, indicator has all periods from reporting_period_start to reporting_period_end with targets
"""

import datetime
from factories import (
    indicators_models as fact_i,
    workflow_models as fact_w
)
from indicators.models import (
    Indicator,
    PeriodicTarget
)
from indicators.queries import MetricsIndicator
from django import test


class TargetsDefinedTestBase(object):
    target_frequency = None
    program = None

    def get_indicator(self):
        if not self.program:
            self.program = fact_w.ProgramFactory()
        return fact_i.IndicatorFactory(
            program=self.program,
            target_frequency=self.target_frequency
            )

    def get_target(self, indicator, target=100, start_date=None, end_date=None):
        if start_date is None:
            start_date = datetime.date(2014, 1, 1)
        if end_date is None:
            end_date = datetime.date(2015, 1, 1)
        return fact_i.PeriodicTargetFactory(
            indicator=indicator,
            start_date=start_date,
            end_date=end_date,
            target=target
        )

    def get_annotated_indicator(self, indicator=None):
        if indicator is None:
            indicator = self.get_indicator()
        return MetricsIndicator.objects.with_annotations('targets').get(pk=indicator.pk) 

@test.tag('targets', 'metrics', 'fast', 'core')
class TestNoTargetFrequency(test.TestCase, TargetsDefinedTestBase):
    """if indicator has no target frequency set, it should report all_targets_defined=False"""

    def test_no_target_frequency_false(self):
        """no target frequency set => all_targets_defined=False"""
        annotated_indicator = self.get_annotated_indicator()
        self.assertFalse(annotated_indicator.all_targets_defined)

@test.tag('targets', 'metrics', 'fast', 'core')
class TestLOPIndicatorTargetsDefined(test.TestCase, TargetsDefinedTestBase):
    """if indicator is LOP frequency, it should report all_targets_defined iff lop_target is set"""
    target_frequency = Indicator.LOP

    def test_no_lop_target(self):
        """LOP indicator with no lop_target should report all_targets_defined=False"""
        annotated_indicator = self.get_annotated_indicator()
        self.assertFalse(annotated_indicator.all_targets_defined)

    def test_lop_target_set(self):
        """LOP indicator with no lop_target should report all_targets_defined=False"""
        good_indicator = self.get_indicator()
        good_indicator.lop_target = 100
        good_indicator.save()
        annotated_indicator = self.get_annotated_indicator(good_indicator)
        self.assertTrue(annotated_indicator.all_targets_defined)


class RequiresTargetsBase(TargetsDefinedTestBase):
    def test_no_targets_set(self):
        """non-LOP indicator with no targets set should report all_targets_defined=False"""
        annotated_indicator = self.get_annotated_indicator()
        self.assertFalse(annotated_indicator.all_targets_defined)

@test.tag('targets', 'metrics', 'fast', 'core')
class TestMIDENDIndicatorTargetsDefined(test.TestCase, RequiresTargetsBase):
    """if indicator is MID_END frequency, it should report all_targets_defined iff:
        - both targets exist"""
    target_frequency = Indicator.MID_END

    def get_midline_target(self, indicator):
        target = self.get_target(indicator)
        target.period = PeriodicTarget.MIDLINE
        target.customsort = 0
        target.save()
        return target

    def get_endline_target(self, indicator):
        target = self.get_target(indicator)
        target.period = PeriodicTarget.ENDLINE
        target.customsort = 1
        target.save()
        return target

    def test_no_endline_target(self):
        """MID_END indicator with no endline indicator should report all_targets_defined=False"""
        indicator = self.get_indicator()
        self.get_midline_target(indicator)
        annotated_indicator = self.get_annotated_indicator(indicator)
        self.assertFalse(annotated_indicator.all_targets_defined)

    def test_no_midline_target(self):
        """MID_END indicator with no midline indicator should report all_targets_defined=False"""
        indicator = self.get_indicator()
        self.get_endline_target(indicator)
        annotated_indicator = self.get_annotated_indicator(indicator)
        self.assertFalse(annotated_indicator.all_targets_defined)


    def test_midline_and_endline_targets(self):
        """MID_END indicator with no midline indicator should report all_targets_defined=False"""
        indicator = self.get_indicator()
        self.get_midline_target(indicator)
        self.get_endline_target(indicator)
        annotated_indicator = self.get_annotated_indicator(indicator)
        self.assertTrue(annotated_indicator.all_targets_defined)

@test.tag('targets', 'metrics', 'fast')
class TestEVENTIndicatorTargetsDefined(test.TestCase, RequiresTargetsBase):
    """if indicator is EVENT frequency, it should report all_targets_defined iff:
        - at least 1 target"""
    target_frequency = Indicator.EVENT

    def get_event_target(self, indicator):
        return self.get_target(indicator)

    def test_one_event_target(self):
        """EVENT indicator with 1 event target should report all_targets_defined=True"""
        indicator = self.get_indicator()
        self.get_event_target(indicator)
        annotated_indicator = self.get_annotated_indicator(indicator)
        self.assertTrue(annotated_indicator.all_targets_defined)

    def test_two_event_targets(self):
        """EVENT indicator with 2 event targets should report all_targets_defined=True"""
        indicator = self.get_indicator()
        self.get_event_target(indicator)
        self.get_event_target(indicator)
        annotated_indicator = self.get_annotated_indicator(indicator)
        self.assertTrue(annotated_indicator.all_targets_defined)

class TestReportingPeriodAnnotations(test.TestCase):
    """indicator metrics queries require a months annotation based on program dates"""

    def get_indicator_for_program(self, start_date, end_date):
        program = fact_w.ProgramFactory(reporting_period_start=start_date, reporting_period_end=end_date)
        indicator = fact_i.IndicatorFactory(
            program=program
        )
        return MetricsIndicator.objects.with_annotations('months').get(pk=indicator.pk)

    def test_one_year_in_the_past_program_annotation(self):
        """one year program in the past should show program_months=12"""
        annotated_indicator = self.get_indicator_for_program(
            datetime.date(2015, 1, 1),
            datetime.date(2015, 12, 31)
        )
        self.assertEqual(annotated_indicator.program_months, 12)

    def test_one_year_overlapping_present_annotation(self):
        """one year program ending in the future should show program_months=12"""
        last_month = datetime.date.today() - datetime.timedelta(days=40)
        start_date = datetime.date(last_month.year, last_month.month, 1)
        end_date = datetime.date(last_month.year+1, last_month.month, 1) - datetime.timedelta(days=1)
        annotated_indicator = self.get_indicator_for_program(
            start_date,
            end_date
        )
        self.assertEqual(annotated_indicator.program_months, 12)

    def test_35_month_in_the_past_annotation(self):
        """35 month program should show program_months=35"""
        annotated_indicator = self.get_indicator_for_program(
            datetime.date(2014, 7, 1),
            datetime.date(2017, 5, 31)
        )
        self.assertEqual(annotated_indicator.program_months, 35)

class TimeAwareTargetsBase(RequiresTargetsBase):
    def get_program(self, months):
        start_date = datetime.date(2012, 4, 1)
        end_year = 2012 + (4 + months) // 12
        end_month = (4 + months) % 12
        if end_month == 0:
            end_month = 12
            end_year -= 1
        end_date = datetime.date(end_year, end_month, 1) - datetime.timedelta(days=1)
        self.program = fact_w.ProgramFactory(
            reporting_period_start=start_date,
            reporting_period_end=end_date
        )

    def test_two_period_program_one_target_fails(self):
        """TIME_AWARE indicator with a two period program and 1 target set should show all_targets_defined=False"""
        self.get_program(months=2*self.month_count)
        indicator = self.get_indicator()
        self.get_target(indicator)
        annotated_indicator = self.get_annotated_indicator(indicator)
        self.assertFalse(annotated_indicator.all_targets_defined)

    def test_two_period_program_two_targets_passes(self):
        """TIME_AWARE indicator with a two period program and 2 targets set should show all_targets_defined=True"""
        self.get_program(months=2*self.month_count)
        indicator = self.get_indicator()
        self.get_target(indicator)
        self.get_target(indicator)
        annotated_indicator = self.get_annotated_indicator(indicator)
        self.assertTrue(annotated_indicator.all_targets_defined)

    def test_two_period_plus_program_two_targets_fails(self):
        """TIME_AWARE indicator with a 2+ period program and 2 targets set should show all_targets_defined=False"""
        self.get_program(months=(2*self.month_count)+1)
        indicator = self.get_indicator()
        self.get_target(indicator)
        self.get_target(indicator)
        annotated_indicator = self.get_annotated_indicator(indicator)
        self.assertFalse(annotated_indicator.all_targets_defined)

    def test_one_period_plus_program_two_targets_passes(self):
        """TIME_AWARE indicator with a 1+ period program and 2 targets set should show all_targets_defined=False"""
        self.get_program(months=(2*self.month_count)-1)
        indicator = self.get_indicator()
        self.get_target(indicator)
        self.get_target(indicator)
        annotated_indicator = self.get_annotated_indicator(indicator)
        self.assertTrue(annotated_indicator.all_targets_defined)

@test.tag('targets', 'metrics', 'fast')
class TestANNUALIndicatorTargetsDefined(test.TestCase, TimeAwareTargetsBase):
    """if indicator is ANNUAL frequency, it should report all_targets_defined iff:
        - target count = number of years in program"""
    target_frequency = Indicator.ANNUAL
    month_count = 12

@test.tag('targets', 'metrics', 'fast', 'core')
class TestSEMIANNUALIndicatorTargetsDefined(test.TestCase, TimeAwareTargetsBase):
    """if indicator is SEMIANNUAL frequency, it should report all_targets_defined iff:
        - target count = number of half-years in program"""
    target_frequency = Indicator.SEMI_ANNUAL
    month_count = 6

@test.tag('targets', 'metrics', 'fast')
class TestTRIANNUALIndicatorTargetsDefined(test.TestCase, TimeAwareTargetsBase):
    """if indicator is TRI-ANNUAL frequency, it should report all_targets_defined iff:
        - target count = number of tri-annual periods in program"""
    target_frequency = Indicator.TRI_ANNUAL
    month_count = 4

@test.tag('targets', 'metrics', 'fast')
class TestQUARTERLYIndicatorTargetsDefined(test.TestCase, TimeAwareTargetsBase):
    """if indicator is QUARTERLY frequency, it should report all_targets_defined iff:
        - target count = number of quarters in program"""
    target_frequency = Indicator.QUARTERLY
    month_count = 3

@test.tag('targets', 'metrics', 'fast')
class TestMONTHLYIndicatorTargetsDefined(test.TestCase, TimeAwareTargetsBase):
    """if indicator is MONTHLY frequency, it should report all_targets_defined iff:
        - target count = number of months in program"""
    target_frequency = Indicator.MONTHLY
    month_count = 1

    def test_thirteen_month_thirteen_targets_passes(self):
        """thirteen months, thirteen targets - should show all_targets_defined=True"""
        program = self.get_program(13)
        indicator = self.get_indicator()
        for _ in range(13):
            self.get_target(indicator)
        annotated_indicator = self.get_annotated_indicator(indicator)
        self.assertTrue(annotated_indicator.all_targets_defined)

    def test_thirteen_month_twelve_targets_fails(self):
        """thirteen months, twelve targets - should show all_targets_defined=False"""
        program = self.get_program(13)
        indicator = self.get_indicator()
        for _ in range(12):
            self.get_target(indicator)
        annotated_indicator = self.get_annotated_indicator(indicator)
        self.assertFalse(annotated_indicator.all_targets_defined)