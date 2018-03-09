#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar  8 01:16:31 2018

@author: Raoul Schorer
"""

import json, sqlite3
from urllib.request import urlopen

DB_NAME = "phonebook.db"

def db_connect(name):
    conn = sqlite3.connect(name)
    return (conn, conn.cursor())

def build_request_string(name, initial):
    return "".join(["https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?" 
                    "db={remote_db}"
                    "&retmode={mode}"
                    "&tool={tool}"
                    "&email={email}"
                    "&term={name}+{initial}[Author]"
                    "+AND+"
                    "{affiliation}[Affiliation]"
                    ]).format(
    remote_db="pubmed",
    mode="json",
    tool="hcuge_papers",
    email="raoul.schorer@hcuge.ch",
    name=name,
    initial=initial,
    affiliation="geneva"
    )

def get_url(rs):                  
    response = urlopen(rs).read().decode()
    resjson = json.loads(response)
    return resjson

def get_subjects():
    conn, cur = db_connect(DB_NAME)
    cur.execute("SELECT  * FROM subjects")
    subjects = cur.fetchall()
    conn.close()
    return subjects

def fetch_subject_data(subject):
    id_, sex, status, name, initial = subject
    return (id_, get_url(build_request_string(name, initial)))

def insert_subject_data(scrape):
    conn, cur = db_connect(DB_NAME)
    id_, data = scrape
    if data["esearchresult"]["idlist"]:
        table_id = "articles_" + str(id_)
        cur.execute("CREATE TABLE IF NOT EXISTS {} (idlist INTEGER)".format(table_id))
        cur.executemany("INSERT INTO {}(idlist) VALUES (?)".format(table_id),
                        [(int(e),) for e in data["esearchresult"]["idlist"]])
        conn.commit()
    conn.close()

s = get_subjects()
e = fetch_subject_data(s[0])
insert_subject_data(e)