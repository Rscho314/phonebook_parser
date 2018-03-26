#!/home/raoul/anaconda3/envs/web/bin/python3
# -*- coding: utf-8 -*-

from MailingListScraper import MailingListScraper

mls = MailingListScraper('phonebook.db',
                         'AllHug-Interne')

mls.connect_db()
mls.create_db_table()

mls.create_webdriver()
mls.navigate_to("https://owa.hcuge.ch")

mls.login_1st_step()
mls.login_2nd_step()

mls.navigate_to_contacts()
mls.navigate_to_distribution_lists()

for i in range(100):
    mls.navigate_to_mailing_list()
    mls.get_mailing_list_chunk()
    mls.navigate_to_mailing_list_entry()

mls.finish_scrape()

