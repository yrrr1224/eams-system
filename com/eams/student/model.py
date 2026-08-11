# 文件名：student/model.py
"""
学生模块 - 数据访问层

职责：封装 students 表及相关联表（classes/teachers/student_course）的 SQL 操作
包含：增删改查、分班、选老师、关键字查询、分页查询、级联删除（逐条执行）
依赖：common.db.Database
"""
from com.eams.common.db import Database


class StudentModel:
    """学生表（含选课程老师）数据访问"""

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
        return sql, params# params为空列表供追加

    def get_all(self, keyword=''):# 姓名关键字
        """查询所有学生（关联班级名、教师名、选课数），可按姓名模糊查询"""
        sql, params = self._base_sql()
        if keyword:#可选，为空返回全部
            sql += "WHERE s.name LIKE %s "
            params.append(f"%{keyword}%")
        sql += "ORDER BY s.id"
        db = Database()
        try:
            return db.query_all(sql, tuple(params))# 返回学生行字典列表
        finally:
            db.close()



    def get_by_id(self, student_id):
        """按 ID 查询学生（含班级名、教师名）"""
        db = Database()
        try:
            return db.query_one(# 返回学生行dict,不存在返回 None
                "SELECT s.*, c.name AS class_name, t.name AS teacher_name "
                "FROM students s "
                "LEFT JOIN classes c ON s.class_id = c.id "
                "LEFT JOIN teachers t ON s.teacher_id = t.id "
                "WHERE s.id = %s", (student_id,)
            )
        finally:
            db.close()

    def create(self, name, gender, age, grade, class_id, teacher_id, enrollment_date):
        """新增学生信息"""
        db = Database()
        try:
            return db.insert(# 返回新增记录的 ID
                "INSERT INTO students (name, gender, age, grade, class_id, teacher_id, enrollment_date) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (name, gender, age, grade, class_id, teacher_id, enrollment_date)
            )
        except Exception as e:
            # 出错时回滚事务（撤销所有未提交的操作）
            db.rollback()
            print(f'新增学生失败：{e}')
        finally:
            db.close()

    def update(self, student_id, name, gender, age, grade):
        """修改学生基本信息"""
        db = Database()
        try:
            return db.execute(# 返回受影响的行数
                "UPDATE students SET name=%s, gender=%s, age=%s, grade=%s WHERE id=%s",
                (name, gender, age, grade, student_id)
            )
        except Exception as e:
            # 出错时回滚事务（撤销所有未提交的操作）
            db.rollback()
            print(f'修改学生信息失败：{e}')
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
        except Exception as e:
            db.rollback()
            print(f'修改学生班级失败：{e}')
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
        except Exception as e:
            db.rollback()
            print(f'修改学生的老师失败：{e}')
        finally:
            db.close()

    def get_export_data(self, keyword=''):# 姓名关键字
        """导出学生信息,每个学生每门课一行（含课程名、授课老师、成绩）没选课的学生对应信息为空"""
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
        if keyword:# 可选，为空导出所有
            sql += "WHERE s.name LIKE %s "
            params.append(f"%{keyword}%")
        sql += "ORDER BY s.id, c.name"
        db = Database()
        try:
            return db.query_all(sql, tuple(params))# 返回学生行字典列表
        finally:
            db.close()

    def delete(self, student_id):
        """根据学生id删除学生（同时清理其选课记录和账号，逐条执行）,返回受影响行数"""
        db = Database()
        try:
            db.execute("DELETE FROM student_course WHERE student_id = %s", (student_id,))
            db.execute("DELETE FROM users WHERE student_id = %s", (student_id,))
            return db.execute("DELETE FROM students WHERE id = %s", (student_id,))
        except Exception as e:
            # 出错时回滚事务（撤销所有未提交的操作）
            db.rollback()
            print(f'删除学生失败：{e}')
        finally:
            db.close()