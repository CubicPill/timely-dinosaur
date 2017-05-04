import json
import logging
import os
import re
import sys

import requests
from bs4 import BeautifulSoup

try:
   os.chdir(os.path.dirname(sys.argv[0]))  # change work directory
except:
   pass

h = {
   'Cache-Control': 'max-age=0',
   'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.112 Safari/537.36',
   'Accept-Encoding': 'gzip, deflate',
   'Accept-Language': 'en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4'
}

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logging.getLogger('requests').setLevel(logging.ERROR)
MAIN_URL = 'http://jwxt.sustc.edu.cn/jsxsd/'
ENROLL_URL = 'http://jwxt.sustc.edu.cn/jsxsd/xsxkkc/fawxkOper?jx0404id={id}&xkzy=&trjf='
LOGIN_SERVER_ADDR = 'https://cas.sustc.edu.cn'


def do_login(session, username, password):
   logging.info('登录教务系统......')
   soup = BeautifulSoup(session.get(MAIN_URL).content, 'html5lib')
   form = soup.find('form', id='fm1')
   post_url = LOGIN_SERVER_ADDR + form['action']
   login_data = {}
   for element in soup.find('form').find_all('input'):
      if element.has_attr('value'):
         login_data[element['name']] = element['value']
   login_data['username'] = username
   login_data['password'] = password
   response = session.post(post_url, data=login_data, timeout=20, headers=h)
   soup_resp = BeautifulSoup(response.content, 'html5lib')
   error = soup_resp.find('div', {'class': 'errors', 'id': 'msg'})

   if error:
      logging.error('登录失败! 错误信息: ' + error.text.replace('.', '. '))
      return False
   else:
      logging.info('登录成功!')
      return True


def load_config():
   with open('config.json') as f:
      config = json.load(f)
   logging.debug('Config loaded!')
   return config


def do_enroll(session, course_ids, course_name_map):
   success = list()
   failed = list()
   for course_id in course_ids:
      logging.debug('Enrolling course id {}'.format(course_id))
      result = session.get(ENROLL_URL.format(id=course_id)).json()
      course_name = course_name_map.get(course_id)

      if result['success']:
         success.append({'course_id': course_id, 'name': course_name})
         logging.info('课程 {name} ({id}) 选课成功!'.format(name=course_name, id=course_id))
      else:
         failed.append({'course_id': course_id, 'name': course_name, 'message': result['message']})
         logging.warning('课程 {name} ({id}) {message}'.format(name=course_name, id=course_id, message=result['message']))

      logging.debug('Course id {} enrolling done, success: {}'.format(course_id, result['success']))
   return success, failed


def fetch_course_data(session):
   if 'course_data.json' in os.listdir('./'):
      logging.debug('Existing course data found, loading...')
      with open('course_data.json') as f:
         return json.load(f)
   logging.debug('No existing data found, fetching from server...')
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
      logging.error('登录状态错误!')
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
   _map = dict()
   for course in data:
      _map[course['jx0404id']] = course['kcmc']
   logging.debug('ID to name mapping established')
   return _map


def main():
   session = requests.session()
   config = load_config()
   logging.info('课程id: ' + ', '.join(config['course_id']))
   if not do_login(session, config['username'], config['password']):
      exit(1)

   temp = session.get('http://jwxt.sustc.edu.cn/jsxsd/xsxk/xklc_list?Ves632DSdyV=NEW_XSD_PYGL')
   zbid = re.search('/jsxsd/xsxk/xklc_view\?jx0502zbid=([0-9A-Z]*)', temp.text).group(1)
   session.get('http://jwxt.sustc.edu.cn/jsxsd/xsxk/xsxk_index?jx0502zbid=' + zbid)  # complete login

   logging.info('获取全部课程列表......')
   data = fetch_course_data(session)
   course_name_map = create_id_name_map(data)
   logging.info('获取完成!')

   logging.info('开始自动选课......')
   success, failed = do_enroll(session, config['course_id'], course_name_map)
   logging.info('选课完成!')

   logging.info('--------成功列表--------')
   if success:
      for s in success:
         logging.info('{name} ({id}) 选课成功!'.format(name=s['name'], id=s['course_id']))
   else:
      logging.info('无')

   logging.info('')

   logging.info('--------失败列表--------')
   if failed:
      for f in failed:
         logging.info('{name} ({id}) {msg}'.format(name=f['name'], id=f['course_id'], msg=f['message']))
   else:
      logging.info('无')

   logging.info('自动选课完成. 成功 %d, 失败 %d' % (len(success), len(failed)))


if __name__ == '__main__':
   main()
