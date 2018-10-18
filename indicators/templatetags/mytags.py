import simplejson
import re
from datetime import datetime
from django.core.serializers import serialize
from django import template
from django.db.models import QuerySet
from django.utils.translation import ugettext_lazy as _
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
    if hasattr(obj, attr):
        return getattr(obj, attr)
    elif hasattr(obj, 'has_key') and attr in obj:
        return obj.get(attr)
    else:
        return None


@register.inclusion_tag('indicators/tags/gauge-tank.html')
def gauge_tank(filled, label, detail):
    return {
        'filled': filled,
        'not_filled': 100 - filled,
        'label': label,
        'detail': detail,
        'ticks': list(range(1,11)),
        'margin': int(Indicator.ONSCOPE_MARGIN * 100),
    }


@register.inclusion_tag('indicators/tags/gauge-band.html')
def gauge_band(high, on_scope, low):
    return {
        'high': high,
        'on_scope': on_scope,
        'low': low,
        'ticks': list(range(1,11)),
        'margin': int(Indicator.ONSCOPE_MARGIN * 100),
    }
