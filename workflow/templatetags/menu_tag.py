from collections import OrderedDict

from django import template
from workflow.models import Program

register = template.Library()


@register.inclusion_tag('workflow/tags/program_menu.html', takes_context=True)
def program_menu(context):
    request = context['request']
    try:
        countries = request.user.tola_user.countries.all()
    except AttributeError:
        countries = []
    programs = Program.objects.filter(funding_status="Funded", country__in=countries).prefetch_related('country').distinct()

    programs_by_country = OrderedDict((country.country, []) for country in countries)

    for program in programs:
        for country in program.country.all():
            # a program can be in multiple countries, including a country a user is not privy to
            if country.country in programs_by_country:
                programs_by_country[country.country].append(program)

    return {
        'programs': programs,
        'countries': countries,
        'programs_by_country': programs_by_country,
    }
