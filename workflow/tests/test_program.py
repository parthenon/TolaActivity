# -*- coding: utf-8 -*-
import datetime
from unittest import skip

from django.test import TestCase

from django.utils import translation
from indicators.models import Indicator
from tola.test.base_classes import TestBase
from factories.workflow_models import SiteProfileFactory, ProgramFactory
from factories.indicators_models import IndicatorFactory, CollectedDataFactory
from workflow.models import SiteProfile


class TestProgramMethods(TestBase, TestCase):

    def test_get_sites(self):
        """It should return all and only the sites for a given program"""

        expected = SiteProfileFactory()
        expected2 = SiteProfileFactory()
        CollectedDataFactory(
            indicator=self.indicator, sites=[expected, expected2])
        sites = self.program.get_sites()

        IndicatorFactory.create_batch(3)
        CollectedDataFactory.create_batch(3)
        SiteProfileFactory.create_batch(3)

        self.assertEqual(len(sites), 2)
        self.assertEqual(len(SiteProfile.objects.all()), 5)


class TestProgramList(TestBase, TestCase):

    @skip('Test that the correct programs from a single country get loaded.')
    def test_single_country_load(self):
        pass

    @skip('Test the on-track program calculation.')
    def test_calc_program_on_track(self):
        pass

    @skip('Test that the percent of indicators with evidence metric')
    def test_calc_indicators_with_evidence(self):
        pass

class TestProgramGeneratePeriods(TestCase):
    def scenario_asserts(self, scenario):
        program = ProgramFactory(
            reporting_period_start=scenario['start'],
            reporting_period_end=scenario['end']
        )
        periods = [x for x in program.get_periods_for_frequency(scenario['frequency'])]
        self.assertEqual(len(periods), len(scenario['expected_names']))
        for x, name in enumerate(scenario['expected_names']):
            if name:
                self.assertEqual(periods[x]['name'], name)
        for x, start in enumerate(scenario['expected_starts']):
            if start:
                self.assertEqual(periods[x]['start'], start)
        for x, end in enumerate(scenario['expected_ends']):
            if end:
                self.assertEqual(periods[x]['end'], end)

    def test_one_year_annual_program_english(self):
        scenario = {
            'start': datetime.date(2015, 1, 1),
            'end': datetime.date(2015, 12, 31),
            'frequency': Indicator.ANNUAL,
            'expected_names': ['Year 1'],
            'expected_starts': [datetime.date(2015, 1, 1)],
            'expected_ends': [datetime.date(2015, 12, 31)]
        }
        self.scenario_asserts(scenario)

    def test_four_year_annual_program_english(self):
        scenario = {
            'start': datetime.date(2014, 1, 1),
            'end': datetime.date(2017, 12, 31),
            'frequency': Indicator.ANNUAL,
            'expected_names': ['Year 1', None, None, 'Year 4'],
            'expected_starts': [datetime.date(2014, 1, 1), None, datetime.date(2016, 1, 1), None],
            'expected_ends': [None, datetime.date(2015, 12, 31), None, None]
        }
        self.scenario_asserts(scenario)

    def test_two_year_tri_annual_program_english(self):
        scenario = {
            'start': datetime.date(2014, 6, 1),
            'end': datetime.date(2016, 5, 31),
            'frequency': Indicator.TRI_ANNUAL,
            'expected_names': ['Tri-annual period 1', None, None, 'Tri-annual period 4', None, None],
            'expected_starts': [None, None, datetime.date(2015, 2, 1), None, datetime.date(2015, 10, 1), None],
            'expected_ends': [None, None, None, datetime.date(2015, 9, 30), None, None]
        }
        self.scenario_asserts(scenario)

    def test_fifteen_month_monthly_program_english(self):
        scenario = {
            'start': datetime.date(2016, 8, 1),
            'end': datetime.date(2017, 10, 30),
            'frequency': Indicator.MONTHLY,
            'expected_names': ['August 2016', None, None, None, None, 'January 2017'] + [None] * 9,
            'expected_starts': [None, None, datetime.date(2016, 10, 1)],
            'expected_ends': [None, None, None, None, datetime.date(2016, 12, 31)]
        }
        self.scenario_asserts(scenario)

    def test_one_year_annual_program_spanish(self):
        scenario = {
            'start': datetime.date(2015, 1, 1),
            'end': datetime.date(2015, 12, 31),
            'frequency': Indicator.ANNUAL,
            'expected_names': ['A\xc3\xb1o 1'],
            'expected_starts': [datetime.date(2015, 1, 1)],
            'expected_ends': [datetime.date(2015, 12, 31)]
        }
        en = translation.get_language()
        translation.activate('es')
        self.scenario_asserts(scenario)
        translation.activate(en)

    def test_three_month_monthly_program_french(self):
        scenario = {
            'start': datetime.date(2018, 3, 1),
            'end': datetime.date(2018, 6, 30),
            'frequency': Indicator.MONTHLY,
            'expected_names': ['mars 2018', None, None, 'juin 2018'],
            'expected_starts': [],
            'expected_ends': []
        }
        en = translation.get_language()
        translation.activate('fr')
        self.scenario_asserts(scenario)
        translation.activate(en)