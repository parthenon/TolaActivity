import {IndicatorStore} from '../models';
import jsContext from './fixtures/jsContext';


const indicators = jsContext.indicators;


describe('IndicatorStore', () => {

    it('filters by indicators needing targets', () => {
        let is = new IndicatorStore(indicators);
        let indicatorsNeedingTargets = is.getIndicatorsNeedingTargets;
        expect(indicatorsNeedingTargets.length).toEqual(1);
    });

    it('find the sum of all results on all indicators in the store', () => {
        let is = new IndicatorStore(indicators);
        expect(is.getTotalResultsCount).toEqual(3);
    });

    it('find the sum of all results with evidence on all indicators in the store', () => {
        let is = new IndicatorStore(indicators);
        expect(is.getTotalResultsWithEvidenceCount).toEqual(2);
    });

});
