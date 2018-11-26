import dateparser
from django.conf import settings
from datetime import datetime
from functools import partial
from django.core.exceptions import ValidationError
from django.db.models import Q
from django import forms
from django.forms.fields import DateField
from django.utils.translation import ugettext_lazy as _
from django.utils import formats, translation
from workflow.models import (
    Program, SiteProfile, Documentation, ProjectComplete, TolaUser, Sector
)
from tola.util import getCountry
from indicators.models import (
    Indicator, PeriodicTarget, CollectedData, Objective, StrategicObjective,
    TolaTable, DisaggregationType, Level, IndicatorType,
    PinnedReport)
from indicators.widgets import DataAttributesSelect

locale_format = formats.get_format('DATE_INPUT_FORMATS', lang=translation.get_language())[-1]

class DatePicker(forms.DateInput):
    """
    Use in form to create a Jquery datepicker element
    Usage:
        self.fields['some_date_field'].widget = DatePicker.DateInput()
    """
    template_name = 'datepicker.html'
    DateInput = partial(forms.DateInput, {'class': 'datepicker'})


class LocaleDateField(DateField):
    def to_python(self, value):
        if value in self.empty_values:
            return None
        try:
            return dateparser.parse(value).date()
        except (AttributeError):
            raise ValidationError(
                self.error_messages['invalid'], code='invalid')



class IndicatorForm(forms.ModelForm):
    unit_of_measure_type = forms.ChoiceField(
        choices=Indicator.UNIT_OF_MEASURE_TYPES,
        widget=forms.RadioSelect(),
    )

    class Meta:
        model = Indicator
        exclude = ['create_date', 'edit_date']
        widgets = {
            'definition': forms.Textarea(attrs={'rows': 4}),
            'justification': forms.Textarea(attrs={'rows': 4}),
            'quality_assurance': forms.Textarea(attrs={'rows': 4}),
            'data_issues': forms.Textarea(attrs={'rows': 4}),
            'indicator_changes': forms.Textarea(attrs={'rows': 4}),
            'comments': forms.Textarea(attrs={'rows': 4}),
            'notes': forms.Textarea(attrs={'rows': 4}),
            'rationale_for_target': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        indicator = kwargs.get('instance', None)
        if not indicator.unit_of_measure_type:
            kwargs['initial']['unit_of_measure_type'] = Indicator.UNIT_OF_MEASURE_TYPES[0][0]
        self.request = kwargs.pop('request')
        self.programval = kwargs.pop('program')

        super(IndicatorForm, self).__init__(*args, **kwargs)

        countries = getCountry(self.request.user)
        self.fields['disaggregation'].queryset = DisaggregationType.objects\
            .filter(country__in=countries, standard=False)
        self.fields['program'].queryset = Program.objects.filter(
            funding_status="Funded", country__in=countries)
        self.fields['objectives'].queryset = Objective.objects.filter(program__id__in=[self.programval.id])
        self.fields['strategic_objectives'].queryset = StrategicObjective.objects.filter(country__in=countries)
        self.fields['approved_by'].queryset = TolaUser.objects.filter(country__in=countries).distinct()
        self.fields['approval_submitted_by'].queryset = TolaUser.objects.filter(country__in=countries).distinct()
        self.fields['name'].label = _('Indicator Name')
        self.fields['name'].required = True
        self.fields['unit_of_measure'].required = True
        self.fields['target_frequency'].required = True
        self.fields['target_frequency_start'].widget.attrs['class'] = 'monthPicker'
        # self.fields['is_cumulative'].widget = forms.RadioSelect()
        if self.instance.target_frequency and self.instance.target_frequency != Indicator.LOP:
            self.fields['target_frequency'].widget.attrs['readonly'] = True


class CollectedDataForm(forms.ModelForm):

    class Meta:
        model = CollectedData
        exclude = ['create_date', 'edit_date']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def clean_date_collected(self):
        date_collected = self.cleaned_data['date_collected']
        date_collected = datetime.strftime(date_collected, '%Y-%m-%d')
        return date_collected

    program2 = forms.CharField(
        widget=forms.TextInput(
            attrs={'readonly': True, 'label': _('Program')}
        )
    )
    indicator2 = forms.CharField(
        widget=forms.TextInput(
            attrs={'readonly': True, 'label': _('Indicator')}
        )
    )
    target_frequency = forms.CharField()
    date_collected = forms.DateField(
        widget=DatePicker.DateInput(format=locale_format),
        # TODO: this field outputs dates in non-ISO formats in Spanish & French
        localize=True,
        required=True,
    )

    def __init__(self, *args, **kwargs):
        # instance = kwargs.get('instance', None)
        self.request = kwargs.pop('request')
        self.program = kwargs.pop('program')
        self.indicator = kwargs.pop('indicator', None)
        self.tola_table = kwargs.pop('tola_table')
        super(CollectedDataForm, self).__init__(*args, **kwargs)

        # override the program queryset to use request.user for country
        self.fields['evidence'].queryset = Documentation.objects\
            .filter(program=self.program)

        # override the program queryset to use request.user for country
        self.fields['complete'].queryset = ProjectComplete.objects\
            .filter(program=self.program)
        self.fields['complete'].label = _("Project")

        # only display Project field to existing users
        if not self.request.user.tola_user.allow_projects_access:
            self.fields.pop('complete')

        # override the program queryset to use request.user for country
        countries = getCountry(self.request.user)
        # self.fields['program'].queryset = Program.objects\
        #   .filter(funding_status="Funded", country__in=countries).distinct()
        try:
            int(self.program)
            self.program = Program.objects.get(id=self.program)
        except TypeError:
            pass

        # Django will deliver localized strings to the template but the form needs to be able to compare the date
        # entered to the start and end dates of each period.  Data attributes (attached to each option element) are
        # used to provide access to the start and end dates in ISO format, since they are easier to compare to than
        # the localized date strings.
        periodic_targets = PeriodicTarget.objects \
            .filter(indicator=self.indicator) \
            .order_by('customsort', 'create_date', 'period')
        data = {'data-start': {'': ''}, 'data-end': {'': ''}}
        choices = [('', '---------')]
        for pt in periodic_targets:
            data['data-start'].update({str(pt.id): pt.start_date})
            data['data-end'].update({str(pt.id): pt.end_date})
            choices.append((pt.id, str(pt)))
        self.fields['periodic_target'].widget = DataAttributesSelect(data=data, choices=choices)

        self.fields['program2'].initial = self.program
        self.fields['program2'].label = _("Program")

        try:
            int(self.indicator)
            self.indicator = Indicator.objects.get(id=self.indicator)
        except TypeError:
            pass

        self.fields['indicator2'].initial = self.indicator.name
        self.fields['indicator2'].label = _("Indicator")
        self.fields['program'].widget = forms.HiddenInput()
        self.fields['indicator'].widget = forms.HiddenInput()
        self.fields['target_frequency'].initial = self.indicator\
            .target_frequency
        self.fields['target_frequency'].widget = forms.HiddenInput()
        self.fields['site'].queryset = SiteProfile.objects\
            .filter(country__in=countries)
        self.fields['site'].label = _('Site')
        self.fields['tola_table'].queryset = TolaTable.objects\
            .filter(Q(owner=self.request.user) | Q(id=self.tola_table))
        self.fields['periodic_target'].label = _('Measure against target*')
        self.fields['achieved'].label = _('Actual value')
        self.fields['date_collected'].help_text = ' '
        self.fields['date_collected'].label = _('Date collected')


class ReportFormCommon(forms.Form):
    EMPTY = 0
    YEARS = Indicator.ANNUAL
    SEMIANNUAL = Indicator.SEMI_ANNUAL
    TRIANNUAL = Indicator.TRI_ANNUAL
    QUARTERS = Indicator.QUARTERLY
    MONTHS = Indicator.MONTHLY
    TIMEPERIODS_CHOICES = (
        (YEARS, _("Years")),
        (SEMIANNUAL, _("Semi-annual periods")),
        (TRIANNUAL, _("Tri-annual periods")),
        (QUARTERS, _("Quarters")),
        (MONTHS, _("Months"))
    )

    SHOW_ALL = 1
    MOST_RECENT = 2
    TIMEFRAME_CHOICES = (
        (SHOW_ALL, _("Show all")),
        (MOST_RECENT, _("Most recent"))
    )

    EMPTY_OPTION = (EMPTY, "---------")
    # combine the target_frequencies (except EVENT) and the EMPTY option
    TARGETPERIODS_CHOICES = (EMPTY_OPTION,) + Indicator.TARGET_FREQUENCIES[0:7]

    program = forms.ModelChoiceField(queryset=Program.objects.none())
    timeperiods = forms.ChoiceField(choices=TIMEPERIODS_CHOICES, required=False)
    targetperiods = forms.ChoiceField(choices=TARGETPERIODS_CHOICES, required=False)
    timeframe = forms.ChoiceField(choices=TIMEFRAME_CHOICES, widget=forms.RadioSelect(), required=False)
    numrecentperiods = forms.IntegerField(required=False)
    formprefix = forms.CharField(widget=forms.HiddenInput(), required=False)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        countries = getCountry(self.request.user)
        super(ReportFormCommon, self).__init__(*args, **kwargs)
        self.fields['program'].label = _("Program")
        self.fields['timeperiods'].label = _("Time periods")
        self.fields['numrecentperiods'].widget.attrs['placeholder'] = _("enter a number")
        self.fields['targetperiods'].label = _("Target periods")
        self.fields['program'].queryset = Program.objects \
            .filter(country__in=countries,
                    funding_status="Funded",
                    reporting_period_start__isnull=False,
                    reporting_period_end__isnull=False,
                    indicator__target_frequency__isnull=False,) \
            .exclude(indicator__isnull=True) \
            .distinct()


class IPTTReportQuickstartForm(ReportFormCommon):
    prefix = 'timeperiods'
    formprefix = forms.CharField(widget=forms.HiddenInput(), required=False)

    def __init__(self, *args, **kwargs):
        prefix = kwargs.pop('prefix')
        self.prefix = prefix if prefix is not None else self.prefix
        super(IPTTReportQuickstartForm, self).__init__(*args, **kwargs)
        self.fields['formprefix'].initial = self.prefix
        self.fields['timeframe'].initial = self.SHOW_ALL
        # self.fields['timeperiods'].widget = forms.HiddenInput()
        self.fields['timeperiods'].initial = Indicator.MONTHLY


class IPTTReportFilterForm(ReportFormCommon):
    level = forms.ModelMultipleChoiceField(queryset=Level.objects.none(), required=False, label=_('Levels'))
    ind_type = forms.ModelMultipleChoiceField(queryset=IndicatorType.objects.none(), required=False, label=_('Types'))
    sector = forms.ModelMultipleChoiceField(queryset=Sector.objects.none(), required=False, label=_('Sectors'))
    site = forms.ModelMultipleChoiceField(queryset=SiteProfile.objects.none(), required=False, label=_('Sites'))
    indicators = forms.ModelMultipleChoiceField(
        queryset=Indicator.objects.none(), required=False, label=_('Indicators'))

    def __init__(self, *args, **kwargs):
        program = kwargs.pop('program')
        periods_choices_start = kwargs.get('initial').get('period_choices_start') # TODO: localize this date
        periods_choices_end = kwargs.get('initial').get('period_choices_end') # TODO: localize this date

        target_frequencies = program.indicator_set.filter(target_frequency__isnull=False) \
            .exclude(target_frequency=Indicator.EVENT) \
            .values('target_frequency') \
            .distinct() \
            .order_by('target_frequency')

        target_frequency_choices = []
        for tp in target_frequencies:
            try:
                id = int(tp['target_frequency'])
                target_frequency_choices.append((id, Indicator.TARGET_FREQUENCIES[id-1][1]))
                # print("id={}, tf={}".format(id, Indicator.TARGET_FREQUENCIES[id]))
            except TypeError:
                pass

        first_year_first_daterange_key = kwargs.get('initial').get('period_start_initial')
        last_year_last_daterange_key = kwargs.get('initial').get('period_end_initial')

        super(IPTTReportFilterForm, self).__init__(*args, **kwargs)
        del self.fields['formprefix']
        level_ids = program.indicator_set.values(
            'level_id').distinct().order_by('level')

        self.fields['program'].initial = program
        self.fields['sector'].queryset = Sector.objects.filter(
            indicator__program=program).distinct()
        self.fields['level'].queryset = Level.objects.filter(id__in=level_ids).distinct().order_by('customsort')
        ind_type_ids = program.indicator_set.values(
            'indicator_type__id').distinct().order_by('indicator_type')
        self.fields['ind_type'].queryset = IndicatorType.objects.filter(id__in=ind_type_ids).distinct()
        self.fields['site'].queryset = program.get_sites()
        self.fields['indicators'].queryset = program.indicator_set.all()

        # Start and end periods dropdowns are updated dynamically
        self.fields['start_period'] = forms.ChoiceField(choices=periods_choices_start, label=_("START"))
        self.fields['end_period'] = forms.ChoiceField(choices=periods_choices_end, label=_("END"))

        self.fields['start_period'].initial = str(first_year_first_daterange_key)
        self.fields['end_period'].initial = str(last_year_last_daterange_key)

        self.fields['targetperiods'] = forms.ChoiceField(choices=target_frequency_choices, label=_("TARGET PERIODS"))


class PinnedReportForm(forms.ModelForm):
    class Meta:
        model = PinnedReport
        exclude = ('tola_user',)
