import unittest
import datetime
from django.test import Client, RequestFactory, TestCase, tag
from django.urls import reverse_lazy

from factories.indicators_models import IndicatorFactory, PeriodicTargetFactory
from factories.workflow_models import (
    ProgramFactory,
    TolaUserFactory,
    UserFactory
)
from indicators.models import Indicator
from indicators.views.views_reports import IPTTReportQuickstartView, IPTT_Mixin


@tag('iptt', 'fast')
class IPTTReportQuickstartViewTests(TestCase):
    """Unit tests to valid the IPTTReportQuickStartView"""

    def setUp(self):
        self.user = UserFactory(first_name="Indicator", last_name="CreateTest", username="IC")
        self.user.set_password('password')
        self.user.save()
        self.tola_user = TolaUserFactory(user=self.user)
        self.country = self.tola_user.country
        self.program = ProgramFactory(
            funding_status='Funded', reporting_period_start='2016-03-01', reporting_period_end='2020-05-01')
        self.program.country.add(self.country)
        self.program.save()
        self.indicator = IndicatorFactory(
            program=self.program, unit_of_measure_type=Indicator.NUMBER, is_cumulative=False,
            direction_of_change=Indicator.DIRECTION_OF_CHANGE_NONE, target_frequency=Indicator.ANNUAL)
        lop_indicator = IndicatorFactory(
            program=self.program, target_frequency=Indicator.LOP
        )
        self.request_factory = RequestFactory()
        self.client = Client()
        self.client.login(username="IC", password='password')

    def test_page_load_returns_200(self):
        """Do we return 200?"""

        response = self.client.get(reverse_lazy('iptt_quickstart'))
        self.assertEqual(response.status_code, 200)

    def test_page_load_does_not_redirect(self):
        """This page should not redirect"""

        response = self.client.get(reverse_lazy('iptt_quickstart'), follow=True)
        self.assertEqual(len(response.redirect_chain), 0)

    def test_page_loads_correct_template(self):
        """Do we load the right template?"""

        response = self.client.get(reverse_lazy('iptt_quickstart'), follow=True)
        self.assertTemplateUsed(response, 'indicators/iptt_quickstart.html')
        self.assertContains(response, 'Indicator Performance Tracking Table')

    def test_get_form_kwargs(self):
        """Do we get the correct form kwargs?"""

        data = {'csrfmiddlewaretoken': 'lolwut',
                'targetperiods-program': self.program.id,
                'targetperiods-formprefix': IPTTReportQuickstartView.FORM_PREFIX_TARGET,
                'targetperiods-timeframe': Indicator.LOP,
                'targetperiods-targetperiods': 1,
                'targetperiods-numrecentperiods': 1, }
        path = reverse_lazy('iptt_quickstart')
        response = self.client.post(path, data=data, follow=True)
        kwargs = response.resolver_match.kwargs
        self.assertEqual(kwargs['reporttype'], IPTTReportQuickstartView.FORM_PREFIX_TARGET)
        self.assertEqual(int(kwargs['program_id']), self.program.id)

    def test_get_context_data(self):
        """Do we get the correct context data?"""

        data = {'csrfmiddlewaretoken': 'lolwut',
                'targetperiods-program': self.program.id,
                'targetperiods-formprefix': IPTTReportQuickstartView.FORM_PREFIX_TARGET,
                'targetperiods-timeframe': Indicator.LOP,
                'targetperiods-targetperiods': 1,
                'targetperiods-numrecentperiods': 1, }
        path = reverse_lazy('iptt_quickstart')
        response = self.client.post(path, data=data, follow=True)
        context_data = response.context_data

        self.assertEqual(int(context_data['program_id']), self.program.id)
        # self.assertEqual(context['report_wide'], ?)
        # self.assertEqual(context['report_date_ranges'], ?)
        # self.assertEqual(context['indicators'], ?)
        self.assertRegex(str(context_data['program']), self.program.name)
        self.assertEqual(str(context_data['reporttype']),
                         IPTTReportQuickstartView.FORM_PREFIX_TARGET)
        self.assertEqual(str(context_data['report_end_date']),
                         self.program.reporting_period_end)
        self.assertEqual(str(context_data['report_end_date_actual']),
                         self.program.reporting_period_end)
        self.assertEqual(str(context_data['report_start_date']),
                         self.program.reporting_period_start)

    def test_post_with_valid_form(self):
        """Does POSTing to iptt_quickstart with valid form data redirect to the
        correct view (iptt_report)?"""

        data = {'csrfmiddlewaretoken': 'lolwut',
                'targetperiods-program': self.program.id,
                'targetperiods-formprefix': IPTTReportQuickstartView.FORM_PREFIX_TARGET,
                'targetperiods-timeframe': Indicator.LOP,
                'targetperiods-targetperiods': 1,
                'targetperiods-numrecentperiods': 1, }
        path = reverse_lazy('iptt_quickstart')

        response = self.client.post(path, data=data, follow=True)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertTemplateUsed(response, 'indicators/iptt_report.html')
        self.assertEqual(response.status_code, 200)

    def test_post_with_invalid_form(self):
        """Does POSTing to iptt_quickstart with crap form data leave us at
        iptt_quickstart?"""

        path = reverse_lazy('iptt_quickstart')
        response = self.client.post(path, data={'foo': 'bar'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'indicators/iptt_quickstart.html')

@tag('targets', 'iptt', 'fast')
class TargetFrequencyAPITests(TestCase):
    """Tests for the api call /api/programtargetfrequencies/?program_id=#"""
    def setUp(self):
        self.program = ProgramFactory()
        self.url = '/api/programtargetfrequencies/?program_id={pk}'.format(pk=self.program.pk)
        user = UserFactory()
        self.client = Client()
        self.client.force_login(user=user)

    def test_one_indicator_of_each_frequency(self):
        indicator = IndicatorFactory(
            program=self.program
        )
        for frequency, name in Indicator.TARGET_FREQUENCIES:
            if frequency != Indicator.EVENT:
                indicator.target_frequency = frequency
                indicator.save()
                response = self.client.get(self.url).json()
                expected = [{'frequency_name': name, 'target_frequency': frequency}]
                self.assertEqual(
                    response, expected,
                    "One {0} indicator expected {1} but got {2}".format(
                        name, expected, response)
                )

    def test_multiple_indicators(self):
        for frequency in [Indicator.LOP, Indicator.LOP, Indicator.MID_END, Indicator.SEMI_ANNUAL]:
            IndicatorFactory(program=self.program, target_frequency=frequency)
        response = self.client.get(self.url).json()
        self.assertEqual(len(response), 3)
        self.assertEqual(set([x['target_frequency'] for x in response]),
                             set([Indicator.LOP, Indicator.MID_END, Indicator.SEMI_ANNUAL]))

@tag('iptt', 'fast')
class TestIPTTGenerateTargetPeriods(TestCase):
    """Tests for IPTTMixin._generate_targetperiods function
        
        IPTTMixin.program = program
        IPTTMixin.filter_form_initial_data
            - start_period - blank or ISO date to filter targets after
            - end_period - blank or ISO date to filter targets before
            - timeframe - blank (dates) or 1 (show all) or 2 (most recent)
            - numrecentperiods - show X most recent timeperiods (requires 2 timeframe)
        call with (period = frequency #)
        
    """
    def setUp(self):
        pass

    def test_generate_target_periods_annual(self):
        # program with 5 year period
        program = ProgramFactory(
            reporting_period_start=datetime.date(2013, 1, 1),
            reporting_period_end=datetime.date(2017, 12, 31)
        )
        
        mixin = IPTT_Mixin()
        mixin.program = program
        mixin.filter_form_initial_data = {
            'timeframe': 1
        }
        (end_date, date_ranges, targetperiods) = mixin._generate_targetperiods(Indicator.ANNUAL)
        self.assertEqual(end_date, datetime.date(2017, 12, 31))
        self.assertEqual(len(date_ranges), 5)
        self.assertEqual(date_ranges[1]['start'], datetime.date(2014, 1, 1))
        self.assertEqual(len(targetperiods), 5)
        mixin.filter_form_initial_data = {
            'timeframe': 0,
            'start_period': '2013-01-01',
            'end_period': '2016-12-31'
        }
        (end_date, date_ranges, targetperiods) = mixin._generate_targetperiods(Indicator.ANNUAL)
        self.assertEqual(end_date, datetime.date(2016, 12, 31))
        self.assertEqual(len(date_ranges), 5)
        self.assertEqual(len(targetperiods), 4)
        mixin.filter_form_initial_data = {
            'timeframe': 0,
            'start_period': '2013-01-01',
            'end_period': '2014-12-31'
        }
        (end_date, date_ranges, targetperiods) = mixin._generate_targetperiods(Indicator.ANNUAL)
        self.assertEqual(end_date, datetime.date(2014, 12, 31))
        self.assertEqual(len(date_ranges), 5)
        self.assertEqual(len(targetperiods), 2)
        mixin.filter_form_initial_data = {
            'timeframe': 2,
            'numrecentperiods': 3
        }
        (end_date, date_ranges, targetperiods) = mixin._generate_targetperiods(Indicator.ANNUAL)
        self.assertEqual(end_date, datetime.date(2017, 12, 31))
        self.assertEqual(len(date_ranges), 5)
        self.assertEqual(len(targetperiods), 3)
        self.assertEqual(targetperiods[0]['start'], datetime.date(2015, 1, 1))

    def test_generate_target_periods_quarterly(self):
        program = ProgramFactory(
            reporting_period_start=datetime.date(2015, 4, 1),
            reporting_period_end=datetime.date(2016, 6, 30)
        )
        mixin = IPTT_Mixin()
        mixin.program = program
        mixin.filter_form_initial_data = {
            'timeframe': 1
        }
        (end_date, date_ranges, targetperiods) = mixin._generate_targetperiods(Indicator.QUARTERLY)
        self.assertEqual(end_date, datetime.date(2016, 6, 30))
        self.assertEqual(len(date_ranges), 5)
        self.assertEqual(date_ranges[1]['start'], datetime.date(2015, 7, 1))
        self.assertEqual(len(targetperiods), 5)
        mixin.filter_form_initial_data = {
            'timeframe': 0,
            'start_period': '2015-04-01',
            'end_period': '2015-12-31'
        }
        (end_date, date_ranges, targetperiods) = mixin._generate_targetperiods(Indicator.QUARTERLY)
        self.assertEqual(end_date, datetime.date(2015, 12, 31))
        self.assertEqual(len(date_ranges), 5)
        self.assertEqual(len(targetperiods), 3)
        mixin.filter_form_initial_data = {
            'timeframe': 0,
            'start_period': '2015-10-01',
            'end_period': '2016-3-31'
        }
        (end_date, date_ranges, targetperiods) = mixin._generate_targetperiods(Indicator.QUARTERLY)
        self.assertEqual(end_date, datetime.date(2016, 3, 31))
        self.assertEqual(targetperiods[1]['name'], 'Quarter 4')
        self.assertEqual(len(date_ranges), 5)
        self.assertEqual(len(targetperiods), 2)
        mixin.filter_form_initial_data = {
            'timeframe': 2,
            'numrecentperiods': 3
        }
        (end_date, date_ranges, targetperiods) = mixin._generate_targetperiods(Indicator.QUARTERLY)
        self.assertEqual(end_date, datetime.date(2016, 6, 30))
        self.assertEqual(len(date_ranges), 5)
        self.assertEqual(targetperiods[0]['name'], 'Quarter 3')
        self.assertEqual(len(targetperiods), 3)
        self.assertEqual(targetperiods[0]['start'], datetime.date(2015, 10, 1))

    def test_generate_target_periods_lop(self):
        program = ProgramFactory(
            reporting_period_start=datetime.date(2015, 4, 1),
            reporting_period_end=datetime.date(2016, 6, 30)
        )
        mixin = IPTT_Mixin()
        mixin.program = program
        mixin.filter_form_initial_data = {
            'timeframe': 1
        }
        (end_date, date_ranges, targetperiods) = mixin._generate_targetperiods(Indicator.LOP)
        self.assertEqual(end_date, datetime.date(2016, 6, 30))
        self.assertEqual(len(date_ranges), 1)
        self.assertEqual(date_ranges[0]['start'], datetime.date(2015, 4, 1))
        self.assertEqual(date_ranges[0]['end'], datetime.date(2016, 6, 30))
        self.assertEqual(len(targetperiods), 1)

    def test_generate_target_periods_midend(self):
        program = ProgramFactory(
            reporting_period_start=datetime.date(2015, 4, 1),
            reporting_period_end=datetime.date(2016, 6, 30)
        )
        mixin = IPTT_Mixin()
        mixin.program = program
        mixin.filter_form_initial_data = {
            'timeframe': 1
        }
        (end_date, date_ranges, targetperiods) = mixin._generate_targetperiods(Indicator.MID_END)
        self.assertEqual(end_date, datetime.date(2016, 6, 30))
        self.assertEqual(len(date_ranges), 1)
        self.assertEqual(date_ranges[0]['start'], datetime.date(2015, 4, 1))
        self.assertEqual(date_ranges[0]['end'], datetime.date(2016, 6, 30))
        self.assertEqual(len(targetperiods), 2)

    @unittest.skip('generate timeperiods made redundant')
    def test_generate_timeperiods(self):
        program = ProgramFactory(
            reporting_period_start=datetime.date(2015, 1, 1),
            reporting_period_end=datetime.date(2016, 12, 31)
        )
        mixin = IPTT_Mixin()
        mixin.program = program
        mixin.filter_form_initial_data = {
            'timeframe': 1
        }
        (end_date, date_ranges, targetperiods) = mixin._generate_timeperiods()
        self.assertEqual(end_date, datetime.date(2016, 12, 31))
        self.assertEqual(len(date_ranges), 24)
        self.assertEqual(len(targetperiods), 24)
        self.assertEqual(date_ranges[9]['start'], datetime.date(2015, 10, 1))
        mixin.filter_form_initial_data = {
            'timeframe': 0,
            'start_period': '2015-10-1',
            'end_period': '2016-12-31'
        }
        (end_date, date_ranges, targetperiods) = mixin._generate_timeperiods()
        self.assertEqual(end_date, datetime.date(2016, 12, 31))
        self.assertEqual(len(date_ranges), 24)
        self.assertEqual(len(targetperiods), 15)
        self.assertEqual(targetperiods[9]['start'], datetime.date(2016, 7, 1))
        mixin.filter_form_initial_data = {
            'timeframe': 0,
            'start_period': '2015-10-1',
            'end_period': '2016-10-31'
        }
        (end_date, date_ranges, targetperiods) = mixin._generate_timeperiods()
        self.assertEqual(end_date, datetime.date(2016, 10, 31))
        self.assertEqual(len(date_ranges), 24)
        self.assertEqual(len(targetperiods), 13)
        self.assertEqual(targetperiods[-1]['start'], datetime.date(2016, 10, 1))
        mixin.filter_form_initial_data = {
            'timeframe': 2,
            'numrecentperiods': 4
        }
        (end_date, date_ranges, targetperiods) = mixin._generate_timeperiods(Indicator.MONTHLY)
        self.assertEqual(end_date, datetime.date(2016, 12, 31))
        self.assertEqual(len(date_ranges), 24)
        self.assertEqual(len(targetperiods), 4)
        self.assertEqual(targetperiods[0]['start'], datetime.date(2016, 9, 1))
