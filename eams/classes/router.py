# 文件名：eams/classes/router.py
"""
班级模块：班级增删改查（学生分班的数据基础
职责：定义 /classes 前缀下端点，存在性校验（班级/班主任）后委托 ClassModel
"""
import logging
from fastapi import APIRouter, HTTPException,Depends
# 修正包路径 com.wanhe → eams
from eams.classes.model import ClassModel
from eams.classes.vo import ClassCreate, ClassUpdate
from eams.teacher.model import TeacherModel
from eams.common.response import success
from eams.auth.auth_deps import get_current_user, require_teacher
from typing import List

logger = logging.getLogger(__name__)
# 创建子路由
router = APIRouter(prefix="/classes", tags=["班级模块"])

@router.get("/all")  # 路由装饰器：注册 GET 查询接口
def list_classes(keyword: str = ""):
    """查：获取所有班级（含班主任姓名），可按班级名模糊查询"""
    return success(ClassModel().get_all(keyword))

@router.get("/stat")
def class_student_stat(keyword: str = "", grade: str = None):
    """班级人数统计，同时支持班级名模糊筛选 + 年级筛选"""
    data = ClassModel().get_class_student_stat(keyword, grade)
    return success(data, msg="班级人数统计查询成功")

@router.get("/one/{class_id}")  # 路由装饰器：注册 GET 查询接口
def get_class(class_id: int):
    """查：按 ID 获取单个班级"""
    cls = ClassModel().get_by_id(class_id)
    if cls is None:
        raise HTTPException(status_code=404, detail="班级不存在")
    return success(cls)

@router.post("/add")  # 路由装饰器：注册 POST 新增接口
def add_class(data: ClassCreate,user = Depends(require_teacher)):
    """增：新增班级（若指定班主任，先验证教师存在）"""
    if data.head_teacher_id and TeacherModel().get_by_id(data.head_teacher_id) is None:
        raise HTTPException(status_code=404, detail="班主任教师不存在")
    new_id = ClassModel().create(data.name, data.grade, data.head_teacher_id)
    logger.info("新增班级 id:%s 名称:%s", new_id, data.name)
    return success({"id": new_id}, msg="新增成功")

@router.put("/update/{class_id}")  # 路由装饰器：注册 PUT 修改接口
def update_class(class_id: int, data: ClassUpdate,user = Depends(require_teacher)):
    """改：修改班级信息"""
    if ClassModel().get_by_id(class_id) is None:
        raise HTTPException(status_code=404, detail="班级不存在")
    ClassModel().update(class_id, data.name, data.grade, data.head_teacher_id)
    logger.info("修改班级 id:%s", class_id)
    return success(msg="修改成功")

@router.delete("/del/{class_id}")
def delete_class(class_id: int,user = Depends(require_teacher)):
    """删：删除班级，有学生禁止删除"""
    if ClassModel().get_by_id(class_id) is None:
        raise HTTPException(status_code=404, detail="班级不存在")
    try:
        ClassModel().delete(class_id)
        logger.info("删除班级 id:%s", class_id)
        return success(msg="删除成功")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/batch-del")
def batch_delete_class(ids: List[int],user = Depends(require_teacher)):
    """批量删除多个班级，存在学生的班级不允许删除"""
    if not ids:
        raise HTTPException(status_code=400, detail="请勾选需要删除的班级")
    try:
        affect = ClassModel().batch_delete(ids)
        logger.info("批量删除班级，ids=%s，成功删除数量：%s", ids, affect)
        return success(msg=f"操作完成，共删除{affect}个班级")
    except Exception as e:
        # 捕获班级有学生的异常，返回前端提示
        raise HTTPException(status_code=400, detail=str(e))