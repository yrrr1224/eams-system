# 文件名：auth/router.py
"""
认证模块：学生注册、登录（公开接口，无鉴权）
"""
import logging

from fastapi import APIRouter, HTTPException

from eams.auth.model import UserModel
from eams.auth.vo import RegisterRequest, LoginRequest
from eams.student.model import StudentModel
from eams.common.response import success
from eams.common.security import create_access_token

logger = logging.getLogger(__name__)

# 创建子路由：统一接口前缀、文档标签
router = APIRouter(prefix="/auth", tags=["认证模块"])


@router.post("/register")
def register(data: RegisterRequest):
    """
    学生自主注册: 先创建学生记录 → 再用学生ID创建登录账号
    :param data: 注册请求体（用户名/密码/姓名/性别/年龄）
    :return: {"student_id", "username"}
    :raises HTTPException 400: 用户名已存在
    """
    # 1. 校验用户名唯一性
    if UserModel().find_by_username(data.username):
        logger.warning("注册失败 用户名已存在:%s", data.username)
        raise HTTPException(status_code=400, detail="用户名已存在")

    # 2. 新建学生档案（默认高一、暂未分班分配老师）
    student_id = StudentModel().create(
        name=data.name,
        gender=data.gender,
        age=data.age,
        grade='高一',
        class_id=None,
        teacher_id=None,
        enrollment_date='2025-09-01',
    )

    # 3. 创建登录账号，绑定学生ID
    UserModel().create(
        username=data.username,
        password=data.password,
        role='student',
        student_id=student_id,
    )

    logger.info("注册成功 用户:%s", data.username)
    return success({"student_id": student_id, "username": data.username}, msg="注册成功")


@router.post("/login")
def login(data: LoginRequest):
    user = UserModel().find_by_username(data.username)
    if user is None or user['password'] != data.password:
        logger.warning("登录失败 用户:%s", data.username)
        raise HTTPException(status_code=400, detail="用户名或密码错误")

    # 生成token，携带角色
    token = create_access_token(
        user_id=user["id"],
        username=user["username"],
        role=user["role"]
    )
    logger.info("登录成功 用户:%s 角色:%s", data.username, user['role'])
    # 返回token与角色给前端
    return success({
        "access_token": token,
        "token_type": "bearer",
        "role": user["role"],
        "student_id": user["student_id"],
        "user_id": user["id"]
    }, msg="登录成功")