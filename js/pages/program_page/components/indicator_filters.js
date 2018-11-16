import React from 'react';
import classNames from 'classnames';
import { observer } from "mobx-react"
import eventBus from '../../../eventbus';


// TODO: make reusable
/*
  Wrap bootstrap-multiselect

  Props:

    - options: list of objects with 'value' and 'label' (sssumes values are ints!)
    - selected: single value, or array of values of selected options
    - onSelectCb: a callback function that takes a list of selected values
 */
class MultiSelect extends React.Component {
    constructor(props) {
        super(props);

        this.onChange = this.onChange.bind(this);
    }

    onChange() {
        let selectedValues = this.$el.find('option:selected').map(function() { return parseInt($(this).val()) }).get();
        console.log(selectedValues);

        if (this.props.onSelectCb) {
            this.props.onSelectCb(selectedValues);
        }
    }

    componentDidMount() {
        const options = this.props.options;

        const multiSelectOptions = {
            includeSelectAllOption: true,
            enableFiltering: true,
            enableCaseInsensitiveFiltering: true,
            numberDisplayed: 1,
            maxHeight: 320,
            buttonClass: 'btn form-control',
            templates: {
                filter: '<li class="multiselect-item filter"><div class="input-group"><input class="form-control multiselect-search" type="text"></div></li>',
                filterClearBtn: '<span class="input-group-btn"><button class="btn btn-default multiselect-clear-filter" type="button"><i class="fas fa-times-circle"></i></button></span>',
            },

            onChange: this.onChange,
            onSelectAll: this.onChange,
            onDeselectAll: this.onChange,
        };

        // jquery ref to select element
        this.$el = $(this.el);

        // initial setup of BS multiselect
        this.$el.multiselect(multiSelectOptions);

        // set options list
        this.$el.multiselect('dataprovider', options);
    }

    componentDidUpdate(prevProps) {
        const options = this.props.options;
        const selected = this.props.selected;

        // Note: This is pretty terrible if options is huge
        if (JSON.stringify(prevProps.options) !== JSON.stringify(options)) {
            // set options list
            this.$el.multiselect('dataprovider', options);

            // Re-set selected from props
            if (selected !== undefined) {
                this.$el.multiselect('select', selected);
            } else {
                // this component is maintaining selected state internally, so notify
                // the world that we just reset the selection and nothing is selected
                this.onChange();
            }
        }
    }

    componentWillUnmount() {
        this.$el.multiselect('destroy');
      }

    render() {
        return <select className="form-control" ref={el => this.el = el} multiple="multiple" />
    }
}


@observer
export class IndicatorFilters extends React.Component{

    constructor(props) {
        super(props);

        this.state = {
        }
    }


    render() {
        const indicatorLevels = this.props.indicatorLevels;
        const currentIndicatorFilter = this.props.uiStore.currentIndicatorFilter;
        const indicators = this.props.rootStore.indicatorStore.filterIndicators(currentIndicatorFilter);
        const selectedIndicatorIds = this.props.uiStore.selectedIndicatorIds;
        const selectedIndicatorLevelIds = this.props.uiStore.selectedIndicatorLevelIds;

        const indicatorSelectOptions = indicators.map(i => {
            return {
                value: i.id,
                label: i.name,
            }
        });

        const indicatorLevelSelectOptions = indicatorLevels.map(il => {
            return {
                value: il.id,
                label: il.name,
            }
        });

        return <React.Fragment>
            <div className="form-group" id="id_div_indicators">
                <label htmlFor="id_indicators" className="col-form-label text-uppercase">
                    {gettext('Indicators')}
                </label>
                <div className="form-group-row">
                    <MultiSelect options={indicatorSelectOptions}
                                 selected={selectedIndicatorIds}
                                 onSelectCb={(selectedIndicatorIds) => eventBus.emit('select-indicators-to-filter', selectedIndicatorIds)} />
                </div>
            </div>

            <div className="form-group" id="id_div_levels">
                <label htmlFor="id_levels" className="col-form-label text-uppercase">
                    {gettext('Levels')}
                </label>
                <div className="form-group-row">
                    <MultiSelect options={indicatorLevelSelectOptions}
                                 selected={selectedIndicatorLevelIds}
                                 onSelectCb={(selectedIndicatorLevelIds) => eventBus.emit('select-indicator-levels-to-filter', selectedIndicatorLevelIds)} />
                </div>
            </div>
        </React.Fragment>
    }
}
