# 文件名：zhicheng/vo.py
"""
职称模块 - 请求 VO

职责：定义教师职称新增/修改请求体的字段与校验规则
依赖：pydantic（BaseModel / Field）
"""
from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class TeacherTitleCreate(BaseModel):
    """登记教师职称请求体"""
    teacher_id: int = Field(..., description="教师ID")
    title: str = Field(..., max_length=50, description="职称：助教/讲师/副教授/教授")
    level: int = Field(1, ge=1, le=4, description="职称等级（1-4，越大越高）")
    obtain_date: Optional[date] = Field(None, description="获得职称日期，如 2026-01-01")
    remark: str = Field('', max_length=200, description="备注")


class TeacherTitleUpdate(TeacherTitleCreate):
    """修改教师职称请求体（字段与登记一致）"""
    pass
