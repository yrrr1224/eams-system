# 文件名：student/model.py
"""
学生模块 - 数据访问层

职责：封装 students 表及相关联表（classes/teachers/student_course）的 SQL 操作
包含：增删改查、分班、选老师、关键字查询、分页查询、级联删除（逐条执行）
依赖：common.db.Database
"""
from common.db import Database


class StudentModel:
    """学生表（含选老师、分班）数据访问"""

    def _base_sql(self):
        """
        学生列表基础 SQL（含关联班级名、教师名、选课数子查询）
        :return: (sql, params)：sql 不含 WHERE/ORDER/LIMIT，params 为空列表供追加
        """
        sql = (
            "SELECT s.*, c.name AS class_name, t.name AS teacher_name, "
            "       (SELECT COUNT(*) FROM student_course sc "
            "        WHERE sc.student_id = s.id) AS course_count "
            "FROM students s "
            "LEFT JOIN classes c ON s.class_id = c.id "
            "LEFT JOIN teachers t ON s.teacher_id = t.id "
        )
        params = []
        return sql, params

    def get_all(self, keyword=''):
        """
        查询所有学生（关联班级名、教师名、选课数），可按姓名模糊查询
        :param keyword: 姓名关键字（可选，为空返回全部）
        :return: 学生行字典列表
        """
        sql, params = self._base_sql()
        if keyword:
            sql += "WHERE s.name LIKE %s "
            params.append(f"%{keyword}%")
        sql += "ORDER BY s.id"
        db = Database()
        try:
            return db.query_all(sql, tuple(params))
        finally:
            db.close()

    def get_page(self, keyword='', page=1, page_size=10):
        """
        分页查询学生，返回 {"total": int, "items": [...]}
        :param keyword: 姓名关键字（可选）
        :param page: 页码（>=1，自动钳制）
        :param page_size: 每页条数（1~100，自动钳制）
        :return: {"total": 总条数, "items": 当前页学生列表}
        """
        # 参数下限/上限钳制，防止非法输入
        page = max(1, page)
        page_size = max(1, min(100, page_size))
        base_sql, params = self._base_sql()
        where = ""
        if keyword:
            where = "WHERE s.name LIKE %s "
            params.append(f"%{keyword}%")
        db = Database()
        try:
            # 1. 统计总数（与列表同一 WHERE，保证 total 与 items 一致）
            total = db.query_one(
                "SELECT COUNT(*) AS cnt FROM students s " + where,
                tuple(params)
            )["cnt"]
            # 2. 查询当前页数据（LIMIT/OFFSET 分页）
            items = db.query_all(
                base_sql + where + "ORDER BY s.id LIMIT %s OFFSET %s",
                tuple(params) + ((page_size, (page - 1) * page_size))
            )
            return {"total": total, "items": items}
        finally:
            db.close()

    def get_by_id(self, student_id):
        """
        按 ID 查询学生（含班级名、教师名）
        :param student_id: 学生 ID
        :return: 学生行 dict；不存在返回 None
        """
        db = Database()
        try:
            return db.query_one(
                "SELECT s.*, c.name AS class_name, t.name AS teacher_name "
                "FROM students s "
                "LEFT JOIN classes c ON s.class_id = c.id "
                "LEFT JOIN teachers t ON s.teacher_id = t.id "
                "WHERE s.id = %s", (student_id,)
            )
        finally:
            db.close()

    def create(self, name, gender, age, grade, class_id, teacher_id, enrollment_date):
        """
        新增学生
        :return: 新学生自增 ID
        """
        db = Database()
        try:
            return db.insert(
                "INSERT INTO students (name, gender, age, grade, class_id, teacher_id, enrollment_date) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (name, gender, age, grade, class_id, teacher_id, enrollment_date)
            )
        finally:
            db.close()

    def update(self, student_id, name, gender, age, grade):
        """
        修改学生基本信息（姓名/性别/年龄/年级）
        :return: 受影响行数
        """
        db = Database()
        try:
            return db.execute(
                "UPDATE students SET name=%s, gender=%s, age=%s, grade=%s WHERE id=%s",
                (name, gender, age, grade, student_id)
            )
        finally:
            db.close()

    def change_class(self, student_id, class_id):
        """分班：把学生安排到指定班级"""
        db = Database()
        try:
            return db.execute(
                "UPDATE students SET class_id=%s WHERE id=%s",
                (class_id, student_id)
            )
        finally:
            db.close()

    def change_teacher(self, student_id, teacher_id):
        """选老师：把学生分配给指定教师"""
        db = Database()
        try:
            return db.execute(
                "UPDATE students SET teacher_id=%s WHERE id=%s",
                (teacher_id, student_id)
            )
        finally:
            db.close()

    def delete(self, student_id):
        """
        删除学生（同时清理其选课记录和账号，逐条执行）
        :param student_id: 学生 ID
        :return: 删除的学生行数
        """
        db = Database()
        try:
            db.execute("DELETE FROM student_course WHERE student_id = %s", (student_id,))
            db.execute("DELETE FROM users WHERE student_id = %s", (student_id,))
            return db.execute("DELETE FROM students WHERE id = %s", (student_id,))
        finally:
            db.close()
    def get_export_data(self, keyword=''):
        """
        导出用：每个学生每门课一行（含课程名、授课老师、成绩）
        没选课的学生也出现一行（课程/老师/成绩为空）
        :param keyword: 姓名关键字（可选）
        :return: 字典列表
        """
        sql = (
            "SELECT s.id, s.name, s.gender, s.age, s.grade, "
            "       s.enrollment_date, "
            "       cl.name AS class_name, "
            "       c.name AS course_name, "
            "       t.name AS course_teacher, "
            "       sc.score "
            "FROM students s "
            "LEFT JOIN classes cl ON s.class_id = cl.id "
            "LEFT JOIN student_course sc ON s.id = sc.student_id "
            "LEFT JOIN courses c ON sc.course_id = c.id "
            "LEFT JOIN teachers t ON c.teacher_id = t.id "
        )
        params = []
        if keyword:
            sql += "WHERE s.name LIKE %s "
            params.append(f"%{keyword}%")
        sql += "ORDER BY s.id, c.name"
        db = Database()
        try:
            return db.query_all(sql, tuple(params))
        finally:
            db.close()