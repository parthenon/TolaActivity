import React from 'react';
import ReactDOM from 'react-dom';
import {IndicatorList} from '../../components/indicator_list';
import {ProgramPageStore, ProgramPageUIStore} from "../../models";

import jsContext from '../fixtures/jsContext';

import '../test_helpers/django_i18n_stubs';

const rootStore = new ProgramPageStore(jsContext.indicators, jsContext.program);
const uiStore = new ProgramPageUIStore();

describe('IndicatorList', () => {
    it('renders without crashing', () => {
        const div = document.createElement('div');
        ReactDOM.render(<IndicatorList rootStore={rootStore} uiStore={uiStore}/>, div);
    });
});
