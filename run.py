import json
import logging
import os
import pickle
import re
import sys
import time
import traceback
from _thread import start_new_thread
from queue import Queue
from threading import Thread
import getopt
import colorama
import requests
from bs4 import BeautifulSoup
from requests.structures import CaseInsensitiveDict

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
MAIN_URL = 'http://jwxt.sustc.edu.cn/jsxsd/framework/xsMain.jsp'
LOGIN_SERVER_ADDR = 'https://cas.sustc.edu.cn'
VERSION = 'v1.2.2'

session = requests.session()
course_name_map = dict()
q = Queue()
print_queue = Queue()

try:
    os.chdir(os.path.dirname(sys.argv[0]))  # change work directory
except OSError:
    pass

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(name)s %(threadName)s %(message)s',
                    filename='logging.log')
logging.getLogger('requests').setLevel(logging.WARNING)
logging.getLogger('urllib3.connectionpool').setLevel(logging.WARNING)
logging.getLogger('chardet.charsetprober').setLevel(logging.WARNING)


def validate_session():
    try:
        if session.get(MAIN_URL, allow_redirects=False, timeout=10).status_code == 200:
            return True
    except requests.RequestException:
        pass
    return False


def thread_print():
    """
    For multi-thread printing
    :return:
    """
    while True:
        content = print_queue.get()
        print(content, flush=True)


def do_login(username, password):
    session.headers = CaseInsensitiveDict({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
        'Accept-Encoding': ', '.join(('gzip', 'deflate')),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Connection': 'keep-alive',
    })
    req = session.get(MAIN_URL)
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
    response = session.post(post_url, data=login_data, timeout=20)
    soup_resp = BeautifulSoup(response.content, 'html5lib')
    error = soup_resp.find('div', {'class': 'errors', 'id': 'msg'})
    if error:
        print(colorama.Fore.LIGHTRED_EX + '登录失败! 错误信息: ' + error.text.replace('.', '. ') + '\n')
        return False
    else:
        print(colorama.Fore.LIGHTGREEN_EX + '登录成功!\n')
        with open('session.pickle', 'wb') as f:
            pickle.dump(session, f)
        return True


def logout_session():
    session.get('http://jwxt.sustc.edu.cn/jsxsd/xk/LoginToXk?method=exit')
    if os.path.isfile('session.pickle'):
        os.remove('session.pickle')
        logging.info('Pickle removed')
    logging.info('Logged out')


def load_config_from_file():
    if 'config.json' not in os.listdir('./'):
        print(colorama.Fore.LIGHTRED_EX + '未找到配置文件!')
        input('按 Enter 键退出')
        sys.exit(1)
    with open('config.json') as f:
        config = json.load(f)
    config['course_id'] = [str(i) for i in config['course_id']]
    logging.debug('Config loaded!')
    return config


class EnrollThread(Thread):
    def __init__(self, course_id, __type):
        Thread.__init__(self)
        self.id = course_id
        self.type = __type

    def run(self):
        _enroll(self.id, self.type, True)


def _enroll(course_id, __type, thread=False):
    """
    enroll a course
    :param course_id: id of course
    :param __type: course type
    :param thread: if start a separated thread
    :return:
    """
    logging.debug('Enrolling course id {}'.format(course_id))
    start_time = time.time() * 1e3
    try:
        req = session.get(ENROLL_URLS[__type].format(id=course_id), timeout=5)
        result = req.json()
        if req.status_code != 200:
            result['message'] = 'HTTP {}'.format(req.status_code)
            logging.error(
                colorama.Fore.LIGHTRED_EX + 'HTTP status code {} when enrolling course id {}'.format(req.status_code,
                                                                                                     course_id))
            return result
        logging.debug('Course id {} enrolling done, success: {}, Time {}ms'
                      .format(course_id, result['success'], round(time.time() * 1e3 - start_time), 2))
    except requests.Timeout:
        logging.error('Connection timed out!')
        result = {'success': False, 'message': '错误: 网络连接超时'}
    result['course_id'] = course_id
    if course_name_map.get(course_id):
        course_name = course_name_map.get(course_id)['name']
    else:
        course_name = '<id: {}>'.format(course_id)
    result['name'] = course_name

    if result['success']:
        print_queue.put(colorama.Fore.LIGHTGREEN_EX +
                        'SUCCESS!!! 课程 {name} 选课成功!'
                        .format(name=course_name))
    else:
        print_queue.put(colorama.Fore.LIGHTRED_EX +
                        'FAILED!!! 课程 {name} {message}'
                        .format(name=course_name, message=result['message']))
    if thread:
        q.put(result)
    return result


def do_batch_enroll(course_ids):
    """
    do batch enroll
    :param course_ids: list of course_id
    :return:
    """
    success = list()
    failed = list()
    threads = []
    for course_id in course_ids:
        thread = EnrollThread(course_id, course_name_map[course_id]['type'])
        thread.start()
        threads.append(thread)
    for thread in threads:
        thread.join()

    while not q.empty():
        result = q.get_nowait()

        if result['success']:
            success.append(result)
        else:
            failed.append(result)

    return success, failed


def do_interactive_enroll():
    """
    interactive enroll. user will enter the course_ids manually
    :return:
    """
    success = list()
    failed = list()
    print(colorama.Fore.LIGHTYELLOW_EX +
          '警告: 交互式单项选课仅作为调试用途, 输入格式错误可能导致选课失败或程序崩溃, 请谨慎使用')
    print('课程类型(0-5): ' + ' '.join(['必修', '选修', '本学期计划', '跨年级', '跨专业', '公共课']))

    while True:
        try:
            in_text = input('输入课程ID和课程类型编号, 以空格分隔. 输入 "exit" 结束.\nID:')
            if in_text == 'exit':
                break
            elif in_text == '':
                continue
            elif not re.match('.* \d$', in_text):
                print(colorama.Fore.LIGHTRED_EX + '格式错误!')
                continue
            course_id, __type = in_text.split(' ')
            if not re.match('\d{15}$', course_id):
                print(colorama.Fore.LIGHTYELLOW_EX + '输入格式不匹配. 是否继续?(Y/N) ', end='')
                cont = input()
                if cont.lower() == 'y':
                    pass
                else:
                    continue
            __type = int(__type)
            course_name_map[course_id] = dict()
            course_name_map[course_id]['type'] = __type
            course_name_map[course_id]['name'] = '<id: {}>'.format(course_id)
            course_name_map[course_id]['cid'] = 'DUMMY001'

            result = _enroll(course_id, __type, False)
            if result['success']:
                success.append(result)
            else:
                failed.append(result)
        except Exception:
            logging.error('Error occurred in interactive enrolling')
            logging.error(traceback.format_exc())
            print(colorama.Fore.LIGHTRED_EX + traceback.format_exc())
        time.sleep(0.1)

    return success, failed


def fetch_course_data():
    """
    fetch course data from server
    :return: course data
    """
    params = {
        'kcxx': '',
        'skls': '',
        'skxq': '',
        'skjs': '',
        'sfym': False,
        'sfct': False,
        'sEcho': 1,
        'iDisplayStart': 0,
        'iDisplayLength': 750
    }

    url_required = 'http://jwxt.sustc.edu.cn/jsxsd/xsxkkc/xsxkBxxk'
    # 必修选课

    url_elective = 'http://jwxt.sustc.edu.cn/jsxsd/xsxkkc/xsxkXxxk'
    # 选修选课

    url_sem_plan = 'http://jwxt.sustc.edu.cn/jsxsd/xsxkkc/xsxkBxqjhxk'
    # 本学期计划选课

    url_cross_grade = 'http://jwxt.sustc.edu.cn/jsxsd/xsxkkc/xsxkKnjxk'
    # 专业内跨年级选课

    url_cross_dept = 'http://jwxt.sustc.edu.cn/jsxsd/xsxkkc/xsxkFawxk'
    # 跨专业选课

    url_common = 'http://jwxt.sustc.edu.cn/jsxsd/xsxkkc/xsxkGgxxkxk'
    # 公选课选课

    try:
        required = session.post(url_required, data=params)
        if required.status_code == 404:
            print('登录状态错误!')
            logging.critical('Error occurred while querying course data')
            sys.exit(1)
        required = required.json()
        for item in required.get('aaData'):
            item['__type'] = 0
        logging.debug('Required courses fetching done, total: {}, fetched: {}'
                      .format(required['iTotalRecords'], len(required['aaData'])))
    except json.JSONDecodeError:
        logging.warning('Required courses fetching error')
        required = {'aaData': []}
        print('错误: 必修选课课程信息获取失败!')

    try:
        elective = session.post(url_elective, data=params).json()
        for item in elective.get('aaData'):
            item['__type'] = 1
        logging.debug('Elective courses fetching done, total: {}, fetched: {}'
                      .format(elective['iTotalRecords'], len(elective['aaData'])))
    except json.JSONDecodeError:
        logging.warning('Elective courses fetching error')
        elective = {'aaData': []}
        print('错误: 选修选课课程信息获取失败!')

    try:
        sem_plan = session.post(url_sem_plan, data=params).json()
        for item in sem_plan.get('aaData'):
            item['__type'] = 2
        logging.debug('Cross grade courses fetching done, total: {}, fetched: {}'
                      .format(sem_plan['iTotalRecords'], len(sem_plan['aaData'])))
    except json.JSONDecodeError:
        logging.warning('Semester planning courses fetching error')
        sem_plan = {'aaData': []}
        print('错误: 学期内计划选课课程信息获取失败!')

    try:
        cross_grade = session.post(url_cross_grade, data=params).json()
        for item in cross_grade.get('aaData'):
            item['__type'] = 3
        logging.debug('Cross grade courses fetching done, total: {}, fetched: {}'
                      .format(cross_grade['iTotalRecords'], len(cross_grade['aaData'])))
    except json.JSONDecodeError:
        logging.warning('Cross grade courses fetching error')
        cross_grade = {'aaData': []}
        print('错误: 跨年级选课课程信息获取失败!')
    try:
        cross_dept = session.post(url_cross_dept, data=params).json()
        for item in cross_dept.get('aaData'):
            item['__type'] = 4
        logging.debug('Cross department courses fetching done, total: {}, fetched: {}'
                      .format(cross_dept['iTotalRecords'], len(cross_dept['aaData'])))
    except json.JSONDecodeError:
        logging.warning('Cross department courses fetching error')
        cross_dept = {'aaData': []}
        print('错误: 跨专业选课课程信息获取失败!')
    try:
        common = session.post(url_common, data=params).json()
        for item in common.get('aaData'):
            item['__type'] = 5
        logging.debug('Common courses fetching done, total: {}, fetched: {}'
                      .format(common['iTotalRecords'], len(common['aaData'])))
    except json.JSONDecodeError:
        logging.warning('Common courses fetching error')
        common = {'aaData': []}
        print('错误: 公选课选课课程信息获取失败!')

    data = required.get('aaData') + elective.get('aaData') + sem_plan.get('aaData') + cross_grade.get('aaData') \
           + cross_dept.get('aaData') + common.get('aaData')
    logging.debug('All course data fetching done. {} records in total.'.format(len(data)))

    with open('course_data.json', 'w') as f:
        json.dump(data, f, indent=3)
        logging.debug('Course data written to file')

    return data


def create_id_name_map(data):
    """
    create a dict mapping the course id and names
    :param data: course data
    :return:
    """
    global course_name_map

    for course in data:
        course_name_map[course['jx0404id']] = dict()
        if course['fzmc']:
            course_name_map[course['jx0404id']]['name'] = '{}[{}]'.format(course['kcmc'], course['fzmc'])
        else:
            course_name_map[course['jx0404id']]['name'] = course['kcmc']
        course_name_map[course['jx0404id']]['type'] = course['__type']
        course_name_map[course['jx0404id']]['cid'] = course['kch']

    logging.debug('ID to name mapping established')
    with open('./courses.txt', 'w') as f:
        list_arr = list()
        for key, value in course_name_map.items():
            list_arr.append([value['cid'].replace(' ', ''), TYPES_STR[value['type']], value['name']])
            list_arr.sort(key=lambda a: a[0])
        for item in list_arr:
            f.write('{cid} {type} {name}\n'.format(cid=item[0], type=item[1], name=item[2]))
    logging.debug('ID to name map written to file')


def print_result_list(success, failed):
    print_queue.put(colorama.Fore.LIGHTGREEN_EX + '\n--------成功列表--------')
    if success:
        for s in success:
            print_queue.put(colorama.Fore.LIGHTGREEN_EX + s['name'])
    else:
        print_queue.put('无')
    print_queue.put(colorama.Fore.LIGHTGREEN_EX + '------------------------\n')

    print_queue.put(colorama.Fore.LIGHTYELLOW_EX + '--------失败列表--------')
    if failed:
        for f in failed:
            print_queue.put(colorama.Fore.LIGHTYELLOW_EX + f['name'])
    else:
        print_queue.put('无')
    print_queue.put(colorama.Fore.LIGHTYELLOW_EX + '------------------------')
    print_queue.put('成功 %d, 失败 %d\n' % (len(success), len(failed)))


def get_args():
    # priority: command line args, config file, default settings
    config = load_config_from_file()
    mode = config.get('mode') if 'mode' in config else 'batch'
    reload_course = config.get('reload') if 'reload' in config else True
    usn = config.get('username')
    pwd = config.get('password')
    id_list = config.get('course_id')
    wait = config.get('wait') if 'wait' in config else True

    if sys.argv[1:]:
        try:
            opts, args = getopt.getopt(sys.argv[1:], "hm:ru:p:n",
                                       ['help', 'mode=', 'reload', 'username=', 'password=', 'no-wait'])
        except getopt.GetoptError as e:
            logging.error(e.msg)
            print(e.msg)
            print_help()
            sys.exit(1)
        if opts:
            for opt in opts:
                if opt[0] == '-h' or opt[0] == '--help':
                    print_help()
                    sys.exit(0)
                if opt[0] == '-m' or opt[0] == '--mode':
                    mode = opt[1]
                    if mode not in ['batch', 'single']:
                        print(colorama.Fore.LIGHTRED_EX + '错误: 模式错误: {}, 只能为 "batch" 或 "single"'.format(mode))
                        sys.exit(1)
                if opt[0] == '-r' or opt[0] == '--reload':
                    reload_course = True
                if opt[0] == '-u' or opt[0] == '--username':
                    usn = opt[1]
                if opt[0] == '-p' or opt[0] == '--password':
                    pwd = opt[1]
                if opt[0] == '-n' or opt[0] == '--no-wait':
                    wait = True
    if not usn or not pwd:
        if not usn:
            print(colorama.Fore.LIGHTRED_EX + '错误: 学号为空')
        if not pwd:
            print(colorama.Fore.LIGHTRED_EX + '错误: 密码为空')
        logging.critical('No username or no password provided, exiting')
        sys.exit(1)
    if mode != 'single' and id_list is None:
        print(colorama.Fore.LIGHTRED_EX + '错误: 批量选课模式下必须输入课程ID列表')
        logging.critical('No course id list provided in batch mode')
        sys.exit(1)
    return mode, reload_course, usn, pwd, id_list, wait


def print_help():
    """
    print help
    :return:
    """
    print('''
    南方科技大学自动选课
    参数列表:
    hm:ru:p:n
    -h --help                   显示帮助并退出
    -m --mode {batch|single}    模式 (批量/单个交互)
    -r --reload                 是否重新加载课程数据
    -u --username <username>    用户名
    -p --password <password>    密码
    -n --no-wait                是否等待教务系统开放
    ''')


def main():
    colorama.init(autoreset=True)
    print('Timely Dinosaur ' + VERSION + ', Author: CubicPill')
    need_login = True
    mode, reload_course, usn, pwd, id_list, wait = get_args()

    if os.path.isfile('session.pickle'):
        print('读取登陆信息......', end='')
        global session
        with open('session.pickle', 'rb') as f:
            try:
                session = pickle.load(f)
            except:
                logging.error('Corrupted pickle file')
                print(colorama.Fore.LIGHTRED_EX + '文件损坏!')
            else:
                logging.debug('Session restored from pickle file')
                if validate_session():
                    logging.debug('Pickle session valid')
                    need_login = False
                    print(colorama.Fore.LIGHTGREEN_EX + '登录状态已恢复\n')
                else:
                    print(colorama.Fore.LIGHTYELLOW_EX + '登录信息已过期\n')
                    logging.debug('Pickle session expired, try login')
    else:
        logging.debug('No saved session found')
    if need_login:
        print('登录教务系统......', end='')
        start_time = time.time() * 1e3
        if not do_login(usn, pwd):
            logging.critical('CAS login failed')
            sys.exit(1)
        logging.info('Login completed. Time: {}ms'.format(round(time.time() * 1e3 - start_time), 2))
    while True:
        temp = session.get('http://jwxt.sustc.edu.cn/jsxsd/xsxk/xklc_list?Ves632DSdyV=NEW_XSD_PYGL')
        match_group = re.search('/jsxsd/xsxk/xklc_view\?jx0502zbid=([0-9A-Z]*)', temp.text)
        if match_group:
            zbid = match_group.group(1)
            session.get('http://jwxt.sustc.edu.cn/jsxsd/xsxk/xsxk_index?jx0502zbid=' + zbid)  # complete login
            break
        else:
            print('选课入口尚未开放, 5 秒后重试.')
            logging.warning('Entry not found, try again in 5 seconds')
            time.sleep(5)

    if not reload_course and 'course_data.json' in os.listdir('./'):
        with open('course_data.json') as f:
            data = json.load(f)
            logging.debug('Existing course data loaded')
    else:
        logging.debug('No existing data found or overwrite existing data, fetch from the server')
        print('获取全部课程列表......', end='')
        start_time = time.time() * 1e3
        data = fetch_course_data()
        print(colorama.Fore.LIGHTGREEN_EX + '课程列表获取完成!\n')
        logging.info('Course list fetching done. Time {}ms'.format(round(time.time() * 1e3 - start_time), 2))

    create_id_name_map(data)
    start_new_thread(thread_print, ())

    # print below should use the print queue!!!

    for url in ENROLL_URLS:
        session.get(url)

    if mode == 'batch':  # batch mode
        delete_ids = list()
        for course_id in id_list:
            if course_id not in course_name_map:
                logging.error('ID {} not found in data, skip'.format(course_id))
                print_queue.put(colorama.Fore.LIGHTRED_EX + '错误: 课程ID号{}无数据, 将从队列中删除. 使用交互式选课以忽略此错误'.format(course_id))
                delete_ids.append(course_id)
        for id in delete_ids:
            id_list.remove(id)
        print_queue.put('\n选课课程:')
        for course_id in id_list:
            print_queue.put(colorama.Fore.LIGHTCYAN_EX +
                            '{} {}'.format(course_name_map[course_id]['cid'], course_name_map[course_id]['name']))
        if not id_list:
            print_queue.put('无可选课程, 退出')
            sys.exit(1)

        print_queue.put('')
        for item in id_list:
            if item not in course_name_map.keys():
                print_queue.put(colorama.Fore.LIGHTRED_EX +
                                '警告: 课程 id 为 {} 的课程无数据. 尝试更新课程列表或检查课程 id 输入'.format(item))

        while not print_queue.empty(): pass
        input('按 Enter 键继续\n')
        print_queue.put('开始批量自动选课......\n')
        start_time = time.time() * 1e3
        success, failed = do_batch_enroll(id_list)
        logging.info('Batch enrolling done. Time {}ms'.format(round(time.time() * 1e3 - start_time), 2))
    elif mode == 'single':  # interactive mode
        success, failed = do_interactive_enroll()
    else:
        sys.exit(1)

    print_queue.put(colorama.Fore.LIGHTBLUE_EX + '\n自动选课完成!\n')

    print_result_list(success, failed)

    logging.info('Done, %d success, %d failed' % (len(success), len(failed)))
    while len(failed) != 0:
        while not print_queue.empty(): pass
        retry = input('是否尝试重选失败课程? (Y/n) ')
        if retry.lower() == 'n':
            break
        logging.info('Retry enrolling')
        failed_ids = [item['course_id'] for item in failed]
        start_time = time.time() * 1e3
        success, failed = do_batch_enroll(failed_ids)
        logging.info('Batch enrolling done. Time {}ms'.format(round(time.time() * 1e3 - start_time), 2))
        print_result_list(success, failed)
    while not print_queue.empty(): pass
    logout = input('是否退出登陆? (y/N) ')
    if logout.lower() == 'y':
        logout_session()
        print('已退出登陆')


if __name__ == '__main__':
    logging.info('********start********')
    try:
        main()
    except Exception:
        logging.warning('********ERROR OCCURRED********')
        logging.warning(traceback.format_exc())
        print(colorama.Fore.LIGHTRED_EX + '错误!!!!!!')
        print(colorama.Fore.LIGHTRED_EX + traceback.format_exc())
        input('\n按 Enter 键退出')
        sys.exit(1)
    input('\n按 Enter 键退出')
    logging.info('********exit********')
