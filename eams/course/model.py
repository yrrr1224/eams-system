# 文件名：course/model.py
"""
课程模块 - 数据访问层（含选课、成绩）
职责：
CourseModel：封装 courses 表 SQL（增删改查 + 按课程名查询，关联授课教师）
StudentCourseModel：封装 student_course 表 SQL（学生选课 / 退课 / 成绩 / 查询）
依赖：common.db.Database
"""
from eams.common.db import Database


class CourseModel:
    """课程表数据访问"""

    def get_all(self, keyword=''):
        """
        查询所有课程（关联授课教师名 + 选课人数）
        :param keyword: 课程名关键字
        :return: 课程行字典列表（含 teacher_name, student_count）
        """
        sql = (
            "SELECT c.*,-- 课程表全部字段"
            " t.name AS teacher_name, "
            "(SELECT COUNT(*) FROM student_course sc WHERE sc.course_id = c.id) AS student_count "
            "FROM courses c LEFT JOIN teachers t ON c.teacher_id = t.id"
        )

        #关键字逻辑
        params = []
        if keyword:
            sql += " WHERE c.name LIKE %s"
            params.append(f"%{keyword}%")  #前后百分号，表示课程名包含这个关键词就匹配
        sql += " ORDER BY c.id"

        db = Database()
        try:
            return db.query_all(sql, tuple(params))
        finally:
            db.close()

    def create(self, name, credit, teacher_id):
        """
        新增课程
        :return: 新课程自增 ID
        """
        db = Database()
        try:
            return db.insert(
                "INSERT INTO courses (name, credit, teacher_id) VALUES (%s, %s, %s)",
                (name, credit, teacher_id)
            )
        finally:
            db.close()

    def delete(self, course_id):
        """
        删除课程（同时清理选课记录，逐条执行）
        :param course_id: 课程 ID
        :return: 删除的课程行数
        """
        db = Database()
        try:
            db.execute("DELETE FROM student_course WHERE course_id = %s", (course_id,))
            return db.execute("DELETE FROM courses WHERE id = %s", (course_id,))
        finally:
            db.close()

    def update(self, course_id, name, credit, teacher_id):
        """
        修改课程
        :return: 受影响行数
        """
        db = Database()
        try:
            return db.execute(
                "UPDATE courses SET name=%s, credit=%s, teacher_id=%s WHERE id=%s",
                (name, credit, teacher_id, course_id)
            )
        finally:
            db.close()

    def get_by_id(self, course_id):
        """
        按 ID 查询课程（含选课人数）
        :param course_id: 课程 ID
        :return: 课程行 dict（含 student_count）；不存在返回 None
        """
        db = Database()
        try:
            return db.query_one(

                #WHERE sc.course_id = c.id：选课表里的课程 id = 当前这条课程的 id：找出这门课所有的选课记录
                # COUNT(*)：统计匹配到的记录行数即这门课有多少人选课
                "SELECT c.*, "
                "(SELECT COUNT(*) FROM student_course sc WHERE sc.course_id = c.id) AS student_count "
                "FROM courses c WHERE c.id = %s",
                (course_id,)
            )
        finally:
            db.close()

class StudentCourseModel:
    """学生选课"""

    def get_courses_by_student(self, student_id):
        """
        查询某学生已选的课程（关联课程名和教师名）
        :param student_id: 学生 ID
        :return: 已选课程行字典列表（含 course_name/credit/teacher_name/score）
        """
        db = Database()
        try:
            return db.query_all(
                "SELECT sc.*, c.name AS course_name, c.credit, "
                "t.name AS teacher_name "
                "FROM student_course sc "
                "JOIN courses c ON sc.course_id = c.id "
                "LEFT JOIN teachers t ON c.teacher_id = t.id "
                "WHERE sc.student_id = %s", (student_id,)
            )
        finally:
            db.close()

    def is_selected(self, student_id, course_id):
        """
        判断学生是否已选该课程,防止重复选课
        :return: True 表示已选
        """
        db = Database()
        try:
            return db.query_one(
                "SELECT * FROM student_course WHERE student_id=%s AND course_id=%s",
                (student_id, course_id)
            ) is not None
        finally:
            db.close()

    def select(self, student_id, course_id):
        """
        学生选课
        :return: 新选课记录自增 ID
        """
        db = Database()
        try:
            return db.insert(
                "INSERT INTO student_course (student_id, course_id) VALUES (%s, %s)",
                (student_id, course_id)
            )
        finally:
            db.close()

    def unselect(self, student_id, course_id):
        """
        学生退课
        :return: 受影响行数
        """
        db = Database()
        try:
            return db.execute(
                "DELETE FROM student_course WHERE student_id=%s AND course_id=%s",
                (student_id, course_id)
            )
        finally:
            db.close()

    def set_score(self, student_id, course_id, score):
        """
        登记成绩
        :return: 受影响行数
        """
        db = Database()
        try:
            return db.execute(
                "UPDATE student_course SET score=%s WHERE student_id=%s AND course_id=%s",
                (score, student_id, course_id)
            )
        finally:
            db.close()