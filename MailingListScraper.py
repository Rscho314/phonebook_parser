# -*- coding: utf-8 -*-
"""
Created on Fri Mar  9 16:01:35 2018

@author: raoul
"""
import logging
import re
import sqlite3
import time
from copy import deepcopy
from functools import wraps
from unidecode import unidecode
from selenium.common import exceptions
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
#from selenium.webdriver.firefox.options import Options

# Setup logging-----------------------------------------
logging.basicConfig(filename='MailingListScraper.log', level=logging.INFO)

class MailingListScraper(object):
    '''A mailing list scraper'''

    log = logging.getLogger()

    class Retry(object):
        '''WARNING: Works only for functions without return (TODO: improve that)'''
        def __init__(self, e, n, t):
            self.e = e
            self.n = n
            self.t = t

        def __call__(self, f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                for attempt in range(self.n):
                    try:
                        f(*args, **kwargs)
                    except self.e as err:
                        if attempt < (self.n - 1):
                            MailingListScraper.log.warning("%s, on attempt %d",
                                                           err.msg,
                                                           attempt + 1)
                            time.sleep(self.t)
                        else:
                            MailingListScraper.log.critical("%s, failure on final attempt",
                                                            err.msg,
                                                            exc_info=True)
                            raise err from None
            return wrapper

    def __init__(self, db, mailing_list):
        self._db = db
        self.mailing_list = mailing_list
        self._mailing_list_content = None
        self._mailing_list_content_copy = None
        self._dbcon = None
        self._dbcur = None
        self._driver = None
        self._wait = None

    def connect_db(self):
        try:
            self._dbcon = sqlite3.connect(self._db)
            self._dbcur = self._dbcon.cursor()
            MailingListScraper.log.info("Connection to database %s successful.", self._db)
        except Exception as e:
            MailingListScraper.log.critical(
                "Could not connect to %s, aborting.", self._db, exc_info=True)
            raise e from None

    def create_db_table(self):
        try:
            self._dbcur.execute("""CREATE TABLE people (
            id INTEGER PRIMARY KEY,
            firstname TEXT,
            lastname TEXT,
            email TEXT UNIQUE,
            function TEXT,
            department TEXT,
            society TEXT,
            office TEXT)""")
            MailingListScraper.log.info("Sqlite table creation on %s successful.", self._db)
        except sqlite3.OperationalError:
            MailingListScraper.log.error("Could not create sqlite table.", exc_info=True)

    def create_webdriver(self):
        try:
            #opt = Options()
            #opt.add_argument("-headless")
            cap = webdriver.common.desired_capabilities.DesiredCapabilities().FIREFOX
            cap["marionette"] = False
            self._driver = webdriver.Firefox(capabilities=cap)
            self._wait = WebDriverWait(self._driver, 10)
            MailingListScraper.log.info("Webdriver creation successful.")
        except exceptions.WebDriverException as e:
            MailingListScraper.log.critical(
                "Could not create webdriver, aborting.", exc_info=True)
            raise e from None

    @Retry(exceptions.TimeoutException, 5, 5)
    def navigate_to(self, address):
        self._driver.get(address)


    @Retry(exceptions.TimeoutException, 5, 5)
    def navigate_to_contacts(self):
        self._wait.until(EC.element_to_be_clickable((By.ID, "_ariaId_20"))).click()

    @Retry(exceptions.TimeoutException, 5, 5)
    def navigate_to_distribution_lists(self):
        self._wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "span[title='All Distribution Lists']"))).click()

    @Retry(exceptions.TimeoutException, 5, 5)
    def navigate_to_mailing_list(self):
        '''Takes the driver to the named mailing list'''
        self._wait.until(
            EC.element_to_be_clickable((By.XPATH,
                                        "//*[text()='{}']".format(
                                            self.mailing_list)))).click()

    def login_1st_step(self):
        user = input("Please enter username:\n")
        pincode = input("Please enter pincode:\n")
        try:
            userinput = self._wait.until(EC.presence_of_element_located((By.NAME, "username")))
            passinput = self._wait.until(EC.presence_of_element_located((By.NAME, "password")))
            userinput.send_keys(user)
            passinput.send_keys(pincode)
            self._driver.find_element_by_class_name("credentials_input_submit").click()
        except Exception as e:
            MailingListScraper.log.critical("Login 1st step failed", exc_info=True)
            raise e from None

    def login_2nd_step(self):
        '''Uses paper card'''
        try:
            challenge_phrase = self._wait.until(EC.presence_of_element_located(
                (By.ID, "credentials_table_header")))
            challenge = list(input(challenge_phrase.text + '\n'))
            challenge_field = self._driver.find_element_by_class_name(
                "credentials_input_password")
            challenge_field.send_keys(challenge)
            self._driver.find_element_by_class_name("credentials_input_submit").click()
        except Exception as e:
            MailingListScraper.log.critical("Login 2nd step failed", exc_info=True)
            raise e from None

    def get_mailing_list_chunk(self):
        '''Get the 50 people mailing list chunk'''
        mlc = self._wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[@aria-label='Membres du groupe']")))
        self._wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "_pe_7")))
        self._mailing_list_content = mlc.find_elements_by_class_name("_pe_7")

    def load_next_mailing_list_chunk(self):
        '''scrolls to the bottom of the list chunk to trigger a reload event'''
        self._mailing_list_content_copy = deepcopy(self._mailing_list_content)
        self._driver.execute_script("arguments[0].scrollIntoView(true);",
                                    self._mailing_list_content[-1])

    def verify_isnew_mailing_list_chunk(self):
        '''Detects the end of the list by detecting that it has not been reloaded'''
        self._wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[@aria-label='Membres du groupe']")))
        oldmails = [self.scrape_mailing_list_entry_email(entry)
                    for entry in self._mailing_list_content_copy]
        newmails = [self.scrape_mailing_list_entry_email(entry)
                    for entry in self._mailing_list_content]
        if oldmails == newmails:
            self.finish_scrape()

    def scrape_individual_data(self):
        '''Returns data fields for an individual'''
        datafields = self._wait.until(EC.presence_of_element_located((By.CLASS_NAME,
                                                                      '_rpc_r')))
        self._wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, '_rpc_i1')))
        subjectdata = datafields.find_elements_by_class_name('_rpc_i1')
        t = {'function': 'Fonction',
             'department': 'Département',
             'society': 'Société',
             'office': 'Office'}
        individual_data = {}
        individual_data['email'] = datafields.find_element_by_css_selector(
            "span[autoid='_rpc_6']").text
        for k, v in t.items():
            individual_data[k] = unidecode(
                [e.text.split(':') for e in subjectdata if v in e.text][0][1])
        name = unidecode(self._driver.find_element_by_css_selector("span[autoid='_pe_p']").text)
        individual_data['lastname'] = ' '.join(
            re.findall(r"\b([A-Z]+[-][A-Z]+|[A-Z]+)\b", name))
        individual_data['firstname'] = ' '.join(
            re.findall(r"\b([A-Z][a-z]+[-][A-Z][a-z]+|[A-Z][a-z]+)\b", name))
        try:
            with self._dbcon as c:
                c.execute('''INSERT INTO people VALUES (
                NULL,:firstname,:lastname,:email,:function,:department,:society,:office)''',
                          individual_data)
        except sqlite3.IntegrityError:
            MailingListScraper.log.info("error on insertion of record: %s, "\
                                        "likely due to double entry",
                                        individual_data['email'])

    def scrape_mailing_list_entry_email(self, entry):
        return entry.find_element_by_css_selector("span[autoid='_pe_k']").text

    def navigate_to_mailing_list_entry(self):
        '''read the first entry not present in db, and detects the end of list'''
        self._wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "span[autoid='_pe_k']")))
        for entry in self._mailing_list_content:
            email = self.scrape_mailing_list_entry_email(entry)
            self._dbcur.execute("SELECT id FROM people WHERE email = ?", (email,))
            rec = self._dbcur.fetchone()
            if rec is None:
                entry.click()  # entry not in db, navigate to it
                self.scrape_individual_data()
                break
            elif entry == self._mailing_list_content[-1]:
                self.load_next_mailing_list_chunk()
                self.verify_isnew_mailing_list_chunk()
                break

    def finish_scrape(self):
        '''Cleanup and quit'''
        self._dbcur.execute("SELECT * FROM people ORDER BY id DESC LIMIT 1")
        MailingListScraper.log.info("Scraping finished successfully, %d rows inserted into db.",
                                    self._dbcur.fetchone()[0])
        self._dbcon.close()
        self._driver.quit()
