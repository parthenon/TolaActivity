# -*- coding: utf-8 -*-
"""
Verify viewing IPTT reports run without except in none english languages
"""
from datetime import datetime

from django import test
from django.urls import reverse

from factories import UserFactory, TolaUserFactory, ProgramFactory, IndicatorFactory, PeriodicTargetFactory
from indicators.views.views_reports import IPTT_Mixin
from iptt_sample_data import iptt_utility
from indicators.models import Indicator

TEST_LANGUAGES = ['en', 'es', 'fr']

class TestIPTTTimePeriodReportsI18N(iptt_utility.TestIPTTTimePeriodsReportResponseBase):
    """
    Check all time periods against in all languages
    """
    test_time_periods = [
        Indicator.ANNUAL,
        Indicator.SEMI_ANNUAL,
        Indicator.TRI_ANNUAL,
        Indicator.QUARTERLY,
        Indicator.MONTHLY,
    ]

    def setUp(self):
        super(TestIPTTTimePeriodReportsI18N, self).setUp()

        self.set_dates('2016-06-01', '2018-05-30')

        # create indicators w/ collected data
        self.add_indicator_with_data(Indicator.MONTHLY, [100]*24)

        # create and login user (defaulted to 'en' language)
        self.user = UserFactory(first_name="FN", last_name="LN", username="tester")
        self.user.set_password('password')
        self.user.save()

        self.tola_user = TolaUserFactory(user=self.user)

        self.client.login(username="tester", password='password')

    def _set_user_language(self, language):
        self.tola_user.language = language
        self.tola_user.save()

    def test_iptt_report_requests_in_all_languages(self):
        for language in TEST_LANGUAGES:
            self._set_user_language(language)

            for time_period in self.test_time_periods:
                self.request_params['timeperiods'] = time_period

                url = reverse('iptt_report', args=[self.program.id, IPTT_Mixin.REPORT_TYPE_TIMEPERIODS])

                # lack of exception is a win!
                response = self.client.post(url,
                                            self.request_params,
                                            follow=True)
                self.assertEqual(response.status_code, 200,
                                 "response gave status code {0} instead of 200".format(response.status_code))


class TestIPTTTargetReportsI18N(test.TestCase):
    """
    My original thought was to test all target periods in all languages

    I found out the PeriodicTarget.period field is a char field that is actually used as part of the DB
    annotations/query, and needs to line up with the target period your are reporting on. This is
    kind of a nightmare from a testing perspective.

    The bug this is regression testing against was that a PeriodicTarget.period containing unicode
    would throw an encoding exception on view, so just test for that case and call it a day
    """
    test_target_periods = [
        # Indicator.LOP,
        # Indicator.MID_END,
        Indicator.ANNUAL,
        # Indicator.MONTHLY,
        # Indicator.SEMI_ANNUAL,
        # Indicator.TRI_ANNUAL,
        # Indicator.QUARTERLY,
    ]

    def setUp(self):
        startdate = datetime.strptime('2017-02-04', '%Y-%m-%d')
        enddate = datetime.strptime('2019-10-01', '%Y-%m-%d')
        self.program = ProgramFactory(reporting_period_start=startdate,
                                      reporting_period_end=enddate)

        # setting up an indicator of each target type should allow the view to load w/ that target period (I think...)
        for indicator_frequency in self.test_target_periods:
            indicator = IndicatorFactory(target_frequency=indicator_frequency, program=self.program)

            # make periodic target w/ unicode in the period names - this was causing an exception!
            PeriodicTargetFactory(period='Año unicode name', indicator=indicator, start_date=startdate, end_date=enddate)

        # create and login user (defaulted to 'en' language)
        self.user = UserFactory(first_name="FN", last_name="LN", username="tester")
        self.user.set_password('password')
        self.user.save()

        self.tola_user = TolaUserFactory(user=self.user)

        self.client.login(username="tester", password='password')

    def _set_user_language(self, language):
        self.tola_user.language = language
        self.tola_user.save()

    def test_iptt_report_requests_in_all_languages(self):
        for language in TEST_LANGUAGES:
            self._set_user_language(language)

            for target_period in self.test_target_periods:
                url = reverse('iptt_report', args=[self.program.id, IPTT_Mixin.REPORT_TYPE_TARGETPERIODS])

                # lack of exception is a win!
                response = self.client.post(url,
                                            {
                                                'program': self.program.id,
                                                'targetperiods': target_period,
                                                'timeframe': 1,  # show all
                                                'csrfmiddlewaretoken': 'lol',
                                            },
                                            follow=True)
                self.assertEqual(response.status_code, 200,
                                 "response gave status code {0} instead of 200".format(response.status_code))
