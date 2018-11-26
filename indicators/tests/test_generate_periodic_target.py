import datetime

from indicators.models import Indicator
from indicators.views.views_indicators import (
    generate_periodic_target_single,
    generate_periodic_targets
)
from django import test


@test.tag('targets', 'fast')
class GenerateSinglePeriodicTarget(test.TestCase):

    def setUp(self):
        self.start_date = datetime.datetime(2018, 10, 5, 18, 00)
        self.nth_target_period = 10
        self.event_name = 5

    def test_lop_generate_periodic_target_single(self):
        """Do we get back the expected result when we have an LOP?"""
        tf = Indicator.LOP
        expected = {'period': "Life of Program (LoP) only"}
        result = generate_periodic_target_single(tf, self.start_date,
                                                 self.nth_target_period,
                                                 event_name=self.event_name)
        self.assertDictEqual(expected, result)

    def test_mid_generate_periodic_target_single(self):
        """Do we get back the expected result when we have an MID_END?"""
        tf = Indicator.MID_END
        expected = [{'period': 'Midline'}, {'period': 'Endline'}]
        result = generate_periodic_target_single(tf, self.start_date,
                                                 self.nth_target_period,
                                                 event_name=self.event_name)
        self.assertEqual(expected, result)

    def test_event_generate_periodic_target_single(self):
        """Do we get back the expected result when we have an EVENT?"""
        tf = Indicator.EVENT
        expected = {'period': self.event_name}
        result = generate_periodic_target_single(tf, self.start_date,
                                                 0,
                                                 event_name=self.event_name)
        self.assertEqual(expected, result)

    def test_annual(self):
        """Do we get back the correct period name back for ANNUAL frequency"""

        tf = Indicator.ANNUAL
        expected = {'period': 'Year 11', 'end_date': '2029-10-04',
                    'start_date': '2028-10-01'}

        result = generate_periodic_target_single(tf, self.start_date,
                                                 self.nth_target_period,
                                                 event_name='')
        self.assertDictEqual(expected, result)

    def test_semi_annual(self):
        """Do we get the correct period name back for SEMI_ANNUAL frequency"""

        tf = Indicator.SEMI_ANNUAL
        expected = {'end_date': '2024-04-04',
                    'period': 'Semi-annual period 11',
                    'start_date': '2023-10-01'}

        result = generate_periodic_target_single(tf, self.start_date,
                                                 self.nth_target_period,
                                                 event_name='')
        self.assertDictEqual(expected, result)

    def test_tri_annual(self):
        """Do we get the correct period name back for TRI_ANNUAL frequency"""

        tf = Indicator.TRI_ANNUAL
        expected = {'end_date': '2022-06-04',
                    'period': 'Tri-annual period 11',
                    'start_date': '2022-02-01'}

        result = generate_periodic_target_single(tf, self.start_date,
                                                 self.nth_target_period,
                                                 event_name='')
        self.assertDictEqual(expected, result)

    def test_quarterly(self):
        """Do we get the correct period name back for QUARTERLY frequency"""

        tf = Indicator.QUARTERLY
        expected = {'end_date': '2021-07-04',
                    'period': 'Quarter 11',
                    'start_date': '2021-04-01'}

        result = generate_periodic_target_single(tf, self.start_date,
                                                 self.nth_target_period,
                                                 event_name='')
        self.assertDictEqual(expected, result)

    def test_monthly(self):
        """Do we get the correct period name back for MONTHLY frequency"""

        tf = Indicator.MONTHLY
        expected = {'end_date': '2019-09-04',
                    'period': 'August 2019',
                    'start_date': '2019-08-01'}

        result = generate_periodic_target_single(tf, self.start_date,
                                                 self.nth_target_period,
                                                 event_name='')
        self.assertDictEqual(expected, result)


@test.tag('targets', 'fast')
class GenerateMultiplePeriodicTargets(test.TestCase):
    """generate_periodic_targets tests for period name and quantity"""
    def setUp(self):
        self.start_date = datetime.datetime(2018, 10, 5, 18, 00)
        self.total_targets = 10
        self.event_name = ''

    def test_generate(self):
        """Can we bulk generate periodic targets?"""

        tf = Indicator.MONTHLY
        result = generate_periodic_targets(tf, self.start_date, self.total_targets,
                                           self.event_name)

        self.assertTrue(len(result) == 10)

    def test_lop(self):
        """Do we get back the correct response if we are doing
        Life of Project?"""

        tf = Indicator.LOP
        expected = {'period': u'Life of Program (LoP) only'}
        result = generate_periodic_targets(tf, self.start_date,
                                           self.total_targets,
                                           self.event_name)
        self.assertDictEqual(expected, result)

    def test_mid(self):
        """Do we get back the correct response if we are doing MID?"""

        tf = Indicator.MID_END
        expected = [{'period': 'Midline'}, {'period': 'Endline'}]
        result = generate_periodic_targets(tf, self.start_date,
                                           self.total_targets,
                                           self.event_name)

        self.assertEqual(expected, result)

@test.tag('targets', 'fast')
class GenerateNewPeriodicTargetsWithExisting(test.TestCase):
    """adding periodic targets when targets exist"""
    DATE_AWARE_FREQUENCIES = [
        Indicator.ANNUAL,
        Indicator.SEMI_ANNUAL,
        Indicator.TRI_ANNUAL,
        Indicator.QUARTERLY,
    ]
    start_date = datetime.datetime(2018, 10, 5)

    def test_generate_third_annual(self):
        """does the generated period name for a new target end with the right number (counting up from existing)?"""
        for tf in self.DATE_AWARE_FREQUENCIES:
            result = generate_periodic_targets(tf, self.start_date, 1, '', 2)
            self.assertEqual(result[0]['period'][-1], '3',
                             "third {0} target period name should end with 3, got {1}".format(
                                 tf, result[0]['period']))

