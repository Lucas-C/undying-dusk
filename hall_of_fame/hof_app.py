#!/usr/bin/env python3
# coding: utf-8

import os, sqlite3
from base64 import urlsafe_b64decode
from datetime import datetime
from urllib.parse import parse_qsl

from flask import Flask, g, render_template, request


DB_FILEPATH = 'undying-dusk-hof.db'
DB_INIT_FILEPATH = 'undying-dusk-hof-init.sql'
FLASK_APP = Flask(__name__, static_folder='..', static_url_path='', template_folder='.')


@FLASK_APP.route('/', methods=('GET', 'POST'))
def index():
    query = dict(parse_qsl(request.query_string.decode()))
    secrets_found = extract_secrets(query)
    version = query.get('v', '')
    display_form = secrets_found is not None and version
    if display_form and request.method == 'POST':
        upsert_score(request.form['name'], request.form['pdf_reader'], secrets_found, version)
        display_form = False
    scores = query_db('SELECT * FROM scores')
    return render_template('index.html', display_form=bool(display_form), scores=scores)

def extract_secrets(query):
    # pylint: disable=bare-except
    try:
        return set(urlsafe_b64decode(query.get('gs', '')).decode().split(','))
    except:  # Failsafe in case of invalid "gs" query param
        return None

def upsert_score(player_name, pdf_reader, secrets_found, version):
    pdf_readers = ({pdf_reader} if pdf_reader else set())
    existing_score = query_db('SELECT * FROM scores WHERE player_name = ?', (player_name,), one=True)
    if existing_score:
        pdf_readers |= set(existing_score['pdf_readers'].split(','))
        secrets_found |= set(existing_score['secrets_found'].split(','))
    get_db().execute('INSERT OR REPLACE INTO scores VALUES (?, ?, ?, ?, ?)',
                     (player_name, ','.join(sorted(pdf_readers)), ','.join(sorted(secrets_found)), version, datetime.now()))


###############################################################################
# The following code recipe was taken from: https://flask.palletsprojects.com/en/1.1.x/patterns/sqlite3/

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB_FILEPATH, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        db.isolation_level = None  # autocommit mode
        db.row_factory = sqlite3.Row
        with FLASK_APP.open_resource(DB_INIT_FILEPATH, mode='r') as sql_file:
            db.cursor().executescript(sql_file.read())
        db.commit()
    return db

@FLASK_APP.teardown_appcontext
def close_connection(_):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    return_values = cur.fetchall()
    cur.close()
    return (return_values[0] if return_values else None) if one else return_values


if __name__ == '__main__':
    FLASK_APP.run(port=int(os.environ.get('PORT', '8085')))
