from flask import Flask, jsonify, request

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


def save_result():
    pass


def read_current():
    pass


def main():
    print('Please go to http://localhost:2333 to view the web GUI')
    app.run(host='localhost', port=2333)


def init():
    main()


if __name__ == '__main__':
    init()
