import logging
import pymysql
from fastapi import APIRouter, HTTPException
from classes.model import ClassModel,CommitteeModel
from classes.vo import ClassCreate, ClassUpdate,CommitteeAssign, CommitteeUpdate
from teacher.model import TeacherModel
from common.response import success
from student.model import StudentModel
from typing import List

logger = logging.getLogger(__name__)
# 创建子路由
router = APIRouter(prefix="/classes", tags=["班级模块"])

@router.get("/all")
def list_classes(keyword: str = ""):
    """查：获取所有班级，可按班级名模糊查询"""
    return success(ClassModel().get_all(keyword))

@router.get("/stat")
def class_student_stat(keyword: str = "", grade: str = None):
    """班级人数统计，同时支持班级名模糊筛选 + 年级筛选"""
    data = ClassModel().get_class_student_stat(keyword, grade)
    return success(data, msg="班级人数统计查询成功")

@router.get("/one/{class_id}")
def get_class(class_id: int):
    """查：按 ID 获取单个班级"""
    cls = ClassModel().get_by_id(class_id)
    if cls is None:
        raise HTTPException(status_code=404, detail="班级不存在")
    return success(cls)

@router.post("/add")
def add_class(data: ClassCreate):
    """增：新增班级（若指定班主任，先验证教师存在）"""
    if data.head_teacher_id and TeacherModel().get_by_id(data.head_teacher_id) is None:
        raise HTTPException(status_code=404, detail="班主任教师不存在")
    if ClassModel().exists(data.name):
        raise HTTPException(status_code=409, detail="该班级已存在，不能重复新增")
    new_id = ClassModel().create(data.name, data.grade, data.head_teacher_id)
    logger.info("新增班级 id:%s 名称:%s", new_id, data.name)
    return success({"id": new_id}, msg="新增成功")

@router.put("/update/{class_id}")
def update_class(class_id: int, data: ClassUpdate):
    """改：修改班级信息"""
    if ClassModel().get_by_id(class_id) is None:
        raise HTTPException(status_code=404, detail="班级不存在")
    ClassModel().update(class_id, data.name, data.grade, data.head_teacher_id)
    logger.info("修改班级 id:%s", class_id)
    return success(msg="修改成功")

@router.delete("/del/{class_id}")
def delete_class(class_id: int):
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
def batch_delete_class(ids: List[int]):
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

@router.get("/committee/roles")
def list_committee_roles():
    """查：全部班委角色（下拉）"""
    return success(CommitteeModel().list_roles())


@router.get("/{class_id}/committee")
def list_class_committee(class_id: int, term: str = ""):
    """查：某班级的班委名单"""
    if ClassModel().get_by_id(class_id) is None:
        raise HTTPException(status_code=404, detail="班级不存在")
    return success(CommitteeModel().list_by_class(class_id, term or None))


@router.get("/{class_id}/committee/students")
def list_class_students(class_id: int):
    """查：该班级在册学生（班委弹窗下拉用）"""
    if ClassModel().get_by_id(class_id) is None:
        raise HTTPException(status_code=404, detail="班级不存在")
    return success(CommitteeModel().list_class_students(class_id))


@router.post("/{class_id}/committee")
def assign_committee(class_id: int, data: CommitteeAssign):
    """增：设置班委"""
    # 1. 班级存在
    if ClassModel().get_by_id(class_id) is None:
        raise HTTPException(status_code=404, detail="班级不存在")
    # 2. 学生存在
    student = StudentModel().get_by_id(data.student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="学生不存在")
    # 3. 学生确实属于该班级（防止前端传错）
    if student["class_id"] != class_id:
        raise HTTPException(status_code=400, detail="该学生不属于此班级")
    try:
        new_id = CommitteeModel().create(
            class_id, data.student_id, data.role_id, data.term
        )
    except pymysql.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="该学生本学期已担任班委，请先撤销原任职或改用修改"
        )
    logger.info("设置班委 班级:%s 学生:%s 角色:%s 学期:%s",
                class_id, data.student_id, data.role_id, data.term)
    return success({"id": new_id}, msg="设置班委成功")


@router.put("/committee/{committee_id}")
def update_committee(committee_id: int, data: CommitteeUpdate):
    """改：修改班委角色或学期"""
    if CommitteeModel().get_by_id(committee_id) is None:
        raise HTTPException(status_code=404, detail="班委记录不存在")
    try:
        CommitteeModel().update(committee_id, data.role_id, data.term)
    except pymysql.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="修改后与该班级其他同学任职冲突"
        )
    logger.info("修改班委 id:%s", committee_id)
    return success(msg="修改成功")


@router.delete("/committee/{committee_id}")
def delete_committee(committee_id: int):
    """删：撤销班委"""
    if CommitteeModel().get_by_id(committee_id) is None:
        raise HTTPException(status_code=404, detail="班委记录不存在")
    CommitteeModel().delete(committee_id)
    logger.info("撤销班委 id:%s", committee_id)
    return success(msg="已撤销")