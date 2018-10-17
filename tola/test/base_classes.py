from unittest import skip
import datetime
from decimal import Decimal

from django.test import RequestFactory, Client
from django.urls import reverse_lazy
from django.core.exceptions import ImproperlyConfigured

from factories.django_models import UserFactory
from factories.indicators_models import IndicatorFactory
from factories.workflow_models import ProgramFactory, TolaUserFactory
from indicators.models import Indicator
from tola.test.utils import instantiate_scenario, decimalize


class TestBase(object):
    fixtures = ['indicatortype.json', 'levels.json']

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

        self.request_factory = RequestFactory()
        self.client = Client()
        self.client.login(username="IC", password='password')


class FrontendBase(TestBase):

    """
    Stub class to test that I'm receiving valid document responses
    """

    @property
    def scenario(self):
        raise ImproperlyConfigured("A value for scenario hasn't been set")

    @property
    def url_name(self):
        raise ImproperlyConfigured("A value for the url_name variable hasn't been set")

    def setUp(self):
        super(FrontendBase, self).setUp()
        self.indicator.delete()
        self.url = reverse_lazy(self.url_name, args=[self.program.id, 0, 0])
        self.response = self.client.get(self.url)

    def test_indicator_list_has_indicators(self):
        print(self.response) # TODO: parse with BS4 for valid HTML


class ScenarioBase(TestBase):

    """
    Note: many of these tests rely on the indicators and periodic targets being created and rendered to the context
    variable in the correct order.  This is a short cut so the exact periods don't need to be calculated.
    It is assumed that the periodic target generation function will be tested elsewhere.
    """

    @property
    def scenario(self):
        raise ImproperlyConfigured("A value for scenario hasn't been set")

    @property
    def url_name(self):
        raise ImproperlyConfigured("A value for the url_name variable hasn't been set")

    def setUp(self):
        super(ScenarioBase, self).setUp()
        self.indicator.delete()
        self.indicator_ids = instantiate_scenario(self.program.id, self.scenario)
        self.indicators = Indicator.objects.filter(id__in=self.indicator_ids)
        self.url = reverse_lazy(self.url_name, args=[self.indicators.first().id, self.program.id])
        self.response = self.client.get(self.url)

    def test_periodic_targets_have_correct_targets(self):
        scenario_targets = self.scenario.indicators[0].periodic_target_targets
        response_targets = [pt.target for pt in self.response.context['periodictargets']]
        self.assertEqual(scenario_targets, response_targets)

    def test_result_set_is_correct(self):
        scenario_collected_data = self.scenario.indicators[0].collected_data_sets
        response_collected_data = []
        for pt in self.response.context['periodictargets']:
            response_collected_data.append(list(pt.getcollected_data.values_list('achieved', flat=True)))
        self.assertEqual(scenario_collected_data, response_collected_data)

# TODO: see if there is a way to abstract this better so a new base doesn't need to be created for each URL
class ScenarioBase2(TestBase):

    """
    Note: many of these tests rely on the indicators and periodic targets being created and rendered to the context
    variable in the correct order.  This is a short cut so the exact periods don't need to be calculated.
    It is assumed that the periodic target generation function will be tested elsewhere.
    """

    @property
    def scenario(self):
        raise ImproperlyConfigured("A value for scenario hasn't been set")

    @property
    def url_name(self):
        raise ImproperlyConfigured("A value for the url_name variable hasn't been set")

    def setUp(self):
        super(ScenarioBase2, self).setUp()
        self.indicator.delete()
        self.indicator_ids = instantiate_scenario(self.program.id, self.scenario)
        self.indicators = Indicator.objects.filter(id__in=self.indicator_ids)
        self.url = reverse_lazy(self.url_name, args=[self.program.id, 0, 0])
        self.response = self.client.get(self.url)



class IndicatorDetailsMixin(TestBase):

    """ Use this mixin to test the correct targets and collected data is returned from a query"""

    def test_periodic_targets_have_correct_targets(self):
        scenario_targets = self.scenario.indicators[0].periodic_target_targets
        response_targets = [pt.target for pt in self.response.context['periodictargets']]
        self.assertEqual(scenario_targets, response_targets)

    def test_result_set_is_correct(self):
        scenario_collected_data = self.scenario.indicators[0].collected_data_sets
        response_collected_data = []
        for pt in self.response.context['periodictargets']:
            response_collected_data.append(list(pt.getcollected_data.values_list('achieved', flat=True)))
        self.assertEqual(scenario_collected_data, response_collected_data)

    def test_each_periodic_target_result_sum_is_correct(self):
        scenario_sums = self.scenario.indicators[0].collected_data_sum_by_periodic_target
        response_sums = []
        for pt in self.response.context['periodictargets']:
            if self.scenario.indicators[0].unit_of_measure_type == Indicator.NUMBER:
                if self.scenario.indicators[0].is_cumulative:
                    response_sums.append(pt.cumulative_sum)
                else:
                    response_sums.append(pt.achieved_sum)
            else:
                response_sums.append(pt.last_data_row)

        self.assertEqual(scenario_sums, response_sums)

    def test_lop_row_target_value_correct(self):
        response_lop_target = self.response.context['indicator'].lop_target
        self.assertEqual(unicode(self.scenario.indicators[0].lop_target), response_lop_target)

    def test_lop_row_actual_value_correct(self):
        response_value = self.response.context.pop()['grand_achieved_sum']
        scenario_value = decimalize(self.scenario.indicators[0].collected_data_sum)
        self.assertEqual(scenario_value, response_value)

    @skip('Not implemented yet')
    def test_evidence_set_is_correct(self):
        pass

    @skip('Percent is calced in the template, it should be correct if targets and actuals are correct.')
    def test_each_periodic_target_percent_is_correct(self):
        pass

    @skip('Percent is calced in the template, it should be correct if targets and actuals are correct.')
    def test_lop_row_percent_value_correct(self):
        pass


class IndicatorStatsMixin(object):

    """
    Add this to a class based test if you want to test the indicator statistics
    """

    @skip('View not implmented yet')
    def test_indicators_near_target(self):
        buckets_values = {'low': 0, 'on_scope': 0, 'high': 0}
        target_date = datetime.date(2018, 9, 5)
        for i, indicator_id in enumerate(self.indicator_ids):
            db_indicator = Indicator.objects.get(id=indicator_id)
            periodic_target_count = len(db_indicator.periodictargets.filter(end_date__lt=target_date))
            scenario_ratio = self.scenario.indicators[i].program_to_date_achieved_ratio(
                period_ceiling=periodic_target_count)
            if scenario_ratio > 1 + Indicator.ONSCOPE_MARGIN:
                buckets_values['high'] += 1
            elif scenario_ratio < 1 - Indicator.ONSCOPE_MARGIN:
                buckets_values['low'] += 1
            else:
                buckets_values['on_scope'] += 1

        # TODO: git rid of float in fovor of a Decimal?
        buckets_percents = {k: float(v)/len(self.indicator_ids) for (k, v) in buckets_values.iteritems()}

        self.assertEqual(buckets_percents, self.response.context['scope_percents'])

