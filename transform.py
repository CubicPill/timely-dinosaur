import json


def parse_course_data(course_json, type):
    """
    (jx0404id, capacity, name, subName, courseNo, instructor, prerequisite, credit, department, type)
    [(jx0404id, weeks, classroom, time, dayOfWeek, weeks2)]
    :return:
    """
    course_id = int(course_json['jx0404id'])
    capacity = int(course_json['pkrs'])
    course_name = course_json['kcmc']
    course_sub_name = course_json['fzmc']
    course_no = course_json['kch']
    instructor = course_json['skls']
    prerequisite = course_json['pgtj']
    credit = int(course_json['xf'])
    department = course_json['dwmc']

    schedules = list()
    for l in course_json['kkapList']:
        schedules.append([
            course_id,
            ','.join(l['skzcList']),
            l['jsmc'],
            l['skjcmc'],
            int(l['xq']),
            l['kkzc']
        ])

    return ((course_id, capacity, course_name, course_sub_name, course_no, instructor, prerequisite, credit,
             department), type), schedules
