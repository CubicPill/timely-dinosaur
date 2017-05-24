import json
import logging
import os
import re
import sys
import time
import traceback
from queue import Queue
from threading import Thread

import requests
from bs4 import BeautifulSoup

try:
   os.chdir(os.path.dirname(sys.argv[0]))  # change work directory
except OSError:
   pass

session = requests.session()
course_name_map = dict()

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', filename='logging.log')
logging.getLogger('requests').setLevel(logging.ERROR)
q = Queue()
MAIN_URL = 'http://jwxt.sustc.edu.cn/jsxsd/'
ENROLL_URL = 'http://jwxt.sustc.edu.cn/jsxsd/xsxkkc/fawxkOper?jx0404id={id}&xkzy=&trjf='
LOGIN_SERVER_ADDR = 'https://cas.sustc.edu.cn'
VERSION = 'v1.0.2 pre1'


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
   def __init__(self, course_id):
      Thread.__init__(self)
      self.id = course_id

   def run(self):
      _enroll(self.id, True)


def _enroll(course_id, thread=False):
   logging.debug('Enrolling course id {}'.format(course_id))
   start_time = time.time() * 1e3
   try:
      result = session.get(ENROLL_URL.format(id=course_id), timeout=5).json()
      logging.debug('Course id {} enrolling done, success: {}, Time {}ms'
                    .format(course_id, result['success'], round(time.time() * 1e3 - start_time), 2))
   except requests.Timeout:
      logging.error('Connection timed out!')
      result = {'success': False, 'message': '错误: 网络连接超时'}
   result['course_id'] = course_id
   course_name = course_name_map.get(course_id)
   result['name'] = course_name
   if result['success']:
      print('SUCCESS!!! 课程 {name} ({id}) 选课成功!'.format(name=course_name, id=course_id))
   else:
      print('FAILED!!! 课程 {name} ({id}) {message}'.format(name=course_name, id=course_id, message=result['message']))
   if thread:
      q.put(result)
   return result


def do_batch_enroll(course_ids):
   success = list()
   failed = list()
   threads = []
   for course_id in course_ids:
      thread = EnrollThread(course_id)
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
   while True:

      course_id = input('输入课程ID. 输入 "exit" 结束.\nID:')
      if course_id == 'exit':
         break
      elif not re.match('\d{15}$', course_id):
         cont = input('ID {} 格式不匹配. 是否继续?(Y/N)\n>'.format(course_id))
         if cont.lower() == 'y':
            pass
         else:
            continue
      result = _enroll(course_id)
      if result['success']:
         success.append(result)
      else:
         failed.append(result)

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

   url_sem_plan = 'http://jwxt.sustc.edu.cn/jsxsd/xsxkkc/xsxkBxqjhxk'
   # 本学期计划选课

   url_cross_grade = 'http://jwxt.sustc.edu.cn/jsxsd/xsxkkc/xsxkKnjxk'
   # 专业内跨年级选课

   url_cross_dept = 'http://jwxt.sustc.edu.cn/jsxsd/xsxkkc/xsxkFawxk'
   # 跨专业选课

   url_common = 'http://jwxt.sustc.edu.cn/jsxsd/xsxkkc/xsxkGgxxkxk'
   # 公选课选课

   sem_plan = session.post(url_sem_plan, data=params)
   if sem_plan.status_code == 404:
      print('登录状态错误!')
      logging.critical('Error occurred while querying course data')
      sys.exit(1)
   sem_plan = sem_plan.json()
   logging.debug('Semester planning courses fetching done, total: {}, fetched: {}'
                 .format(sem_plan['iTotalRecords'], len(sem_plan['aaData'])))

   cross_grade = session.post(url_cross_grade, data=params).json()
   logging.debug('Cross grade courses fetching done, total: {}, fetched: {}'
                 .format(cross_grade['iTotalRecords'], len(cross_grade['aaData'])))

   cross_dept = session.post(url_cross_dept, data=params).json()
   logging.debug('Cross department courses fetching done, total: {}, fetched: {}'
                 .format(cross_dept['iTotalRecords'], len(cross_dept['aaData'])))

   common = session.post(url_common, data=params).json()
   logging.debug('Common courses fetching done, total: {}, fetched: {}'
                 .format(common['iTotalRecords'], len(common['aaData'])))

   data = sem_plan['aaData'] + cross_grade['aaData'] + cross_dept['aaData'] + common['aaData']
   logging.debug('All course data fetching done. {} records in total.'.format(len(data)))

   with open('course_data.json', 'w') as f:
      json.dump(data, f, indent=3)
      logging.debug('Course data written to file')

   return data


def create_id_name_map(data):
   global course_name_map

   for course in data:
      if course['fzmc']:
         course_name_map[course['jx0404id']] = '{}[{}]'.format(course['kcmc'], course['fzmc'])
      else:
         course_name_map[course['jx0404id']] = course['kcmc']

   logging.debug('ID to name mapping established')
   with open('./courses.txt', 'w') as f:
      list_arr = list()
      for id, cname in course_name_map.items():
         list_arr.append([id, cname])
         list_arr.sort(key=lambda a: int(a[0]))
      for item in list_arr:
         f.write('{id} {name}\n'.format(id=item[0], name=item[1]))
   logging.debug('ID to name map written to file')


def print_result_list(success, failed):
   print('--------成功列表--------')
   if success:
      for s in success:
         print('{name} ({id}) 选课成功!'.format(name=s['name'], id=s['course_id']))
   else:
      print('无')
   print('------------------------\n')

   print('--------失败列表--------')
   if failed:
      for f in failed:
         print('{name} ({id}) {msg}'.format(name=f['name'], id=f['course_id'], msg=f['message']))
   else:
      print('无')
   print('------------------------')
   print('\n成功 %d, 失败 %d' % (len(success), len(failed)))


def load_course_data():
   with open('course_data.json') as f:
      r = json.load(f)
      logging.debug('Existing course data loaded')
      return r


def main():
   print('Timely Dinosaur ' + VERSION + ' Author: CubicPill')
   config = load_config()
   m = int(input('选择模式: 1 批量选课 2 单项选课\n>'))

   mode = ['batch', 'interactive'][m - 1]
   load_course_data_from_file = False
   if 'course_data.json' in os.listdir('./'):
      if input('是否重新加载课程数据?(Y/N)\n>').lower() == 'y':
         load_course_data_from_file = False
         logging.info('Overwrite existing course data')

   print('登录教务系统......')
   start_time = time.time() * 1e3
   if not do_login(config['username'], config['password']):
      logging.critical('CAS login failed')
      sys.exit(1)
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

   logging.info('Login completed. Time: {}ms'.format(round(time.time() * 1e3 - start_time), 2))

   if load_course_data_from_file:
      data = load_course_data()
   else:
      logging.debug('No existing data found or overwrite existing data, fetch from the server')
      print('\n获取全部课程列表......')
      start_time = time.time() * 1e3
      data = fetch_course_data()
      print('课程列表获取完成!')
      logging.info('Course list fetching done. Time {}ms'.format(round(time.time() * 1e3 - start_time), 2))

   create_id_name_map(data)
   if mode == 'batch':
      print('选课课程:\n\n' + '\n'.join(['{} {}'.format(item, course_name_map.get(item)) for item in config['course_id']]))
      print()
      for item in config['course_id']:
         if item not in course_name_map.keys():
            print('警告: 课程 id 为 {} 的课程无数据. 尝试更新课程列表或检查课程 id 输入'.format(item))
      input('\n按 Enter 键继续')
      print('开始批量自动选课......')
      start_time = time.time() * 1e3
      success, failed = do_batch_enroll(config['course_id'])
      logging.info('Batch enrolling done. Time {}ms'.format(round(time.time() * 1e3 - start_time), 2))
   elif mode == 'interactive':
      success, failed = do_interactive_enroll()
   else:
      sys.exit(1)

   print('自动选课完成!')

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
      input('按 Enter 键退出')
   except Exception:
      logging.warning('********ERROR OCCURRED********')
      logging.warning(traceback.format_exc())
   logging.info('********exit********')
