import re
import time
import unittest

from django.test import tag

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as expect
from selenium.webdriver.support.ui import WebDriverWait

# from tola.settings import local

def is_iso_date(datestr):
    if re.match('\d{4}-\d{2}-\d{2}', datestr):
        return True
    else:
        return False

@tag('functional')
class IpttReportTests(unittest.TestCase):
    baseurl = 'http://localhost:8000/'
    # username = local.app_settings['TOLAUSER']
    # password = local.app_settings['TOLAPASS']

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
    
    def test_iptt_localizes_lop_target_dates(self):
        browser = self.browser
        testurl = self.baseurl + 'indicators/iptt_report/265/targetperiods/?targetperiods=1&timeframe=1'
        browser.get(testurl)

        start_period = WebDriverWait(browser, 2).until(
            expect.element_to_be_clickable((By.ID, 'id_start_period'))
        )
        self.assertFalse(is_iso_date(start_period.text), msg='Unexpected ISO-formatted start period')

        end_period = WebDriverWait(browser, 2).until(
            expect.element_to_be_clickable((By.ID, 'id_end_period'))
        )
        self.assertFalse(is_iso_date(end_period.text), msg='Unexpected ISO-formatted end period')
    
    def test_iptt_localizes_midline_endline_target_dates(self):
        browser = self.browser
        testurl = self.baseurl + 'indicators/iptt_report/542/targetperiods/?targetperiods=2&timeframe=1'
        browser.get(testurl)

        start_period = WebDriverWait(browser, 2).until(
            expect.element_to_be_clickable((By.ID, 'id_start_period'))
        )
        self.assertFalse(is_iso_date(start_period.text), msg='Unexpected ISO-formatted start period')

        end_period = WebDriverWait(browser, 2).until(
            expect.element_to_be_clickable((By.ID, 'id_end_period'))
        )
        self.assertFalse(is_iso_date(end_period.text), msg='Unexpected ISO-formatted end period')


if __name__ == '__main__':
    unittest.main(verbosity=2)
