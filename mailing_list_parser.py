#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar  9 16:01:35 2018

@author: raoul
"""
import time
from access_card import CARD, username, password
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.firefox.options import Options

# Setup driver------------------------------------------
#options = Options()
#options.set_headless(headless=True)
cap = webdriver.common.desired_capabilities.DesiredCapabilities().FIREFOX
cap["marionette"] = False
driver = webdriver.Firefox(capabilities=cap)


wait = WebDriverWait(driver, 10)

try:
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

    # relevant mailing lists----------------------------
    wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Chefs de clinique')]")))
    cdc_list = driver.find_element_by_xpath("//*[contains(text(), 'Chefs de clinique')]")

    # mailing lists content-----------------------------
    cdc_list.click()
    driver.implicitly_wait(5)
    cdc_names = driver.find_elements_by_xpath("//*[@autoid='_pe_j']")
    cdc_names_text = [e.text for e in cdc_names]
    print(cdc_names_text)

# close and quit------------------------------------
finally:
    driver.quit()
