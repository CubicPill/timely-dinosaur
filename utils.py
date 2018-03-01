import logging
import os
import pickle
import requests
from bs4 import BeautifulSoup
from requests.structures import CaseInsensitiveDict

MAIN_URL = 'http://jwxt.sustc.edu.cn/jsxsd/framework/xsMain.jsp'
LOGIN_SERVER_ADDR = 'https://cas.sustc.edu.cn'
_global_session = requests.session()


def validate_session(_session=None) -> bool:
    if not _session:
        _session = _global_session
    try:
        if _session.get(MAIN_URL, allow_redirects=False, timeout=10).status_code == 200:
            return True
    except requests.RequestException:
        pass
    return False


def get_session():
    return _global_session


def do_login(username, password) -> dict:
    _global_session.headers = CaseInsensitiveDict({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
        'Accept-Encoding': ', '.join(('gzip', 'deflate')),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Connection': 'keep-alive',
    })
    req = _global_session.get(MAIN_URL)
    soup = BeautifulSoup(req.content, 'html5lib')
    post_url = 'https://cas.sustc.edu.cn/cas/login?service=http%3A%2F%2Fjwxt.sustc.edu.cn%2Fjsxsd%2F'
    login_data = {}
    for element in soup.find('form', {'id': 'fm1'}).find_all('input'):
        if element.has_attr('name'):
            value = ''
            if element.has_attr('value'):
                value = element['value']
            login_data[element['name']] = value
    login_data['username'] = username
    login_data['password'] = password
    response = _global_session.post(post_url, data=login_data, timeout=20)
    soup_resp = BeautifulSoup(response.content, 'html5lib')
    error = soup_resp.find('div', {'class': 'alert-danger'})
    if error:
        return {'ok': False, 'error': ' '.join(error.text.replace('.', '. ').split())}
    else:
        return {'ok': True}


def dump_session_pickle():
    with open('session.pickle', 'wb') as f:
        pickle.dump(_global_session, f)


def load_session_pickle() -> str:
    with open('session.pickle', 'rb') as f:
        try:
            _session = pickle.load(f)
        except:
            return 'CORRUPTED'

        else:
            logging.debug('Session restored from pickle file')
            if validate_session(_session):
                global _global_session
                _global_session = _session
                return 'OK'

            else:
                return 'EXPIRED'


def logout_session():
    _global_session.get('http://jwxt.sustc.edu.cn/jsxsd/xk/LoginToXk?method=exit')


def remove_session_pickle():
    if os.path.isfile('session.pickle'):
        os.remove('session.pickle')
        return True
    return False


ENROLL_URLS = [
    'http://jwxt.sustc.edu.cn/jsxsd/xsxkkc/bxxkOper?jx0404id={id}&xkzy=&trjf=',
    # 必修选课
    'http://jwxt.sustc.edu.cn/jsxsd/xsxkkc/xxxkOper?jx0404id={id}&xkzy=&trjf=',
    # 选修选课
    'http://jwxt.sustc.edu.cn/jsxsd/xsxkkc/bxqjhxkOper?jx0404id={id}&xkzy=&trjf=',
    # 本学期计划选课
    'http://jwxt.sustc.edu.cn/jsxsd/xsxkkc/knjxkOper?jx0404id={id}&xkzy=&trjf=',
    # 跨年级
    'http://jwxt.sustc.edu.cn/jsxsd/xsxkkc/fawxkOper?jx0404id={id}&xkzy=&trjf=',
    # 跨专业
    'http://jwxt.sustc.edu.cn/jsxsd/xsxkkc/ggxxkxkOper?jx0404id={id}&xkzy=&trjf='
    # 公选课
]
TYPES_STR = ['必修', '选修', '本学期计划', '跨年级', '跨专业', '公共课']
