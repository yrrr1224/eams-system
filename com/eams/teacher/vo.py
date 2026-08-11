# 文件名：teacher/vo.py
"""
教师模块 - 请求 VO

职责：定义教师新增/修改请求体的字段与校验规则
依赖：pydantic（BaseModel / Field）
"""
from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class TeacherCreate(BaseModel):
    """新增教师请求体"""
    name: str = Field(..., max_length=50, description="姓名")
    gender: str = Field('男', max_length=10, description="性别")
    age: int = Field(..., ge=20, le=70, description="年龄")
    subject: str = Field(..., max_length=50, description="教授科目")
    phone: str = Field('', max_length=20, description="联系电话")


class TeacherUpdate(BaseModel):
    """修改教师信息请求体（字段与新增一致）"""
    name: str = Field(..., max_length=50, description="姓名")
    gender: str = Field('男', max_length=10, description="性别")
    age: int = Field(..., ge=20, le=70, description="年龄")
    subject: str = Field(..., max_length=50, description="教授科目")
    phone: str = Field('', max_length=20, description="联系电话")


# ============================================================
# 教师退休 + 教师奖金请求 VO（由原 teacher_extra.py 整合进本模块）
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
