import json
import logging
import os
import pickle
import re
import sys
import time
import traceback
from queue import Queue
from threading import Thread

import colorama
import requests
from bs4 import BeautifulSoup

try:
   os.chdir(os.path.dirname(sys.argv[0]))  # change work directory
except OSError:
   pass

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
session = requests.session()
course_name_map = dict()

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', filename='logging.log')
logging.getLogger('requests').setLevel(logging.ERROR)
q = Queue()
MAIN_URL = 'http://jwxt.sustc.edu.cn/jsxsd/framework/main.jsp'
LOGIN_SERVER_ADDR = 'https://cas.sustc.edu.cn'
VERSION = 'v1.1.0 pre1'


def validate_session():
   try:
      if session.get(MAIN_URL, allow_redirects=False, timeout=10).status_code == 200:
         return True
   except requests.RequestException:
      pass
   return False


def do_login(username, password):
   soup = BeautifulSoup(session.get(MAIN_URL).content, 'html5lib')
   form = soup.find('form', id='fm1')
   post_url = LOGIN_SERVER_ADDR + form['action']
   login_data = {}
   for element in soup.find('form').find_all('input'):
      if element.has_attr('value'):
         login_data[element['name']] = element['value']
   login_data['username'] = username
   login_data['password'] = password
   response = session.post(post_url, data=login_data, timeout=20)
   soup_resp = BeautifulSoup(response.content, 'html5lib')
   error = soup_resp.find('div', {'class': 'errors', 'id': 'msg'})

   if error:
      print('登录失败! 错误信息: ' + error.text.replace('.', '. '))
      return False
   else:
      print('登录成功!')
      with open('session.pickle', 'wb') as f:
         pickle.dump(session, f)
      return True


def load_config():
   if 'config.json' not in os.listdir('./'):
      print('未找到配置文件!')
      input('按 Enter 键退出')
      sys.exit(1)
   with open('config.json') as f:
      config = json.load(f)
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
   logging.debug('Enrolling course id {}'.format(course_id))
   start_time = time.time() * 1e3
   try:
      result = session.get(ENROLL_URLS[__type].format(id=course_id), timeout=5).json()
      logging.debug('Course id {} enrolling done, success: {}, Time {}ms'
                    .format(course_id, result['success'], round(time.time() * 1e3 - start_time), 2))
   except requests.Timeout:
      logging.error('Connection timed out!')
      result = {'success': False, 'message': '错误: 网络连接超时'}
   result['course_id'] = course_id
   course_name = course_name_map.get(course_id)['name']
   result['name'] = course_name
   if result['success']:
      print(colorama.Fore.LIGHTGREEN_EX +
            'SUCCESS!!! 课程 {name} ({id}) 选课成功!'.format(name=course_name, id=course_id))
   else:
      print(colorama.Fore.LIGHTRED_EX +
            'FAILED!!! 课程 {name} ({id}) {message}'.format(name=course_name, id=course_id, message=result['message']))
   sys.stdout.flush()
   if thread:
      q.put(result)
   return result


def do_batch_enroll(course_ids):
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
   success = list()
   failed = list()
   print(colorama.Fore.LIGHTYELLOW_EX +
         '警告: 交互式单项选课仅作为调试用途, 输入格式错误可能导致选课失败或程序崩溃, 请谨慎使用')

   while True:
      try:
         in_text = input('输入课程ID和课程类型编号(0-5), 以空格分隔. 输入 "exit" 结束.\nID:')
         if in_text == 'exit':
            break
         elif not re.match('\d{15} \d$', in_text):
            cont = input('输入格式不匹配. 是否继续?(Y/N)\n>')
            if cont.lower() == 'y':
               pass
            else:
               continue
         course_id, __type = in_text.split(' ')
         __type = int(__type)
         result = _enroll(course_id, __type, False)
         if result['success']:
            success.append(result)
         else:
            failed.append(result)
      except Exception:
         logging.error('Error occurred in interactive enrolling')
         logging.error(traceback.format_exc())
         print(traceback.format_exc())

   return success, failed


def fetch_course_data():
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
   print('\n--------成功列表--------')
   if success:
      for s in success:
         print(colorama.Fore.LIGHTGREEN_EX +
               '{name} ({id}) 选课成功!'.format(name=s['name'], id=s['course_id']))
   else:
      print('无')
   print('------------------------\n')

   print('--------失败列表--------')
   if failed:
      for f in failed:
         print(colorama.Fore.LIGHTYELLOW_EX +
               '{name} ({id}) {msg}'.format(name=f['name'], id=f['course_id'], msg=f['message']))
   else:
      print('无')
   print('------------------------')
   print('成功 %d, 失败 %d\n' % (len(success), len(failed)))


def main():
   colorama.init(autoreset=True)
   print('Timely Dinosaur ' + VERSION + ' Author: CubicPill')
   config = load_config()
   need_login = True
   m = int(input('选择模式: 1 批量选课 2 单项选课\n>'))

   mode = ['batch', 'interactive'][m - 1]
   load_course_data_from_file = False
   if 'course_data.json' in os.listdir('./'):
      if not input('是否重新加载课程数据?(Y/N)\n>').lower() == 'n':
         logging.info('Overwrite existing course data')
      else:
         load_course_data_from_file = True
   if 'session.pickle' in os.listdir('./'):
      global session
      with open('session.pickle', 'rb') as f:
         session = pickle.load(f)
         logging.debug('Session restored from pickle file')
      if validate_session():
         logging.debug('Pickle session valid')
         need_login = False
         print(colorama.Fore.LIGHTGREEN_EX + '登录状态已恢复')
      else:
         logging.debug('Pickle session expired, try login')
   else:
      logging.debug('No saved session found')
   if need_login:
      print('登录教务系统......', end='')
      start_time = time.time() * 1e3
      if not do_login(config['username'], config['password']):
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

   if load_course_data_from_file:
      with open('course_data.json') as f:
         data = json.load(f)
         logging.debug('Existing course data loaded')
   else:
      logging.debug('No existing data found or overwrite existing data, fetch from the server')
      print('\n获取全部课程列表......', end='')
      start_time = time.time() * 1e3
      data = fetch_course_data()
      print('课程列表获取完成!')
      logging.info('Course list fetching done. Time {}ms'.format(round(time.time() * 1e3 - start_time), 2))

   create_id_name_map(data)
   for course_id in config['course_id']:
      if course_id not in course_name_map.keys():
         logging.error('ID {} not found in data, skip'.format(course_id))
         print(colorama.Fore.LIGHTRED_EX + '错误: 课程ID号{}无数据, 将从队列中删除. 使用交互式选课以忽略此错误'.format(course_id))
         config['course_id'].remove(course_id)

   if mode == 'batch':
      print('\n选课课程:')
      for course_id in config['course_id']:
         print('{} {}'.format(course_name_map[course_id]['cid'], course_name_map[course_id]['name']))
      print()
      for item in config['course_id']:
         if item not in course_name_map.keys():
            print(colorama.Fore.LIGHTRED_EX +
                  '警告: 课程 id 为 {} 的课程无数据. 尝试更新课程列表或检查课程 id 输入'.format(item))

      input('按 Enter 键继续\n')
      print('开始批量自动选课......')
      start_time = time.time() * 1e3
      success, failed = do_batch_enroll(config['course_id'])
      logging.info('Batch enrolling done. Time {}ms'.format(round(time.time() * 1e3 - start_time), 2))
   elif mode == 'interactive':
      success, failed = do_interactive_enroll()
   else:
      sys.exit(1)

   print('自动选课完成!\n')

   print_result_list(success, failed)

   logging.info('Done, %d success, %d failed' % (len(success), len(failed)))

   while len(failed) != 0:
      retry = input('是否尝试重选失败课程? (Y/N)\n>')
      if not retry.lower() == 'y':
         break
      logging.info('Retry enrolling')
      failed_ids = [item['course_id'] for item in failed]
      start_time = time.time() * 1e3
      success, failed = do_batch_enroll(failed_ids)
      logging.info('Batch enrolling done. Time {}ms'.format(round(time.time() * 1e3 - start_time), 2))
      print_result_list(success, failed)


if __name__ == '__main__':
   logging.info('********start********')
   try:
      main()
   except Exception:
      logging.warning('********ERROR OCCURRED********')
      logging.warning(traceback.format_exc())
      print(colorama.Fore.LIGHTRED_EX + '错误!!!!!!')
      print(colorama.Fore.LIGHTRED_EX + traceback.format_exc())
      input('按 Enter 键退出')
      sys.exit(1)
   input('按 Enter 键退出')
   logging.info('********exit********')
