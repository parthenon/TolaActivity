from .serializers import (
    PeriodicTargetSerializer, ProgramIndicatorSerializer, ProgramSerializer, UserSerializer,
    SectorSerializer, ProjectTypeSerializer, OfficeSerializer, SiteProfileSerializer, CountrySerializer,
    AgreementSerializer, CompleteSerializer, IndicatorSerializer, ReportingFrequencySerializer, TolaUserSerializer,
    IndicatorTypeSerializer, ObjectiveSerializer, DisaggregationTypeSerializer, LevelSerializer, StakeholderSerializer,
    ExternalServiceRecordSerializer, ExternalServiceSerializer, StrategicObjectiveSerializer, CapacitySerializer,
    StakeholderTypeSerializer, EvaluateSerializer, ProfileTypeSerializer, ProvinceSerializer, DistrictSerializer,
    AdminLevelThreeSerializer, TolaTableSerializer, DisaggregationValueSerializer, VillageSerializer,
    ContactSerializer, DocumentationSerializer, CollectedDataSerializer, LoggedUserSerializer,
    ChecklistSerializer, OrganizationSerializer, SiteProfileLightSerializer, IndicatorIdAndNameSerializer,
    SectorIdAndNameSerializer, ProgramTargetFrequenciesSerializer
)

from workflow.models import (
    Program, Sector, ProjectType, Office, SiteProfile, Country, ProjectComplete, Organization,
    ProjectAgreement, Stakeholder, Capacity, Evaluate, ProfileType, LoggedUser,
    Province, District, AdminLevelThree, Village, StakeholderType, Contact, Documentation, Checklist
)
from indicators.models import (
    Indicator, Objective, ReportingFrequency, TolaUser, IndicatorType, DisaggregationType,
    Level, ExternalService, ExternalServiceRecord, StrategicObjective, CollectedData, TolaTable,
    DisaggregationValue, PeriodicTarget
)

from django.contrib.auth.models import User
from django.db import models
from django.shortcuts import get_object_or_404
from tola.util import getCountry
from django.shortcuts import get_object_or_404

from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
import django_filters

from workflow.mixins import APIDefaultsMixin


class LargeResultsSetPagination(PageNumberPagination):
    page_size = 1000
    page_size_query_param = 'page_size'
    max_page_size = 10000


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 1000


class SmallResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 50


class PeriodicTargetReadOnlyViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PeriodicTargetSerializer

    def get_queryset(self):
        queryset = PeriodicTarget.objects.all()
        indicator_id = self.request.query_params.get('indicator', None)
        if indicator_id:
            queryset = queryset.filter(indicator=indicator_id)
        return queryset


class PogramIndicatorReadOnlyViewSet(viewsets.ReadOnlyModelViewSet):
    # serializer_class = ProgramIndicatorSerializer
    pagination_class = StandardResultsSetPagination

    def get_serializer_class(self):
        if self.request.query_params.get('program', None):
            return IndicatorIdAndNameSerializer
        return ProgramIndicatorSerializer

    def get_queryset(self):
        program_id = self.request.query_params.get('program', None)
        if program_id:
            queryset = Indicator.objects.filter(program__in=[program_id]).values('id', 'name')
        else:
            queryset = Program.objects.prefetch_related(
                'indicator_set', 'indicator_set__indicator_type', 'indicator_set__sector', 'indicator_set__level',
                'indicator_set__collecteddata_set').all()
        return queryset


# API Classes
class UserViewSet(viewsets.ModelViewSet):
    """
    A ViewSet for listing or retrieving users.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer


class ProgramViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    search by country name and program name
    limit to users logged in country permissions
    """
    def list(self, request):
        user_countries = getCountry(request.user)
        queryset = Program.objects.all().filter(country__in=user_countries)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    filter_fields = ('country__country','name')
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    queryset = Program.objects.all()
    serializer_class = ProgramSerializer


class SectorViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    """
    def get_serializer_class(self):
        if self.request.query_params.get('program', None):
            return SectorIdAndNameSerializer
        return SectorSerializer

    def get_queryset(self):
        program_id = self.request.query_params.get('program', None)
        if program_id:
            queryset = Sector.objects.filter(indicator__program__in=[program_id]).values('id', 'sector').distinct()
        else:
            queryset = Sector.objects.all()
        return queryset


class ProjectTypeViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    """
    queryset = ProjectType.objects.all()
    serializer_class = ProjectTypeSerializer


class OfficeViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    """
    queryset = Office.objects.all()
    serializer_class = OfficeSerializer


class SiteProfileViewSet(viewsets.ModelViewSet):
    """
    Search by country name and program name
    limit to users logged in country permissions
    """
    def get_serializer_class(self):
        if self.request.query_params.get('program', None):
            return SiteProfileLightSerializer
        return SiteProfileSerializer

    def list(self, request):
        program_id = request.query_params.get('program', None)
        if program_id:
            program = Program.objects.get(pk=program_id)
            queryset = program.get_sites()
        else:
            user_countries = getCountry(request.user)
            queryset = SiteProfile.objects.all().filter(country__in=user_countries)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    filter_fields = ('country__country',)
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    queryset = SiteProfile .objects.all()


class CountryViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    """
    queryset = Country.objects.all()
    serializer_class = CountrySerializer


class AgreementViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    Search by country name and program name
    limit to users logged in country permissions
    """
    def list(self, request):
        user_countries = getCountry(request.user)
        queryset = ProjectAgreement.objects.all().filter(program__country__in=user_countries)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    """
    def post(self,request):

        for each agreement
            insert int and string fields direct
            if FK field

        return blank
    """

    filter_fields = ('program__country__country', 'program__name')
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    queryset = ProjectAgreement.objects.all()
    serializer_class = AgreementSerializer
    pagination_class = SmallResultsSetPagination


class CompleteViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    Search by country name and program name
    limit to users logged in country permissions
    """
    def list(self, request):
        user_countries = getCountry(request.user)
        queryset = ProjectComplete.objects.all().filter(program__country__in=user_countries)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    filter_fields = ('program__country__country', 'program__name')
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    queryset = ProjectComplete.objects.all()
    serializer_class = CompleteSerializer
    pagination_class = SmallResultsSetPagination


class IndicatorViewSet(viewsets.ModelViewSet):
    def get_serializer_class(self):
        if self.request.query_params.get('program', None):
            return IndicatorIdAndNameSerializer
        return IndicatorSerializer

    def list(self, request):
        program_id = request.query_params.get('program', None)
        if program_id:
            queryset = Indicator.objects.filter(program__in=[program_id])
        else:
            user_countries = getCountry(request.user)
            queryset = Indicator.objects.filter(program__country__in=user_countries)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    filter_fields = ('program__country__country', 'program__name')
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    queryset = Indicator.objects.all()


class ReportingFrequencyViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    """
    queryset = ReportingFrequency.objects.all()
    serializer_class = ReportingFrequencySerializer


class TolaUserViewSet(viewsets.ModelViewSet):
    """
    A ViewSet for listing or retrieving TolaUsers.

    """
    def list(self, request):
        queryset = TolaUser.objects.all()
        serializer = TolaUserSerializer(instance=queryset, context={'request': request}, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        queryset = TolaUser.objects.all()
        user = get_object_or_404(queryset, pk=pk)
        serializer = TolaUserSerializer(instance=user, context={'request': request})
        return Response(serializer.data)

    queryset = TolaUser.objects.all()
    serializer_class = TolaUserSerializer


class IndicatorTypeViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    """
    queryset = IndicatorType.objects.all()
    serializer_class = IndicatorTypeSerializer

    def get_queryset(self):
        program_id = self.request.query_params.get('program', None)
        if program_id:
            type_ids = Indicator.objects.filter(program__in=[program_id]).values(
                'indicator_type__id').distinct().order_by('indicator_type')
            queryset = IndicatorType.objects.filter(id__in=type_ids).distinct()
        else:
            queryset = IndicatorType.objects.all()
        return queryset


class ObjectiveViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    """
    queryset = Objective.objects.all()
    serializer_class = ObjectiveSerializer


class DisaggregationTypeViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    """
    queryset = DisaggregationType.objects.all()
    serializer_class = DisaggregationTypeSerializer


class LevelViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    """
    queryset = Level.objects.all()
    serializer_class = LevelSerializer

    def get_queryset(self):
        program_id = self.request.query_params.get('program', None)
        if program_id:
            level_ids = Indicator.objects.filter(program__in=[program_id]).values(
                'level__id').distinct().order_by('level')
            queryset = Level.objects.filter(id__in=level_ids).distinct()
        else:
            queryset = Level.objects.all()
        return queryset


class StakeholderViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    Search by Country
    Limited to logged in users accessible countires
    """
    def list(self, request):
        user_countries = getCountry(request.user)
        queryset = Stakeholder.objects.all().filter(country__in=user_countries)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    filter_fields = ('country__country',)
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    queryset = Stakeholder.objects.all()
    serializer_class = StakeholderSerializer


class ExternalServiceViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    """
    queryset = ExternalService.objects.all()
    serializer_class = ExternalServiceSerializer


class ExternalServiceRecordViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    """
    queryset = ExternalServiceRecord.objects.all()
    serializer_class = ExternalServiceRecordSerializer


class StrategicObjectiveViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    """
    queryset = StrategicObjective.objects.all()
    serializer_class = StrategicObjectiveSerializer


class StakeholderTypeViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    """
    queryset = StakeholderType.objects.all()
    serializer_class = StakeholderTypeSerializer


class CapacityViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    """
    queryset = Capacity.objects.all()
    serializer_class = CapacitySerializer


class EvaluateViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    """
    queryset = Evaluate.objects.all()
    serializer_class = EvaluateSerializer


class ProfileTypeViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    """
    queryset = ProfileType.objects.all()
    serializer_class = ProfileTypeSerializer


class ProvinceViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    """
    queryset = Province.objects.all()
    serializer_class = ProvinceSerializer


class DistrictViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    """
    queryset = District.objects.all()
    serializer_class = DistrictSerializer


class AdminLevelThreeViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    """
    queryset = AdminLevelThree.objects.all()
    serializer_class = AdminLevelThreeSerializer


class VillageViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    """
    queryset = Village.objects.all()
    serializer_class = VillageSerializer


class ContactViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    """
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer


class DocumentationViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    """
    queryset = Documentation.objects.all()
    serializer_class = DocumentationSerializer


class CollectedDataViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    """

    def list(self, request):
        user_countries = getCountry(request.user)
        queryset = CollectedData.objects.all().filter(program__country__in=user_countries)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    filter_fields = ('indicator__program__country__country', 'indicator__program__name')
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    queryset = CollectedData.objects.all()
    serializer_class = CollectedDataSerializer
    pagination_class = SmallResultsSetPagination


class TolaTableViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    """

    def list(self, request):
        #user_countries = getCountry(request.user)
        #queryset = TolaTable.objects.all().filter(country__in=user_countries)
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get_queryset(self):
        user_countries = getCountry(self.request.user)
        queryset = TolaTable.objects.filter(country__in=user_countries)
        table_id = self.request.query_params.get('table_id', None)
        if table_id is not None:
            queryset = queryset.filter(table_id=table_id)
        return queryset

    filter_fields = ('table_id', 'country__country', 'collecteddata__indicator__program__name')
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    serializer_class = TolaTableSerializer
    pagination_class = StandardResultsSetPagination


class DisaggregationValueViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    """

    def list(self, request):
        user_countries = getCountry(request.user)
        queryset = DisaggregationValue.objects.all().filter(country__in=user_countries)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    filter_fields = ('country__country', 'indicator__program__name')
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    queryset = DisaggregationValue.objects.all()
    serializer_class = DisaggregationValueSerializer
    pagination_class = StandardResultsSetPagination


class ProjectAgreementViewSet(APIDefaultsMixin, viewsets.ModelViewSet):
    """API endpoint for getting ProjectAgreement."""

    queryset = ProjectAgreement.objects.order_by('create_date')
    serializer_class = AgreementSerializer


class LoggedUserViewSet(APIDefaultsMixin, viewsets.ModelViewSet):
    """API endpoint for getting Logged Users."""

    queryset = LoggedUser.objects.all()
    serializer_class = LoggedUserSerializer


class ChecklistViewSet(APIDefaultsMixin, viewsets.ModelViewSet):
    queryset = Checklist.objects.all()
    serializer_class = ChecklistSerializer


class OrganizationViewSet(APIDefaultsMixin, viewsets.ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer


class ProgramTargetFrequencies(viewsets.ViewSet):
    def list(self, request):
        program = get_object_or_404(Program, pk=request.query_params.get('program_id', None))
        queryset = program.indicator_set.exclude(
            models.Q(target_frequency=Indicator.EVENT) | models.Q(target_frequency__isnull=True)
            ).values('target_frequency').distinct().order_by('target_frequency')
        serializer = ProgramTargetFrequenciesSerializer(queryset, many=True)
        return Response(serializer.data)
