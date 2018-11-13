from django.db.models import Sum

from rest_framework import serializers

from workflow.models import Program
from .models import PeriodicTarget, CollectedData, Indicator


class CollecteddataSerializer(serializers.ModelSerializer):
    cumsum = serializers.SerializerMethodField()

    class Meta:
        model = CollectedData
        fields = ('id', 'program', 'indicator', 'periodic_target', 'achieved',
                  'cumsum', 'date_collected', 'evidence', 'tola_table',
                  'agreement', 'complete', 'site', 'create_date', 'edit_date')

    def get_cumsum(self, obj):
      total_achieved = CollectedData.objects.filter(
                indicator=obj.indicator,
                create_date__lt=obj.create_date)\
            .aggregate(Sum('achieved'))['achieved__sum']

      if total_achieved is None:
            total_achieved = 0
      total_achieved = total_achieved + obj.achieved
      return total_achieved


class PeriodictargetSerializer(serializers.ModelSerializer):
    collecteddata_set = CollecteddataSerializer(many=True, read_only=True)
    collecteddata__achieved__sum = serializers.IntegerField()
    cumulative_sum = serializers.IntegerField()

    class Meta:
        model = PeriodicTarget
        fields = ('id', 'indicator', 'period', 'target', 'start_date',
                  'end_date', 'customsort', 'create_date', 'edit_date',
                  'collecteddata_set', 'collecteddata__achieved__sum',
                  'cumulative_sum')


class IndicatorSerializer(serializers.ModelSerializer):
    """
    Serializer specific to the Program Page
    """
    reporting = serializers.BooleanField()
    defined_targets = serializers.IntegerField()
    reported_results = serializers.IntegerField()
    all_results_backed_up = serializers.BooleanField()
    over_under = serializers.IntegerField()

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
            'reporting',  # whether indicator progress towards targets is reported (min. one target period complete, one result reported)
            'defined_targets',  # whether all targets are defined for this indicator
            'reported_results',  # whether any collecteddata is reported for this indicator
            'all_results_backed_up',
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
        ]
