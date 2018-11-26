from random import randint

import faker
from django.utils import timezone
from factory import DjangoModelFactory, post_generation, SubFactory, lazy_attribute, Sequence
from factory.fuzzy import FuzzyChoice

from indicators.models import (
    TolaTable as TolaTableM,
    CollectedData as CollectedDataM,
    ExternalService as ExternalServiceM,
    ReportingFrequency as ReportingFrequencyM,
    Indicator as IndicatorM,
    IndicatorType as IndicatorTypeM,
    Level as LevelM,
    Objective as ObjectiveM,
    PeriodicTarget as PeriodicTargetM,
    StrategicObjective as StrategicObjectiveM,
    PinnedReport as PinnedReportM,
    DisaggregationType as DisaggregationTypeM,
    DataCollectionFrequency as DataCollectionFrequencyM
)
from workflow_models import OrganizationFactory, ProgramFactory, CountryFactory, UserFactory

FAKER = faker.Faker(locale='en_US')


class ReportingFrequency(DjangoModelFactory):
    class Meta:
        model = ReportingFrequencyM

    frequency = 'Bi-weekly'
    description = 'Every two weeks'
    organization = SubFactory(OrganizationFactory)


class RandomIndicatorFactory(DjangoModelFactory):
    class Meta:
        model = IndicatorM

    name = lazy_attribute(lambda n: FAKER.sentence(nb_words=8))
    number = lazy_attribute(
        lambda n: "%s.%s.%s" % (randint(1, 2), randint(1, 4), randint(1, 5)))
    create_date = lazy_attribute(lambda t: timezone.now())


class IndicatorFactory(DjangoModelFactory):
    class Meta:
        model = IndicatorM
        django_get_or_create = ('name',)

    name = Sequence(lambda n: 'Indicator {0}'.format(n))


class DefinedIndicatorFactory(IndicatorFactory):
    number = Sequence(lambda n: '1.1.{0}'.format(n))
    source = "indicator source"
    definition = "indicator definition"
    justification = "rationale or justification"
    unit_of_measure = "a unit of measure"
    unit_of_measure_type = IndicatorM.NUMBER
    baseline = 100
    lop_target = 1000
    target_frequency = IndicatorM.QUARTERLY
    means_of_verification = "some means of verifying"
    data_collection_method = "some method of collecting data"
    data_collection_frequency = SubFactory('factories.indicators_models.DataCollectionFrequencyFactory')

class Objective(DjangoModelFactory):
    class Meta:
        model = ObjectiveM

    name = 'Get Tola rocking!'


class LevelFactory(DjangoModelFactory):
    class Meta:
        model = LevelM

    name = Sequence(lambda n: 'Level: {0}'.format(n))


class CollectedDataFactory(DjangoModelFactory):
    class Meta:
        model = CollectedDataM

    program = SubFactory(ProgramFactory)
    indicator = SubFactory(IndicatorFactory)
    description = Sequence(lambda n: 'Data description {0}'.format(n))
    achieved = 10

    @post_generation
    def sites(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if type(extracted) is list:
            # A list of program were passed in, use them
            for site in extracted:
                self.site.add(site)


class IndicatorTypeFactory(DjangoModelFactory):
    class Meta:
        model = IndicatorTypeM
        django_get_or_create = ('indicator_type',)

    indicator_type = Sequence(lambda n: 'Indicator Type {0}'.format(n))


class ExternalServiceFactory(DjangoModelFactory):
    class Meta:
        model = ExternalServiceM

    name = Sequence(lambda n: 'External Service {0}'.format(n))


class StrategicObjective(DjangoModelFactory):
    class Meta:
        model = StrategicObjectiveM

    name = Sequence(lambda n: 'Stratigic Objective {0}'.format(n))


class PeriodicTargetFactory(DjangoModelFactory):
    class Meta:
        model = PeriodicTargetM

    target = 0
    period = lazy_attribute(
        lambda pt: 'PeriodicTarget for %s: %s - %s' % (pt.indicator.name, pt.start_date, pt.end_date))
    customsort = Sequence(lambda n: n)


class PinnedReportFactory(DjangoModelFactory):
    class Meta:
        model = PinnedReportM

    name = Sequence(lambda n: 'Test pinned report: {0}'.format(n))
    report_type = FuzzyChoice(['timeperiods', 'targetperiods'])

class DisaggregationTypeFactory(DjangoModelFactory):
    class Meta:
        model = DisaggregationTypeM
    disaggregation_type = Sequence(lambda n: "disagg type {0}".format(n))
    description = "disaggregation description"
    country = SubFactory(CountryFactory)

class DataCollectionFrequencyFactory(DjangoModelFactory):
    class Meta:
        model = DataCollectionFrequencyM

    frequency = "some reasonable frequency"
    description = "a description of how frequent this is"
    numdays = 10

class TolaTableFactory(DjangoModelFactory):
    class Meta:
        model = TolaTableM
    name = Sequence(lambda n: 'Tola Table {0}'.format(n))
    owner = SubFactory(UserFactory)
