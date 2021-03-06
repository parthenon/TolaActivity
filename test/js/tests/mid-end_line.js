import IndPage from '../pages/indicators.page'
import NavBar from '../pages/navbar.page'
import TargetsTab from '../pages/targets.page'
import Util from '../lib/testutil'
import { expect } from 'chai'

describe('Midline and endline target frequency', function() {
  // Disable timeouts
  this.timeout(0)

  before(function () {
    browser.windowHandleMaximize()
    Util.loginTola()
  })

  it('should require value in Midline target field', function() {
  NavBar.Indicators.click()
  expect('Program Indicators' == IndPage.getPageName())
  IndPage.createBasicIndicator()

  // This should succeed
  TargetsTab.setIndicatorName('Midline target required testing')
  TargetsTab.setUnitOfMeasure('Furlongs per fortnight')
  TargetsTab.setLoPTarget(38)
  TargetsTab.setBaseline(39)
  TargetsTab.setTargetFrequency('Midline and endline')
  TargetsTab.saveIndicatorChanges()

  // This should fail without midline target
  TargetsTab.setEndlineTarget(44)
  TargetsTab.saveIndicatorChanges()
  let errorMessage = TargetsTab.getTargetValueErrorHint()
  expect(true === errorMessage.includes('Please enter a target value.'))

  })

  it('should require value in Endline target field', function() {
  NavBar.Indicators.click()
  IndPage.createBasicIndicator()

  // This should succeed
  TargetsTab.setIndicatorName('Endline target required testing')
  TargetsTab.setUnitOfMeasure('Gargoyles per gable')
  TargetsTab.setLoPTarget(57)
  TargetsTab.setBaseline(58)
  TargetsTab.setTargetFrequency('Midline and endline')
  TargetsTab.saveIndicatorChanges()

  // This should fail without endline target
  TargetsTab.setMidlineTarget(63)
  TargetsTab.saveIndicatorChanges()
  let errorMessage = TargetsTab.getTargetValueErrorHint()
  expect(true === errorMessage.includes('Please enter a target value.'))
  })
})
