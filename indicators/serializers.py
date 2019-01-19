from rest_framework import serializers

from workflow.models import Program
from indicators.models import PeriodicTarget, Result, Indicator, Level
from django.db.models import Sum

class ResultSerializer(serializers.ModelSerializer):
    cumsum = serializers.SerializerMethodField()

    class Meta:
        model = Result
        fields = ('id', 'program', 'indicator', 'periodic_target', 'achieved',
                  'cumsum', 'date_collected', 'evidence', 'tola_table',
                  'agreement', 'complete', 'site', 'create_date', 'edit_date')

    def get_cumsum(self, obj):
        total_achieved = Result.objects.filter(
            indicator=obj.indicator,
            create_date__lt=obj.create_date).aggregate(Sum('achieved'))['achieved__sum']

        if total_achieved is None:
            total_achieved = 0
        total_achieved = total_achieved + obj.achieved
        return total_achieved


class PeriodictargetSerializer(serializers.ModelSerializer):
    result_set = ResultSerializer(many=True, read_only=True)
    result__achieved__sum = serializers.IntegerField()
    cumulative_sum = serializers.IntegerField()

    class Meta:
        model = PeriodicTarget
        fields = ('id', 'indicator', 'period', 'target', 'start_date',
                  'end_date', 'customsort', 'create_date', 'edit_date',
                  'result_set', 'result__achieved__sum',
                  'cumulative_sum')


class LevelSerializer(serializers.ModelSerializer):
    """
    Level serializer for Program Page
    """
    class Meta:
        model = Level
        fields = [
            'id',
            'name'
        ]


class IndicatorSerializer(serializers.ModelSerializer):
    """
    Serializer specific to the Program Page
    """
    reporting = serializers.BooleanField()
    all_targets_defined = serializers.IntegerField()
    results_count = serializers.IntegerField()
    results_with_evidence_count = serializers.IntegerField()
    over_under = serializers.IntegerField()
    target_period_last_end_date = serializers.DateField()
    level = LevelSerializer(read_only=True)

    class Meta:
        model = Indicator
        fields = [
            'id',
            'name',
            'number',
            'level',
            'unit_of_measure',
            'baseline_display',
            'lop_target_display',
            'key_performance_indicator',
            'just_created',

            # DB annotations
            #  whether indicator progress towards targets is reported
            #  (min. one target period complete, one result reported):
            'reporting',
            'all_targets_defined',  # whether all targets are defined for this indicator
            'results_count',
            'results_with_evidence_count',
            'target_period_last_end_date', # last end date of last target period, for time-aware indicators
            'over_under',  # indicator progress towards targets (1: over, 0: within 15% of target, -1: under, "None": non reporting
        ]


class ProgramSerializer(serializers.ModelSerializer):
    """
    Serializer specific to the Program Page
    """
    class Meta:
        model = Program
        fields = [
            'id',
            'does_it_need_additional_target_periods',
            'reporting_period_end',
        ]
