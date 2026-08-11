# 文件名：teacher/teacher_extra.py
"""
教师模块扩展 - 教师退休管理 + 教师奖金管理（独立扩展文件，不修改原代码）

一、功能说明
    1. 教师退休管理：登记退休 / 查询退休记录 / 修改 / 撤销（删除）
    2. 教师奖金管理：发放奖金 / 查询奖金记录 / 按教师汇总统计
    本文件不改动原 teacher 模块（model.py / router.py / vo.py）任何一行，
    仅作为独立扩展模块，新增 2 张表 + 2 个独立路由，
    并复用原 TeacherModel 做教师存在性校验。

二、依赖
    - Group6.eams.common.db.Database        数据库封装
    - Group6.eams.common.response.success   统一成功响应
    - Group6.eams.teacher.model.TeacherModel 复用原教师查询（存在性校验）
    - fastapi / pydantic                  FastAPI 框架

三、使用步骤（两步）
    1. 建表：执行下方 CREATE_TABLES_SQL 建两张新表（与 teachers 表互不影响）
       方式A：MySQL 命令行执行该 SQL
       方式B：调用一次 init_db()：
           python -c "from Group6.eams.teacher.teacher_extra import init_db; init_db()"
    2. 挂载路由：在 main.py 中追加 3 行（不改已有代码，仅新增注册）：
       from Group6.eams.teacher.teacher_extra import retire_router, bonus_router
       app.include_router(retire_router)
       app.include_router(bonus_router)

四、接口清单
    教师退休（前缀 /teachers/retire）：
      POST   /teachers/retire/add          登记退休
      GET    /teachers/retire/all          全部退休记录（含教师姓名）
      GET    /teachers/retire/one/{id}     按退休记录ID查询
      GET    /teachers/retire/by-teacher/{teacher_id}  按教师ID查询
      PUT    /teachers/retire/update/{id}  修改退休记录
      DELETE /teachers/retire/del/{id}     撤销（删除）退休记录
    教师奖金（前缀 /teachers/bonus）：
      POST   /teachers/bonus/add           发放奖金
      GET    /teachers/bonus/all           全部奖金记录（含教师姓名）
      GET    /teachers/bonus/one/{id}      按奖金记录ID查询
      GET    /teachers/bonus/by-teacher/{teacher_id}  按教师ID查询
      GET    /teachers/bonus/sum/{teacher_id}         某教师奖金总额
      GET    /teachers/bonus/stat          按教师汇总统计
      PUT    /teachers/bonus/update/{id}   修改奖金记录
      DELETE /teachers/bonus/del/{id}      删除奖金记录
"""

import logging
from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from Group6.eams.common.db import Database
from Group6.eams.common.response import success
from Group6.eams.teacher.model import TeacherModel

logger = logging.getLogger(__name__)

# ============================================================
# 一、建表 SQL（首次使用前执行）
# 说明：新增独立表，不修改原 teachers 表结构，不干扰原有功能
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


# ============================================================
# 二、数据访问层（Model）
# ============================================================
def _ensure_teacher_exists(teacher_id):
    """教师存在性校验，复用原 TeacherModel（不修改原代码）"""
    if TeacherModel().get_by_id(teacher_id) is None:
        raise HTTPException(status_code=404, detail=f"教师(id={teacher_id})不存在")


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


# ============================================================
# 三、请求 VO（pydantic 校验）
# ============================================================
class TeacherRetireCreate(BaseModel):
    """登记退休请求体"""
    teacher_id: int = Field(..., description="教师ID")
    retire_date: Optional[date] = Field(None, description="退休日期，如 2026-06-30")
    reason: str = Field('正常退休', max_length=100, description="退休原因")
    pension: float = Field(0.0, ge=0, description="月退休金（元）")
    remark: str = Field('', max_length=200, description="备注")


class TeacherRetireUpdate(TeacherRetireCreate):
    """修改退休记录请求体（字段与登记一致）"""
    pass


class TeacherBonusCreate(BaseModel):
    """发放奖金请求体"""
    teacher_id: int = Field(..., description="教师ID")
    bonus_type: str = Field(..., max_length=50, description="奖金类型：年终奖/绩效奖/优秀教师奖等")
    amount: float = Field(..., gt=0, description="奖金金额（元）")
    bonus_date: Optional[date] = Field(None, description="发放日期，如 2026-01-15")
    remark: str = Field('', max_length=200, description="备注")


class TeacherBonusUpdate(TeacherBonusCreate):
    """修改奖金记录请求体（字段与发放一致）"""
    pass


# ============================================================
# 四、路由（Router）
# ============================================================
# 退休路由：/teachers/retire 前缀
retire_router = APIRouter(prefix="/teachers/retire", tags=["教师退休扩展"])

# 奖金路由：/teachers/bonus 前缀
bonus_router = APIRouter(prefix="/teachers/bonus", tags=["教师奖金扩展"])


# ---------- 教师退休 ----------
@retire_router.post("/add")
def add_retirement(data: TeacherRetireCreate):
    """登记退休：校验教师存在后写入退休记录"""
    _ensure_teacher_exists(data.teacher_id)
    new_id = TeacherRetireModel().create(
        data.teacher_id, data.retire_date, data.reason, data.pension, data.remark
    )
    logger.info("登记教师退休 id:%s teacher_id:%s", new_id, data.teacher_id)
    return success({"id": new_id}, msg="退休登记成功")


@retire_router.get("/all")
def list_retirements(keyword: str = ""):
    """查询所有退休记录，可按教师姓名模糊查询"""
    return success(TeacherRetireModel().get_all(keyword))


@retire_router.get("/one/{retire_id}")
def get_retirement(retire_id: int):
    """按退休记录ID查询"""
    record = TeacherRetireModel().get_by_id(retire_id)
    if record is None:
        raise HTTPException(status_code=404, detail="退休记录不存在")
    return success(record)


@retire_router.get("/by-teacher/{teacher_id}")
def list_retirements_by_teacher(teacher_id: int):
    """按教师ID查询其退休记录"""
    _ensure_teacher_exists(teacher_id)
    return success(TeacherRetireModel().get_by_teacher(teacher_id))


@retire_router.put("/update/{retire_id}")
def update_retirement(retire_id: int, data: TeacherRetireUpdate):
    """修改退休记录"""
    if TeacherRetireModel().get_by_id(retire_id) is None:
        raise HTTPException(status_code=404, detail="退休记录不存在")
    _ensure_teacher_exists(data.teacher_id)
    TeacherRetireModel().update(
        retire_id, data.teacher_id, data.retire_date, data.reason, data.pension, data.remark
    )
    logger.info("修改退休记录 id:%s", retire_id)
    return success(msg="修改成功")


@retire_router.delete("/del/{retire_id}")
def delete_retirement(retire_id: int):
    """撤销（删除）退休记录"""
    if TeacherRetireModel().get_by_id(retire_id) is None:
        raise HTTPException(status_code=404, detail="退休记录不存在")
    TeacherRetireModel().delete(retire_id)
    logger.info("撤销退休记录 id:%s", retire_id)
    return success(msg="撤销成功")


# ---------- 教师奖金 ----------
@bonus_router.post("/add")
def add_bonus(data: TeacherBonusCreate):
    """发放奖金：校验教师存在后写入奖金记录"""
    _ensure_teacher_exists(data.teacher_id)
    new_id = TeacherBonusModel().create(
        data.teacher_id, data.bonus_type, data.amount, data.bonus_date, data.remark
    )
    logger.info("发放教师奖金 id:%s teacher_id:%s 金额:%s", new_id, data.teacher_id, data.amount)
    return success({"id": new_id}, msg="奖金发放成功")


@bonus_router.get("/all")
def list_bonuses(keyword: str = ""):
    """查询所有奖金记录，可按教师姓名模糊查询"""
    return success(TeacherBonusModel().get_all(keyword))


@bonus_router.get("/one/{bonus_id}")  # 前端编辑奖金记录时预填详情
def get_bonus(bonus_id: int):
    """按奖金记录ID查询"""
    record = TeacherBonusModel().get_by_id(bonus_id)
    if record is None:
        raise HTTPException(status_code=404, detail="奖金记录不存在")
    return success(record)


@bonus_router.get("/by-teacher/{teacher_id}")
def list_bonuses_by_teacher(teacher_id: int):
    """按教师ID查询其奖金记录"""
    _ensure_teacher_exists(teacher_id)
    return success(TeacherBonusModel().get_by_teacher(teacher_id))


@bonus_router.get("/sum/{teacher_id}")
def sum_bonuses_by_teacher(teacher_id: int):
    """某教师奖金总额"""
    _ensure_teacher_exists(teacher_id)
    total = TeacherBonusModel().sum_by_teacher(teacher_id)
    return success({"teacher_id": teacher_id, "total": total})


@bonus_router.get("/stat")
def stat_bonuses():
    """按教师汇总统计奖金（发放次数 + 总额）"""
    return success(TeacherBonusModel().stat_by_teacher())


@bonus_router.put("/update/{bonus_id}")
def update_bonus(bonus_id: int, data: TeacherBonusUpdate):
    """修改奖金记录"""
    if TeacherBonusModel().get_by_id(bonus_id) is None:
        raise HTTPException(status_code=404, detail="奖金记录不存在")
    _ensure_teacher_exists(data.teacher_id)
    TeacherBonusModel().update(
        bonus_id, data.teacher_id, data.bonus_type, data.amount, data.bonus_date, data.remark
    )
    logger.info("修改奖金记录 id:%s", bonus_id)
    return success(msg="修改成功")


@bonus_router.delete("/del/{bonus_id}")
def delete_bonus(bonus_id: int):
    """删除奖金记录"""
    if TeacherBonusModel().get_by_id(bonus_id) is None:
        raise HTTPException(status_code=404, detail="奖金记录不存在")
    TeacherBonusModel().delete(bonus_id)
    logger.info("删除奖金记录 id:%s", bonus_id)
    return success(msg="删除成功")


__all__ = ["init_db", "retire_router", "bonus_router"]
