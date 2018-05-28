from flask import Flask, jsonify, request
import json
import os
import logging
import sys

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(name)s %(threadName)s %(message)s',
                    filename='td_web.log')
logging.getLogger('requests').setLevel(logging.WARNING)
logging.getLogger('urllib3.connectionpool').setLevel(logging.WARNING)
logging.getLogger('chardet.charsetprober').setLevel(logging.WARNING)

app = Flask(__name__, static_path='')


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


@app.route('/save', methods=['POST'])
def save_result():
    json_data = request.get_json()
    with open('web_saved.json', 'w') as f:
        json.dump(json_data, f)
    return jsonify({'ok': True})


@app.route('/load', methods=['GET'])
def read_saved_result():
    if not os.path.isfile('web_saved.json'):
        return jsonify({})
    else:
        return app.send_static_file('web_saved.json')


@app.route('/exit', methods=['POST'])
def exit_program():
    sys.exit(0)


def main():
    print('Please go to http://localhost:2333 to view the web GUI')
    app.run(host='localhost', port=2333)


def init():
    main()


if __name__ == '__main__':
    init()
