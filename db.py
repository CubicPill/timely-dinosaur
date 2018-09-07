import sqlite3
from utils import CourseType

DB_PATH = './td.sqlite'


class Database:
    def __init__(self):
        self._connection = sqlite3.connect(DB_PATH)

    def add_course(self, course_basic_data, course_schedule, course_type):
        cursor = self._connection.cursor()
        cursor.execute('INSERT INTO course '
                       '(jx0404id, capacity, name, subName, courseNo, instructor, prerequisite, credit, department, type)'
                       'VALUES '
                       '(?,?,?,?,?,?,?,?,?,?)', course_basic_data + course_type)
        for s in course_schedule:
            cursor.execute('INSERT INTO courseSchedule '
                           '(jx0404id, weeks, classroom, time, dayOfWeek, weeks2) '
                           'VALUES '
                           '(?,?,?,?,?,?)', s)
        self._connection.commit()

    def get_course_basic_data(self, course_id):
        cursor = self._connection.cursor()
        cursor.execute(
            'SELECT jx0404id, capacity, name, subName, courseNo, instructor, prerequisite, credit, department, type '
            'FROM course WHERE jx0404id = ?', (course_id,))
        return dict(zip(['jx0404id', 'capacity', 'name', 'subName', 'courseNo', 'instructor', 'prerequisite', 'credit',
                         'department', 'type'], cursor.fetchone()))

    def get_course_time(self, course_id):
        cursor = self._connection.cursor()
        cursor.execute(
            'SELECT jx0404id, weeks, classroom, time, dayOfWeek, weeks2 '
            'FROM courseSchedule WHERE jx0404id = ?', (course_id,))
        return dict(zip(['jx0404id', 'weeks', 'classroom', 'time', 'dayOfWeek', 'weeks2'], cursor.fetchone()))
