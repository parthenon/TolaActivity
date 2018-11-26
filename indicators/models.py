# -*- coding: utf-8 -*-
import uuid
from datetime import timedelta, date
from decimal import Decimal

import dateparser
from django.db import models
from django.db.models import Avg
from django.http import QueryDict
from django.urls import reverse
from django.utils import formats, timezone, functional
from django.utils.translation import ugettext_lazy as _
from tola.l10n_utils import l10n_date_year_month, l10n_date_medium
from django.contrib import admin
from django.utils.functional import cached_property


from simple_history.models import HistoricalRecords

from workflow.models import (
    Program, Sector, SiteProfile, ProjectAgreement, ProjectComplete, Country,
    Documentation, TolaUser
)


class TolaTable(models.Model):
    name = models.CharField(_("Name"), max_length=255, blank=True)
    table_id = models.IntegerField(_("Table id"), blank=True, null=True)
    owner = models.ForeignKey('auth.User', verbose_name=_("Owner"))
    remote_owner = models.CharField(_("Remote owner"), max_length=255, blank=True)
    country = models.ManyToManyField(Country, blank=True, verbose_name=_("Country"))
    url = models.CharField(_("Url"), max_length=255, blank=True)
    unique_count = models.IntegerField(_("Unique count"), blank=True, null=True)
    create_date = models.DateTimeField(_("Create date"), null=True, blank=True)
    edit_date = models.DateTimeField(_("Edit date"), null=True, blank=True)

    def __unicode__(self):
        return self.name


class TolaTableAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'owner', 'url', 'create_date',
                    'edit_date')
    search_fields = ('country', 'name')
    list_filter = ('country__country',)
    display = 'Tola Table'


class IndicatorType(models.Model):
    indicator_type = models.CharField(_("Indicator type"), max_length=135, blank=True)
    description = models.TextField(_("Description"), max_length=765, blank=True)
    create_date = models.DateTimeField(_("Create date"), null=True, blank=True)
    edit_date = models.DateTimeField(_("Edit date"), null=True, blank=True)

    class Meta:
        verbose_name = _("Indicator Type")

    def __unicode__(self):
        return self.indicator_type


class IndicatorTypeAdmin(admin.ModelAdmin):
    list_display = ('indicator_type', 'description', 'create_date',
                    'edit_date')
    display = 'Indicator Type'


class StrategicObjective(models.Model):
    name = models.CharField(_("Name"), max_length=135, blank=True)
    country = models.ForeignKey(Country, null=True, blank=True, verbose_name=_("Country"))
    description = models.TextField(_("Description"), max_length=765, blank=True)
    create_date = models.DateTimeField(_("Create date"), null=True, blank=True)
    edit_date = models.DateTimeField(_("Edit date"), null=True, blank=True)

    class Meta:
        verbose_name = _("Country Strategic Objectives")
        ordering = ('country', 'name')

    def __unicode__(self):
        return self.name

    def save(self):
        if self.create_date is None:
            self.create_date = timezone.now()
        super(StrategicObjective, self).save()


class Objective(models.Model):
    name = models.CharField(_("Name"), max_length=135, blank=True)
    program = models.ForeignKey(Program, null=True, blank=True, verbose_name=_("Program"))
    description = models.TextField(_("Description"), max_length=765, blank=True)
    create_date = models.DateTimeField(_("Create date"), null=True, blank=True)
    edit_date = models.DateTimeField(_("Edit date"), null=True, blank=True)

    class Meta:
        verbose_name = _("Program Objective")
        ordering = ('program', 'name')

    def __unicode__(self):
        return self.name

    def save(self):
        if self.create_date is None:
            self.create_date = timezone.now()
        super(Objective, self).save()


class Level(models.Model):
    name = models.CharField(_("Name"), max_length=135, blank=True)
    description = models.TextField(
        _("Description"), max_length=765, blank=True)
    customsort = models.IntegerField(_("Customsort"), blank=True, null=True)
    create_date = models.DateTimeField(_("Create date"), null=True, blank=True)
    edit_date = models.DateTimeField(_("Edit date"), null=True, blank=True)

    class Meta:
        ordering = ('customsort', )
        verbose_name = _("Level")

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.create_date is None:
            self.create_date = timezone.now()
        super(Level, self).save(*args, **kwargs)


class LevelAdmin(admin.ModelAdmin):
    list_display = ('name')
    display = 'Levels'


class DisaggregationType(models.Model):
    disaggregation_type = models.CharField(_("Disaggregation type"), max_length=135, blank=True)
    description = models.CharField(_("Description"), max_length=765, blank=True)
    country = models.ForeignKey(Country, null=True, blank=True, verbose_name="Country")
    standard = models.BooleanField(default=False, verbose_name=_("Standard (TolaData Admins Only)"))
    create_date = models.DateTimeField(_("Create date"), null=True, blank=True)
    edit_date = models.DateTimeField(_("Edit date"), null=True, blank=True)

    def __unicode__(self):
        return self.disaggregation_type


class DisaggregationLabel(models.Model):
    disaggregation_type = models.ForeignKey(DisaggregationType, verbose_name=_("Disaggregation type"))
    label = models.CharField(_("Label"), max_length=765, blank=True)
    customsort = models.IntegerField(_("Customsort"), blank=True, null=True)
    create_date = models.DateTimeField(_("Create date"), null=True, blank=True)
    edit_date = models.DateTimeField(_("Edit date"), null=True, blank=True)

    def __unicode__(self):
        return self.label


class DisaggregationValue(models.Model):
    disaggregation_label = models.ForeignKey(
        DisaggregationLabel, verbose_name=_("Disaggregation label"))
    value = models.CharField(_("Value"), max_length=765, blank=True)
    create_date = models.DateTimeField(_("Create date"), null=True, blank=True)
    edit_date = models.DateTimeField(_("Edit date"), null=True, blank=True)

    def __unicode__(self):
        return self.value


class DisaggregationValueAdmin(admin.ModelAdmin):
    list_display = ('disaggregation_label', 'value', 'create_date',
                    'edit_date')
    list_filter = (
        'disaggregation_label__disaggregation_type__disaggregation_type',
        'disaggregation_label'
    )
    display = 'Disaggregation Value'


class ReportingFrequency(models.Model):
    frequency = models.CharField(
        _("Frequency"), max_length=135, blank=True)
    description = models.CharField(
        _("Description"), max_length=765, blank=True)
    create_date = models.DateTimeField(_("Create date"), null=True, blank=True)
    edit_date = models.DateTimeField(_("Edit date"), null=True, blank=True)

    class Meta:
        verbose_name = _("Reporting Frequency")

    def __unicode__(self):
        return self.frequency


class DataCollectionFrequency(models.Model):
    frequency = models.CharField(
        _("Frequency"), max_length=135, blank=True, null=True)
    description = models.CharField(
        _("Description"), max_length=255, blank=True, null=True)
    numdays = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Frequency in number of days")
    )
    create_date = models.DateTimeField(_("Create date"), null=True, blank=True)
    edit_date = models.DateTimeField(_("Edit date"), null=True, blank=True)

    class Meta:
        verbose_name = _("Data Collection Frequency")

    def __unicode__(self):
        return self.frequency


class DataCollectionFrequencyAdmin(admin.ModelAdmin):
    list_display = ('frequency', 'description', 'create_date', 'edit_date')
    display = 'Data Collection Frequency'


# TODO: Delete ReportingPeriod and ReportingPeriodAdmin? Not linked to other models and doesn't seem to be
# utilized in views
class ReportingPeriod(models.Model):
    frequency = models.ForeignKey(
        ReportingFrequency, verbose_name=_("Frequency")
    )
    create_date = models.DateTimeField(_("Create date"), null=True, blank=True)
    edit_date = models.DateTimeField(_("Edit date"), null=True, blank=True)

    class Meta:
        verbose_name = _("Reporting Period")

    def __unicode__(self):
        return self.frequency


class ReportingPeriodAdmin(admin.ModelAdmin):
    list_display = ('frequency', 'create_date', 'edit_date')
    display = 'Reporting Frequency'


class ExternalService(models.Model):
    name = models.CharField(_("Name"), max_length=255, blank=True)
    url = models.CharField(_("Url"), max_length=765, blank=True)
    feed_url = models.CharField(_("Feed url"), max_length=765, blank=True)
    create_date = models.DateTimeField(_("Create date"), null=True, blank=True)
    edit_date = models.DateTimeField(_("Edit date"), null=True, blank=True)

    class Meta:
        verbose_name = _("External Service")

    def __unicode__(self):
        return self.name


class ExternalServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'url', 'feed_url', 'create_date', 'edit_date')
    display = 'External Indicator Data Service'


class ExternalServiceRecord(models.Model):
    external_service = models.ForeignKey(
        ExternalService, blank=True, null=True, on_delete=models.SET_NULL,
        verbose_name=_("External service"))
    full_url = models.CharField(_("Full URL"), max_length=765, blank=True)
    record_id = models.CharField(_("Unique ID"), max_length=765, blank=True)
    create_date = models.DateTimeField(null=True, blank=True)
    edit_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("External Service Record")

    def __unicode__(self):
        return self.full_url


class ExternalServiceRecordAdmin(admin.ModelAdmin):
    list_display = ('external_service', 'full_url', 'record_id', 'create_date',
                    'edit_date')
    display = 'Exeternal Indicator Data Service'


class IndicatorManager(models.Manager):
    def get_queryset(self):
        return super(IndicatorManager, self).get_queryset()\
            .prefetch_related('program')\
            .select_related('sector')


class Indicator(models.Model):
    LOP = 1
    MID_END = 2
    ANNUAL = 3
    SEMI_ANNUAL = 4
    TRI_ANNUAL = 5
    QUARTERLY = 6
    MONTHLY = 7
    EVENT = 8
    TARGET_FREQUENCIES = (
        (LOP, _('Life of Program (LoP) only')),
        (MID_END, _('Midline and endline')),
        (ANNUAL, _('Annual')),
        (SEMI_ANNUAL, _('Semi-annual')),
        (TRI_ANNUAL, _('Tri-annual')),
        (QUARTERLY, _('Quarterly')),
        (MONTHLY, _('Monthly')),
        (EVENT, _('Event'))
    )

    NUMBER = 1
    PERCENTAGE = 2
    UNIT_OF_MEASURE_TYPES = (
        (NUMBER, _('Number (#)')),
        (PERCENTAGE, _("Percentage (%)"))
    )

    DIRECTION_OF_CHANGE_NONE = 1
    DIRECTION_OF_CHANGE_POSITIVE = 2
    DIRECTION_OF_CHANGE_NEGATIVE = 3
    DIRECTION_OF_CHANGE = (
        (DIRECTION_OF_CHANGE_NONE, _("Direction of change (not applicable)")),
        (DIRECTION_OF_CHANGE_POSITIVE, _("Increase (+)")),
        (DIRECTION_OF_CHANGE_NEGATIVE, _("Decrease (-)"))
    )
    SEPARATOR = ','

    ONSCOPE_MARGIN = .15


    indicator_key = models.UUIDField(
        default=uuid.uuid4, unique=True, help_text=" "),

    # i.e. Alpha, Donor, Standard
    # TODO: make this a foreign key
    indicator_type = models.ManyToManyField(
        IndicatorType, blank=True, help_text=" ",
        verbose_name=_("Indicator type")
    )

    # the Log Frame level (i.e. Goal, Output, Outcome, etc.)
    level = models.ForeignKey(
        Level, blank=True, null=True, verbose_name=_("Level"),
        on_delete=models.SET_NULL
    )

    # this includes a relationship to a program
    objectives = models.ManyToManyField(
        Objective, blank=True, verbose_name=_("Program Objective"),
        related_name="obj_indicator", help_text=" "
    )

    # this includes a relationship to a country
    strategic_objectives = models.ManyToManyField(
        StrategicObjective, verbose_name=_("Country Strategic Objective"),
        blank=True, related_name="strat_indicator", help_text=" "
    )

    name = models.CharField(verbose_name=_("Name"), max_length=255,
                            null=False, help_text=" ")

    number = models.CharField(
        _("Number"), max_length=255, null=True, blank=True, help_text=" "
    )

    source = models.CharField(
        _("Source"), max_length=255, null=True, blank=True, help_text=" "
    )

    definition = models.TextField(
        _("Definition"), null=True, blank=True, help_text=" "
    )

    justification = models.TextField(
        max_length=500, null=True, blank=True,
        verbose_name=_("Rationale or Justification for Indicator"),
        help_text=" "
    )

    unit_of_measure = models.CharField(
        max_length=135, null=True, blank=True,
        verbose_name=_("Unit of measure*"),
        help_text=" "
    )

    unit_of_measure_type = models.IntegerField(
        blank=False, null=True, choices=UNIT_OF_MEASURE_TYPES,
        default=NUMBER,
        verbose_name=_("Unit Type"), help_text=" "
    )

    disaggregation = models.ManyToManyField(
        DisaggregationType, blank=True, help_text=" ",
        verbose_name=_("Disaggregation"))

    baseline = models.CharField(
        verbose_name=_("Baseline*"), max_length=255, null=True, blank=True,
        help_text=" "
    )

    baseline_na = models.BooleanField(
        verbose_name=_("Not applicable"), default=False, help_text=" "
    )

    lop_target = models.CharField(
        verbose_name=_("Life of Program (LoP) target*"), max_length=255,
        null=True, blank=True, help_text=" "
    )

    direction_of_change = models.IntegerField(
        blank=False, null=True, choices=DIRECTION_OF_CHANGE,
        default=DIRECTION_OF_CHANGE_NONE,
        verbose_name=_("Direction of Change"), help_text=" "
    )

    is_cumulative = models.NullBooleanField(
        blank=False, verbose_name=_("C / NC"), help_text=" "
    )

    rationale_for_target = models.TextField(
        _("Rationale for target"), max_length=255, null=True,
        blank=True, help_text=" "
    )

    target_frequency = models.IntegerField(
        blank=False, null=True, choices=TARGET_FREQUENCIES,
        verbose_name=_("Target frequency"), help_text=" "
    )

    target_frequency_custom = models.CharField(
        null=True, blank=True, max_length=100,
        verbose_name=_("First event name*"), help_text=" "
    )

    target_frequency_start = models.DateField(
        blank=True, null=True, auto_now=False, auto_now_add=False,
        verbose_name=_("First target period begins*"), help_text=" "
    )

    target_frequency_num_periods = models.IntegerField(
        blank=True, null=True, verbose_name=_("Number of target periods*"),
        help_text=" "
    )

    means_of_verification = models.CharField(
        max_length=255, null=True, blank=True,
        verbose_name=_("Means of Verification / Data Source"), help_text=" "
    )

    data_collection_method = models.CharField(
        max_length=255, null=True, blank=True,
        verbose_name=_("Data Collection Method"), help_text=" "
    )

    data_collection_frequency = models.ForeignKey(
        DataCollectionFrequency, null=True, blank=True, on_delete=models.SET_NULL,
        verbose_name=_("Frequency of Data Collection"), help_text=" "
    )

    data_points = models.TextField(
        max_length=500, null=True, blank=True, verbose_name=_("Data points"),
        help_text=" "
    )

    responsible_person = models.CharField(
        max_length=255, null=True, blank=True,
        verbose_name=_("Responsible Person(s) and Team"), help_text=" "
    )

    method_of_analysis = models.CharField(
        max_length=255, null=True, blank=True,
        verbose_name=_("Method of Analysis"), help_text=" "
    )

    information_use = models.CharField(
        max_length=255, null=True, blank=True,
        verbose_name=_("Information Use"), help_text=" "
    )

    reporting_frequency = models.ForeignKey(
        ReportingFrequency, null=True, blank=True, on_delete=models.SET_NULL,
        verbose_name=_("Frequency of Reporting"), help_text=" "
    )

    quality_assurance = models.TextField(
        max_length=500, null=True, blank=True,
        verbose_name=_("Quality Assurance Measures"), help_text=" "
    )

    data_issues = models.TextField(
        max_length=500, null=True, blank=True, verbose_name=_("Data issues"),
        help_text=" "
    )

    indicator_changes = models.TextField(
        max_length=500, null=True, blank=True,
        verbose_name=_("Changes to Indicator"), help_text=" "
    )

    comments = models.TextField(
        _("Comments"), max_length=255, null=True, blank=True, help_text=" "
    )

    program = models.ForeignKey(
        Program, verbose_name=_("Program"),
        blank=True, null=True, on_delete=models.CASCADE,
    )

    sector = models.ForeignKey(
        Sector, null=True, blank=True, on_delete=models.SET_NULL, help_text=" ", verbose_name=_("Sector")
    )

    key_performance_indicator = models.BooleanField(
        verbose_name=_("Key Performance Indicator for this program?"),
        default=False, help_text=" "
    )

    approved_by = models.ForeignKey(
        TolaUser, blank=True, null=True, on_delete=models.SET_NULL, related_name="approving_indicator",
        verbose_name=_("Approved by"), help_text=" "
    )

    approval_submitted_by = models.ForeignKey(
        TolaUser, blank=True, null=True, on_delete=models.SET_NULL, related_name="indicator_submitted_by",
        verbose_name=_("Approval submitted by"), help_text=" "
    )

    external_service_record = models.ForeignKey(
        ExternalServiceRecord, verbose_name=_("External Service ID"),
        blank=True, null=True, on_delete=models.SET_NULL, help_text=" "
    )

    create_date = models.DateTimeField(
        _("Create date"), null=True, blank=True, help_text=" "
    )

    edit_date = models.DateTimeField(
        _("Edit date"), null=True, blank=True, help_text=" "
    )

    history = HistoricalRecords()

    notes = models.TextField(_("Notes"), max_length=500, null=True, blank=True)
    # optimize query for class based views etc.
    objects = IndicatorManager()

    class Meta:
        ordering = ('create_date',)
        verbose_name = _("Indicator")

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.create_date is None:
            self.create_date = timezone.now()
        self.edit_date = timezone.now()
        super(Indicator, self).save(*args, **kwargs)

    @property
    def is_target_frequency_time_aware(self):
        return self.target_frequency in (self.ANNUAL, self.SEMI_ANNUAL,
                                         self.TRI_ANNUAL, self.QUARTERLY,
                                         self.MONTHLY)

    @property
    def just_created(self):
        if self.create_date >= timezone.now() - timedelta(minutes=5):
            return True
        return False

    @property
    def name_clean(self):
        return self.name.encode('ascii', 'ignore')

    @property
    def objectives_list(self):
        return ', '.join([x.name for x in self.objectives.all()])

    @property
    def strategicobjectives_list(self):
        return ', '.join([x.name for x in self.strategic_objectives.all()])

    @property
    def programs(self):
        return ', '.join([x.name for x in self.program.all()])

    @property
    def indicator_types(self):
        return ', '.join([x.indicator_type for x in self.indicator_type.all()])

    @property
    def disaggregations(self):
        disaggregations = self.disaggregation.all()
        return self.SEPARATOR.join([x.disaggregation_type for x in disaggregations])

    @property
    def get_target_frequency_label(self):
        if self.target_frequency:
            return Indicator.TARGET_FREQUENCIES[self.target_frequency-1][1]
        return None

    @property
    def get_unit_of_measure_type(self):
        if self.unit_of_measure_type == self.NUMBER:
            return _("#")
        elif self.unit_of_measure_type == self.PERCENTAGE:
            return _("%")
        return ""

    @property
    def get_direction_of_change(self):
        if self.direction_of_change == self.DIRECTION_OF_CHANGE_NEGATIVE:
            return _("-")
        elif self.direction_of_change == self.DIRECTION_OF_CHANGE_POSITIVE:
            return _("+")
        return "N/A"

    @property
    def get_collecteddata_average(self):
        avg = self.collecteddata_set.aggregate(Avg('achieved'))['achieved__avg']
        return avg

    @property
    def baseline_display(self):
        if self.baseline and self.unit_of_measure_type == self.PERCENTAGE:
            return self.baseline + '%'
        return self.baseline

    @property
    def lop_target_display(self):
        if self.lop_target and self.unit_of_measure_type == self.PERCENTAGE:
            return self.lop_target + '%'
        return self.lop_target

    @cached_property
    def cached_data_count(self):
        return self.collecteddata_set.count()


class PeriodicTarget(models.Model):
    LOP_PERIOD = 'Life of Program (LoP) only'
    MIDLINE = 'Midline'
    ENDLINE = 'Endline'
    ANNUAL_PERIOD = 'Year'
    SEMI_ANNUAL_PERIOD = 'Semi-annual period'
    TRI_ANNUAL_PERIOD = 'Tri-annual period'
    QUARTERLY_PERIOD = 'Quarter'

    indicator = models.ForeignKey(
        Indicator, null=False, blank=False, verbose_name=_("Indicator"), related_name="periodictargets"
    )

    period = models.CharField(
        _("Period"), max_length=255, null=True, blank=True
    )

    target = models.DecimalField(
        _("Target"), max_digits=20, decimal_places=2, default=Decimal('0.00')
    )

    start_date = models.DateField(
        _("Start date"), auto_now=False, auto_now_add=False, null=True,
        blank=True
    )

    end_date = models.DateField(
        _("End date"), auto_now=False, auto_now_add=False, null=True,
        blank=True
    )

    customsort = models.IntegerField(_("Customsort"), default=0)
    create_date = models.DateTimeField(_("Create date"), null=True, blank=True)
    edit_date = models.DateTimeField(_("Edit date"), null=True, blank=True)

    class Meta:
        ordering = ('customsort', '-create_date')
        verbose_name = _("Periodic Target")
        unique_together = (('indicator', 'customsort'),)

    def __unicode__(self):
        period_name = None
        # used in the collected data modal to display options in the target period dropdown
        if self.indicator.target_frequency == Indicator.MID_END:
            # midline is the translated "midline" or "endline" based on customsort
            period_name = _(self.MIDLINE) if self.customsort == 0 else _(self.ENDLINE)
        if self.indicator.target_frequency == Indicator.LOP:
            # lop always has translated lop value
            period_name = _(self.LOP_PERIOD)
        if period_name is not None:
            return u'{0}'.format(period_name)
        # for time-based frequencies get translated name of period:
        if self.indicator.target_frequency == Indicator.ANNUAL:
            period_name = _(self.ANNUAL_PERIOD)
        elif self.indicator.target_frequency == Indicator.SEMI_ANNUAL:
            period_name = _(self.SEMI_ANNUAL_PERIOD)
        elif self.indicator.target_frequency == Indicator.TRI_ANNUAL:
            period_name = _(self.TRI_ANNUAL_PERIOD)
        elif self.indicator.target_frequency == Indicator.QUARTERLY:
            period_name = _(self.QUARTERLY_PERIOD)
        if period_name and self.start_date and self.end_date:
            # e.g "Year 1 (date - date)" or "Quarter 2 (date - date)"
            return "{period_name} {period_number} ({start_date} - {end_date})".format(
                period_name=period_name,
                period_number=self.customsort+1,
                start_date=self.start_date,
                end_date=self.end_date
            )
        elif period_name:
            # if no date for some reason but time-based frequency:
            return "{period_name} {period_number}".format(
                period_name=period_name,
                period_number=self.customsort
                )
        if self.indicator.target_frequency == Indicator.MONTHLY:
            # translate month name, add year
            month_name = _(self.start_date.strftime("%B"))
            year = self.start_date.strftime('%Y')
            return "{month_name} {year}".format(month_name=month_name, year=year)
        return self.period

    @property
    def getcollected_data(self):
        return self.collecteddata_set.all().order_by('date_collected')

    @classmethod
    def generate_for_frequency(cls, frequency):
        """ returns a generator function to yield periods based on start and end dates for a given frequency"""
        months_per_period = {
            Indicator.SEMI_ANNUAL: 6,
            Indicator.TRI_ANNUAL: 4,
            Indicator.QUARTERLY: 3,
            Indicator.MONTHLY: 1
        }
        if frequency == Indicator.ANNUAL:
            next_date_func = lambda x: date(x.year + 1, x.month, x.day)
            name_func = lambda start, count: '{period_name} {count}'.format(
                period_name=_(cls.ANNUAL_PERIOD), count=count)
        elif frequency in months_per_period:
            next_date_func = lambda x: date(
                x.year if x.month <= 12-months_per_period[frequency] else x.year + 1,
                x.month + months_per_period[frequency] if x.month <= 12 - months_per_period[frequency] \
                else x.month + months_per_period[frequency] - 12,
                x.day)
            if frequency == Indicator.MONTHLY:
                name_func = lambda start, count: '{month_name} {year}'.format(
                    month_name=_(start.strftime('%B')),
                    year=start.strftime('%Y')
                    )
            else:
                period_name = {
                    Indicator.SEMI_ANNUAL: cls.SEMI_ANNUAL_PERIOD,
                    Indicator.TRI_ANNUAL: cls.TRI_ANNUAL_PERIOD,
                    Indicator.QUARTERLY: cls.QUARTERLY_PERIOD
                }[frequency]
                name_func = lambda start, count: '{period_name} {count}'.format(
                    period_name=_(period_name), count=count)
        elif frequency == Indicator.LOP:
            return lambda start, end: [{
                'name': _(cls.LOP_PERIOD),
                'start': start,
                'label': '{0} - {1}'.format(l10n_date_medium(start), l10n_date_medium(end)),
                'end': end,
                'customsort': 0
                }]
        elif frequency == Indicator.MID_END:
            return lambda start, end: [
                {'name': _(cls.MIDLINE),
                 'start': start,
                 'label': None,
                 'end': end,
                 'customsort': 0},
                {'name': _(cls.ENDLINE),
                 'start': start,
                 'label': None,
                 'end': end,
                 'customsort': 1}
            ]
        else:
            next_date_func = None
            name_func = None
        def period_generator(start, end):
            count = 0
            while start < end:
                next_start = next_date_func(start)
                yield {
                    'name': name_func(start, count+1),
                    'start': start,
                    'label': '{0} - {1}'.format(
                        l10n_date_medium(start), l10n_date_medium(next_start - timedelta(days=1))
                        ) if frequency != Indicator.MONTHLY else None,
                    'end': next_start - timedelta(days=1),
                    'customsort': count
                }
                count += 1
                start = next_start
        return period_generator


class PeriodicTargetAdmin(admin.ModelAdmin):
    list_display = ('period', 'target', 'customsort',)
    display = 'Indicator Periodic Target'
    list_filter = ('period',)


class CollectedDataManager(models.Manager):
    def get_queryset(self):
        return super(CollectedDataManager, self).get_queryset()\
            .prefetch_related('site', 'disaggregation_value')\
            .select_related('program', 'indicator', 'agreement', 'complete',
                            'evidence', 'tola_table')


class CollectedData(models.Model):
    data_key = models.UUIDField(
        default=uuid.uuid4, unique=True, help_text=" "),

    periodic_target = models.ForeignKey(
        PeriodicTarget, null=True, blank=True, on_delete=models.SET_NULL, help_text=" ",
        verbose_name=_("Periodic target")
    )

    achieved = models.DecimalField(
        verbose_name=_("Actual"), max_digits=20, decimal_places=2,
        help_text=" ")

    # cumulative_achieved = models.DecimalField(
    #     verbose_name=_('Cumulative Actuals'), max_digits=20, decimal_places=2,
    #     null=True, blank=True, help_text=" ")

    disaggregation_value = models.ManyToManyField(
        DisaggregationValue, blank=True, help_text=" ",
        verbose_name=_("Disaggregation Value")
    )

    description = models.TextField(
        _("Remarks/comments"), blank=True, null=True, help_text=" ")

    indicator = models.ForeignKey(
        Indicator, help_text=" ", verbose_name=_("Indicator"),
        db_index=True
    )

    agreement = models.ForeignKey(
        ProjectAgreement, blank=True, null=True, on_delete=models.SET_NULL, related_name="q_agreement2",
        verbose_name=_("Project Initiation"), help_text=" ")

    complete = models.ForeignKey(
        ProjectComplete, blank=True, null=True, related_name="q_complete2",
        on_delete=models.SET_NULL, help_text=" ",
        verbose_name=_("Project Complete")
    )

    program = models.ForeignKey(
        Program, blank=True, null=True, related_name="i_program",
        help_text=" ", verbose_name=_("Program"))

    date_collected = models.DateField(
        null=True, blank=True, help_text=" ", verbose_name=_("Date collected"))

    comment = models.TextField(
        _("Comment/Explanation"), max_length=255, blank=True, null=True,
        help_text=" ")

    evidence = models.ForeignKey(
        Documentation, null=True, blank=True, on_delete=models.SET_NULL,
        verbose_name=_("Evidence Document or Link"), help_text=" ")

    approved_by = models.ForeignKey(
        TolaUser, blank=True, null=True, on_delete=models.SET_NULL, verbose_name=_("Originated By"),
        related_name="approving_data", help_text=" ")

    tola_table = models.ForeignKey(
        TolaTable, blank=True, null=True, on_delete=models.SET_NULL, verbose_name=_("TolaTable"), help_text=" ")

    update_count_tola_table = models.BooleanField(
        verbose_name=_("Would you like to update the achieved total with the \
        row count from TolaTables?"), default=False, help_text=" ")

    create_date = models.DateTimeField(null=True, blank=True, help_text=" ")
    edit_date = models.DateTimeField(null=True, blank=True, help_text=" ")
    site = models.ManyToManyField(SiteProfile, blank=True, help_text=" ")
    history = HistoricalRecords()
    objects = CollectedDataManager()

    class Meta:
        ordering = ('indicator', 'date_collected')
        verbose_name_plural = "Indicator Output/Outcome Collected Data"

    def __unicode__(self):
        return self.description

    def save(self, *args, **kwargs):
        if self.create_date is None:
            self.create_date = timezone.now()
        self.edit_date = timezone.now()

        # if self.achieved is not None:
        #     # calculate the cumulative sum of achieved value
        #     total_achieved = CollectedData.objects.filter(
        #         indicator=self.indicator,
        #         create_date__lt=self.create_date)\
        #         .aggregate(Sum('achieved'))['achieved__sum']

        #     if total_achieved is None:
        #         total_achieved = 0

        #     total_achieved = total_achieved + self.achieved
        #     self.cumulative_achieved = total_achieved
        super(CollectedData, self).save()

    def achieved_sum(self):
        achieved = CollectedData.targeted.filter(indicator__id=self)\
            .sum('achieved')
        return achieved

    @property
    def date_collected_formatted(self):
        # apparently unused?
        if self.date_collected:
            return formats.date_format(self.date_collected, "MEDIUM_DATE_FORMAT")
        return self.date_collected

    @property
    def disaggregations(self):
        disaggs = self.disaggregation_value.all()
        return ', '.join([y.disaggregation_label.label + ': ' + y.value for y in disaggs])


# @receiver(post_delete, sender=CollectedData)
# def model_post_delete(sender, **kwargs):
#     instance = kwargs.get('instance', None)
#     # print('Deleted: {}'.format(kwargs['instance'].__dict__))

#     # the cumulative_achieved values need to be recalculated after an a
#     # CollectedData record is deleted
#     collecteddata = CollectedData.objects.filter(
#         indicator=instance.indicator)\
#         .order_by('id')

#     # by saving each data reecord the cumulative_achieved is recalculated in
#     # the save method of the CollectedData model class.
#     for c in collecteddata:
#         c.save()


class CollectedDataAdmin(admin.ModelAdmin):
    list_display = ('indicator', 'date_collected', 'create_date', 'edit_date')
    list_filter = ['indicator__program__country__country']
    display = 'Indicator Output/Outcome Collected Data'


class PinnedReport(models.Model):
    """
    A named IPTT report for a given program and user
    """
    name = models.CharField(max_length=50, verbose_name=_('Report Name'))
    tola_user = models.ForeignKey(TolaUser, on_delete=models.CASCADE)
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='pinned_reports')
    report_type = models.CharField(max_length=32)
    query_string = models.CharField(max_length=255)
    creation_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-creation_date']

    def parse_query_string(self):
        return QueryDict(self.query_string)

    @property
    def report_url(self):
        """
        Return the fully parameterized IPTT report URL string
        """
        return "{}?{}".format(reverse('iptt_report', kwargs={
            'program_id': self.program_id,
            'reporttype': self.report_type
        }), self.query_string)

    @property
    def date_range_str(self):
        """
        A localized string showing the date range covered by the pinned report

        There are several types of pinned reports w/ regards to date ranges and report type:

          * A report with a fixed start/end date
            * Recent progress
            * Annual vs targets
          * A relative report (show previous N months/quarters/year relative to today)
            * Recent progress
            * Annual vs targets
          * Show all with a time period selected (annual/monthly)
            * Recent progress
            * Annual vs targets
          * Show all with LoP/Midline+Endline/Event
            * Annual vs targets

        Currently the query string is used to determine the date range type, and thus the returned string
        """
        qs = self.parse_query_string()

        start_period = qs.get('start_period')
        end_period = qs.get('end_period')

        time_frame = qs.get('timeframe')  # show all/most recent
        num_recent_periods = qs.get('numrecentperiods')  # "most recent" input
        time_periods = qs.get('timeperiods')  # quarters/months/years/etc (recent progress)
        target_periods = qs.get('targetperiods')  # LoP/Midline+Endline/Annual/Quarterly/etc (target vs actuals)

        df = lambda d: formats.date_format(dateparser.parse(d), 'MEDIUM_DATE_FORMAT')

        # Fixed start/end date
        if start_period and end_period:
            return '{} – {}'.format(df(start_period), df(end_period))

        from indicators.forms import ReportFormCommon

        # This is confusing but ReportFormCommon defines TIMEPERIODS_CHOICES
        # which is defined in terms of enum values in Indicators
        # Indicators also defines TARGET_FREQUENCIES which is also used by ReportFormCommon
        # Because of this, the enum values are interchangeable between ReportFormCommon and Indicators

        # TIMEPERIODS_CHOICES = (
        #     (YEARS, _("Years")),
        #     (SEMIANNUAL, _("Semi-annual periods")),
        #     (TRIANNUAL, _("Tri-annual periods")),
        #     (QUARTERS, _("Quarters")),
        #     (MONTHS, _("Months"))
        # )

        # TARGETPERIOD_CHOICES = [empty] +
        # TARGET_FREQUENCIES = (
        #     (LOP, _('Life of Program (LoP) only')),
        #     (MID_END, _('Midline and endline')),
        #     (ANNUAL, _('Annual')),
        #     (SEMI_ANNUAL, _('Semi-annual')),
        #     (TRI_ANNUAL, _('Tri-annual')),
        #     (QUARTERLY, _('Quarterly')),
        #     (MONTHLY, _('Monthly')),
        #     (EVENT, _('Event'))
        # )

        # time period strings are used for BOTH timeperiod and targetperiod values
        time_period_str_lookup = dict(ReportFormCommon.TIMEPERIODS_CHOICES)

        time_or_target_period_str = None
        if time_periods:
            time_or_target_period_str = time_period_str_lookup.get(int(time_periods))
        if target_periods:
            time_or_target_period_str = time_period_str_lookup.get(int(target_periods))

        # A relative report (Recent progress || Target vs Actuals)
        if time_frame == str(ReportFormCommon.MOST_RECENT) and num_recent_periods and time_or_target_period_str:
            #  Translators: Example: Most recent 2 Months
            return _('Most recent {} {}'.format(num_recent_periods, time_or_target_period_str))

        # Show all (Recent progress || Target vs Actuals w/ time period (such as annual))
        if time_frame == str(ReportFormCommon.SHOW_ALL) and time_or_target_period_str:
            # Translators: Example: Show all Years
            return _('Show all {}').format(time_or_target_period_str)

        # Show all (Target vs Actuals LoP/Midline+End/Event)
        remaining_target_freq_set = {
            Indicator.LOP,
            Indicator.MID_END,
            Indicator.EVENT,
        }
        if time_frame == str(ReportFormCommon.SHOW_ALL) and target_periods \
                and int(target_periods) in remaining_target_freq_set:
            return _('Show all results')

        # It's possible to submit bad input, but have the view "fix" it..
        if time_frame == str(ReportFormCommon.MOST_RECENT) and num_recent_periods and not time_or_target_period_str:
            return _('Show all results')

        return ''


    @staticmethod
    def default_report(program_id):
        """
        Create a default hardcoded pinned report

        Shows recent progress for all indicators
        Does not exist in the DB
        """
        return PinnedReport(
            name=_('Recent progress for all indicators'),
            program_id=program_id,
            report_type='timeperiods',
            query_string='timeperiods=7&timeframe=2&numrecentperiods=2',
        )
