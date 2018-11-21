import {IndicatorStore} from '../models';
import jsContext from './fixtures/jsContext';


const indicators = jsContext.indicators;


describe('IndicatorStore', () => {

    it('filters by indicators needing targets', () => {
        let is = new IndicatorStore(indicators);
        let indicatorsNeedingTargets = is.getIndicatorsNeedingTargets;
        expect(indicatorsNeedingTargets.length).toEqual(1);
    });

});
