import React from 'react';
import classNames from 'classnames';
import { observer } from "mobx-react"
import eventBus from '../../../eventbus';
import {IndicatorFilter} from "../models";


@observer
class GaugeTank extends React.Component {
    constructor(props) {
        super(props);

        this.onGuageClick = this.onGuageClick.bind(this);
    }

    onGuageClick() {
        eventBus.emit('apply-gauge-tank-filter', this.props.filterType);
    }

    render() {
        const tickCount = 10;

        const {allIndicatorsLength, filteredIndicatorsLength, title, filledLabel, unfilledLabel, cta} = this.props;

        const filterType = this.props.filterType;
        const currentIndicatorFilter = this.props.currentIndicatorFilter;

        const isHighlighted = filterType === currentIndicatorFilter;

        const unfilledPercent = allIndicatorsLength > 0 ? Math.round((filteredIndicatorsLength / allIndicatorsLength) * 100) : 100;
        const filledPercent = 100 - unfilledPercent;

        return <div className={classNames('gauge', 'filter-trigger', {'is-highlighted': isHighlighted})}
                    data-target-positive="-1"
                    onClick={this.onGuageClick}>
            <h6 className="gauge__title">{title}</h6>
            <div className="gauge__overview">
                <div className="gauge__graphic gauge__graphic--tank">
                    <div className="graphic__tick-marks">
                        {[...Array(tickCount)].map((e, i) => <div key={i} className="graphic__tick" />)}
                    </div>
                    <div className="graphic__tank--unfilled" style={{'flexBasis': `${unfilledPercent}%`}} />
                    <div className="graphic__tank--filled" style={{'flexBasis': `${filledPercent}%`}} />
                </div>
                <div className="gauge__labels">
                    <div className="gauge__label text-muted">
                        {unfilledPercent}% {unfilledLabel}
                    </div>
                    <div className="gauge__label">
                        <span className="gauge__value">{filledPercent}% {filledLabel}</span>
                    </div>
                </div>
            </div>
            {unfilledPercent > 0 &&
            <div className="gauge__cta">
                <span className="btn-link btn-inline"><i
                    className="fas fa-exclamation-triangle text-warning"/> {cta}</span>
            </div>
            }
        </div>
    }
}


@observer
class GaugeBand extends React.Component {
    constructor(props) {
        super(props);

        this.handledFilterTypes = new Set([
            IndicatorFilter.nonReporting,
            IndicatorFilter.aboveTarget,
            IndicatorFilter.belowTarget,
            IndicatorFilter.onTarget,
        ]);

        this.onFilterLinkClick = this.onFilterLinkClick.bind(this);
    }

    onFilterLinkClick(e, filterType) {
        e.preventDefault();
        eventBus.emit('apply-gauge-tank-filter', filterType);
    }

    render() {
        const tickCount = 10;

        const {indicatorStore} = this.props;

        const currentIndicatorFilter = this.props.currentIndicatorFilter;

        const isHighlighted = this.handledFilterTypes.has(currentIndicatorFilter);

        const totalIndicatorCount = indicatorStore.indicators.length;
        const nonReportingCount = indicatorStore.getIndicatorsNotReporting.length;
        const highCount = indicatorStore.getIndicatorsAboveTarget.length;
        const lowCount = indicatorStore.getIndicatorsBelowTarget.length;
        const onTargetCount = indicatorStore.getIndicatorsOnTarget.length;

        const makePercent = totalIndicatorCount > 0 ? (x) => Math.round((x / totalIndicatorCount) * 100) : (x) => 0;

        const percentHigh = makePercent(highCount);
        const percentOnTarget = makePercent(onTargetCount);
        const percentBelow = makePercent(lowCount);
        const percentNonReporting = makePercent(nonReportingCount);

        const marginPercent = this.props.indicatorOnScopeMargin * 100;

        return <div className={classNames('gauge', {'is-highlighted': isHighlighted})}>
            <h6 className="gauge__title">{gettext('Indicators on track')}</h6>
            <div className="gauge__overview">
                <div className="gauge__graphic gauge__graphic--performance-band">
                    <div className="graphic__tick-marks">
                        {[...Array(tickCount)].map((e, i) => <div key={i} className="graphic__tick" />)}
                    </div>
                    <div className="graphic__performance-band--above-target"
                         style={{'flexBasis': `${percentHigh}%`}}/>
                    <div className="graphic__performance-band--on-target"
                         style={{'flexBasis': `${percentOnTarget}%`}}/>
                    <div className="graphic__performance-band--below-target"
                         style={{'flexBasis': `${percentBelow}%`}}/>
                </div>
                <div className="gauge__labels">
                    <div className="gauge__label">

                        <a href="#" className="text-muted" onClick={e => this.onFilterLinkClick(e, IndicatorFilter.nonReporting)}>
                            {
                                /*Translators: shows how many indicators have indicators with non-reporting targets. Example: 31% are non-reporting*/
                                interpolate('%s% are non-reporting', [percentNonReporting])
                            }
                        </a>
                    </div>
                    <div className="gauge__label" onClick={e => this.onFilterLinkClick(e, IndicatorFilter.aboveTarget)}>
                        <a href="#" className="gauge__value--above">
                            {
                                /*Translators: shows how many indicators are a certain percentage above target. Example: 31% are >15% above target*/
                                interpolate('%s% are >%s% above target', [percentHigh, marginPercent])
                            }
                        </a>
                    </div>
                    <div className="gauge__label" onClick={e => this.onFilterLinkClick(e, IndicatorFilter.onTarget)}>
                        <a href="#" className="gauge__value">
                            {
                                /*Translators: shows how many indicators are within a set range of target. Example: 31% are on track*/
                                interpolate('%s% are on track', [percentOnTarget])
                            }
                        </a>
                    </div>
                    <div className="gauge__label" onClick={e => this.onFilterLinkClick(e, IndicatorFilter.belowTarget)}>
                        <a href="#" className="gauge__value--below">
                            {
                                /*Translators: shows how many indicators are a certain percentage below target. Example: 31% are >15% below target*/
                                interpolate('%s% are >%s% below target', [percentBelow, marginPercent])
                            }
                        </a>
                    </div>
                </div>
            </div>
        </div>
    }
}


export const ProgramMetrics = observer(function (props) {
    const program = props.rootStore.program;
    const indicatorStore = props.rootStore.indicatorStore;
    const indicators = indicatorStore.indicators;

    const currentIndicatorFilter = props.uiStore.currentIndicatorFilter;

    const indicatorOnScopeMargin = this.props.indicatorOnScopeMargin;

    if (indicators.length === 0) return null;

    return <aside className="program__status">
        <h2>{gettext("Program metrics")}</h2>
        <div className="status__gauges">

            <GaugeBand currentIndicatorFilter={currentIndicatorFilter}
                       indicatorOnScopeMargin={indicatorOnScopeMargin}
                       indicatorStore={indicatorStore}
            />

            <GaugeTank title={gettext("Indicators with targets")}
                       filledLabel={gettext("have targets defined")}
                       unfilledLabel={gettext("have no targets")}
                       cta={gettext("Add missing targets")}

                       filterType={IndicatorFilter.missingTarget}
                       currentIndicatorFilter={currentIndicatorFilter}

                       allIndicatorsLength={indicators.length}
                       filteredIndicatorsLength={indicatorStore.getIndicatorsNeedingTargets.length}
                       />

            <GaugeTank title={gettext("Indicators with results")}
                       filledLabel={gettext("have reported results")}
                       unfilledLabel={gettext("have no results")}
                       cta={gettext("Add missing results")}

                       filterType={IndicatorFilter.missingResults}
                       currentIndicatorFilter={currentIndicatorFilter}

                       allIndicatorsLength={indicators.length}
                       filteredIndicatorsLength={indicatorStore.getIndicatorsNeedingResults.length}
                       />

            <GaugeTank title={gettext("Results with evidence")}
                       filledLabel={gettext("have evidence")}
                       unfilledLabel={gettext("are missing evidence")}
                       cta={gettext("Add missing evidence")}

                       filterType={IndicatorFilter.missingEvidence}
                       currentIndicatorFilter={currentIndicatorFilter}

                       // The names below are misleading as this gauge is measuring *results*, not indicators
                       allIndicatorsLength={indicatorStore.getTotalResultsCount}
                       filteredIndicatorsLength={indicatorStore.getTotalResultsCount - indicatorStore.getTotalResultsWithEvidenceCount}
                       />

        </div>
    </aside>
});
