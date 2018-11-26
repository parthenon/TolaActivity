# pylint: disable=W0611
# These are the unit tests for the program metrics used on the home page:
from program_metric_tests.program_unit.percent_complete_queries_unit_tests import (
    TestProgramPercentComplete
)

from program_metric_tests.program_unit.program_metrics_queries_unit_tests import (
    TestIndicatorCounts,
    TestLOPTargetsDefined,
    TestMidEndTargetsDefined,
    TestEventTargetsDefined,
    TestAnnualTargetsDefined,
    TestSemiAnnualTargetCounts,
    TestTriAnnualTargetCounts,
    TestQuarterlyTargetCounts,
    TestMonthlyTargetCounts,
    TestProgramReportedResultsQueries,
    TestProgramWithEvidenceQueries,
    TestIndicatorReportingEdgeCases
)

from program_metric_tests.program_unit.program_reporting_count_unit_tests import (
    TestSingleNonReportingIndicator,
    TestSingleReportingIndicator,
    TestMixedReportingAndNonIndicators
)

from program_metric_tests.program_unit.program_scope_queries_unit_tests import (
        TestProgramReportingingCounts,
        TestTargetsActualsOverUnderCorrect
)