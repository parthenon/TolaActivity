from django.conf.urls import url

from .views.views_indicators import (
    indicator_create,
    CollectedDataCreate,
    CollectedDataUpdate,
    CollectedDataDelete,
    IndicatorCreate,
    IndicatorDelete,
    IndicatorUpdate,
    IndicatorList,
    IndicatorExport,
    IndicatorReportData,
    CollectedDataReportData,
    collecteddata_import,
    service_json,
    PeriodicTargetView,
    PeriodicTargetDeleteView,
    collected_data_view,
    program_indicators_json,
    programIndicatorReport,
    indicator_report,
    IndicatorReport,
    IndicatorDataExport,
    TVAReport,
    DisaggregationReport,
    TVAPrint,
    DisaggregationPrint,
    api_indicator_view)

from .views.views_reports import (
    IPTTReportQuickstartView,
    IPTT_ReportView,
    IPTT_ReportIndicatorsWithVariedStartDate,
    IPTT_ExcelExport,
    create_pinned_report,
    delete_pinned_report,
    IPTT_ExcelExport,
    IPTT_CSVExport
)


urlpatterns = [
    url(r'^home/(?P<program>\d+)/(?P<indicator>\d+)/(?P<type>\d+)/$', IndicatorList.as_view(), name='indicator_list'),

    url(r'^indicator_create/(?P<id>\d+)/$', indicator_create, name='indicator_create'),

    url(r'^indicator_add/(?P<id>\d+)/$', IndicatorCreate.as_view(), name='indicator_add'),

    url(r'^indicator_update/(?P<pk>\d+)/$', IndicatorUpdate.as_view(), name='indicator_update'),

    url(r'^indicator_delete/(?P<pk>\d+)/$', IndicatorDelete.as_view(), name='indicator_delete'),

    url(r'^periodic_target_delete/(?P<pk>\d+)/$', PeriodicTargetDeleteView.as_view(), name='pt_delete'),

    url(r'^periodic_target_generate/(?P<indicator>\d+)/$', PeriodicTargetView.as_view(), name='pt_generate'),

    url(r'^periodic_target_deleteall/(?P<indicator>\d+)/(?P<deleteall>\w+)/$',
        PeriodicTargetView.as_view(), name='pt_deleteall'),

    url(r'^collecteddata_add/(?P<program>\d+)/(?P<indicator>\d+)/$',
        CollectedDataCreate.as_view(), name='collecteddata_add'),

    url(r'^collecteddata_import/$', collecteddata_import, name='collecteddata_import'),

    url(r'^collecteddata_update/(?P<pk>\d+)/$', CollectedDataUpdate.as_view(), name='collecteddata_update'),

    url(r'^collecteddata_delete/(?P<pk>\d+)/$', CollectedDataDelete.as_view(), name='collecteddata_delete'),

    url(r'^report/(?P<program>\d+)/(?P<indicator>\d+)/(?P<type>\d+)/$', indicator_report, name='indicator_report'),

    url(r'^tvareport/$', TVAReport.as_view(), name='tvareport'),

    url(r'^tvaprint/(?P<program>\d+)/$', TVAPrint.as_view(), name='tvaprint'),

    url(r'^disrep/(?P<program>\d+)/$', DisaggregationReport.as_view(), name='disrep'),

    url(r'^disrepprint/(?P<program>\d+)/$', DisaggregationPrint.as_view(), name='disrepprint'),

    url(r'^report_table/(?P<program>\d+)/(?P<indicator>\d+)/(?P<type>\d+)/$',
        IndicatorReport.as_view(), name='indicator_table'),

    url(r'^program_report/(?P<program>\d+)/$', programIndicatorReport, name='programIndicatorReport'),


    url(r'^export/(?P<id>\d+)/(?P<program>\d+)/(?P<indicator_type>\d+)/$',
        IndicatorExport.as_view(), name='indicator_export'),

    url(r'^service/(?P<service>[-\w]+)/service_json/', service_json, name='service_json'),

    url(r'^collected_data_table/(?P<indicator>\d+)/(?P<program>\d+)/',
        collected_data_view, name='collected_data_view'),

    url(r'^program_indicators/(?P<program>\d+)/(?P<indicator>\d+)/'
        r'(?P<type>\d+)', program_indicators_json, name='program_indicators_json'),

    url(r'^report_data/(?P<id>\w+)/(?P<program>\d+)/(?P<type>\d+)/$',
        IndicatorReportData.as_view(), name='indicator_report_data'),

    url(r'^report_data/(?P<id>\w+)/(?P<program>\d+)/(?P<indicator_type>\d+)/'
        r'export/$',
        IndicatorExport.as_view(),
        name='indicator_export'),

    url(r'^collecteddata_report_data/(?P<program>\d+)/(?P<indicator>\d+)/'
        r'(?P<type>\d+)/$',
        CollectedDataReportData.as_view(),
        name='collecteddata_report_data'),

    url(r'^collecteddata_report_data/(?P<program>\d+)/(?P<indicator>\d+)/'
        r'(?P<type>\d+)/export/$',
        IndicatorDataExport.as_view(),
        name='collecteddata_report_data_export'),

    url(r'^iptt_quickstart/', IPTTReportQuickstartView.as_view(), name='iptt_quickstart'),

    url(r'^iptt_report/(?P<program_id>\d+)/(?P<reporttype>\w+)/$', IPTT_ReportView.as_view(), name='iptt_report'),

    url(r'^iptt_redirect/(?P<program_id>\d+)/$', IPTT_ReportIndicatorsWithVariedStartDate.as_view(),
        name='iptt_redirect'),

    url(r'^iptt_excel/(?P<program_id>\d+)/(?P<reporttype>\w+)/$', IPTT_ExcelExport.as_view(), name='iptt_excel'),

    url(r'^pinned_report/$', create_pinned_report, name='create_pinned_report'),
    url(r'^pinned_report/delete/$', delete_pinned_report, name='delete_pinned_report'),

    url(r'^iptt_csv/(?P<program_id>\d+)/(?P<reporttype>\w+)/$', IPTT_CSVExport.as_view(), name='iptt_csv'),

    # API call for program page
    url(r'^api/indicator/(?P<indicator_id>\d+)', api_indicator_view, name='api_indicator_view'),
]
