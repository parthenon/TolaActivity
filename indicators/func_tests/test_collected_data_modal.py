import re
import time
import unittest

from django.test import tag

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as expect
from selenium.webdriver.support.ui import WebDriverWait

from tola.settings import local


@tag('functional')
class CollectedDataModalTests(unittest.TestCase):
    baseurl = 'http://localhost:8000/'
    username = local.app_settings['TOLAUSER']
    password = local.app_settings['TOLAPASS']

    def do_login(self):
        browser = self.browser
        browser.get('http://localhost:8000/')

        # Localhost uses Google auth services
        browser.find_element_by_link_text('Google+').click()

        username = WebDriverWait(browser, 2).until(
            expect.presence_of_element_located((By.ID, 'identifierId'))
        )
        username.send_keys(self.username)

        next = WebDriverWait(browser, 2).until(
            expect.presence_of_element_located((By.ID, 'identifierNext'))
        )
        next.click()

        passwd = WebDriverWait(browser, 2).until(
            expect.presence_of_element_located((By.NAME, 'password'))
        )
        # TODO: this is just horrible
        time.sleep(2)
        passwd.send_keys(self.password)

        browser.find_element_by_id('passwordNext').click()
        self.assertIn('Dashboard | TolaActivity', browser.title)

    def setUp(self):
        self.browser = webdriver.Firefox()
        self.do_login()

    def tearDown(self):
        self.browser.quit()

    def test_shows_localized_dates_for_lop_targets(self):
        testurl = self.baseurl + 'indicators/home/442/0/0/'
        self.browser.get(testurl)


        time.sleep(5)

    # def test_shows_localized_dates_for_midline_endline_targets(self):
    #     pass
    #
    # def test_shows_localized_dates_for_event_targets(self):
    #     pass
    #
    # def test_shows_localized_dates_for_annual_targets(self):
    #     pass
    #
    # def test_shows_localized_dates_for_semiannual_targets(self):
    #     pass
    #
    # def test_shows_localized_dates_for_triannual_targets(self):
    #     pass
    #
    # def test_shows_localized_dates_for_quarterly_targets(self):
    #     pass
    #
    # def test_shows_localized_dates_for_monthly_targets(self):
    #     pass

if __name__ == '__main__':
    unittest.main(verbosity=2)
