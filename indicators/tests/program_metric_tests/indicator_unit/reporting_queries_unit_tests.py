"""Indicator reporting status tests for program page

Business rules:
    reporting only if:
        - LOP indicator in closed program with lop_target
        - Midline/Endline/Event with set target and 1+ data
        - Time aware indicator with completed target period and set target and 1+ data"""

import unittest
import datetime
from factories import (
    workflow_models as w_factories,
    indicators_models as i_factories
    )
from indicators.models import Indicator, PeriodicTarget
from indicators.queries import MetricsIndicator
from django import test


class ReportingIndicatorBase(test.TestCase):
    TIME_AWARE_FREQUENCIES = [
        Indicator.ANNUAL,
        Indicator.SEMI_ANNUAL,
        Indicator.TRI_ANNUAL,
        Indicator.QUARTERLY,
        Indicator.MONTHLY
    ]

    DATE_FUNCS = {
        Indicator.ANNUAL: lambda x: datetime.date(x.year+1, x.month, x.day),
        Indicator.SEMI_ANNUAL: lambda x: datetime.date(
            x.year + 1 if x.month > 6 else x.year,
            x.month - 6 if x.month > 6 else x.month + 6,
            1
        ) - datetime.timedelta(days=1),
        Indicator.TRI_ANNUAL: lambda x: datetime.date(
            x.year + 1 if x.month > 8 else x.year,
            x.month - 8 if x.month > 8 else x.month + 4,
            1
        ) - datetime.timedelta(days=1),
        Indicator.QUARTERLY: lambda x: datetime.date(
            x.year + 1 if x.month > 9 else x.year,
            x.month - 9 if x.month > 9 else x.month + 3,
            1
        ) - datetime.timedelta(days=1),
        Indicator.MONTHLY: lambda x: datetime.date(
            x.year + 1 if x.month == 12 else x.year,
            1 if x.month == 12 else x.month + 1,
            1
        ) - datetime.timedelta(days=1)
    }

    indicator = None
    program = None
    targets = []
    data = []

    def load_base_indicator(self):
        """loads a bare indicator in this program"""
        self.indicator = i_factories.IndicatorFactory()
        if self.program is not None:
            self.indicator.program = self.program
            self.indicator.save()

    def load_data(self, indicator=None, achieved=None, date=None, target=None):
        """adds data to the indicator"""
        indicator = self.indicator if indicator is None else indicator
        achieved = 800 if achieved is None else achieved
        date = self.program.reporting_period_start + datetime.timedelta(days=5) if date is None else date
        datum = i_factories.CollectedDataFactory(
            indicator=indicator,
            achieved=achieved,
            date_collected=date,
            periodic_target=target
        )
        self.data.append(datum)

    def load_target(self, indicator, target, period=None, start_date=None):
        end_date = start_date
        period = "Period {0}".format(len(self.targets)) if period is None else period
        if start_date is not None:
            end_date = self.DATE_FUNCS[indicator.target_frequency](start_date)
        target = i_factories.PeriodicTargetFactory(
                indicator=indicator,
                period=period,
                target=target,
                start_date=start_date,
                end_date=end_date
            )
        self.targets.append(target)
        return target
        

    def get_time_aware_dates(self, target_frequency):
        start_date = self.program.reporting_period_start
        date_func = self.DATE_FUNCS[target_frequency]
        end_date = date_func(start_date)
        dates = [start_date,]
        while end_date < self.program.reporting_period_end:
            start_date = end_date + datetime.timedelta(days=1)
            end_date = date_func(start_date)
            dates.append(start_date)
        return dates

    def load_targets(self, indicator=None, targets=None):
        indicator = self.indicator if indicator is None else indicator
        target_frequency = indicator.target_frequency
        if target_frequency == Indicator.MID_END:
            targets = [500, 800] if targets is None else targets
            self.load_target(indicator, targets[0], period=PeriodicTarget.MIDLINE)
            self.load_target(indicator, targets[1], period=PeriodicTarget.ENDLINE)
        elif target_frequency == Indicator.EVENT:
            targets = [1200,] if targets is None else targets
            for target in targets:
                self.load_target(indicator, target)
        elif target_frequency in self.TIME_AWARE_FREQUENCIES:
            dates = self.get_time_aware_dates(target_frequency)
            targets = [400]*len(dates) if targets is None else targets
            for target, start_date in zip(targets, dates):
                self.load_target(indicator, target, start_date=start_date)

    def get_closed_program(self):
        self.program = w_factories.ProgramFactory(
            reporting_period_start=datetime.date(2016, 1, 1),
            reporting_period_end=datetime.date(2016, 12, 31)
        )

    def get_annotated_indicator(self, indicator=None):
        if indicator is None:
            indicator = self.indicator
        return MetricsIndicator.objects.with_annotations('reporting').get(pk=indicator.pk) 

class TestSingleNonReportingIndicator(ReportingIndicatorBase):
    """test conditions under which indicator should report reporting as false"""
    def one_incomplete_assert(self, program, scenario):
        nonreporting = program.scope_counts['nonreporting']
        reporting = program.scope_counts['reporting_count']
        self.assertEqual(
            nonreporting, 1,
            "For {0}, program should have 1 incomplete indicator, got {1}".format(
                scenario, nonreporting
            )
        )
        self.assertEqual(
            reporting, 0,
            "For {0}, program should have 0 complete indicators, got {1}".format(
                scenario, reporting
            )
        )

    def test_lop_indicator_in_open_program(self):
        # get open (reporting period not over) program:
        # set dates from today so test doesn't become obsolete at some arbitrary future date:
        start_date = datetime.date.today() - datetime.timedelta(days=10)
        end_date = datetime.date.today() + datetime.timedelta(days=100)
        self.program = w_factories.ProgramFactory(
            reporting_period_start=start_date,
            reporting_period_end=end_date
        )
        self.load_base_indicator()
        self.indicator.target_frequency = Indicator.LOP
        # lop_target and data should be set to ensure it's only program openness restricting from "complete"
        self.indicator.lop_target = 1000
        self.indicator.save()
        self.load_data()
        indicator = self.get_annotated_indicator()
        self.assertFalse(indicator.reporting)

    def test_lop_indicator_no_lop_target(self):
        #program is complete:
        self.get_closed_program()
        # add indicator with data:
        self.load_base_indicator()
        self.indicator.target_frequency = Indicator.LOP
        self.indicator.save()
        self.load_data()
        indicator = self.get_annotated_indicator()
        self.assertFalse(indicator.reporting)

    def test_lop_indicator_no_data(self):
        self.get_closed_program()
        self.load_base_indicator()
        self.indicator.target_frequency = Indicator.LOP
        self.indicator.lop_target = 1400
        self.indicator.save()
        indicator = self.get_annotated_indicator()
        self.assertFalse(indicator.reporting)

    def test_midend_indicator_no_targets(self):
        self.get_closed_program()
        self.load_base_indicator()
        self.indicator.target_frequency = Indicator.MID_END
        self.indicator.save()
        # ensure indicator has data for midline indicator:
        self.load_data()
        indicator = self.get_annotated_indicator()
        self.assertFalse(indicator.reporting)

    def test_midend_indicator_no_data(self):
        self.get_closed_program()
        self.load_base_indicator()
        self.indicator.target_frequency = Indicator.MID_END
        self.indicator.save()
        # ensure indicator has targets for midline indicator:
        self.load_targets()
        indicator = self.get_annotated_indicator()
        self.assertFalse(indicator.reporting)

    def test_event_indicator_no_target(self):
        self.get_closed_program()
        self.load_base_indicator()
        self.indicator.target_frequency = Indicator.EVENT
        self.indicator.save()
        self.load_data()
        indicator = self.get_annotated_indicator()
        self.assertFalse(indicator.reporting)

    def test_event_indicator_no_data(self):
        self.get_closed_program()
        self.load_base_indicator()
        self.indicator.target_frequency = Indicator.EVENT
        self.indicator.save()
        self.load_targets()
        indicator = self.get_annotated_indicator()
        self.assertFalse(indicator.reporting)

    def test_time_aware_indicators_no_targets(self):
        self.get_closed_program()
        for frequency in self.TIME_AWARE_FREQUENCIES:
            self.load_base_indicator()
            self.indicator.target_frequency = frequency
            self.indicator.save()
            self.load_data()
            indicator = self.get_annotated_indicator()
            self.assertFalse(indicator.reporting)
            for datum in self.data:
                datum.delete()
            self.data = []
            self.indicator.delete()
            self.indicator = None

    def test_time_aware_indicators_no_data(self):
        self.targets = []
        self.get_closed_program()
        for frequency in self.TIME_AWARE_FREQUENCIES:
            self.load_base_indicator()
            self.indicator.target_frequency = frequency
            self.indicator.save()
            self.load_targets()
            indicator = self.get_annotated_indicator()
            self.assertFalse(indicator.reporting)
            for target in self.targets:
                target.delete()
            self.targets = []
            self.indicator.delete()
            self.indicator = None

    def test_time_aware_indicators_no_completed_periods(self):
        # if program started yesterday then no targets will be finished by today:
        today = datetime.date.today() + datetime.timedelta(days=1)
        self.program = w_factories.ProgramFactory(
            reporting_period_start=datetime.date(today.year, today.month, 1),
            reporting_period_end=datetime.date(today.year+1, today.month, 1) - datetime.timedelta(days=1)
        )
        for frequency in self.TIME_AWARE_FREQUENCIES:
            self.load_base_indicator()
            self.indicator.target_frequency = frequency
            self.indicator.save()
            self.load_targets()
            self.load_data(date=datetime.date.today()-datetime.timedelta(days=1))
            indicator = self.get_annotated_indicator()
            self.assertFalse(indicator.reporting)
            for target in self.targets:
                target.delete()
            self.targets = []
            self.indicator.delete()
            self.indicator = None

class TestSingleReportingIndicator(ReportingIndicatorBase):
    def test_lop_indicator_closed_program_target_set_with_data(self):
        #program is complete:
        self.get_closed_program()
        # add indicator with data:
        self.load_base_indicator()
        self.indicator.target_frequency = Indicator.LOP
        self.indicator.lop_target = 1400
        self.indicator.save()
        self.load_data()
        indicator = self.get_annotated_indicator()
        self.assertTrue(indicator.reporting)

    def test_midend_indicator_midline_target_and_data(self):
        self.get_closed_program()
        self.load_base_indicator()
        self.indicator.target_frequency = Indicator.MID_END
        self.indicator.save()
        # ensure indicator has targets for midline indicator:
        target = self.load_target(self.indicator, 800, period=PeriodicTarget.MIDLINE)
        self.load_data(indicator=self.indicator, achieved=500, date=None, target=target)
        indicator = self.get_annotated_indicator()
        self.assertTrue(indicator.reporting)

    def test_midend_indicator_both_targets_and_data(self):
        self.get_closed_program()
        self.load_base_indicator()
        self.indicator.target_frequency = Indicator.MID_END
        self.indicator.save()
        # ensure indicator has targets for midline indicator:
        target1 = self.load_target(self.indicator, 800, period=PeriodicTarget.MIDLINE)
        target2 = self.load_target(self.indicator, 400, period=PeriodicTarget.ENDLINE)
        self.load_data(indicator=self.indicator, achieved=500, date=None, target=target1)
        self.load_data(indicator=self.indicator, achieved=700, date=None, target=target2)
        indicator = self.get_annotated_indicator()
        self.assertTrue(indicator.reporting)

    def test_event_indicator_with_target_and_data(self):
        self.get_closed_program()
        self.load_base_indicator()
        self.indicator.target_frequency = Indicator.EVENT
        self.indicator.save()
        # ensure indicator has targets for midline indicator:
        target = self.load_target(self.indicator, 800)
        self.load_data(indicator=self.indicator, achieved=500, date=None, target=target)
        indicator = self.get_annotated_indicator()
        self.assertTrue(indicator.reporting)

    def test_time_aware_indicators_with_completed_targets_and_data(self):
        self.get_closed_program()
        self.targets = []
        self.data = []
        for frequency in self.TIME_AWARE_FREQUENCIES:
            self.load_base_indicator()
            self.indicator.target_frequency = frequency
            self.indicator.save()
            self.load_targets()
            self.load_data()
            indicator = self.get_annotated_indicator()
            self.assertTrue(indicator.reporting)
            for target in self.targets:
                target.delete()
            for datum in self.data:
                datum.delete()
            self.data = []
            self.targets = []
            self.indicator.delete()
            self.indicator = None

class TestMixedReportingAndNonIndicators(ReportingIndicatorBase):

    def test_lop_and_midend_just_mid_reporting(self):
        self.get_closed_program()
        indicator_lop = i_factories.IndicatorFactory(
            target_frequency=Indicator.LOP,
            lop_target=1000,
            program=self.program
        )
        lop_data = i_factories.CollectedDataFactory(
            indicator=indicator_lop,
            achieved=400,
            date_collected=self.program.reporting_period_end - datetime.timedelta(days=10)
        )
        indicator_midend = i_factories.IndicatorFactory(
            target_frequency=Indicator.MID_END,
            program=self.program
        )
        mid_target = i_factories.PeriodicTargetFactory(
            indicator=indicator_midend,
            period=PeriodicTarget.MIDLINE,
            target=1000
        )
        mid_data = i_factories.CollectedDataFactory(
            indicator=indicator_midend,
            periodic_target=mid_target,
            achieved=400,
            date_collected=self.program.reporting_period_start + datetime.timedelta(days=20)
        )
        for indicator in MetricsIndicator.objects.with_annotations('reporting').all():
            self.assertTrue(indicator.reporting)

    def test_multiple_time_aware_indicators(self):
        self.get_closed_program()
        for frequency in self.TIME_AWARE_FREQUENCIES:
            indicator = i_factories.IndicatorFactory(
                target_frequency=frequency,
                program=self.program
            )
            self.load_targets(indicator=indicator)
            self.load_data(indicator=indicator)
        for indicator in MetricsIndicator.objects.with_annotations('reporting').all():
            self.assertTrue(indicator.reporting)