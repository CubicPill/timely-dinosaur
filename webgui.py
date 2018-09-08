from flask import Flask, jsonify, request
import json
import os
import logging
import sys
from transform import parse_course_data
from utils import get_course_type_enum_from_int
from db import Database

logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(asctime)s %(name)s %(threadName)s %(message)s',
                    filename='td_web.log')
logging.getLogger('requests').setLevel(logging.WARNING)
logging.getLogger('urllib3.connectionpool').setLevel(logging.WARNING)
logging.getLogger('chardet.charsetprober').setLevel(logging.WARNING)

app = Flask(__name__, static_path='')

database = Database()


@app.route('/')
def index():
    return app.send_static_file('page.html')


@app.route('/search', methods=['POST'])
def search():
    json_data = request.get_json()
    query = json_data.get('query')
    if not query:
        return jsonify({'ok': False, 'error': 'No query data'})

    return jsonify({'ok': True})


@app.route('/detail/<course_id>', methods=['GET'])
def get_course_detail(course_id):
    return jsonify({'ok': True})


@app.route('/save', methods=['POST'])
def save_result():
    json_data = request.get_json()
    with open('web_saved.json', 'w') as f:
        json.dump(json_data, f)
    return jsonify({'ok': True})


def main():
    print('Please go to http://localhost:2333 to view the web GUI')
    app.run(host='localhost', port=2333)


def init_data():
    database.init_db()
    with open('course_data.json', encoding='utf-8') as f:
        data = json.load(f)
        for d in data:
            (basic_data, course_type), schedule_data = parse_course_data(d, get_course_type_enum_from_int(d['__type']))
            database.add_course(basic_data, schedule_data, course_type)
            logging.debug('Loaded: %s', basic_data[0])


def init():
    logging.info('**********Start web gui**********')
    print('Loading data into database...')
    init_data()
    print('...Done!')
    main()


if __name__ == '__main__':
    init()
