import json
import logging
import os
import re
import sys
import time

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

MAIN_URL = 'http://jwxt.sustc.edu.cn/jsxsd/'
ENROLL_URL = 'http://jwxt.sustc.edu.cn/jsxsd/xsxkkc/fawxkOper?jx0404id={id}&xkzy=&trjf='
LOGIN_SERVER_ADDR = 'https://cas.sustc.edu.cn'


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
   with open('config.json') as f:
      config = json.load(f)
   logging.debug('Config loaded!')
   return config


def post_enroll_data(course_id):
   logging.debug('Enrolling course id {}'.format(course_id))
   start_time = time.time() * 1e3
   try:
      result = session.get(ENROLL_URL.format(id=course_id), timeout=5).json()
      logging.debug('Course id {} enrolling done, success: {}, Time {}ms'
                    .format(course_id, result['success'], round(time.time() * 1e3 - start_time), 2))
   except requests.Timeout:
      logging.error('Connection timed out!')
      result = {'success': False, 'message': '错误: 网络连接超时'}
   return result


def do_batch_enroll(course_ids):
   success = list()
   failed = list()
   for course_id in course_ids:
      result = post_enroll_data(course_id)
      course_name = course_name_map.get(course_id)

      if result['success']:
         success.append({'course_id': course_id, 'name': course_name})
         print('SUCCESS!!! 课程 {name} ({id}) 选课成功!'.format(name=course_name, id=course_id))
      else:
         failed.append({'course_id': course_id, 'name': course_name, 'message': result['message']})
         print('FAILED!!! 课程 {name} ({id}) {message}'.format(name=course_name, id=course_id, message=result['message']))

   return success, failed


def do_interactive_enroll():
   success = list()
   failed = list()
   while True:

      course_id = input('输入课程ID. 输入 "exit" 退出.\nID:')
      if course_id == 'exit':
         break
      elif not re.match('\d{15}$', course_id):
         cont = input('ID {} 格式不匹配. 是否继续?(Y/N)\n>'.format(course_id))
         if cont.lower() == 'y':
            pass
         else:
            continue
      result = post_enroll_data(course_id)
      course_name = course_name_map.get(course_id)
      if result['success']:
         success.append({'course_id': course_id, 'name': course_name})
         print('SUCCESS!!! 课程 {name} ({id}) 选课成功!'.format(name=course_name, id=course_id))
      else:
         failed.append({'course_id': course_id, 'name': course_name, 'message': result['message']})
         print('FAILED!!! 课程 {name} ({id}) {message}'.format(name=course_name, id=course_id, message=result['message']))

   return success, failed


def fetch_course_data():
   if 'course_data.json' in os.listdir('./'):
      with open('course_data.json') as f:
         r = json.load(f)
         logging.debug('Existing course data loaded')
         return r
   logging.debug('No existing data found, fetch from the server')

   url_sem_plan = 'http://jwxt.sustc.edu.cn/jsxsd/xsxkkc/xsxkBxqjhxk?kcxx=&skls=&skxq=&skjc=&sfym=false&sfct=false'
   data_sem_plan = 'sEcho=1&iColumns=10&sColumns=&iDisplayStart=0&iDisplayLength=750&mDataProp_0=kch&mDataProp_1=kcmc&mDataProp_2=xf&mDataProp_3=skls&mDataProp_4=sksj&mDataProp_5=skdd&mDataProp_6=xkrs&mDataProp_7=syrs&mDataProp_8=ctsm&mDataProp_9=czOper'
   # 本学期计划选课

   url_cross_grade = 'http://jwxt.sustc.edu.cn/jsxsd/xsxkkc/xsxkKnjxk?kcxx=&skls=&skxq=&skjc=&sfym=false&sfct=false'
   data_cross_grade = 'sEcho=1&iColumns=10&sColumns=&iDisplayStart=0&iDisplayLength=750&mDataProp_0=kch&mDataProp_1=kcmc&mDataProp_2=xf&mDataProp_3=skls&mDataProp_4=sksj&mDataProp_5=skdd&mDataProp_6=xkrs&mDataProp_7=syrs&mDataProp_8=ctsm&mDataProp_9=czOper'
   # 专业内跨年级选课

   url_cross_dept = 'http://jwxt.sustc.edu.cn/jsxsd/xsxkkc/xsxkFawxk?kcxx=&skls=&skxq=&skjc=&sfym=false&sfct=false'
   data_cross_dept = 'sEcho=1&iColumns=10&sColumns=&iDisplayStart=0&iDisplayLength=750&mDataProp_0=kch&mDataProp_1=kcmc&mDataProp_2=xf&mDataProp_3=skls&mDataProp_4=sksj&mDataProp_5=skdd&mDataProp_6=xkrs&mDataProp_7=syrs&mDataProp_8=ctsm&mDataProp_9=czOper'
   # 跨专业选课

   url_common = 'http://jwxt.sustc.edu.cn/jsxsd/xsxkkc/xsxkGgxxkxk?kcxx=&skls=&skxq=&skjc=&sfym=false&sfct=false&szjylb='
   data_common = 'sEcho=1&iColumns=11&sColumns=&iDisplayStart=0&iDisplayLength=750&mDataProp_0=kch&mDataProp_1=kcmc&mDataProp_2=xf&mDataProp_3=skls&mDataProp_4=sksj&mDataProp_5=skdd&mDataProp_6=xkrs&mDataProp_7=syrs&mDataProp_8=ctsm&mDataProp_9=szkcflmc&mDataProp_10=czOper'
   # 公选课选课

   sem_plan = session.post(url_sem_plan + '&' + data_sem_plan)
   if sem_plan.status_code == 404:
      print('登录状态错误!')
      logging.critical('Error occurred while querying course data')
      exit(1)
   sem_plan = sem_plan.json()
   logging.debug('Semester planning courses fetching done, total: {}, fetched: {}'
                 .format(sem_plan['iTotalRecords'], len(sem_plan['aaData'])))

   cross_grade = session.post(url_cross_grade + '&' + data_cross_grade).json()
   logging.debug('Cross grade courses fetching done, total: {}, fetched: {}'
                 .format(cross_grade['iTotalRecords'], len(cross_grade['aaData'])))

   cross_dept = session.post(url_cross_dept + '&' + data_cross_dept).json()
   logging.debug('Cross department courses fetching done, total: {}, fetched: {}'
                 .format(cross_dept['iTotalRecords'], len(cross_dept['aaData'])))

   common = session.post(url_common + '&' + data_common).json()
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
      course_name_map[course['jx0404id']] = course['kcmc']
   logging.debug('ID to name mapping established')


def print_result_list(success, failed):
   print('--------成功列表--------')
   if success:
      for s in success:
         print('{name} ({id}) 选课成功!'.format(name=s['name'], id=s['course_id']))
   else:
      print('无')
   print('------------------------')

   print('--------失败列表--------')
   if failed:
      for f in failed:
         print('{name} ({id}) {msg}'.format(name=f['name'], id=f['course_id'], msg=f['message']))
   else:
      print('无')
   print('------------------------')
   print('\n成功 %d, 失败 %d' % (len(success), len(failed)))


def main():
   config = load_config()
   m = int(input('选择模式: 1 批量选课 2 单项选课\n>'))

   mode = ['batch', 'interactive'][m - 1]

   print('登录教务系统......')
   start_time = time.time() * 1e3
   if not do_login(config['username'], config['password']):
      logging.critical('CAS login failed')
      exit(1)

   temp = session.get('http://jwxt.sustc.edu.cn/jsxsd/xsxk/xklc_list?Ves632DSdyV=NEW_XSD_PYGL')
   zbid = re.search('/jsxsd/xsxk/xklc_view\?jx0502zbid=([0-9A-Z]*)', temp.text).group(1)
   session.get('http://jwxt.sustc.edu.cn/jsxsd/xsxk/xsxk_index?jx0502zbid=' + zbid)  # complete login

   logging.info('Login completed. Time: {}ms'.format(round(time.time() * 1e3 - start_time), 2))

   # TODO:如选课系统未开放, 轮询等待

   print('获取全部课程列表......')
   start_time = time.time() * 1e3
   data = fetch_course_data()
   create_id_name_map(data)
   print('课程列表获取完成!')
   logging.info('Course list fetching done. Time {}ms'.format(round(time.time() * 1e3 - start_time), 2))

   if mode == 'batch':
      print('选课课程:\n' + '\n'.join([item + ' ' + course_name_map[item] for item in config['course_id']]))
      input('按 Enter 键继续')
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

   while True:
      retry = input('是否尝试重选失败课程? (Y/N)\n>')
      if not retry.lower() == 'y':
         break
      failed_ids = [item['course_id'] for item in failed]
      success, failed = do_batch_enroll(failed_ids)
      print_result_list(success, failed)


if __name__ == '__main__':
   logging.info('********start********')
   main()
   input('按 Enter 键退出')
   logging.info('********exit********')
