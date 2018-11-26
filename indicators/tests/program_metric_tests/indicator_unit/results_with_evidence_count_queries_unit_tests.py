"""Results With Evidence Queries for Program Page Indicator List

Business Rules:
 - count = # of collecteddata with either
    -an evidence FK to a Documentation model or
    -a tolatable fk to a TolaTable model
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

    def add_data(self, indicator):
        return i_factories.CollectedDataFactory(
            indicator=indicator,
            achieved=100
        )

    def get_annotated_indicator(self, indicator=None):
        if indicator is None:
            indicator = self.get_indicator()
        return MetricsIndicator.objects.with_annotations('evidence').get(pk=indicator.pk)

    def add_evidence(self, data):
        evidence = w_factories.DocumentationFactory()
        data.evidence = evidence
        data.save()
        return evidence

    def add_tolatable(self, data):
        tolatable = i_factories.TolaTableFactory()
        data.tola_table = tolatable
        data.save()
        return tolatable

@test.tag('evidence', 'metrics', 'core')
class TestResultswithEvidenceCount(test.TestCase, EvidenceMixin):
    """results_with_evidence_count should match number of results with evidence"""

    def test_no_data_no_evidence(self):
        """no data and no evidence should have results_with_evidence_count of 0"""
        annotated_indicator = self.get_annotated_indicator()
        self.assertEqual(annotated_indicator.results_with_evidence_count, 0)

    def test_one_data_no_evidence(self):
        """one collecteddata and no evidence should have results_with_evidence_count of 0"""
        indicator = self.get_indicator()
        self.add_data(indicator)
        annotated_indicator = self.get_annotated_indicator(indicator)
        self.assertEqual(annotated_indicator.results_with_evidence_count, 0)

    def test_one_data_one_evidence(self):
        """one collecteddata and one evidence should have results_with_evidence_count of 1"""
        indicator = self.get_indicator()
        data = self.add_data(indicator)
        self.add_evidence(data)
        annotated_indicator = self.get_annotated_indicator(indicator)
        self.assertEqual(annotated_indicator.results_with_evidence_count, 1)

    def test_one_data_one_tolatable(self):
        """one collecteddata and one tolatable should have results_with_evidence_count of 1"""
        indicator = self.get_indicator()
        data = self.add_data(indicator)
        self.add_tolatable(data)
        annotated_indicator = self.get_annotated_indicator(indicator)
        self.assertEqual(annotated_indicator.results_with_evidence_count, 1)

class TestResultsMixedEvidenceTypes(test.TestCase, EvidenceMixin):
    """results_with_evidence_count should match number of results with evidence or tolatables"""

    def test_one_of_each_type(self):
        """one evidence and one tolatable should show results_with_evidence_count of 2"""
        indicator = self.get_indicator()
        data = self.add_data(indicator)
        self.add_evidence(data)
        data2 = self.add_data(indicator)
        self.add_tolatable(data2)
        annotated_indicator = self.get_annotated_indicator(indicator)
        self.assertEqual(annotated_indicator.results_with_evidence_count, 2)

    def test_mixed_evidence_types_multiple_indicators(self):
        """for multiple indicators, results_with_evidence_count should be 11"""
        expected = [0, 3, 0, 2, 5]
        none_indicator = self.get_indicator()
        self.add_data(none_indicator)
        three_indicator = self.get_indicator()
        self.add_evidence(self.add_data(three_indicator))
        self.add_evidence(self.add_data(three_indicator))
        self.add_evidence(self.add_data(three_indicator))
        self.get_indicator()
        two_indicator = self.get_indicator()
        self.add_tolatable(self.add_data(two_indicator))
        self.add_tolatable(self.add_data(two_indicator))
        five_indicator = self.get_indicator()
        self.add_evidence(self.add_data(five_indicator))
        self.add_tolatable(self.add_data(five_indicator))
        self.add_evidence(self.add_data(five_indicator))
        self.add_tolatable(self.add_data(five_indicator))
        self.add_evidence(self.add_data(five_indicator))
        for count, indicator in zip(expected, MetricsIndicator.objects.with_annotations('evidence').order_by('pk')):
            self.assertEqual(count, indicator.results_with_evidence_count)
        