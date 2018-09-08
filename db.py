import sqlite3
from utils import CourseType

DB_PATH = './td.sqlite'


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
                       '(jx0404id, capacity, name, subName, courseNo, instructor, prerequisite, credit, department, type)'
                       'VALUES '
                       '(?,?,?,?,?,?,?,?,?,?)', course_basic_data + (course_type.name,))
        for s in course_schedule:
            cursor.execute('INSERT INTO courseSchedule '
                           '(jx0404id, weeks, classroom, time, dayOfWeek, weeks2) '
                           'VALUES '
                           '(?,?,?,?,?,?)', s)
        self._connection.commit()

    def search_by_course_no(self, course_no):
        cursor = self._connection.execute('SELECT '
                                          'jx0404id, capacity, name, subName, courseNo, instructor, prerequisite, credit, department, type '
                                          'FROM course '
                                          'WHERE courseNo LIKE \'?%\'', (course_no,))
        return [dict(zip(['jx0404id', 'capacity', 'name', 'subName', 'courseNo', 'instructor', 'prerequisite', 'credit',
                          'department', 'type'], row)) for row in cursor]

    def search_by_course_name(self, course_name):
        cursor = self._connection.execute('SELECT '
                                          'jx0404id, capacity, name, subName, courseNo, instructor, prerequisite, credit, department, type '
                                          'FROM course '
                                          'WHERE name LIKE \'%?%\'', (course_name,))
        return [dict(zip(['jx0404id', 'capacity', 'name', 'subName', 'courseNo', 'instructor', 'prerequisite', 'credit',
                          'department', 'type'], row)) for row in cursor]

    def search_by_department(self, department):
        cursor = self._connection.execute('SELECT '
                                          'jx0404id, capacity, name, subName, courseNo, instructor, prerequisite, credit, department, type '
                                          'FROM course '
                                          'WHERE department LIKE \'%?%\'', (department,))
        return [dict(zip(['jx0404id', 'capacity', 'name', 'subName', 'courseNo', 'instructor', 'prerequisite', 'credit',
                          'department', 'type'], row)) for row in cursor]

    def search_by_instructor(self, instructor):
        cursor = self._connection.execute('SELECT '
                                          'jx0404id, capacity, name, subName, courseNo, instructor, prerequisite, credit, department, type '
                                          'FROM course '
                                          'WHERE instructor LIKE \'%?%\'', (instructor,))
        return [dict(zip(['jx0404id', 'capacity', 'name', 'subName', 'courseNo', 'instructor', 'prerequisite', 'credit',
                          'department', 'type'], row)) for row in cursor]

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
