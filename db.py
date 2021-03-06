import sqlite3
from utils import CourseType

DB_PATH = ':memory:'

COURSE_TABLE_KEYS = ['jx0404id', 'capacity', 'name', 'subName', 'courseNo', 'instructor', 'prerequisite', 'credit',
                     'department', 'time', 'classroom', 'type']
COURSE_SCHEDULE_TABLE_KEYS = ['jx0404id', 'weeks', 'classroom', 'time', 'dayOfWeek', 'weekShort']


class Database:
    def __init__(self):
        self._connection = sqlite3.connect(DB_PATH)

    def init_db(self):
        with open('create.sql', encoding='utf-8') as f:
            cursor = self._connection.cursor()
            cursor.executescript(f.read())
        self._connection.commit()

    def add_course(self, course_basic_data, course_schedule, course_type: CourseType):
        cursor = self._connection.cursor()
        cursor.execute('INSERT INTO course '
                       '('
                       + ','.join(COURSE_TABLE_KEYS) +
                       ')'
                       'VALUES '
                       '(?,?,?,?,?,?,?,?,?,?,?,?)', course_basic_data + (course_type.name,))
        for s in course_schedule:
            cursor.execute('INSERT INTO courseSchedule '
                           '('
                           + ','.join(COURSE_SCHEDULE_TABLE_KEYS) +
                           ') '
                           'VALUES '
                           '(?,?,?,?,?,?)', s)
        self._connection.commit()

    def search_by_course_no(self, course_no):
        cursor = self._connection.execute('SELECT '
                                          + ','.join(COURSE_TABLE_KEYS) +
                                          ' FROM course '
                                          'WHERE courseNo LIKE ?', (course_no + '%',))
        return [dict(zip(COURSE_TABLE_KEYS, row)) for row in cursor]

    def search_by_course_name(self, course_name):
        cursor = self._connection.execute('SELECT '
                                          + ','.join(COURSE_TABLE_KEYS) +
                                          ' FROM course '
                                          'WHERE name LIKE ?', ('%' + course_name + '%',))
        return [dict(zip(COURSE_TABLE_KEYS, row)) for row in cursor]

    def search_by_department(self, department):
        cursor = self._connection.execute('SELECT '
                                          + ','.join(COURSE_TABLE_KEYS) +
                                          ' FROM course '
                                          'WHERE department LIKE ?', ('%' + department + '%',))
        return [dict(zip(COURSE_TABLE_KEYS, row)) for row in cursor]

    def search_by_instructor(self, instructor):
        cursor = self._connection.execute('SELECT '
                                          + ','.join(COURSE_TABLE_KEYS) +
                                          ' FROM course '
                                          'WHERE instructor LIKE ?', ('%' + instructor + '%',))
        return [dict(zip(COURSE_TABLE_KEYS, row)) for row in cursor]

    def get_course_basic_data(self, course_id):
        cursor = self._connection.cursor()
        cursor.execute(
            'SELECT '
            + ','.join(COURSE_TABLE_KEYS) +
            ' FROM course WHERE jx0404id = ?', (course_id,))
        return dict(zip(COURSE_TABLE_KEYS, cursor.fetchone()))

    def get_course_time(self, course_id):
        cursor = self._connection.cursor()
        cursor.execute(
            'SELECT jx0404id, weeks, classroom, time, dayOfWeek, weekShort '
            'FROM courseSchedule WHERE jx0404id = ?', (course_id,))
        return [dict(zip(COURSE_SCHEDULE_TABLE_KEYS, row)) for row in
                cursor.fetchall()]
