from tola import views
from tola.views import *
from feed.views import (
    UserViewSet, ProgramViewSet, SectorViewSet, ProjectTypeViewSet, SiteProfileViewSet, OfficeViewSet,
    CountryViewSet, AgreementViewSet, CompleteViewSet, IndicatorViewSet, ReportingFrequencyViewSet,
    TolaUserViewSet, IndicatorTypeViewSet, ObjectiveViewSet, DisaggregationTypeViewSet, LevelViewSet,
    ExternalServiceViewSet, ExternalServiceRecordViewSet, StrategicObjectiveViewSet, StakeholderViewSet,
    StakeholderTypeViewSet, CapacityViewSet, EvaluateViewSet, ProfileTypeViewSet, ProvinceViewSet,
    DistrictViewSet, AdminLevelThreeViewSet, VillageViewSet, ContactViewSet, DocumentationViewSet,
    CollectedDataViewSet, TolaTableViewSet, DisaggregationValueViewSet, ProjectAgreementViewSet,
    LoggedUserViewSet, ChecklistViewSet, OrganizationViewSet, PogramIndicatorReadOnlyViewSet,
    PeriodicTargetReadOnlyViewSet, ProgramTargetFrequencies
)
from django.conf.urls import include, url
# Import i18n_patterns
from django.views.i18n import JavaScriptCatalog
from django.views.generic import TemplateView
from rest_framework import routers
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.authtoken import views as auth_views
from django.contrib.auth import views as authviews

from tola import views as tolaviews
from indicators.views.views_indicators import ProgramPage

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()
admin.site.site_header = 'Tola Activity administration'
from workflow.views import dated_target_info

#REST FRAMEWORK
router = routers.DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'programs', ProgramViewSet)
router.register(r'sector', SectorViewSet, base_name='sectors')
router.register(r'projecttype', ProjectTypeViewSet)
router.register(r'office', OfficeViewSet)
router.register(r'siteprofile', SiteProfileViewSet)
router.register(r'country', CountryViewSet)
router.register(r'initiations', AgreementViewSet)
router.register(r'tracking', CompleteViewSet)
router.register(r'indicator', IndicatorViewSet)
router.register(r'reportingfrequency', ReportingFrequencyViewSet)
router.register(r'tolauser', TolaUserViewSet)
router.register(r'indicatortype', IndicatorTypeViewSet)
router.register(r'objective', ObjectiveViewSet)
router.register(r'disaggregationtype', DisaggregationTypeViewSet)
router.register(r'level', LevelViewSet)
router.register(r'externalservice', ExternalServiceViewSet)
router.register(r'externalservicerecord', ExternalServiceRecordViewSet)
router.register(r'strategicobjective', StrategicObjectiveViewSet)
router.register(r'stakeholder', StakeholderViewSet)
router.register(r'stakeholdertype', StakeholderTypeViewSet)
router.register(r'capacity', CapacityViewSet)
router.register(r'evaluate', EvaluateViewSet)
router.register(r'profiletype', ProfileTypeViewSet)
router.register(r'province', ProvinceViewSet)
router.register(r'district', DistrictViewSet)
router.register(r'adminlevelthree', AdminLevelThreeViewSet)
router.register(r'village', VillageViewSet)
router.register(r'contact', ContactViewSet)
router.register(r'documentation', DocumentationViewSet)
router.register(r'collecteddata', CollectedDataViewSet)
router.register(r'tolatable', TolaTableViewSet, base_name='tolatable')
router.register(r'disaggregationvalue', DisaggregationValueViewSet)
router.register(r'projectagreements', ProjectAgreementViewSet)
router.register(r'loggedusers', LoggedUserViewSet)
router.register(r'checklist', ChecklistViewSet)
router.register(r'organization', OrganizationViewSet)
router.register(r'pindicators', PogramIndicatorReadOnlyViewSet, base_name='pindicators')
router.register(r'periodictargets', PeriodicTargetReadOnlyViewSet, base_name='periodictargets')
router.register(r'programtargetfrequencies', ProgramTargetFrequencies, base_name='programtargetfrequencies')

urlpatterns = [
                url(r'^jsi18n/$', JavaScriptCatalog.as_view(), name='javascript-catalog'),

                # rest framework
                url(r'^api/', include(router.urls)),
                url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
                url(r'^api-token-auth/', auth_views.obtain_auth_token),

                # enable the admin:
                url(r'^admin/', include(admin.site.urls)),

                # enable admin documentation:
                url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

                url(r'^bootstrap/', TemplateView.as_view(template_name="bootstrap4.html")),
                url(r'^datedtargetinfo/(?P<pk>\w+)/$', dated_target_info, name='datedtargetinfo'),
                # internationalization
                url(r'^i18n/', include('django.conf.urls.i18n')),

                # Site home page filtered by country
                url(r'^(?P<selected_country>\w+)/$', views.index, name='index'),

                # Site home page
                url(r'^$', views.index, name='index'),

                # program page
                url(r'^program/(?P<program_id>\d+)/(?P<indicator_id>\d+)/(?P<type_id>\d+)/$',
                    ProgramPage.as_view(), name='program_page'),

                # program ajax update for metrics
                url(r'^program/(?P<program_id>\d+)/metrics/$',
                    ProgramPage.as_view(metrics=True), name='program_metrics'),

                # app include of workflow urls
                url(r'^workflow/', include('workflow.urls')),

                # app include of indicator urls
                url(r'^indicators/', include('indicators.urls')),

                # app include of customdashboard urls
                url(r'^customdashboard/', include('customdashboard.urls')),

                # app include of reports urls
                url(r'^reports/', include('reports.urls')),

                # app include of workflow urls
                url(r'^formlibrary/', include('formlibrary.urls')),

                # app include of configurable dashboard urls
                # url(r'^configurabledashboard/', include('configurabledashboard.urls')),

                # local login
                url(r'^login/$', authviews.login, name='login'),
                url(r'^accounts/login/$', authviews.login, name='login'),
                url(r'^accounts/logout/$', views.logout_view, name='logout'),

                # accounts
                url(r'^accounts/profile/$', views.profile, name='profile'),
                url(r'^accounts/register/$', views.register, name='register'),

                #bookmarks
                url(r'^bookmark_list', BookmarkList.as_view(), name='bookmark_list'),
                url(r'^bookmark_add', BookmarkCreate.as_view(), name='bookmark_add'),
                url(r'^bookmark_update/(?P<pk>\w+)/$', BookmarkUpdate.as_view(), name='bookmark_update'),
                url(r'^bookmark_delete/(?P<pk>\w+)/$', BookmarkDelete.as_view(), name='bookmark_delete'),


                # Auth backend URL's
                url('', include('django.contrib.auth.urls', namespace='auth')),
                #url('', include('social.apps.django_app.urls', namespace='social')),
                url('', include('social_django.urls', namespace='social'))
                #url(r'^oauth/', include('social_django.urls', namespace='social')),

    ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
