
// State of what is currently being filtered
let gas_tank_filter_target;
let gas_tank_filter_target_positive;
let selected_indicator_ids = [];
let selected_indicator_levels = [];


function hide_row_factory(positive, target) {
    return function() {
        let elem = $(this);
        let this_show = 1;

        if (target === "results_evidence") {
            this_show = elem.data('has-evidence') * positive;
        } else if (target === "reported_results") {
            this_show = elem.data('reported-results') * positive;
        } else if (target === "targets_defined") {
            this_show = elem.data('defined-targets') * positive;
        }

        let indicator_id = elem.data('indicator-id'); // int;
        let indicator_level_ids = elem.data('indicator-level-ids'); // array of ints

        let hideElem = function() {
            elem.hide();
            elem.next().hide();
        };

        if (this_show <= 0) {
            hideElem();
        } else if (selected_indicator_ids.length > 0 && selected_indicator_ids.indexOf(indicator_id) < 0) {
            hideElem();
        } else if (selected_indicator_levels.length > 0 && !indicator_level_ids.some(function (r) {
            return selected_indicator_levels.indexOf(r) >= 0
        })) {
            hideElem();
        } else  {
            elem.show();
            elem.next().show();
        }
    }
}

function apply_filters_to_indicator_rows() {
    let callback = hide_row_factory(gas_tank_filter_target_positive, gas_tank_filter_target);
    $('.indicators-list__row').each(callback);
}

$(document).ready(function() {
    let default_list_title = $('#indicators-list-title').text();

    // Apply top level gas tank filters
    $('.filter-trigger').on('click', function(e) {
        e.preventDefault();
        let target, positive, highlighted_tab, list_title;
        highlighted_tab = $(this);
        target = $(this).data('target');
        list_title = $(this).data('list-title');
        positive = $(this).data('target-positive');
        if (positive === 0) {
            return;
        }

        $('.gauge').removeClass('is-highlighted');
        highlighted_tab.addClass('is-highlighted');
        $('#indicators-list-title').text(list_title);
        $('#show-all-indicators').removeClass('is-display-none');


        clear_side_bar_filters();
        gas_tank_filter_target = target;
        gas_tank_filter_target_positive = positive;
        apply_filters_to_indicator_rows();
    });

    // Clear all page filters
    $('#show-all-indicators').on('click', function(e) {
        $('.gauge').removeClass('is-highlighted');
        $('#show-all-indicators').addClass('is-display-none');
        $('#indicators-list-title').text(default_list_title);

        clear_side_bar_filters();
        gas_tank_filter_target = '';
        apply_filters_to_indicator_rows();
    });

    // indicator/level filters
    const indicators_select = $("#id_indicators");
    const levels_select = $("#id_levels");

    let multiselectOptions = {
        includeSelectAllOption: true,
        enableFiltering: true,
        enableCaseInsensitiveFiltering: true,
        numberDisplayed: 1,
        maxHeight: 320,
        buttonClass: 'btn form-control',
        templates: {
            filter: '<li class="multiselect-item filter"><div class="input-group"><input class="form-control multiselect-search" type="text"></div></li>',
            filterClearBtn: '<span class="input-group-btn"><button class="btn btn-default multiselect-clear-filter" type="button"><i class="fas fa-times-circle"></i></button></span>',
        }
    };

    function on_indicators_change() {
        selected_indicator_ids = indicators_select.find('option:selected').map(function() { return parseInt($(this).val()) }).get();
        apply_filters_to_indicator_rows();
    }

    function on_levels_change() {
        selected_indicator_levels = levels_select.find('option:selected').map(function() { return parseInt($(this).val()) }).get();
        apply_filters_to_indicator_rows();
    }

    function clear_side_bar_filters() {
        // these do not trigger any callbacks
        indicators_select.multiselect('deselectAll', false);
        indicators_select.multiselect('updateButtonText');
        levels_select.multiselect('deselectAll', false);
        levels_select.multiselect('updateButtonText');

        selected_indicator_ids = [];
        selected_indicator_levels = [];
    }

    indicators_select.multiselect(Object.assign(multiselectOptions, {
        onChange: on_indicators_change,
        onSelectAll: on_indicators_change,
        onDeselectAll: on_indicators_change,
    }));
    levels_select.multiselect(Object.assign(multiselectOptions, {
        onChange: on_levels_change,
        onSelectAll: on_levels_change,
        onDeselectAll: on_levels_change,
    }));
});