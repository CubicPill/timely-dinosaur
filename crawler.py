import json
import logging
import sys
from utils import CourseType
from utils import get_session


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
    session = get_session()
    try:
        required = session.post(url_required, data=params)
        if required.status_code == 404:
            print('登录状态错误!')
            logging.critical('Error occurred while querying course data')
            sys.exit(1)
        required = required.json()
        for item in required.get('aaData'):
            item['__type'] = CourseType.REQUIRED
        logging.debug('Required courses fetching done, total: {}, fetched: {}'
                      .format(required['iTotalRecords'], len(required['aaData'])))
    except json.JSONDecodeError:
        logging.warning('Required courses fetching error')
        required = {'aaData': []}
        print('错误: 必修选课课程信息获取失败!')

    try:
        elective = session.post(url_elective, data=params).json()
        for item in elective.get('aaData'):
            item['__type'] = CourseType.ELECTIVE
        logging.debug('Elective courses fetching done, total: {}, fetched: {}'
                      .format(elective['iTotalRecords'], len(elective['aaData'])))
    except json.JSONDecodeError:
        logging.warning('Elective courses fetching error')
        elective = {'aaData': []}
        print('错误: 选修选课课程信息获取失败!')

    try:
        sem_plan = session.post(url_sem_plan, data=params).json()
        for item in sem_plan.get('aaData'):
            item['__type'] = CourseType.PLANNED
        logging.debug('Cross grade courses fetching done, total: {}, fetched: {}'
                      .format(sem_plan['iTotalRecords'], len(sem_plan['aaData'])))
    except json.JSONDecodeError:
        logging.warning('Semester planning courses fetching error')
        sem_plan = {'aaData': []}
        print('错误: 学期内计划选课课程信息获取失败!')

    try:
        cross_grade = session.post(url_cross_grade, data=params).json()
        for item in cross_grade.get('aaData'):
            item['__type'] = CourseType.CROSS_GRADE
        logging.debug('Cross grade courses fetching done, total: {}, fetched: {}'
                      .format(cross_grade['iTotalRecords'], len(cross_grade['aaData'])))
    except json.JSONDecodeError:
        logging.warning('Cross grade courses fetching error')
        cross_grade = {'aaData': []}
        print('错误: 跨年级选课课程信息获取失败!')
    try:
        cross_dept = session.post(url_cross_dept, data=params).json()
        for item in cross_dept.get('aaData'):
            item['__type'] = CourseType.CROSS_DEPT
        logging.debug('Cross department courses fetching done, total: {}, fetched: {}'
                      .format(cross_dept['iTotalRecords'], len(cross_dept['aaData'])))
    except json.JSONDecodeError:
        logging.warning('Cross department courses fetching error')
        cross_dept = {'aaData': []}
        print('错误: 跨专业选课课程信息获取失败!')
    try:
        common = session.post(url_common, data=params).json()
        for item in common.get('aaData'):
            item['__type'] = CourseType.COMMON
        logging.debug('Common courses fetching done, total: {}, fetched: {}'
                      .format(common['iTotalRecords'], len(common['aaData'])))
    except json.JSONDecodeError:
        logging.warning('Common courses fetching error')
        common = {'aaData': []}
        print('错误: 公选课选课课程信息获取失败!')

    data = required.get('aaData') + elective.get('aaData') + sem_plan.get('aaData') + cross_grade.get('aaData') \
           + cross_dept.get('aaData') + common.get('aaData')
    logging.debug('All course data fetching done. {} records in total.'.format(len(data)))

    return data
