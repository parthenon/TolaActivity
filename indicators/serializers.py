from rest_framework import serializers

from workflow.models import Program
from indicators.models import PeriodicTarget, Result, Indicator
from django.db.models import Sum


class IndicatorSerializer(serializers.ModelSerializer):
    """
    Serializer specific to the Program Page
    """
    reporting = serializers.BooleanField()
    all_targets_defined = serializers.IntegerField()
    results_count = serializers.IntegerField()
    results_with_evidence_count = serializers.IntegerField()
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
            #  whether indicator progress towards targets is reported
            #  (min. one target period complete, one result reported):
            'reporting',
            'all_targets_defined',  # whether all targets are defined for this indicator
            'results_count',
            'results_with_evidence_count',
            #  indicator progress towards targets (1: over, 0: within 15% of target, -1: under, "None": non reporting:
            'over_under',
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
