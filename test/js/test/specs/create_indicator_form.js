var assert = require('chai').assert;
var expect = require('chai').expect;
var LoginPage = require('../pages/login.page.js');
var IndPage = require('../pages/indicators.page.js');
var TargetsTab = require('../pages/targets.page.js');
var util = require('../lib/testutil.js');
const msec = 1000;
const delay = 10*msec;

describe('Create an Indicator form', function() {
  before(function() {
    // Disable timeouts
    this.timeout(0);
    browser.windowHandleMaximize();
    let parms = util.readConfig();
    LoginPage.open(parms.baseurl);
    LoginPage.setUserName(parms.username);
    LoginPage.setPassword(parms.password);
    LoginPage.clickLoginButton();
  });

  it('should exist', function() {
    IndPage.open();
    // FIXME: pageName should be a property
    assert.equal('Program Indicators', IndPage.pageName());
  });

  it('should have an Indicator Service Templates dropdown', function() {
    TargetsTab.clickNewIndicatorButton();
    let control = $('select#services');
    assert.equal(true, control.isVisible());
    TargetsTab.saveNewIndicator();
  });

  it('should have a Service Indicator dropdown', function() {
    IndPage.clickIndicatorsLink();
    TargetsTab.clickNewIndicatorButton();
    let control = $('select#service_indicator');
    assert.equal(true, control.isVisible());
    TargetsTab.saveNewIndicator();
  });

  it('should have a Country dropdown', function() {
    IndPage.clickIndicatorsLink();
    TargetsTab.clickNewIndicatorButton();
    let control = $('select#country');
    assert.equal(true, control.isVisible());
    TargetsTab.saveNewIndicator();
  });

  it('should have a Program dropdown', function() {
    IndPage.clickIndicatorsLink();
    TargetsTab.clickNewIndicatorButton();
    let control = $('select#program');
    assert.equal(true, control.isVisible());
    TargetsTab.saveNewIndicator();
  });

  it('should have a save button', function() {
    IndPage.clickIndicatorsLink();
    TargetsTab.clickNewIndicatorButton();
    let control = $('form').$('input[value="save"]');
    assert.equal(true, control.isVisible(),
      'Save button is not visible');
    control.click();
  });

  it('should confirm indicator created', function() {
    IndPage.clickIndicatorsLink();
    TargetsTab.clickNewIndicatorButton();
    TargetsTab.saveNewIndicator();
    let message = IndPage.getAlertMsg();
    assert(message.includes('Success, Basic Indicator Created!'),
      'Unexpected message during indicator creation');
  });

  it('should open Indicator detail form after clicking Save button');
  it('should have a Cancel button');
  it('should reset and close form when Cancel button clicked');
  it('should return to previous screen when Cancel button clicked');
  it('should have a Reset button to reset form');
  it('should have a Help link');
  it('should have a Save Changes button');
  it('should have a Reset button');
  it('should have a Cancel button');
  it('should trigger cancel action by pressing Escape key');
  it('should validate input data after clicking Save Changes button');
  it('should validate input data before committing it');
  it('should restore form to pre-edit state when Reset button is clicked');
}); // end create new indicator form tests
