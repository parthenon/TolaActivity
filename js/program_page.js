

// On pinned report delete btn click
$('[data-delete-pinned-report]').click(function (e) {
    e.preventDefault();

    let prId = $(this).data('deletePinnedReport');
    let pinnedReport = $(this).closest('.pinned-report');

    if (window.confirm(gettext('Warning: This action connot be undone. Are you sure you want to delete this pinned report?'))) {
        $.ajax({
            type: "POST",
            url: jsContext.delete_pinned_report_url,
            data: {
                pinned_report_id: prId,
            },
            success: function () {
                pinnedReport.remove();
            }
        });
    }
});
