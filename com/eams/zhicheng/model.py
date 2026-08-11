# 文件名：zhicheng/model.py
"""
职称模块 - 数据访问层

职责：封装 teacher_titles 表 SQL 操作（增删改查 + 按教师/职称查询）
依赖：eams.common.db.Database
"""
import logging

from com.eams.common.db import Database

logger = logging.getLogger(__name__)


def init_db():
    """建表：执行 CREATE_TABLES_SQL，幂等（表已存在不重复创建）"""
    db = Database()
    try:
        for stmt in CREATE_TABLES_SQL.strip().split(';'):
            stmt = stmt.strip()
            if stmt:
                db.execute(stmt)
        logger.info("教师职称扩展建表完成")
        return {"teacher_titles": "teacher_titles"}
    finally:
        db.close()


class TeacherTitleModel:
    """教师职称表数据访问"""

    def get_all(self, keyword=''):
        """
        查询所有职称记录（关联教师姓名、科目），可按教师姓名或职称模糊查询
        :return: 职称记录字典列表
        """
        sql = (
            "SELECT t.*, tea.name AS teacher_name, tea.subject "
            "FROM teacher_titles t "
            "LEFT JOIN teachers tea ON t.teacher_id = tea.id "
        )
        params = []
        if keyword:
            sql += "WHERE tea.name LIKE %s OR t.title LIKE %s "
            params.extend([f"%{keyword}%", f"%{keyword}%"])
        sql += "ORDER BY t.level DESC, t.id"
        db = Database()
        try:
            return db.query_all(sql, tuple(params))
        finally:
            db.close()

    def get_by_id(self, title_id):
        """按职称记录ID查询（关联教师姓名）"""
        db = Database()
        try:
            return db.query_one(
                "SELECT t.*, tea.name AS teacher_name, tea.subject "
                "FROM teacher_titles t "
                "LEFT JOIN teachers tea ON t.teacher_id = tea.id "
                "WHERE t.id = %s", (title_id,)
            )
        finally:
            db.close()

    def get_by_teacher(self, teacher_id):
        """按教师ID查询其职称记录（等级高的在前）"""
        db = Database()
        try:
            return db.query_all(
                "SELECT t.*, tea.name AS teacher_name, tea.subject "
                "FROM teacher_titles t "
                "LEFT JOIN teachers tea ON t.teacher_id = tea.id "
                "WHERE t.teacher_id = %s ORDER BY t.level DESC", (teacher_id,)
            )
        finally:
            db.close()

    def create(self, teacher_id, title, level, obtain_date, remark):
        """登记职称，返回新记录自增ID"""
        db = Database()
        try:
            return db.insert(
                "INSERT INTO teacher_titles "
                "(teacher_id, title, level, obtain_date, remark) "
                "VALUES (%s, %s, %s, %s, %s)",
                (teacher_id, title, level, obtain_date, remark)
            )
        finally:
            db.close()

    def update(self, title_id, teacher_id, title, level, obtain_date, remark):
        """修改职称记录，返回受影响行数"""
        db = Database()
        try:
            return db.execute(
                "UPDATE teacher_titles SET teacher_id=%s, title=%s, level=%s, "
                "obtain_date=%s, remark=%s WHERE id=%s",
                (teacher_id, title, level, obtain_date, remark, title_id)
            )
        finally:
            db.close()

    def delete(self, title_id):
        """删除职称记录，返回受影响行数"""
        db = Database()
        try:
            return db.execute("DELETE FROM teacher_titles WHERE id = %s", (title_id,))
        finally:
            db.close()
