import json


def strip(text):
    if text is None:
        return ''
    return text.strip()


def parse_course_data(course_json, type: str):
    """
    (jx0404id, capacity, name, subName, courseNo, instructor, prerequisite, credit, department, type)
    [(jx0404id, weeks, classroom, time, dayOfWeek, weeks2)]
    :return:
    """
    course_id = int(course_json['jx0404id'])
    capacity = int(course_json['pkrs'])
    course_name = strip(course_json['kcmc'])
    course_sub_name = strip(course_json['fzmc'])
    course_no = course_json['kch']
    instructor = strip(course_json['skls'])
    prerequisite = course_json['pgtj']
    credit = int(course_json['xf'])
    department = strip(course_json['dwmc'])
    course_time = strip(course_json['sksj']).replace('<br>', ',')
    classroom = strip(course_json['skdd']).replace('<br>', ',')

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
             department, course_time, classroom), type), schedules
