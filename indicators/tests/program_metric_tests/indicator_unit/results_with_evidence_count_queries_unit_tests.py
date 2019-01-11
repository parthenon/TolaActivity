"""Results With Evidence Queries for Program Page Indicator List

Business Rules:
 - count = # of results with wn evidence_url that is non-empty
"""

from factories import (
    indicators_models as i_factories,
    workflow_models as w_factories
)
from indicators.queries import MetricsIndicator
from django import test

@test.tag('evidence', 'metrics', 'fast')
class EvidenceMixin(object):
    def get_indicator(self):
        return i_factories.IndicatorFactory()

    def add_result(self, indicator):
        return i_factories.ResultFactory(
            indicator=indicator,
            achieved=100
        )

    def get_annotated_indicator(self, indicator=None):
        if indicator is None:
            indicator = self.get_indicator()
        return MetricsIndicator.objects.with_annotations('evidence').get(pk=indicator.pk)

    def add_evidence(self, data):
        data.evidence_url = 'http://test_evidence_url'
        data.save()


@test.tag('evidence', 'metrics', 'core')
class TestResultswithEvidenceCount(test.TestCase, EvidenceMixin):
    """results_with_evidence_count should match number of results with evidence"""

    def test_no_data_no_evidence(self):
        """no data and no evidence should have results_with_evidence_count of 0"""
        annotated_indicator = self.get_annotated_indicator()
        self.assertEqual(annotated_indicator.results_with_evidence_count, 0)

    def test_one_data_no_evidence(self):
        """one result and no evidence should have results_with_evidence_count of 0"""
        indicator = self.get_indicator()
        self.add_result(indicator)
        annotated_indicator = self.get_annotated_indicator(indicator)
        self.assertEqual(annotated_indicator.results_with_evidence_count, 0)

    def test_one_data_one_evidence(self):
        """one result and one evidence should have results_with_evidence_count of 1"""
        indicator = self.get_indicator()
        data = self.add_result(indicator)
        self.add_evidence(data)
        annotated_indicator = self.get_annotated_indicator(indicator)
        self.assertEqual(annotated_indicator.results_with_evidence_count, 1)

    def test_one_data_two_evidence(self):
        """one result and two evidence should have results_with_evidence_count of 2"""
        indicator = self.get_indicator()
        data = self.add_result(indicator)
        self.add_evidence(data)
        data2 = self.add_result(indicator)
        self.add_evidence(data2)
        annotated_indicator = self.get_annotated_indicator(indicator)
        self.assertEqual(annotated_indicator.results_with_evidence_count, 2)
