import json
from django.test import RequestFactory, TestCase
from django.urls import reverse_lazy

from indicators.models import Indicator
from tola.test.base_classes import TestBase


class IndicatorCreateFunctionTests(TestBase, TestCase):

    def setUp(self):
        super(IndicatorCreateFunctionTests, self).setUp()

    def test_get(self):
        url = reverse_lazy('indicator_create', args=[self.program.id])
        response = self.client.get(url)

        self.assertContains(response, 'Indicator Performance Tracking Table')
        self.assertTemplateUsed(response, 'indicators/indicator_create.html')

    def test_post(self):
        request_content = {
            'program': self.program.id, 'country': self.country.id, 'services': 0, 'service_indicator': 0}
        response = self.client.post('/indicators/indicator_create/%s/' % self.program.id, request_content)

        self.assertEqual(response.status_code, 302)


class IndicatorUpdateTests(TestBase, TestCase):

    def setUp(self):
        super(IndicatorUpdateTests, self).setUp()
        self.url = reverse_lazy('indicator_update', args=[self.indicator.id])

    def test_get(self):
        url = reverse_lazy('indicator_update', args=[self.indicator.id])
        response = self.client.get(url)

        self.assertContains(response, 'Indicator Performance Tracking Table')
        self.assertTemplateUsed(response, 'indicators/indicator_form.html')

    def test_post(self):
        # build form data using URL encoded form key value pairs
        data = {
            'name': 'Test+Name',
            'program2': self.program.id,
            'target_frequency': Indicator.ANNUAL,
            'level': 1,
            'indicator_type': 1,
            'unit_of_measure_type': 1,
            'unit_of_measure': 1,
            'lop_target': 3223,
            'program': self.program.id,
            'direction_of_change': Indicator.DIRECTION_OF_CHANGE_NONE,
        }

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 200)
        self.indicator = Indicator.objects.get(pk=self.indicator.id)
        self.assertEqual(int(self.indicator.lop_target), 3223,
                         "expected indicator lop target to update to 3223, got {0}".format(self.indicator.lop_target))

    def test_post_ajax(self):
        """ensures that an AJAX post returns a correct JSON response to update the indicator rows with JS"""
        data = {
            'name': 'Updated Name',
            'level': 2,
            'unit_of_measure': 'bananas',
            'unit_of_measure_type': self.indicator.unit_of_measure_type,
            'program': self.indicator.program.first().id,
            'target_frequency': self.indicator.target_frequency,
            'direction_of_change': self.indicator.direction_of_change,
            'program2': self.indicator.program.first().id,
        }
        response = self.client.post(self.url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        # HERE is where the keys/values assumptions for the JSON response as expected by JS should go
        expected_response = json.dumps({
            'key': 'expectedvalue',
            'otherkey': ['listitem1', 'listitem2']
        })
        self.assertJSONEqual(response.content, expected_response,
                             "expected:\n {0} but indicator_update returned:\n {1}".format(
                                expected_response, response.content))