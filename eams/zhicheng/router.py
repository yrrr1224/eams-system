# 文件名：zhicheng/router.py
"""
职称模块：教师职称增删改查

职责：定义 /zhicheng 前缀下端点，校验教师存在后委托 TeacherTitleModel
"""
import logging

from fastapi import APIRouter, HTTPException

from Group6.eams.zhicheng.model import TeacherTitleModel
from Group6.eams.zhicheng.vo import TeacherTitleCreate, TeacherTitleUpdate
from Group6.eams.teacher.model import TeacherModel
from Group6.eams.common.response import success

logger = logging.getLogger(__name__)

# 创建子路由
router = APIRouter(prefix="/zhicheng", tags=["职称模块"])


def _ensure_teacher_exists(teacher_id):
    """教师存在性校验"""
    if TeacherModel().get_by_id(teacher_id) is None:
        raise HTTPException(status_code=404, detail=f"教师(id={teacher_id})不存在")


@router.get("/all")  # 路由装饰器：注册 GET 查询接口
def list_titles(keyword: str = ""):
    """查：获取所有职称记录（含教师姓名），可按教师姓名或职称模糊查询"""
    return success(TeacherTitleModel().get_all(keyword))


@router.get("/one/{title_id}")  # 路由装饰器：注册 GET 查询接口
def get_title(title_id: int):
    """查：按 ID 获取单条职称记录"""
    record = TeacherTitleModel().get_by_id(title_id)
    if record is None:
        raise HTTPException(status_code=404, detail="职称记录不存在")
    return success(record)


@router.get("/by-teacher/{teacher_id}")  # 路由装饰器：注册 GET 查询接口
def list_titles_by_teacher(teacher_id: int):
    """查：按教师 ID 查询其全部职称记录"""
    _ensure_teacher_exists(teacher_id)
    return success(TeacherTitleModel().get_by_teacher(teacher_id))


@router.post("/add")  # 路由装饰器：注册 POST 新增接口
def add_title(data: TeacherTitleCreate):
    """增：登记教师职称"""
    _ensure_teacher_exists(data.teacher_id)
    new_id = TeacherTitleModel().create(
        data.teacher_id, data.title, data.level, data.obtain_date, data.remark
    )
    logger.info("登记教师职称 id:%s teacher_id:%s 职称:%s", new_id, data.teacher_id, data.title)
    return success({"id": new_id}, msg="登记成功")


@router.put("/update/{title_id}")  # 路由装饰器：注册 PUT 修改接口
def update_title(title_id: int, data: TeacherTitleUpdate):
    """改：修改职称记录"""
    if TeacherTitleModel().get_by_id(title_id) is None:
        raise HTTPException(status_code=404, detail="职称记录不存在")
    _ensure_teacher_exists(data.teacher_id)
    TeacherTitleModel().update(
        title_id, data.teacher_id, data.title, data.level, data.obtain_date, data.remark
    )
    logger.info("修改职称记录 id:%s", title_id)
    return success(msg="修改成功")


@router.delete("/del/{title_id}")  # 路由装饰器：注册 DELETE 删除接口
def delete_title(title_id: int):
    """删：删除职称记录"""
    if TeacherTitleModel().get_by_id(title_id) is None:
        raise HTTPException(status_code=404, detail="职称记录不存在")
    TeacherTitleModel().delete(title_id)
    logger.info("删除职称记录 id:%s", title_id)
    return success(msg="删除成功")
