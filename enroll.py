import json
import logging
import os
import re
import sys
import time
import traceback
from _thread import start_new_thread
from queue import Queue
from threading import Thread

import colorama
import requests

from crawler import fetch_course_data
from utils import do_login, logout_session, ENROLL_URLS, TYPES_STR, load_session_pickle, get_session, \
    dump_session_pickle, remove_session_pickle, load_config_from_file

session: requests.session = get_session()
course_name_map = dict()
q = Queue()
print_queue = Queue()

try:
    os.chdir(os.path.dirname(sys.argv[0]))  # change work directory
except OSError:
    pass

logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(asctime)s %(name)s %(threadName)s %(message)s',
                    filename='td.log')
logging.getLogger('requests').setLevel(logging.WARNING)
logging.getLogger('urllib3.connectionpool').setLevel(logging.WARNING)
logging.getLogger('chardet.charsetprober').setLevel(logging.WARNING)


def thread_print():
    """
    For multi-thread printing
    :return:
    """
    while True:
        content = print_queue.get()
        print(content, flush=True)


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
        course_name_map[course['jx0404id']]['credit'] = course['xf']

    logging.debug('ID to name mapping established')
    with open('./courses.txt', 'w', encoding='utf-8') as f:
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
    # priority: config file > default settings
    if 'config.json' not in os.listdir('./'):
        print(colorama.Fore.LIGHTRED_EX + '未找到配置文件 config.json!')
        input('按 Enter 键退出')
        sys.exit(1)
    if 'course_list.txt' not in os.listdir('./'):
        print(colorama.Fore.LIGHTRED_EX + '未找到配置文件 course_list.txt!')
        input('按 Enter 键退出')
        sys.exit(1)
    config = load_config_from_file()
    logging.debug('Config loaded!')
    reload_course = config.get('reload') if 'reload' in config else True
    usn = config.get('username')
    pwd = config.get('password')
    id_list = config.get('course_id')
    wait = config.get('wait') if 'wait' in config else True

    if not usn or not pwd:
        if not usn:
            print(colorama.Fore.LIGHTRED_EX + '错误: 学号为空')
        if not pwd:
            print(colorama.Fore.LIGHTRED_EX + '错误: 密码为空')
        logging.critical('No username or no password provided, exiting')
        sys.exit(1)
    if id_list is None:
        print(colorama.Fore.LIGHTRED_EX + '错误: 必须输入课程ID列表')
        logging.critical('No course id list provided in batch mode')
        sys.exit(1)
    return {
        'reload_course': reload_course,
        'usn': usn,
        'pwd': pwd,
        'id_list': id_list,
        'wait': wait
    }


def main(reload_course, usn, pwd, id_list, wait):
    colorama.init(autoreset=True)
    need_login = True

    if os.path.isfile('session.pickle'):
        print('读取登陆信息......', end='')
        ret = load_session_pickle()
        if ret == 'CORRUPTED':
            logging.error('Corrupted pickle file')
            print(colorama.Fore.LIGHTRED_EX + '文件损坏!')
        elif ret == 'OK':
            logging.debug('Pickle session valid')
            need_login = False
            print(colorama.Fore.LIGHTGREEN_EX + '登录状态已恢复\n')
        elif ret == 'EXPIRED':
            print(colorama.Fore.LIGHTYELLOW_EX + '登录信息已过期\n')
            logging.debug('Pickle session expired, try login')
    else:
        logging.debug('No saved session found')
    if need_login:
        print('登录教务系统......', end='')
        start_time = time.time() * 1e3
        result = do_login(usn, pwd)
        if not result['ok']:
            print(colorama.Fore.LIGHTRED_EX + '登录失败! 错误信息: ' + result['error'] + '\n')
            logging.critical('CAS login failed: ' + result['error'])
            sys.exit(1)
        print(colorama.Fore.LIGHTGREEN_EX + '登录成功!\n')
        logging.info('Login completed. Time: {}ms'.format(round(time.time() * 1e3 - start_time), 2))
        dump_session_pickle()
        logging.debug('Session pickle dumped')
    global session
    session = get_session()
    while True:
        temp = session.get('http://jwxt.sustc.edu.cn/jsxsd/xsxk/xklc_list?Ves632DSdyV=NEW_XSD_PYGL',
                           allow_redirects=False, timeout=10)
        if temp.status_code != 200:
            logging.critical('Login seems failed')
            print(colorama.Fore.LIGHTRED_EX + 'Unexpected auth error, exit')
            sys.exit(1)
        match_group = re.search('/jsxsd/xsxk/xklc_view\?jx0502zbid=([0-9A-Z]*)', temp.text)
        if match_group:
            zbid = match_group.group(1)
            session.get('http://jwxt.sustc.edu.cn/jsxsd/xsxk/xsxk_index?jx0502zbid=' + zbid)  # complete login
            break
        else:
            if not wait:
                print('选课入口尚未开放')
                sys.exit(0)
            print('选课入口尚未开放, 2 秒后重试.')
            logging.warning('Entry not found, try again in 2 seconds')
            time.sleep(2)

    if not reload_course and 'course_data.json' in os.listdir('./'):
        with open('course_data.json', encoding='utf8') as f:
            data = json.load(f)
            logging.debug('Existing course data loaded')
    else:
        logging.debug('No existing data found or overwrite existing data, fetch from the server')
        print('获取全部课程列表......', end='')
        start_time = time.time() * 1e3
        data = fetch_course_data()
        with open('course_data.json', 'w', encoding='utf8') as f:
            d = json.dumps(data, indent=3, ensure_ascii=False).encode().decode('utf-8')
            f.write(d)
            logging.debug('Course data written to file')
        print(colorama.Fore.LIGHTGREEN_EX + '课程列表获取完成!\n')
        logging.info('Course list fetching done. Time {}ms'.format(round(time.time() * 1e3 - start_time), 2))

    create_id_name_map(data)
    start_new_thread(thread_print, ())

    # print below should use the print queue!!!

    for url in ENROLL_URLS:
        session.get(url)

    delete_ids = list()
    for course_id in id_list:
        if course_id not in course_name_map:
            logging.error('ID {} not found in data, skip'.format(course_id))
            print_queue.put(colorama.Fore.LIGHTRED_EX + '错误: 课程ID号{}无数据, 将从队列中删除. 使用交互式选课以忽略此错误'.format(course_id))
            delete_ids.append(course_id)
    for cid in delete_ids:
        id_list.remove(cid)
    print_queue.put('\n选课课程:')
    for course_id in id_list:
        print_queue.put(colorama.Fore.LIGHTCYAN_EX +
                        '{} {}'.format(course_name_map[course_id]['cid'], course_name_map[course_id]['name']))

    if not id_list:
        print_queue.put('无可选课程, 退出')
        sys.exit(1)
    print_queue.put('总学分: {}'.format(sum([course_name_map[cid]['credit'] for cid in id_list])))
    print_queue.put('')
    for item in id_list:
        if item not in course_name_map.keys():
            print_queue.put(colorama.Fore.LIGHTRED_EX +
                            '警告: 课程 id 为 {} 的课程无数据. 尝试更新课程列表或检查课程 id 输入'.format(item))

    while not print_queue.empty():
        pass
    input('按 Enter 键继续\n')
    print_queue.put('开始批量自动选课......\n')
    start_time = time.time() * 1e3
    success, failed = do_batch_enroll(id_list)
    logging.info('Batch enrolling done. Time {}ms'.format(round(time.time() * 1e3 - start_time), 2))

    print_queue.put(colorama.Fore.LIGHTBLUE_EX + '\n自动选课完成!\n')

    print_result_list(success, failed)

    logging.info('Done, %d success, %d failed' % (len(success), len(failed)))
    while len(failed) != 0:
        while not print_queue.empty():
            pass
        retry = input('是否尝试重选失败课程? (Y/n) ')
        if retry.lower() == 'n':
            break
        logging.info('Retry enrolling')
        failed_ids = [item['course_id'] for item in failed]
        start_time = time.time() * 1e3
        success, failed = do_batch_enroll(failed_ids)
        logging.info('Batch enrolling done. Time {}ms'.format(round(time.time() * 1e3 - start_time), 2))
        print_result_list(success, failed)
    while not print_queue.empty():
        pass
    logout = input('是否退出登陆? (y/N) ')
    if logout.lower() == 'y':
        logout_session()
        if remove_session_pickle():
            logging.info('Pickle removed')
        logging.info('Logged out')
        print('已退出登陆')


def init():
    logging.info('********start********')
    try:
        main(**get_args())
    except KeyboardInterrupt:
        logging.info('KeyboardInterrupt, exiting')
        print('已停止')
    except Exception:
        logging.warning('********ERROR OCCURRED********')
        logging.warning(traceback.format_exc())
        print(colorama.Fore.LIGHTRED_EX + '错误!!!!!!')
        print(colorama.Fore.LIGHTRED_EX + traceback.format_exc())
        input('\n按 Enter 键退出')
        sys.exit(1)
    input('\n按 Enter 键退出')
    logging.info('********exit********')


if __name__ == '__main__':
    init()
