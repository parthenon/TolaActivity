import math
import simplejson
from datetime import datetime
from django.core.serializers import serialize
from django import template
from django.db.models import QuerySet
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
from indicators.models import Indicator
from django.conf import settings

register = template.Library()

@register.filter('convert2dateobject')
def convert2dateobject(value):
    try:
        return datetime.strptime(value, '%Y-%m-%d')
    except AttributeError:
        return value
    except Exception:
        return value

@register.filter
def concat_string(value1, value2):
    """
    concatenates two strings together
    Usage: <a href="{{ SOME_LINK|concat_string:object.pk }}">LINK</a>
    """
    return "%s%s" % (value1, value2)

@register.filter('jsonify')
def jsonify(object):
    if isinstance(object, QuerySet):
        return serialize('json', object)
    return simplejson.dumps(object)


@register.filter('symbolize_change')
def symbolize_change(value):
    """
    Returns corresponding math symbol for Direction of change
    Usage:
    {{ indicator.direction_of_change|symbolize_change}}
    """
    if value == Indicator.DIRECTION_OF_CHANGE_NEGATIVE:
        return _("-")

    if value == Indicator.DIRECTION_OF_CHANGE_POSITIVE:
        return _("+")

    return _("N/A")


@register.filter('target_frequency_label')
def target_frequency_label(value):
    """
    Returns corresponding math symbol for Direction of change
    Usage:
    {{ indicator.target_frequency|target_frequency_label}}
    """
    try:
        value = value - 1
        return Indicator.TARGET_FREQUENCIES[value][1]
    except Exception:
        return value


@register.filter('symbolize_measuretype')
def symbolize_measuretype(value):
    """
    Returns corresponding math symbol for Direction of change
    Usage:
    {{ indicator.direction_of_change|symbolize_measuretype}}
    """
    if value == Indicator.NUMBER:
        return _("#")

    if value == Indicator.PERCENTAGE:
        return _("%")

    return ""


@register.filter('hash')
def hash(obj, attr):
    """
    Extracts an attributes's value from the object
    Usage:
    {{ object|getattr:attribute }}
    """
    # try:
    #     return obj.get(attr)
    # except Exception:
    #     return None
    if isinstance(attr, unicode) and hasattr(obj, attr.encode('utf-8')):
        return getattr(obj, attr.encode('utf-8'))
    elif isinstance(attr, str) and hasattr(obj, attr):
        return getattr(obj, attr)
    elif hasattr(obj, 'has_key') and attr in obj:
        return obj.get(attr)
    else:
        return None


@register.filter('js', is_safe=True)
def js(obj):
    """
    Render out JSON to get context data to JS

    Ex.

        <script type="text/javascript">
            var someVar = {{ some_var | js }};
        </script>
    """
    return mark_safe(jsonify(obj))


@register.inclusion_tag('indicators/tags/gauge-tank.html', takes_context=True)
def gauge_tank(context, metric, has_filters=True):
    labels = {
        'targets_defined' : {
            'title': _('Indicators with targets'),
            'filled_label': _('have targets'),
            'unfilled_label': _('no targets'),
            'cta': _('Add missing targets'),
            'filter_title': _('have missing targets'),
            'empty': _('No targets'),
            'help_text': _(''), # currently unused
            'data_target': 'defined-targets',
        },
        'reported_results' : {
            'title': _('Indicators with results'),
            'filled_label': _('have results'),
            'unfilled_label': _('no results'),
            'cta': _('Add missing results'),
            'filter_title': _('have missing results'),
            'empty': _('No results'),
            'help_text': _(''), # currently unused
            'data_target': 'reported-results',
        },
        'results_evidence': {
            'title': _('Results with evidence'),
            'filled_label': _('have evidence'),
            'unfilled_label': _('no evidence'),
            'cta': _('Add missing evidence'),
            'filter_title': _('have missing evidence'),
            'empty': _('No evidence'),
            'help_text': _(''), # currently unused
            'data_target': 'has-evidence',
        },
    }
    program = context['program']
    filled_value = program.metrics[metric]
    results_count = program.metrics['results_count']
    indicator_count = program.metrics['indicator_count']
    unfilled_value = indicator_count - filled_value
    filter_title_count = program.metrics['needs_evidence'] if metric == 'results_evidence' else unfilled_value
    denominator = results_count if metric == 'results_evidence' else indicator_count
    filled_percent = int(round(float(filled_value*100)/denominator)) if denominator > 0 else 0
    tick_count = 10
    return {
        'program': program,
        'title': labels[metric]['title'],
        'data_target': labels[metric]['data_target'],
        'id_tag': metric,
        'filled_value': filled_value,
        'unfilled_value': unfilled_value,
        'indicator_count': indicator_count,
        'results_count': results_count,
        'filled_percent': filled_percent,
        'unfilled_percent': 100 - filled_percent,
        'filled_label': labels[metric]['filled_label'],
        'unfilled_label': labels[metric]['unfilled_label'],
        'ticks': list(range(1,tick_count+1)),
        'cta': labels[metric]['cta'],
        'filter_title': labels[metric]['filter_title'],
        'has_filters': has_filters,
        'filter_title_count': filter_title_count,
        'empty_label': labels[metric]['empty'],
        'help_text': labels[metric]['help_text'],
    }

@register.inclusion_tag('indicators/tags/gauge-tank-small.html', takes_context=True)
def gauge_tank_small(context, metric):
    labels = {
        'targets_defined': {
            'filled_label': _('programs have all targets defined'),
            'help_text': _('Each indicator must have a target frequency selected and targets entered for all periods'),
        },
        'reported_results': {
            'filled_label': _('indicators have reported results'),
            'help_text': ('Each indicator must have at least one reported result.'),
        },
        'results_evidence': {
            'filled_label': _('results are backed up with evidence'),
            'help_text': ('Each result must include a link to an evidence file or folder.'),
        },
    }
    unfilled_percent = 25
    filled_percent = 75
    tick_count = 10

    return {
        'unfilled_percent': unfilled_percent,
        'filled_percent': filled_percent,
        'filled_label': labels[metric]['filled_label'],
        'help_text': labels[metric]['help_text'],
        'ticks': list(range(1,tick_count+1)),
    }



@register.inclusion_tag('indicators/tags/gauge-band.html', takes_context=True)
def gauge_band(context, has_filters=True):
    program = context['program']
    scope_counts = program.scope_counts
    denominator = scope_counts['indicator_count']
    if denominator == 0:
        make_percent = lambda x: 0
    else:
        make_percent = lambda x: int(round(float(x*100)/denominator))
    scope_percents = {
        'high': make_percent(scope_counts['high']),
        'on_scope': make_percent(scope_counts['on_scope']),
        'low': make_percent(scope_counts['low']),
        'nonreporting': make_percent(scope_counts['nonreporting_count'])
    }
    return {
        'scope_percents': scope_percents,
        'scope_counts': scope_counts,
        'ticks': list(range(1,11)),
        'margin': int(Indicator.ONSCOPE_MARGIN * 100),
        'has_filters': has_filters,
    }


@register.inclusion_tag('indicators/tags/program-complete.html', takes_context=True)
def program_complete(context):
    """
    Renders percentage complete with a graphic icon.
    Takes percent_complete as an integer percentage value
    """
    program = context['program']
    return {
        'program.id': program.id,
        'program.start_date': program.start_date,
        'program.end_date': program.end_date,
        'program.reporting_period_start': program.reporting_period_start,
        'program.percent_complete': program.percent_complete,
    }
