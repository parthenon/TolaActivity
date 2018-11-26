# pylint: disable=W0611
# These are the unit tests for the indicator metrics used on the program page:

from program_metric_tests.indicator_unit.all_targets_defined_queries_unit_tests import (
    TestNoTargetFrequency,
    TestLOPIndicatorTargetsDefined,
    TestMIDENDIndicatorTargetsDefined,
    TestEVENTIndicatorTargetsDefined,
    TestReportingPeriodAnnotations,
    TestANNUALIndicatorTargetsDefined,
    TestSEMIANNUALIndicatorTargetsDefined,
    TestTRIANNUALIndicatorTargetsDefined,
    TestQUARTERLYIndicatorTargetsDefined,
    TestMONTHLYIndicatorTargetsDefined
)

from program_metric_tests.indicator_unit.has_reported_results_queries_unit_tests import (
    TestHasReportedResults,
)

from program_metric_tests.indicator_unit.results_with_evidence_count_queries_unit_tests import (
    TestResultswithEvidenceCount,
    TestResultsMixedEvidenceTypes
)

from program_metric_tests.indicator_unit.reporting_queries_unit_tests import (
    TestSingleNonReportingIndicator,
    TestSingleReportingIndicator,
    TestMixedReportingAndNonIndicators
)

from program_metric_tests.indicator_unit.over_under_queries_unit_tests import (
    TestTargetsActualsOverUnderCorrect
)
