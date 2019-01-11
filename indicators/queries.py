"""Querymanagers and proxymodels to abstract complex queries on indicator models

"""

import datetime
from indicators.models import (
    Indicator,
    Level,
    PeriodicTarget,
    Result,
    IndicatorSortingManagerMixin,
    IndicatorSortingQSMixin
)
from workflow import models as wf_models
from django.db import models
from django.db.models.functions import Concat
from django.utils.functional import cached_property

# pylint: disable=W0223
class Round(models.Func):
    """One argument, rounds to integer level (0 decimal places)"""
    function = 'ROUND'
    template = '%(function)s(%(expressions)s, 0)'

# pylint: disable=W0223
class MonthDate(models.Func):
    """takes a date and outputs a YYYYMM format date for period_diff comparison"""
    function = 'DATE_FORMAT'
    template = '%(function)s(%(expressions)s, \'%%%%Y%%%%m\')'

# pylint: disable=W0223
class MonthsCount(models.Func):
    """takes two date fields, finds their value, converts them to MonthDate format, and finds the difference in months

        note: +1 is due to the 'first of the month to end of the month' inclusive month ranges in our dates
        note: wrapping parens due to this field being used in division math"""
    function = 'PERIOD_DIFF'
    template = '(%(function)s(%(expressions)s)+1)'

    def __init__(self, end_date, start_date, **extra):
        if not start_date:
            raise ValueError('two dates required for diff')
        expressions = MonthDate(models.F(end_date)), MonthDate(models.F(start_date))
        super(MonthsCount, self).__init__(*expressions)

def indicator_lop_annotations():
    """generates annotations for LOP target and actual data

    takes into account cumulative/noncumulative and number/percent"""
    # we only want targets that are either time naive or for completed periods:
    data_subquery = Result.objects.filter(
        periodic_target_id=models.OuterRef('pk')
    ).order_by().values('id')
    indicator_targets = PeriodicTarget.objects.annotate(
        data_count=models.Subquery(
            data_subquery.annotate(total=models.Count('achieved')).values('total')[:1],
            output_field=models.IntegerField()
        )
    ).filter(
        models.Q(indicator=models.OuterRef('pk')),
        (
            models.Q(indicator__target_frequency__in=[Indicator.LOP, Indicator.MID_END, Indicator.EVENT]) &
            models.Q(data_count__gt=0)
        ) | models.Q(end_date__lte=models.functions.Now())
    )
    indicator_data = Result.objects.filter(
        models.Q(indicator=models.OuterRef('pk'))
    )
    lop_target_sum = models.Case(
        models.When(
            # the only target for a LOP indicator is the "lop_target" value on the indicator itself:
            target_frequency=Indicator.LOP,
            then=models.ExpressionWrapper(
                models.F('lop_target'),
                output_field=models.FloatField()
            )
        ),
        models.When(
            # cumulative indicator means sort and take the most recent:
            is_cumulative=True,
            then=models.Case(
                # midline/endling and event indicators sort on customsort (with fallbacks)
                models.When(
                    target_frequency__in=[Indicator.MID_END, Indicator.EVENT],
                    then=models.Subquery(
                        indicator_targets.order_by(
                            '-customsort', '-end_date', '-create_date'
                        ).values('target')[:1],
                        output_field=models.FloatField()
                    )
                ),
                # not midline/endline means it's time-aware, sort on end_date:
                default=models.Subquery(
                    indicator_targets.order_by('-end_date').values('target')[:1],
                    output_field=models.FloatField())
                )
        ),
        default=models.Subquery(
            indicator_targets.order_by().values(
                'indicator_id'
            ).annotate(
                total=models.Sum('target')
            ).values('total'),
            output_field=models.FloatField()
        )
    )
    # lop_actual_sum = sum of all the results:
    lop_actual_sum = models.Case(
        models.When(
            unit_of_measure_type=Indicator.PERCENTAGE,
            then=Round(
                models.Subquery(
                    indicator_data.order_by(
                        '-date_collected'
                    ).values('achieved')[:1],
                    output_field=models.FloatField()
                    )
                )
            ),
        default=models.Subquery(
            indicator_data.order_by().values(
                'indicator_id'
            ).annotate(
                total=models.Sum('achieved')
            ).values('total'),
            output_field=models.FloatField()
        )
    )
    return {
        'lop_target_sum': lop_target_sum,
        'lop_actual_sum': lop_actual_sum,
    }

def indicator_reporting_annotation():
    """annotation to sort indicators into 'reporting' and 'nonreporting' based on business rules:
        LOP only reports when the program reporting period has ended
        all indicators only report when their targets are defined
        all indicators only report when they have at least one data point (an actual data sum)
        for target_sum and actual_sum business logic see indicator_lop_annotations"""
    return models.Case(
        models.When(
            models.Q(target_frequency=Indicator.LOP) &
            models.Q(program__reporting_period_end__gt=models.functions.Now()),
            then=models.Value(False)
        ),
        models.When(
            models.Q(lop_target_sum__isnull=True) |
            models.Q(lop_target_sum=0),
            then=models.Value(False)
        ),
        models.When(
            lop_actual_sum__isnull=True,
            then=models.Value(False)
        ),
        default=models.Value(True),
        output_field=models.BooleanField()
    )

def indicator_lop_met_real_annotation():
    """for a reporting indicator, determines how close actual values are to target values"""
    return models.Case(
        models.When(
            models.Q(lop_target_sum__isnull=True) |
            models.Q(lop_actual_sum__isnull=True),
            then=models.Value(None)
            ),
        default=models.ExpressionWrapper(
            models.F('lop_actual_sum') / models.F('lop_target_sum'),
            output_field=models.FloatField()
        )
    )

def indicator_over_under_annotation():
    """annotates indicators with how close to on-track they are:
        -1 : under target by a 15% margin
        0 : within 15% of target
        1 : over target by a 15% margin
        None: nonreporting indicator"""
    over_scope = 1 + Indicator.ONSCOPE_MARGIN
    under_scope = 1 - Indicator.ONSCOPE_MARGIN
    return models.Case(
        # None for indicators missing targets or data:
        models.When(
            models.Q(reporting=False) |
            models.Q(lop_met_real__isnull=True),
            then=models.Value(None)
            ),
        models.When(
            # over is negative if DOC is Negative
            models.Q(lop_met_real__gt=over_scope) &
            models.Q(direction_of_change=Indicator.DIRECTION_OF_CHANGE_NEGATIVE),
            then=models.Value(-1)
            ),
        models.When(
            lop_met_real__gt=over_scope,
            then=models.Value(1)
        ),
        models.When(
            # under is positive if DOC is Negative:
            models.Q(lop_met_real__lt=under_scope) &
            models.Q(direction_of_change=Indicator.DIRECTION_OF_CHANGE_NEGATIVE),
            then=models.Value(1)
        ),
        models.When(
            lop_met_real__lt=under_scope,
            then=models.Value(-1)
        ),
        default=models.Value(0),
        output_field=models.IntegerField(null=True)
    )

TIME_AWARE_FREQUENCIES = [
    (Indicator.ANNUAL, 12),
    (Indicator.SEMI_ANNUAL, 6),
    (Indicator.TRI_ANNUAL, 4),
    (Indicator.QUARTERLY, 3),
    (Indicator.MONTHLY, 1)
]

def indicator_get_program_months_annotation():
    """annotates an indicator with the number of months in the associated program
        this annotation is used by the defined_targets_filter"""
    return MonthsCount('program__reporting_period_end', 'program__reporting_period_start')


def program_get_program_months_annotation():
    """annotates a program with the number of months in the associated program"""
    return MonthsCount('reporting_period_end', 'reporting_period_start')


def indicator_get_defined_targets_filter():
    """returns a set of filters that filter out indicators that do not have all defined targets
        this version is used for an indicator_set that has been annotated with program_months
        (see get_program_months_annotation)"""
    filters = []
    # LOP indicators require a defined lop_target:
    filters.append(models.Q(target_frequency=Indicator.LOP) & models.Q(lop_target__isnull=False))
    # MID_END indicators require 2 defined targets (mid and end):
    filters.append(models.Q(target_frequency=Indicator.MID_END) &
                   models.Q(defined_targets__isnull=False) &
                   models.Q(defined_targets__gte=2))
    # EVENT indicators require at least 1 defined target:
    filters.append(models.Q(target_frequency=Indicator.EVENT) &
                   models.Q(defined_targets__isnull=False) &
                   models.Q(defined_targets__gte=1))
    # TIME_AWARE indicators need a number of indicators defined by the annotation on the program:
    # note the program_months field annotation is required for this annotation to succeed
    for frequency, month_count in TIME_AWARE_FREQUENCIES:
        period_count_filter = models.Q(defined_targets__gte=models.F('program_months') / month_count)
        filters.append(models.Q(target_frequency=frequency) &
                       models.Q(defined_targets__isnull=False) &
                       period_count_filter)
    combined_filter = filters.pop()
    for filt in filters:
        combined_filter |= filt
    return combined_filter

def indicator_defined_targets_months():
    """annotates a queryset of indicators with the number of months their targets cover
        (number of targets * months in period) for time-aware target frequencies
        used by the program level get_defined_targets filter"""
    cases = []
    for frequency, month_count in TIME_AWARE_FREQUENCIES:
        cases.append(
            models.When(
                target_frequency=frequency,
                then=models.ExpressionWrapper(
                    (models.F('defined_targets') * month_count),
                    output_field=models.IntegerField()
                )
            )
        )
    return models.Case(
        *cases, default=models.Value(None, output_field=models.IntegerField(null=True))
        )

def program_get_defined_targets_filter():
    """returns a set of filters that filter out indicators that do not have all defined targets
        this version of the filter is for a program prefetch-related queryset, which does not have
        the program_months annotation, and instead requires the get_defined_targets_months annotation"""
    filters = []
    # LOP indicators require a defined lop_target:
    filters.append(models.Q(target_frequency=Indicator.LOP) & models.Q(lop_target__isnull=False))
    # MID_END indicators require 2 defined targets (mid and end):
    filters.append(models.Q(target_frequency=Indicator.MID_END) &
                   models.Q(defined_targets__isnull=False) &
                   models.Q(defined_targets__gte=2))
    # EVENT indicators require at least 1 defined target:
    filters.append(models.Q(target_frequency=Indicator.EVENT) &
                   models.Q(defined_targets__isnull=False) &
                   models.Q(defined_targets__gte=1))
    filters.append(models.Q(defined_targets_months__isnull=False) &
                   models.Q(defined_targets_months__gte=models.OuterRef('program_months')))
    combined_filter = filters.pop()
    for filt in filters:
        combined_filter |= filt
    return combined_filter


def program_all_targets_defined_annotation():
    """annotates a queryset of programs with whether all targets are defined for all indicators for that program"""
    targets_subquery = PeriodicTarget.objects.filter(
        indicator_id=models.OuterRef('pk')
    ).order_by().values('indicator_id').annotate(
        target_count=models.Count('pk')
    ).values('target_count')[:1]
    target_subquery = Indicator.objects.filter(
        program_id=models.OuterRef('pk')
    ).order_by().values('program_id').annotate(
        defined_targets=models.Subquery(
            targets_subquery,
            output_field=models.IntegerField()
        )
    ).annotate(defined_targets_months=indicator_defined_targets_months())
    return models.functions.Coalesce(
        models.Subquery(
            target_subquery.filter(
                program_get_defined_targets_filter()
            ).order_by().values('program_id').annotate(
                 all_defined_targets_count=models.Count('id')
            ).values('all_defined_targets_count')[:1],
            output_field=models.IntegerField()
        ), 0)



def program_results_annotation(total=True):
    """annotates a program with the count of indicators which have any reported results
        or the count of reported results for the program in total
        Total=True: all results for program, Total=False: number of indicators with results"""
    data_subquery = Result.objects.filter(
        indicator__program=models.OuterRef('pk')
    ).order_by().values('indicator__program').annotate(
        data_count=models.Count('indicator_id', distinct=total)).values('data_count')[:1]
    return models.functions.Coalesce(
        models.Subquery(
            data_subquery,
            output_field=models.IntegerField()
        ), 0)

def program_evidence_annotation():
    """annotates a program with the count of results for any of the program's indicators which have evidence"""
    cd = Result.objects.filter(
        indicator__program_id=models.OuterRef('pk')
    ).exclude(
        evidence_url=''
    ).order_by().values('indicator__program').annotate(evidence_count=models.Count('pk')).values('evidence_count')[:1]
    return models.functions.Coalesce(
        models.Subquery(
            cd,
            output_field=models.IntegerField()
        ), 0)

def program_scope_annotations(*annotations):
    """annotates a program's indicators prefetch query with the required annotations to report their on scope status"""
    indicators_subquery = Indicator.objects.select_related('program').all()
    if any(key in annotations for key in ['reporting', 'scope']):
        indicators_subquery = indicators_subquery.annotate(
            **indicator_lop_annotations()
        ).annotate(reporting=indicator_reporting_annotation())
    if 'scope' in annotations:
        indicators_subquery = indicators_subquery.annotate(
            lop_met_real=indicator_lop_met_real_annotation()
        ).annotate(
            over_under=indicator_over_under_annotation()
        )
    return models.Prefetch(
        'indicator_set', queryset=indicators_subquery, to_attr='scope_indicators'
        )

def indicator_results_count_annotation():
    """annotates an indicator queryset with the number of results associated with each indicator"""
    return models.functions.Coalesce(
        models.Subquery(
            Result.objects.filter(
                indicator=models.OuterRef('pk')
                ).order_by().values('indicator').annotate(
                    total_results=models.Count('id')
                ).values('total_results')[:1],
            output_field=models.IntegerField()
        ), 0)

def indicator_results_evidence_annotation():
    """annotates an indicator queryset with the number of results associated with each indicator that have
        either a Documentation or TolaTable as evidence"""
    return models.functions.Coalesce(
        models.Subquery(
            Result.objects.filter(
                indicator=models.OuterRef('pk')
                ).exclude(
                    evidence_url=''
                ).order_by().values('indicator').annotate(
                    total_results=models.Count('id')
                ).values('total_results')[:1],
            output_field=models.IntegerField()
        ), 0)


class MetricsIndicatorQuerySet(models.QuerySet, IndicatorSortingQSMixin):
    """QuerySet for indicators returned for Program Page with annotated metrics"""

    def with_annotations(self, *annotations):
        qs = self.all()
        if 'months' in annotations or 'targets' in annotations:
            # 'months' is for unit testing,
            # 'targets' because program_months is a prerequisite for measuring all_targets_defined
            qs = qs.annotate(program_months=indicator_get_program_months_annotation())
        if 'targets' in annotations:
            # sets all_targets_defined to True/False based on business rules
            qs = qs.annotate(defined_targets=models.Count('periodictargets'))
            defined_targets_filter = indicator_get_defined_targets_filter()
            qs = qs.annotate(
                all_targets_defined=models.Case(
                    models.When(
                        defined_targets_filter,
                        then=models.Value(True)
                    ),
                    default=models.Value(False),
                    output_field=models.BooleanField()
                )
            )
        if 'results' in annotations:
            # result count = count of results associated with indicator:
            qs = qs.annotate(results_count=indicator_results_count_annotation())
        if 'evidence' in annotations:
            # results with evidence count = count of results that have evidence associated
            qs = qs.annotate(results_with_evidence_count=indicator_results_evidence_annotation())
        if 'reporting' in annotations or 'scope' in annotations:
            # reporting indicates whether indicator should be counted towards on-scope reporting
            # note: "reporting" alone is for testing, scope relies on these annotations as a prerequisite
            qs = qs.annotate(**indicator_lop_annotations())
            qs = qs.annotate(reporting=indicator_reporting_annotation())
        if 'scope' in annotations:
            qs = qs.annotate(lop_met_real=indicator_lop_met_real_annotation())
            qs = qs.annotate(over_under=indicator_over_under_annotation())
        if 'table' in annotations:
            qs = qs.select_related('level')
        return qs

class MetricsIndicatorManager(models.Manager, IndicatorSortingManagerMixin):
    def get_queryset(self):
        return MetricsIndicatorQuerySet(self.model, using=self._db)

    def with_annotations(self, *annotations):
        return self.get_queryset().with_annotations(*annotations)

class MetricsIndicator(Indicator):
    """Indicator for reporting metrics to Program Page and HomePage"""
    class Meta:
        proxy = True

    objects = MetricsIndicatorManager()

    @property
    def has_reported_results(self):
        return self.results_count > 0

    @property
    def all_results_backed_up(self):
        return self.results_count == self.results_with_evidence_count

    @cached_property
    def cached_data_count(self):
        if hasattr(self, 'data_count'):
            return self.data_count
        return self.result_set.count()

class IPTTIndicatorQuerySet(models.QuerySet, IndicatorSortingQSMixin):
    """This overrides the count method because ONLY_FULL_GROUP_BY errors appear otherwise on this custom query"""
    def count(self):
        return self.values('id').aggregate(total=models.Count('id', distinct=True))['total']


class IPTTIndicatorManager(models.Manager, IndicatorSortingManagerMixin):
    """this is the general manager for all IPTT (annotated) indicators - generates totals over LOP"""

    def add_labels(self, qs):
        most_recent_level = Level.objects.filter(indicator__id=models.OuterRef('pk')).order_by('-id')
        return qs.annotate(
            level_name=models.Subquery(most_recent_level.values('name')[:1])
        )

    def add_scope_annotations(self, qs):
        # set the margins for reporting as over or under scope:
        over_scope = 1 + Indicator.ONSCOPE_MARGIN
        under_scope = 1 - Indicator.ONSCOPE_MARGIN
        return qs.annotate(
            # first establish the real lop-to-date progress against targets:
            lop_met_real=models.Case(
                models.When(
                    models.Q(lop_target_sum__isnull=True) |
                    models.Q(lop_actual_sum__isnull=True),
                    then=models.Value(None)
                    ),
                default=models.ExpressionWrapper(
                    models.F('lop_actual_sum') / models.F('lop_target_sum'),
                    output_field=models.FloatField()
                )
            )
        ).annotate(
            over_under=models.Case(
                # None for indicators missing targets or data:
                models.When(
                    lop_met_real__isnull=True,
                    then=models.Value(None)
                    ),
                models.When(
                    # over is negative if DOC is Negative
                    models.Q(lop_met_real__gt=over_scope) &
                    models.Q(direction_of_change=Indicator.DIRECTION_OF_CHANGE_NEGATIVE),
                    then=models.Value(-1)
                    ),
                models.When(
                    lop_met_real__gt=over_scope,
                    then=models.Value(1)
                ),
                models.When(
                    # under is positive if DOC is Negative:
                    models.Q(lop_met_real__lt=under_scope) &
                    models.Q(direction_of_change=Indicator.DIRECTION_OF_CHANGE_NEGATIVE),
                    then=models.Value(1)
                ),
                models.When(
                    lop_met_real__lt=under_scope,
                    then=models.Value(-1)
                ),
                default=models.Value(0),
                output_field=models.IntegerField(null=True)
            )
        )

    def get_queryset(self):
        return self._get_annotated_queryset()

    def _get_annotated_queryset(self, label=False, lop=False, report=False, scope=False):
        qs = IPTTIndicatorQuerySet(self.model, using=self._db)
        # add labels such as "level:"
        if label:
            qs = self.add_labels(qs)
        if lop:
            # add lop annotations (target_sum and actual_sum):
            lop_annotations = indicator_lop_annotations()
            qs = qs.annotate(**lop_annotations)
        if report:
            # add reporting annotations (whether this indicator should be counted for on-target reporting)
            qs = qs.annotate(reporting=indicator_reporting_annotation())
        if report and scope:
            # add over_under calculation:
            qs = self.add_scope_annotations(qs)
        return qs

class NoTargetsIndicatorManager(IPTTIndicatorManager):
    def periods(self, periods):
        """annotate a query with actual data sums for a set of time periods"""
        period_annotations = {}
        for c, period in enumerate(periods):
            date_range = "{0}-{1}".format(
                period['start_date'].strftime('%Y-%m-%d'),
                period['end_date'].strftime('%Y-%m-%d')
            )
            period_annotations[date_range] = models.Case(
                models.When(
                    unit_of_measure_type=Indicator.PERCENTAGE,
                    then=models.Subquery(
                        Result.objects.filter(
                            indicator_id=models.OuterRef('pk'),
                            date_collected__lte=period['end_date']
                        ).order_by('-date_collected').values('achieved')[:1],
                        output_field=models.FloatField()
                    )),
                default=models.Subquery(
                    Result.objects.filter(
                        indicator_id=models.OuterRef('pk'),
                        date_collected__lte=period['end_date']
                    ).filter(
                        models.Q(date_collected__gte=period['start_date']) |
                        models.Q(indicator__is_cumulative=True)
                    ).order_by().values('indicator_id').annotate(
                        total=models.Sum('achieved')).values('total'),
                    output_field=models.FloatField())
            )
            period_annotations["period_{0}".format(c)] = models.Value(
                date_range, output_field=models.CharField())
        return self.get_queryset().annotate(**period_annotations)

    def get_queryset(self):
        # pylint: disable=E1124
        qs = self._get_annotated_queryset(label=True, lop=True)
        return qs


class WithTargetsIndicatorManager(IPTTIndicatorManager):
    """Manager for Indicator with PeriodicTargets and Results

    automatically annotates for lop target and actual lop sum of results
    also can self-annotate for periodic target and actual sum
    returns % met for the above"""

    def get_target_prefetch(self):
        # inner query to apply target_id to results within target range
        target_inner_query = PeriodicTarget.objects.filter(
            indicator_id=models.OuterRef('indicator_id'),
            start_date__lte=models.OuterRef('date_collected'),
            end_date__gte=models.OuterRef('date_collected')
        ).order_by().values('id')[:1]
        # inner query to collect data annotated by target_id
        data_with_periods_non_cumulative = Result.objects.filter(
            indicator_id=models.OuterRef('indicator_id')
        ).annotate(
            target_id=models.Subquery(target_inner_query)
        ).filter(
            target_id=models.OuterRef('id')
        ).order_by().values('target_id')
        data_with_periods_cumulative = Result.objects.filter(
            indicator_id=models.OuterRef('indicator_id'),
            date_collected__lte=models.OuterRef('end_date')
        ).order_by().values('indicator_id')
        # targets with data sums attached
        targets = PeriodicTarget.objects.annotate(
            data_sum=models.Case(
                models.When(
                    indicator__unit_of_measure_type=Indicator.PERCENTAGE,
                    then=models.Subquery(
                        data_with_periods_non_cumulative.order_by(
                            '-date_collected'
                            ).values('achieved')[:1],
                        output_field=models.FloatField()
                    )
                ),
                models.When(
                    indicator__is_cumulative=True,
                    then=models.Subquery(
                        data_with_periods_cumulative.annotate(
                            total=models.Sum('achieved')
                        ).values('total'),
                        output_field=models.FloatField()
                    )
                ),
                default=models.Subquery(
                    data_with_periods_non_cumulative.annotate(
                        total=models.Sum('achieved')
                    ).values('total'),
                    output_field=models.FloatField()
                )
            )
        ).annotate(
            met_real=models.ExpressionWrapper(
                models.F('data_sum')/models.F('target'),
                output_field=models.FloatField()
            ),
            met=models.ExpressionWrapper(
                Concat(Round(models.F('data_sum')*100/models.F('target')), models.Value("%")),
                output_field=models.CharField()
            )
        ).annotate(
            within_target_range=models.Case(
                models.When(
                    met_real__gt=1.15,
                    then=models.Case(
                        models.When(
                            indicator__direction_of_change=Indicator.DIRECTION_OF_CHANGE_NEGATIVE,
                            then=models.Value(-1)
                        ),
                        default=models.Value(1)
                    )
                ),
                models.When(
                    met_real__lt=0.85,
                    then=models.Case(
                        models.When(
                            indicator__direction_of_change=Indicator.DIRECTION_OF_CHANGE_NEGATIVE,
                            then=models.Value(1)
                        ),
                        default=models.Value(-1)
                    )
                ),
                models.When(
                    met_real__isnull=True,
                    then=models.Value(None)
                ),
                default=models.Value(0),
                output_field=models.IntegerField()
            )
        )
        prefetch = models.Prefetch(
            'periodictargets',
            queryset=targets,
            to_attr='data_targets'
        )
        return prefetch

    def get_queryset(self):
        # pylint: disable=E1124
        qs = self._get_annotated_queryset(label=True, lop=True).prefetch_related(
            self.get_target_prefetch()
        )
        return qs

class WithMetricsIndicatorManager(IPTTIndicatorManager):
    """queryset annotated to provide counts to the with_metrics Program call

    Attributes used by program page for filtering:
        indicator.reporting: T/F whether it is counted towards scope
        indicator.on_scope: 1/0/-1 (1=high, 0=on-target, -1=low)
        indicator.all_targets_defined: T/F whether all targets are defined
        indicator.has_reported_results: T/F indicator has SOME results reported
        indicator.all_results_backed_up: T/F
            # True = either has targets and results and all results have evidence, or has no results,
            # False = has targets AND results AND at least one result is missing evidence
        """

    def with_filter_labels(self, program):
        """Booleans for program page filters:

            indicator.reporting and on_scope are part of IPTTIndicatorManager"""
        qs = self.get_queryset()
        defined_targets_filter = get_defined_targets_filter(program)
        qs = qs.annotate(
            all_targets_defined=models.Case(
                models.When(
                    defined_targets_filter,
                    then=models.Value(True)
                ),
                default=models.Value(False),
                output_field=models.BooleanField()
            )
        )
        return qs

    def get_evidence_count(self, qs):
        """annotates qs with evidence_count= # of results that have evidence, and all_results_backed_up=Boolean"""
        data_with_evidence = Result.objects.filter(
            models.Q(indicator_id=models.OuterRef('pk')) |
            models.Q(periodic_target__indicator_id=models.OuterRef('pk')),
        ).exclude(
            evidence_url=''
        ).order_by().values('indicator_id')
        qs = qs.annotate(
            evidence_count=models.functions.Coalesce(
                models.Subquery(
                    data_with_evidence.annotate(
                        total_count=models.Count('date_collected')
                        ).order_by().values('total_count')[:1],
                    output_field=models.IntegerField()
                ), 0)
        )
        qs = qs.annotate(
            all_results_backed_up=models.Case(
                models.When(
                    # if no results, then it isn't "missing" data, so we count this as all_backed_up
                    models.Q(reported_results=0) |
                    models.Q(
                        #models.Q(reported_results__isnull=False) &
                        models.Q(evidence_count__isnull=False) &
                        models.Q(evidence_count=models.F('reported_results'))
                        ),
                    then=models.Value(True)
                ),
                default=models.Value(False),
                output_field=models.BooleanField()
            )
        )
        return qs

    def get_defined_targets(self, qs):
        periodic_targets_with_target_values = PeriodicTarget.objects.filter(
            indicator_id=models.OuterRef('pk'),
            target__isnull=False
        ).order_by().values('indicator_id')
        qs = qs.annotate(
            defined_targets=models.functions.Coalesce(
                models.Subquery(
                    periodic_targets_with_target_values.annotate(
                        target_count=models.Count('period')).values('target_count')[:1],
                    output_field=models.IntegerField()
                ), 0)
        )
        return qs

    def get_reported_results(self, qs):
        results_with_achieved_values = Result.objects.filter(
            models.Q(indicator_id=models.OuterRef('pk')),
            models.Q(achieved__isnull=False)
        ).order_by().values('indicator_id')
        qs = qs.annotate(
            reported_results=models.functions.Coalesce( # coalesce to return 0 if the subquery is empty (not None)
                models.Subquery(
                    results_with_achieved_values.annotate(
                        result_count=models.Count('date_collected')).values('result_count')[:1],
                    output_field=models.IntegerField()
                ), 0)
        ).annotate(
            has_reported_results=models.Case(
                models.When(
                    reported_results__gte=1,
                    then=models.Value(True)
                ),
                default=models.Value(False),
                output_field=models.BooleanField()
            ))
        return qs

    def get_queryset(self):
        qs = self._get_annotated_queryset(lop=True, report=True, scope=True)
        qs = self.get_defined_targets(qs)
        qs = self.get_reported_results(qs)
        qs = self.get_evidence_count(qs)
        return qs

class IPTTIndicator(Indicator):
    SEPARATOR = '/' # this is used by CSV output as a default joiner for multiple values
    class Meta:
        proxy = True

    notargets = NoTargetsIndicatorManager()
    withtargets = WithTargetsIndicatorManager()
    with_metrics = WithMetricsIndicatorManager()

    @property
    def lop_met_target(self):
        return str(int(round(float(self.lop_actual_sum)*100/self.lop_target_sum))) + "%"

    @property
    def timeperiods(self):
        if self.unit_of_measure_type == self.PERCENTAGE and not self.is_cumulative:
            return
        else:
            count = 0
            while getattr(self, "period_{0}".format(count), None) is not None:
                yield getattr(self, "period_{0}".format(count))
                count += 1


class ProgramMetricsQuerySet(models.QuerySet):
    def count(self):
        return self.values('id').aggregate(total=models.Count('id', distinct=True))['total']


class ProgramForProgramPageManager(models.Manager):
    def get_queryset(self):
        qs = ProgramMetricsQuerySet(self.model, using=self._db)
        return qs

class ProgramForHomePageQuerySet(ProgramMetricsQuerySet):
    @property
    def program_count(self):
        return self.count()

    @property
    def all_targets_defined_for_all_indicators_count(self):
        return len([program for program in self if program.all_targets_defined_for_all_indicators])

    @property
    def indicators_count(self):
        return sum([program.indicator_count for program in self])

    @property
    def results_count(self):
        return sum([program.total_results_count for program in self])

    @property
    def indicators_with_results_count(self):
        return sum([program.reported_results_count for program in self])

    @property
    def results_with_evidence_count(self):
        return sum([program.results_evidence_count for program in self])

    def with_annotations(self, *annotations):
        if not annotations:
            annotations = ['targets', 'results', 'evidence', 'scope']
        qs = self
        if any(key in annotations for key in ['count', 'targets', 'results', 'evidence', 'reporting', 'scope']):
            qs = qs.annotate(indicator_count=models.Count('indicator'))
        if any(key in annotations for key in ['results_count', 'results', 'evidence']):
            qs = qs.annotate(reported_results_sum=program_results_annotation(False))
        if 'targets' in annotations:
            qs = qs.annotate(program_months=program_get_program_months_annotation())
            qs = qs.annotate(targets_defined_count=program_all_targets_defined_annotation())
        if 'results' in annotations:
            qs = qs.annotate(total_results_count=program_results_annotation(False))
            qs = qs.annotate(reported_results_count=program_results_annotation(True))
        if 'evidence' in annotations:
            qs = qs.annotate(results_evidence_count=program_evidence_annotation())
        if 'reporting' in annotations or 'scope' in annotations:
            qs = qs.prefetch_related(program_scope_annotations(*annotations))
        return qs

class ProgramForHomePageManager(models.Manager):
    def get_queryset(self):
        qs = ProgramForHomePageQuerySet(self.model, using=self._db)
        return qs

    def with_annotations(self, *annotations):
        return self.get_queryset().with_annotations(*annotations)

class ProgramWithMetrics(wf_models.Program):
    metrics_set = None
    cached_annotated_indicators = None
    program_page = ProgramForProgramPageManager()
    home_page = ProgramForHomePageManager()
    indicator_filters = {}

    class Meta:
        proxy = True

    def set_metrics(self, indicators=None):
        if indicators is None:
            indicators = self.annotated_indicators
        self.metrics_set = {
            'indicator_count': len(indicators),
            'targets_defined': len(
                [indicator for indicator in indicators
                 if indicator.all_targets_defined]
            ),
            'reported_results': len(
                [indicator for indicator in indicators
                 if indicator.has_reported_results]
            ),
            'results_evidence': sum(
                [indicator.results_with_evidence_count for indicator in indicators]
            ),
            'results_count': sum(
                [indicator.results_count for indicator in indicators]
            ),
            'needs_evidence': len(
                [indicator for indicator in indicators
                 if indicator.results_count > indicator.results_with_evidence_count]
            ),
        }

    @cached_property
    def all_targets_defined_for_all_indicators(self):
        """note: we define a program with 0 indicators as _not_ having all targets defined"""
        return self.indicator_count == self.metrics['targets_defined'] and self.indicator_count != 0

    @cached_property
    def indicator_count(self):
        return self.indicator_set.count()

    @cached_property
    def annotated_indicators(self):
        if self.cached_annotated_indicators is None:
            self.indicator_filters['program'] = self
            program_page_annotations = ['targets', 'results', 'evidence', 'scope', 'table']
            self.cached_annotated_indicators = MetricsIndicator.objects.filter(
                **self.indicator_filters
            ).with_annotations(
                *program_page_annotations
            ).with_logframe_sorting()
        return self.cached_annotated_indicators


    @property
    def percent_complete(self):
        if self.reporting_period_end is None or self.reporting_period_start is None:
            return -1 # otherwise the UI might show "None% complete"
        if self.reporting_period_start > datetime.date.today():
            return 0
        total_days = (self.reporting_period_end - self.reporting_period_start).days
        complete = (datetime.date.today() - self.reporting_period_start).days
        return int(round(float(complete)*100/total_days)) if complete < total_days else 100

    @property
    def metrics(self):
        """ 'reported_results': # of indicators with any results
            'targets_defined': # of indicators with all targets defined
            'indicator_count': # of indicators total
            'results_evidence': # of _results_ with evidence provided
            'results_count': # of_results_ total for all indicators in the program
        """
        if not hasattr(self, 'targets_defined_count'):
            if self.metrics_set is None:
                self.set_metrics()
            return self.metrics_set
        if self.indicator_count == 0:
            return {
                'reported_results': 0,
                'targets_defined': 0,
                'indicator_count': 0,
                'results_evidence': 0,
                'results_count': 0,
                'needs_evidence': 0
            }
        return {
            'reported_results': getattr(self, 'reported_results_count', None),
            'targets_defined': getattr(self, 'targets_defined_count', None),
            'indicator_count': getattr(self, 'indicator_count', None),
            'results_evidence': getattr(self, 'results_evidence_count', None),
            'results_count': getattr(self, 'reported_results_sum', None),
            'needs_evidence': getattr(self, 'needs_evidence_count', None)
        }

    @property
    def scope_counts(self):
        if self.indicator_count == 0:
            return {
                'indicator_count': 0,
                'nonreporting_count': 0,
                'reporting_count': 0,
                'low': 0,
                'on_scope': 0,
                'high': 0
            }
        if hasattr(self, 'scope_indicators'):
            scope_indicators = self.scope_indicators
        else:
            scope_indicators = self.annotated_indicators
        return {
            'indicator_count': getattr(self, 'indicator_count', None),
            'nonreporting_count': len(
                [indicator for indicator in scope_indicators if not indicator.reporting]
            ),
            'reporting_count': len(
                [indicator for indicator in scope_indicators if indicator.reporting]
            ),

            'low': len(
                [indicator for indicator in scope_indicators
                 if indicator.reporting and hasattr(indicator, 'over_under') and indicator.over_under == -1]
                ),
            'on_scope': len(
                [indicator for indicator in scope_indicators
                 if indicator.reporting and hasattr(indicator, 'over_under') and indicator.over_under == 0]
                ),
            'high': len(
                [indicator for indicator in scope_indicators
                 if indicator.reporting and hasattr(indicator, 'over_under') and indicator.over_under == 1]
                ),
        }
