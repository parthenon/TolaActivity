from datetime import datetime
from unittest import skip

from django.core.urlresolvers import reverse_lazy
from django.test import Client, TestCase

from indicators.models import Indicator
from indicators.views.views_reports import IPTT_Mixin
from workflow.models import Program


class IPTT_MixinTestCase(TestCase):
    freqs = {
        Indicator.ANNUAL: 12,
        Indicator.SEMI_ANNUAL: 6,
        Indicator.TRI_ANNUAL: 4,
        Indicator.QUARTERLY: 3,
        Indicator.MONTHLY: 1,
    }

    def setUp(self):
        self.client = Client()
        self.mixin = IPTT_Mixin()

    def test_page_load_returns_200(self):
        """Do we return 200?"""
        response = self.client.get(reverse_lazy('iptt_quickstart'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.redirect_chain), 0)

    def test_page_loads_correct_template(self):
        """Do we load the right template?"""
        response = self.client.get(reverse_lazy('iptt_quickstart'), follow=True)
        self.assertTemplateUsed(response, 'indicators/iptt_quickstart.html')
        self.assertContains(response, 'Indicator Performance Tracking Table')

    def test_get_num_months(self):
        """Do we return the right number of months per period?"""
        for freq in IPTT_MixinTestCase.freqs:
            num_months_in_period = self.mixin._get_num_months(freq)
            self.assertEqual(num_months_in_period, IPTT_MixinTestCase.freqs[freq])

    def test_get_num_periods(self):
        """Do we return the correct number of periods"""
        _get_num_periods = IPTT_Mixin._get_num_periods
        start_date = datetime.strptime("2016-01-15", "%Y-%m-%d").date()
        end_date = datetime.strptime("2017-12-16", "%Y-%m-%d").date()

        self.assertEqual(_get_num_periods(start_date, end_date, Indicator.ANNUAL), 2)
        self.assertEqual(_get_num_periods(start_date, end_date, Indicator.SEMI_ANNUAL), 4)
        self.assertEqual(_get_num_periods(start_date, end_date, Indicator.TRI_ANNUAL), 6)
        self.assertEqual(_get_num_periods(start_date, end_date, Indicator.QUARTERLY), 8)
        self.assertEqual(_get_num_periods(start_date, end_date, Indicator.MONTHLY), 24)

    def test_get_num_periods_returns_0_for_reversed_date_range(self):
        """Do we return 0 if end date is before start date?"""
        _get_num_periods = IPTT_Mixin._get_num_periods
        start_date = datetime.strptime("2020-01-01", "%Y-%m-%d").date()
        end_date = datetime.strptime("2019-01-01", "%Y-%m-%d").date()

        self.assertEqual(_get_num_periods(start_date, end_date, Indicator.ANNUAL), 0)
        self.assertEqual(_get_num_periods(start_date, end_date, Indicator.SEMI_ANNUAL), 0)
        self.assertEqual(_get_num_periods(start_date, end_date, Indicator.TRI_ANNUAL), 0)
        self.assertEqual(_get_num_periods(start_date, end_date, Indicator.QUARTERLY), 0)
        self.assertEqual(_get_num_periods(start_date, end_date, Indicator.MONTHLY), 0)

    def test_get_period_names(self):
        """Do we return the correct period names?"""
        _get_period_name = IPTT_Mixin._get_period_name

        self.assertEqual(_get_period_name(Indicator.ANNUAL), "Year")
        self.assertEqual(_get_period_name(Indicator.SEMI_ANNUAL), "Semi-annual")
        self.assertEqual(_get_period_name(Indicator.TRI_ANNUAL), "Tri-annual")
        self.assertEqual(_get_period_name(Indicator.QUARTERLY), "Quarter")
        self.assertEqual(_get_period_name(Indicator.MONTHLY), "Month")

    def test_get_first_period(self):
        """Do we calculate the first period of a date range correctly?"""
        real_start_date = datetime.strptime("2016-07-15", "%Y-%m-%d").date()
        for freq in IPTT_MixinTestCase.freqs:
            num_months = self.mixin._get_num_months(freq)

            _get_first_period = self.mixin._get_first_period(real_start_date, num_months)
            if freq == Indicator.ANNUAL:
                self.assertEqual(_get_first_period,
                                 datetime.strptime("2016-01-01", "%Y-%m-%d").date())
            elif freq == Indicator.SEMI_ANNUAL:
                self.assertEqual(_get_first_period,
                                 datetime.strptime("2016-07-01", "%Y-%m-%d").date())
            elif freq == Indicator.TRI_ANNUAL:
                self.assertEqual(_get_first_period,
                                 datetime.strptime("2016-05-01", "%Y-%m-%d").date())
            elif freq == Indicator.QUARTERLY:
                self.assertEqual(_get_first_period,
                                 datetime.strptime("2016-07-01", "%Y-%m-%d").date())
            elif freq == Indicator.MONTHLY:
                self.assertEqual(_get_first_period,
                                 datetime.strptime("2016-07-01", "%Y-%m-%d").date())
            else:
                self.assertEqual(1, 0, msg="Unexpected target frequency: " + freq)

    @skip('Patience, grasshopper. When you can snatch the pebble...')
    def test_generate_annotations(self):
        pass

    def test_generate_targetperiods(self):
        """Can we generate target periods correctly"""
        filter_start_date = datetime.strptime("2018-01-01", "%Y-%m-%d").date()
        filter_end_date = datetime.strptime("2019-12-31", "%Y-%m-%d").date()
        freq = Indicator.ANNUAL
        num_recents = 0
        show_all = True
        self.mixin.program = Program()
        self.mixin.program.reporting_period_start = filter_start_date
        self.mixin.program.reporting_period_end = filter_end_date

        report_end_date, all_date_ranges, targetperiods = \
            self.mixin._generate_targetperiods(self.mixin.program,
                                               filter_start_date,
                                               filter_end_date,
                                               freq,
                                               show_all,
                                               num_recents)
        self.assertEqual(filter_end_date, report_end_date)
        self.assertEqual(len(all_date_ranges), 0)
        self.assertEqual(len(targetperiods), 0)

    def test_generate_timeperiods(self):
        """Can we generate time periods correctly?"""
        filter_start_date = datetime.strptime("2018-01-01", "%Y-%m-%d").date()
        filter_end_date = datetime.strptime("2019-12-31", "%Y-%m-%d").date()
        freq = Indicator.ANNUAL
        num_recents = 0
        show_all = True
        self.mixin.program = Program()
        self.mixin.program.reporting_period_start = filter_start_date
        self.mixin.program.reporting_period_end = filter_end_date

        report_end_date, all_date_ranges, periods_date_ranges = \
            self.mixin._generate_timeperiods(filter_start_date,
                                             filter_end_date,
                                             freq,
                                             show_all,
                                             num_recents)
        self.assertEqual(filter_end_date, report_end_date)
        self.assertEqual(len(all_date_ranges), 2)
        self.assertEqual(len(periods_date_ranges), 2)

    @skip('Patience, grasshopper. When you can snatch the pebble...')
    def test_update_filter_form_initial(self):
        """Do we populate the initial filter form properly?"""
        # _update_filter_form_initial(self, formdata)
        # _update_filter_form_initial(self.request.GET)
        pass

    @skip('Patience, grasshopper. When you can snatch the pebble...')
    def test_get_filters(self):
        pass

    @skip('Patience, grasshopper. When you can snatch the pebble...')
    def test_prepare_indicators(self):
        pass

    @skip('Patience, grasshopper. When you can snatch the pebble...')
    def test_prepare_iptt_period_dateranges(self):
        pass

    @skip('Patience, grasshopper. When you can snatch the pebble...')
    def test_get_context_data(self):
        pass


class IPTT_ExcelExportTestCase(TestCase):

    @skip('Patience, grasshopper. When you can snatch the pebble...')
    def test_get_filename(self):
        pass

    @skip('Patience, grasshopper. When you can snatch the pebble...')
    def test_style_range(self):
        pass

    @skip('Patience, grasshopper. When you can snatch the pebble...')
    def test_add_headers(self):
        pass

    @skip('Patience, grasshopper. When you can snatch the pebble...')
    def test_add_data(self):
        pass

    @skip('Patience, grasshopper. When you can snatch the pebble...')
    def test_set_column_widths(self):
        pass

    @skip('Patience, grasshopper. When you can snatch the pebble...')
    def test_get(self):
        pass


class IPTT_ReportIndicatorsWithVariedStartDateTestCase(TestCase):
    @skip('Patience, grasshopper. When you can snatch the pebble...')
    def test_get_context_data(self):
        pass

    @skip('Patience, grasshopper. When you can snatch the pebble...')
    def test_get(self):
        pass


class IPTTReportQuickstartViewTestCase(TestCase):

    @skip('Patience, grasshopper. When you can snatch the pebble...')
    def test_get_context_data(self):
        pass

    @skip('Patience, grasshopper. When you can snatch the pebble...')
    def test_get_form_kwargs(self):
        pass

    @skip('Patience, grasshopper. When you can snatch the pebble...')
    def test_post(self):
        pass

    @skip('Patience, grasshopper. When you can snatch the pebble...')
    def test_form_valid(self):
        pass

    @skip('Patience, grasshopper. When you can snatch the pebble...')
    def test_form_invalid(self):
        pass


class IPTT_ReportViewTestCase(TestCase):
    @skip('Patience, grasshopper. When you can snatch the pebble...')
    def test_get(self):
        pass

    @skip('Patience, grasshopper. When you can snatch the pebble...')
    def test_post(self):
        pass
