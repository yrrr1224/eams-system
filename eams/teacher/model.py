# 文件名：teacher/model.py
"""
教师模块 - 数据访问层

职责：封装 teachers 表 SQL 操作（增删改查 + 按姓名关键字查询）
依赖：common.db.Database
"""
import logging


from eams.common.db import Database

logger = logging.getLogger(__name__)


class TeacherModel:
    """教师表数据访问"""

    def get_all(self, keyword=''):
        """
        查询所有教师，可按姓名模糊查询
        :param keyword: 姓名关键字（可选）
        :return: 教师行字典列表
        """
        sql = "SELECT * FROM teachers "
        params = []
        if keyword:
            sql += "WHERE name LIKE %s "
            params.append(f"%{keyword}%")
        sql += "ORDER BY id"
        db = Database()
        try:
            return db.query_all(sql, tuple(params))
        finally:
            db.close()

    def get_by_id(self, teacher_id):
        """
        按 ID 查询教师
        :param teacher_id: 教师 ID
        :return: 教师行 dict；不存在返回 None
        """
        db = Database()
        try:
            return db.query_one("SELECT * FROM teachers WHERE id = %s", (teacher_id,))
        finally:
            db.close()

    def create(self, name, gender, age, subject, phone):
        """
        新增教师
        :return: 新教师自增 ID
        """
        db = Database()
        try:
            return db.insert(
                "INSERT INTO teachers (name, gender, age, subject, phone) "
                "VALUES (%s, %s, %s, %s, %s)",
                (name, gender, age, subject, phone)
            )
        finally:
            db.close()

    def update(self, teacher_id, name, gender, age, subject, phone):
        """
        修改教师信息
        :return: 受影响行数
        """
        db = Database()
        try:
            return db.execute(
                "UPDATE teachers SET name=%s, gender=%s, age=%s, "
                "subject=%s, phone=%s WHERE id=%s",
                (name, gender, age, subject, phone, teacher_id)
            )
        finally:
            db.close()

    def delete(self, teacher_id):
        """
        删除教师
        :return: 受影响行数
        """
        db = Database()
        try:
            return db.execute("DELETE FROM teachers WHERE id = %s", (teacher_id,))
        finally:
            db.close()


# ============================================================
# 教师退休 + 教师奖金扩展（由原 teacher_extra.py 整合进本模块）
# 新增两张独立扩展表：teacher_retirements / teacher_bonuses
# 与 teachers 表互不影响；已有数据库升级时调用一次 init_db() 建表
# ============================================================
CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS teacher_retirements (
    id          INT          PRIMARY KEY AUTO_INCREMENT COMMENT '退休记录ID',
    teacher_id  INT          NOT NULL                   COMMENT '教师ID（关联 teachers.id）',
    retire_date DATE                                     COMMENT '退休日期',
    reason      VARCHAR(100) DEFAULT '正常退休'          COMMENT '退休原因',
    pension     DECIMAL(10,2) DEFAULT 0.00              COMMENT '月退休金（养老金）',
    remark      VARCHAR(200)                             COMMENT '备注',
    create_time DATETIME     DEFAULT CURRENT_TIMESTAMP   COMMENT '登记时间'
) COMMENT '教师退休记录表';

CREATE TABLE IF NOT EXISTS teacher_bonuses (
    id          INT          PRIMARY KEY AUTO_INCREMENT COMMENT '奖金记录ID',
    teacher_id  INT          NOT NULL                   COMMENT '教师ID（关联 teachers.id）',
    bonus_type  VARCHAR(50)  NOT NULL                   COMMENT '奖金类型：年终奖/绩效奖/优秀教师奖等',
    amount      DECIMAL(10,2) NOT NULL                  COMMENT '奖金金额',
    bonus_date  DATE                                     COMMENT '发放日期',
    remark      VARCHAR(200)                             COMMENT '备注',
    create_time DATETIME     DEFAULT CURRENT_TIMESTAMP   COMMENT '发放时间'
) COMMENT '教师奖金记录表';

"""


def init_db():
    """建表：执行 CREATE_TABLES_SQL，幂等（表已存在不重复创建）"""
    db = Database()
    try:
        for stmt in CREATE_TABLES_SQL.strip().split(';'):
            stmt = stmt.strip()
            if stmt:
                db.execute(stmt)
        logger.info("教师退休/奖金扩展建表完成")
        return {"retirements": "teacher_retirements", "bonuses": "teacher_bonuses"}
    finally:
        db.close()


class TeacherRetireModel:
    """教师退休记录表数据访问"""

    def get_all(self, keyword=''):
        """
        查询所有退休记录（关联教师姓名、科目），可按教师姓名模糊查询
        :return: 退休记录字典列表
        """
        sql = (
            "SELECT r.*, t.name AS teacher_name, t.subject "
            "FROM teacher_retirements r "
            "LEFT JOIN teachers t ON r.teacher_id = t.id "
        )
        params = []
        if keyword:
            sql += "WHERE t.name LIKE %s "
            params.append(f"%{keyword}%")
        sql += "ORDER BY r.id"
        db = Database()
        try:
            return db.query_all(sql, tuple(params))
        finally:
            db.close()

    def get_by_id(self, retire_id):
        """按退休记录ID查询（关联教师姓名）"""
        db = Database()
        try:
            return db.query_one(
                "SELECT r.*, t.name AS teacher_name, t.subject "
                "FROM teacher_retirements r "
                "LEFT JOIN teachers t ON r.teacher_id = t.id "
                "WHERE r.id = %s", (retire_id,)
            )
        finally:
            db.close()

    def get_by_teacher(self, teacher_id):
        """按教师ID查询该教师的所有退休记录"""
        db = Database()
        try:
            return db.query_all(
                "SELECT r.*, t.name AS teacher_name, t.subject "
                "FROM teacher_retirements r "
                "LEFT JOIN teachers t ON r.teacher_id = t.id "
                "WHERE r.teacher_id = %s ORDER BY r.id", (teacher_id,)
            )
        finally:
            db.close()

    def create(self, teacher_id, retire_date, reason, pension, remark):
        """登记退休，返回新记录自增ID"""
        db = Database()
        try:
            return db.insert(
                "INSERT INTO teacher_retirements "
                "(teacher_id, retire_date, reason, pension, remark) "
                "VALUES (%s, %s, %s, %s, %s)",
                (teacher_id, retire_date, reason, pension, remark)
            )
        finally:
            db.close()

    def update(self, retire_id, teacher_id, retire_date, reason, pension, remark):
        """修改退休记录，返回受影响行数"""
        db = Database()
        try:
            return db.execute(
                "UPDATE teacher_retirements SET teacher_id=%s, retire_date=%s, "
                "reason=%s, pension=%s, remark=%s WHERE id=%s",
                (teacher_id, retire_date, reason, pension, remark, retire_id)
            )
        finally:
            db.close()

    def delete(self, retire_id):
        """撤销（删除）退休记录，返回受影响行数"""
        db = Database()
        try:
            return db.execute("DELETE FROM teacher_retirements WHERE id = %s", (retire_id,))
        finally:
            db.close()


class TeacherBonusModel:
    """教师奖金记录表数据访问"""

    def get_all(self, keyword=''):
        """
        查询所有奖金记录（关联教师姓名、科目），可按教师姓名模糊查询
        :return: 奖金记录字典列表
        """
        sql = (
            "SELECT b.*, t.name AS teacher_name, t.subject "
            "FROM teacher_bonuses b "
            "LEFT JOIN teachers t ON b.teacher_id = t.id "
        )
        params = []
        if keyword:
            sql += "WHERE t.name LIKE %s "
            params.append(f"%{keyword}%")
        sql += "ORDER BY b.id"
        db = Database()
        try:
            return db.query_all(sql, tuple(params))
        finally:
            db.close()

    def get_by_id(self, bonus_id):
        """按奖金记录ID查询（关联教师姓名）"""
        db = Database()
        try:
            return db.query_one(
                "SELECT b.*, t.name AS teacher_name, t.subject "
                "FROM teacher_bonuses b "
                "LEFT JOIN teachers t ON b.teacher_id = t.id "
                "WHERE b.id = %s", (bonus_id,)
            )
        finally:
            db.close()

    def get_by_teacher(self, teacher_id):
        """按教师ID查询该教师的所有奖金记录"""
        db = Database()
        try:
            return db.query_all(
                "SELECT b.*, t.name AS teacher_name, t.subject "
                "FROM teacher_bonuses b "
                "LEFT JOIN teachers t ON b.teacher_id = t.id "
                "WHERE b.teacher_id = %s ORDER BY b.id", (teacher_id,)
            )
        finally:
            db.close()

    def sum_by_teacher(self, teacher_id):
        """某教师奖金总额"""
        db = Database()
        try:
            row = db.query_one(
                "SELECT COALESCE(SUM(amount), 0) AS total FROM teacher_bonuses "
                "WHERE teacher_id = %s", (teacher_id,)
            )
            return float(row['total']) if row else 0.0
        finally:
            db.close()

    def stat_by_teacher(self):
        """
        按教师汇总统计奖金（发放次数 + 总额），供展示
        :return: [{teacher_id, teacher_name, subject, cnt, total_amount}, ...]
        """
        db = Database()
        try:
            rows = db.query_all(
                "SELECT b.teacher_id, t.name AS teacher_name, t.subject, "
                "       COUNT(*) AS cnt, SUM(b.amount) AS total_amount "
                "FROM teacher_bonuses b "
                "LEFT JOIN teachers t ON b.teacher_id = t.id "
                "GROUP BY b.teacher_id, t.name, t.subject "
                "ORDER BY total_amount DESC"
            )
            for r in rows:
                r['total_amount'] = float(r['total_amount'] or 0)
            return rows
        finally:
            db.close()

    def create(self, teacher_id, bonus_type, amount, bonus_date, remark):
        """发放奖金，返回新记录自增ID"""
        db = Database()
        try:
            return db.insert(
                "INSERT INTO teacher_bonuses "
                "(teacher_id, bonus_type, amount, bonus_date, remark) "
                "VALUES (%s, %s, %s, %s, %s)",
                (teacher_id, bonus_type, amount, bonus_date, remark)
            )
        finally:
            db.close()

    def update(self, bonus_id, teacher_id, bonus_type, amount, bonus_date, remark):
        """修改奖金记录，返回受影响行数"""
        db = Database()
        try:
            return db.execute(
                "UPDATE teacher_bonuses SET teacher_id=%s, bonus_type=%s, "
                "amount=%s, bonus_date=%s, remark=%s WHERE id=%s",
                (bonus_id, teacher_id, bonus_type, amount, bonus_date, remark)
            )
        finally:
            db.close()

    def delete(self, bonus_id):
        """删除奖金记录，返回受影响行数"""
        db = Database()
        try:
            return db.execute("DELETE FROM teacher_bonuses WHERE id = %s", (bonus_id,))
        finally:
            db.close()