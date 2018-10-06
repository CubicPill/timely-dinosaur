import json
import logging

from flask import Flask, jsonify, request

from db import Database
from transform import parse_course_data
from utils import get_course_type_enum_from_int

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
    query_type = json_data.get('queryType')
    if not query:
        return jsonify({'ok': False, 'error': 'No query data'})
    if not query_type:
        return jsonify({'ok': False, 'error': 'No query type'})
    if query_type == 'courseNo':
        query_function = database.search_by_course_no
    elif query_type == 'courseName':
        query_function = database.search_by_course_name
    elif query_type == 'department':
        query_function = database.search_by_department
    elif query_type == 'instructor':
        query_function = database.search_by_instructor
    else:
        return jsonify({'ok': False, 'error': 'unknown query type: {}'.format(query_type)})
    return jsonify({'ok': True, 'data': query_function(query)})


@app.route('/schedule/<course_id>', methods=['GET'])
def get_course_schedule(course_id):
    return jsonify({'ok': True, 'data': database.get_course_time(course_id)})


@app.route('/save', methods=['POST'])
def save_result():
    json_data = request.get_json()
    save_list = list()
    if not json_data.get('id'):
        return jsonify({'ok': False, 'error': 'bad request'})
    for jx0404id in json_data['id']:
        detail = database.get_course_basic_data(jx0404id)
        save_list.append(
            '{}#{}|{}|{}|{}'.format(jx0404id, detail['courseNo'], detail['name'], detail['subName'], detail['time']))
    with open('course_list.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(save_list))
    return jsonify({'ok': True})


@app.route('/save', methods=['GET'])
def load_saved_result():
    course_id_list = list()
    with open('course_list.txt', encoding='utf-8') as f:
        for line in f.readlines():
            course_id_list.append(line.split('#', 1)[0])
    return jsonify({
        'ok': True,
        'data': [
            {
                'basic': database.get_course_basic_data(cid),
                'schedule': database.get_course_time(cid)
            }
            for cid in course_id_list]
    })


def main():
    print('Please go to http://localhost:2333 to view the web GUI')
    app.run(host='localhost', port=2333)


def init_data():
    database.init_db()
    logging.debug('db init done')
    with open('course_data.json', encoding='utf-8') as f:
        data = json.load(f)
        for d in data:
            (basic_data, course_type), schedule_data = parse_course_data(d, get_course_type_enum_from_int(d['__type']))
            database.add_course(basic_data, schedule_data, course_type)
            logging.debug('Loaded: %s', basic_data[0])


def init():
    logging.info('**********Start web gui**********')
    logging.info('load data into db')
    print('Loading data into database...')
    init_data()
    print('...Done!')
    logging.info('data loading done')
    main()


if __name__ == '__main__':
    init()
