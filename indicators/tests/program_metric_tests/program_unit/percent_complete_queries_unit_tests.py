""" Program Percent Complete tests for the Program and Home pages

business rules:
- if reporting period start or end is null reports -1
- reports percent of program complete (0 if program has not yet started, 100 if it is finished)
"""

import datetime
from factories import workflow_models as factory
from indicators.queries import ProgramWithMetrics
from django import test

class TestProgramPercentComplete(test.TestCase):
    def get_program(self, start_date, end_date):
        program = factory.ProgramFactory(
            reporting_period_start=start_date,
            reporting_period_end=end_date
        )
        return ProgramWithMetrics.home_page.get(pk=program.pk)

    def test_no_start_or_end_date(self):
        """no start or end date should report percent_complete=-1"""
        program = self.get_program(None, None)
        self.assertEqual(program.percent_complete, -1)

    def test_no_start_date(self):
        """no start date should report percent_complete=-1"""
        program = self.get_program(None, datetime.date(2015, 1, 1))
        self.assertEqual(program.percent_complete, -1)

    def test_no_end_date(self):
        """no end date should report percent_complete=-1"""
        program = self.get_program(datetime.date(2015, 1, 1), None)
        self.assertEqual(program.percent_complete, -1)

    def test_program_not_started(self):
        """program with start date in future should report percent_complete = 0"""
        program = self.get_program(
            datetime.date(2030, 1, 1),
            datetime.date(2040, 1, 1)
        )
        self.assertEqual(program.percent_complete, 0)

    def test_program_completed(self):
        """ program with start and end date in past should report percent_complete = 100"""
        program = self.get_program(
            datetime.date(2010, 1, 1),
            datetime.date(2011, 1, 1)
        )
        self.assertEqual(program.percent_complete, 100)

    def test_program_halfway_done(self):
        """ program with start date halfway done should report percent_complete = 50"""
        start_date = datetime.date.today() - datetime.timedelta(days=100)
        end_date = datetime.date.today() + datetime.timedelta(days=100)
        program = self.get_program(
            start_date, end_date
        )
        self.assertEqual(program.percent_complete, 50)

    def test_program_one_third_done(self):
        """ program with start date halfway done should report percent_complete = 50"""
        start_date = datetime.date.today() - datetime.timedelta(days=30)
        end_date = datetime.date.today() + datetime.timedelta(days=60)
        program = self.get_program(
            start_date, end_date
        )
        self.assertEqual(program.percent_complete, 33)
        