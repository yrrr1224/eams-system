"""
统计模块 - 数据访问层
职责：封装首页多维度统计SQL
1. 首页大盘汇总：学生/教师/课程/班级总数、选课总人次、未分配班级学生数
2. 各班级人数统计（柱状图）
3. 学生男女占比（饼图）
4. 各门课程选课人数热度统计（新增柱状/折线图）
依赖：common.db.Database（每次新建连接，方法内finally关闭连接）
"""
import logging

from ..common.db import Database

logger = logging.getLogger(__name__)


class StatsModel:
    """教务首页统计数据分析封装"""

    def get_home_total_overview(self):
        """
        首页顶部大盘汇总数据（6项统计卡片）
        返回字典：学生总数、教师总数、课程总数、班级总数、选课总人次、无班级学生人数
        适配前端首页数字卡片+图标展示
        """
        db = Database()
        try:
            sql = """
            SELECT
                (SELECT COUNT(id) FROM students) AS student_total,
                (SELECT COUNT(id) FROM teachers) AS teacher_total,
                (SELECT COUNT(id) FROM courses) AS course_total,
                (SELECT COUNT(id) FROM classes) AS class_total,
                (SELECT COUNT(id) FROM student_course) AS select_total,
                (SELECT COUNT(id) FROM students WHERE class_id IS NULL) AS no_class_student
            """
            data = db.query_one(sql)
            logger.info("首页大盘总览数据查询完成")
            return data
        finally:
            db.close()

    def class_count(self):
        """
        统计各班级人数（含班级名与年级），供柱状图展示
        LEFT JOIN：无学生的班级也返回 cnt=0
        :return: [{class_name, grade, cnt}, ...] 按年级、班级ID排序
        """
        db = Database()
        try:
            rows = db.query_all(
                "SELECT c.id, c.name AS class_name, c.grade, COUNT(s.id) AS cnt "
                "FROM classes c LEFT JOIN students s ON s.class_id = c.id "
                "GROUP BY c.id, c.name, c.grade "
                "ORDER BY c.grade, c.id"
            )
            logger.info("统计各班级人数，返回 %s 条", len(rows))
            return rows
        finally:
            db.close()

    def gender_ratio(self):
        """
        统计在校学生男女占比，供饼状图展示
        :return: [{gender, cnt}, ...]（男/女各自人数）
        """
        db = Database()
        try:
            rows = db.query_all(
                "SELECT gender, COUNT(*) AS cnt FROM students GROUP BY gender"
            )
            logger.info("统计在校学生男女占比，返回 %s 条", len(rows))
            return rows
        finally:
            db.close()

    def course_selected_stats(self):
        """
        各门课程选课人数热度统计
        用于课程受欢迎度柱状图/折线图
        :return: [{course_name, select_num}, ...] 按选课人数降序排列
        """
        db = Database()
        try:
            rows = db.query_all(
                "SELECT c.name AS course_name, COUNT(sc.id) AS select_num "
                "FROM courses c LEFT JOIN student_course sc ON c.id = sc.course_id "
                "GROUP BY c.id, c.name "
                "ORDER BY select_num DESC"
            )
            logger.info("课程选课热度统计，返回 %s 条", len(rows))
            return rows
        finally:
            db.close()