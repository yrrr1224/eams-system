# 文件名：course/router.py
"""
课程模块：课程增删改查 + 学生选课 / 退课 / 成绩
职责：
定义 /courses 前缀下端点

课程 CRUD、学生选课 / 退课 / 成绩登记、查询学生已选课程
存在性校验（学生 / 课程不存在抛 404）、重复选课拦截（400）
"""
import logging
from typing import List
from fastapi import APIRouter, HTTPException, Depends

from eams.course.model import CourseModel, StudentCourseModel
from eams.course.vo import (
    CourseCreate, CourseUpdate, CourseSelect, ScoreUpdate, CourseResponse
)
from eams.student.model import StudentModel
from eams.teacher.model import TeacherModel
from eams.common.response import success
from eams.auth.auth_deps import get_current_user, require_teacher

logger = logging.getLogger(__name__)

# 创建子路由
router = APIRouter(prefix="/courses", tags=["课程模块"])


# ---------- 课程管理 ----------

@router.get("/all")
def list_courses(keyword: str = "", user = Depends(get_current_user)):
    """获取课程列表，支持课程名称模糊检索，返回教师名称、选课人数"""
    course_list = CourseModel().get_all(keyword=keyword)
    return success(course_list)

@router.get("/detail/{course_id}")
def get_course_detail(course_id: int, login_user=Depends(get_current_user)):
    """获取单门课程详情，携带选课人数"""
    course_info = CourseModel().get_by_id(course_id)
    if not course_info:
        raise HTTPException(status_code=404, detail="目标课程不存在")
    return success(data=course_info)

@router.get("/student/{student_id}/selected")
def get_student_selected_course(student_id: int, login_user=Depends(get_current_user)):
    """查询某个学生已经选上的全部课程，包含课程信息、教师、分数"""
    stu_model = StudentModel()
    if stu_model.get_by_id(student_id) is None:
        raise HTTPException(status_code=404, detail="找不到该学生信息")

    sc_model = StudentCourseModel()
    selected_data = sc_model.get_courses_by_student(student_id)
    return success(data=selected_data)

# 课程维护接口 仅教师
@router.post("/add")
def add_course(data: CourseCreate, user = Depends(require_teacher)):
    if data.teacher_id and TeacherModel().get_by_id(data.teacher_id) is None:
        raise HTTPException(status_code=404, detail="授课教师不存在")
    # BUG修复：原代码 .add → model实际方法是 .create
    new_id = CourseModel().create(data.name, data.credit, data.teacher_id)
    logger.info("新增课程 id:%s 名称:%s", new_id, data.name)
    return success({"id": new_id}, msg="新增成功")

@router.put("/update/{course_id}")
def update_course(course_id: int, data: CourseUpdate, user = Depends(require_teacher)):
    if CourseModel().get_by_id(course_id) is None:
        raise HTTPException(status_code=404, detail="课程不存在")
    CourseModel().update(course_id, data.name, data.credit, data.teacher_id)
    logger.info("修改课程 id:%s", course_id)
    return success(msg="修改成功")

@router.delete("/del/{course_id}")
def delete_course(course_id: int, user = Depends(require_teacher)):
    if CourseModel().get_by_id(course_id) is None:
        raise HTTPException(status_code=404, detail="课程不存在")
    CourseModel().delete(course_id)
    logger.info("删除课程 id:%s", course_id)
    return success(msg="删除成功")

# 选课/退课：学生自己可用，只校验登录
@router.post("/select/{student_id}")
def select_course(student_id: int, data: CourseSelect, user = Depends(get_current_user)):
    if StudentModel().get_by_id(student_id) is None:
        raise HTTPException(status_code=404, detail="学生不存在")
    if CourseModel().get_by_id(data.course_id) is None:
        raise HTTPException(status_code=404, detail="课程不存在")
    if StudentCourseModel().is_selected(student_id, data.course_id):
        raise HTTPException(status_code=400, detail="该课程已选过，不能重复选")
    StudentCourseModel().select(student_id, data.course_id)
    logger.info("学生选课 学生id:%s → 课程%s", student_id, data.course_id)
    return success(msg="选课成功")

@router.delete("/unselect/{student_id}")
def unselect_course(student_id: int, data: CourseSelect, user = Depends(get_current_user)):
    if not StudentCourseModel().is_selected(student_id, data.course_id):
        raise HTTPException(status_code=400, detail="未选该课程，无法退课")
    StudentCourseModel().unselect(student_id, data.course_id)
    logger.info("学生退课 学生id:%s 课程%s", student_id, data.course_id)
    return success(msg="退课成功")

# 成绩录入仅教师
@router.put("/score/write/{student_id}")
def write_student_score(student_id: int, form: ScoreUpdate, _=Depends(require_teacher)):
    """教师给学生登记课程成绩，必须是已选课程才允许录入"""
    scm = StudentCourseModel()
    # 校验该学生是否选了这门课
    if not scm.is_selected(student_id, form.course_id):
        raise HTTPException(status_code=400, detail="该学生尚未选修该课程，不能录入成绩")

    scm.set_score(student_id, form.course_id, form.score)
    logger.info(f"录入成绩：学生{student_id}，课程{form.course_id}，分数{form.score}")
    return success(msg="成绩登记成功")