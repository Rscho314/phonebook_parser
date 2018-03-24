#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar  9 16:01:35 2018

@author: raoul
"""
import re
import sqlite3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
#from selenium.webdriver.firefox.options import Options
from access_card import CARD, username, password

# Setup database----------------------------------------
con = sqlite3.connect(":memory:")
cur = con.cursor()

con.execute("""CREATE TABLE hug_people (
id INTEGER PRIMARY KEY,
firstname TEXT,
lastname TEXT,
email TEXT,
function TEXT,
department TEXT,
society TEXT,
office TEXT)""")

# Setup driver------------------------------------------
#opt = Options()
#opt.add_argument("-headless")
cap = webdriver.common.desired_capabilities.DesiredCapabilities().FIREFOX
cap["marionette"] = False
driver = webdriver.Firefox(capabilities=cap)


wait = WebDriverWait(driver, 10)

# go to mailbox----------------------------------------
driver.get("https://owa.hcuge.ch")

# Validate welcome page--------------------------------
userinput = driver.find_element_by_name("username")
passinput = driver.find_element_by_name("password")

userinput.send_keys(username)
passinput.send_keys(password)
driver.find_element_by_class_name("credentials_input_submit").click()

# Pass security challenge----------------------------
challenge_phrase = driver.find_element_by_id("credentials_table_header")
challenge_letter = challenge_phrase.text[-2]
challenge_number = challenge_phrase.text[-1]
challenge_input = driver.find_element_by_class_name("credentials_input_password")
challenge_input.send_keys(CARD[challenge_letter][challenge_number])
driver.find_element_by_class_name("credentials_input_submit").click()

# go to contacts page ------------------------------
wait.until(EC.element_to_be_clickable((By.ID, "_ariaId_20")))
driver.find_element_by_id("_ariaId_20").click()

# go to mailing lists-------------------------------
wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@title='All Distribution Lists']")))
driver.find_element_by_xpath("//*[@title='All Distribution Lists']").click()

def go_to_mailing_list(name):
    '''Takes the driver to the named mailing list'''
    # relevant mailing list (whole hospital)----------------------------
    wait.until(EC.element_to_be_clickable((By.XPATH, "//*[text()='{}']".format(name))))
    mailing_list = driver.find_element_by_xpath("//*[text()='{}']".format(name))
    # mailing lists content-----------------------------
    driver.execute_script("arguments[0].scrollIntoView(true);", mailing_list)
    mailing_list.click()
    driver.implicitly_wait(5)
go_to_mailing_list("AllHug-Interne")

def get_mailing_list_chunk():
    '''Get the 50 people mailing list chunk'''
    # select mailing list contents----------------------
    mailing_list_content = driver.find_element_by_xpath("//*[@aria-label='Membres du groupe']")
    return mailing_list_content.find_elements_by_class_name("_pe_7")
memberlist = get_mailing_list_chunk()

# scroll to last chunk member and trigger next member chunk download-
driver.execute_script("arguments[0].scrollIntoView(true);", memberlist[-1])
# click on 1st member------------------------------
memberlist[0].click()

def get_individual_data():
    '''Returns data fields for an individual'''
    # individual data page-----------------------------
    datafields = driver.find_element_by_class_name('_rpc_r')
    subjectdata = datafields.find_elements_by_class_name('_rpc_i1')
    t = {'function': 'Fonction',
         'department': 'Département',
         'society': 'Société',
         'office': 'Office'}
    d = {}
    d['email'] = datafields.find_element_by_css_selector("span[autoid='_rpc_6']").text
    for k, v in t.items():
        d[k] = [e.text.split(':') for e in subjectdata if v in e.text][0][1]
    name = driver.find_element_by_css_selector("span[autoid='_pe_p']").text
    d['lastname'] = ' '.join(re.findall(r"\b([A-Z]+[-][A-Z]+|[A-Z]+)\b", name))
    d['firstname'] = ' '.join(re.findall(r"\b([A-Z][a-z]+[-][A-Z][a-z]+|[A-Z][a-z]+)\b", name))
    return d
indd = get_individual_data()

try:
    with con:
        con.execute("INSERT INTO hug_people VALUES (NULL,:firstname,:lastname,:email,:function,:department,:society,:office)",
                    indd)
except sqlite3.DataError:
    print("You're an idiot!")

# close and quit------------------------------------
with open("dump.sql", "w") as dump:
    for line in con.iterdump():
        dump.write("%s\n" % line)
driver.quit()
con.close()
