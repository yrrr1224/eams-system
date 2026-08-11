# 文件名：student/router.py
"""
学生模块：学生增删改查、分班、选老师、学生信息导出

职责：
- 定义 /students 前缀下全部端点
- 路由层做存在性校验（学生/班级/教师不存在抛 404），数据访问委托 StudentModel
- 列表支持关键字查询与分页（/students/page 返回 {total, items}）
"""
import csv
import io
import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from com.eams.student.model import StudentModel
from com.eams.student.vo import StudentCreate, StudentUpdate, ClassAssign, TeacherAssign
from com.eams.classes.model import ClassModel
from com.eams.teacher.model import TeacherModel
from com.eams.common.response import success

logger = logging.getLogger(__name__)

# 创建子路由：统一接口前缀、文档标签
router = APIRouter(prefix="/students", tags=["学生模块"])


@router.get("/all")  # 路由装饰器：注册GET查询接口
def list_students(keyword: str = ""):
    """获取所有学生（含班级名、教师名、选课数），可按姓名模糊查询"""
    return success(StudentModel().get_all(keyword))

@router.get("/one/{student_id}")  # 路由装饰器：注册GET查询接口
def get_student(student_id: int):
    """根据student_id获取单个学生"""
    student = StudentModel().get_by_id(student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="学生不存在")
    return success(student)

@router.get("/by-grade/{grade}")# 路由装饰器：注册GET新增接口
def list_by_grade(grade: str):
    """根据grade获取该年级所有学生"""
    students = StudentModel().get_all()
    # 用filter进行条件过滤
    result = list(filter(lambda s: s['grade'] == grade, students))
    return success(result)

@router.get("/export-csv")# 路由装饰器：注册GET新增接口
def export_students_csv(keyword: str = ""):
    """导出学生列表为 CSV：每人每门课一行，含课程名、授课老师、成绩"""
    rows = StudentModel().get_export_data(keyword)
    # 在内存中构建 CSV，不写磁盘
    output = io.StringIO()
    writer = csv.writer(output)

    # 表头
    writer.writerow(["ID", "姓名", "性别", "年龄", "年级", "班级", "入学日期","课程", "授课老师", "成绩"])

    # 数据行
    for r in rows:
        writer.writerow([# writerow 构造并写入一条CSV记录，数据来自字段的可迭代对象。非字符串元素将被转换为字符串
            r.get("id", ""),
            r.get("name", ""),
            r.get("gender", ""),
            r.get("age", ""),
            r.get("grade", ""),
            r.get("class_name", "") or "未分班",
            r.get("enrollment_date", ""),
            r.get("course_name", "") or "未选课",
            r.get("course_teacher", "") or "-",
            r.get("score") if r.get("score") is not None else "未登记",
        ])

    csv_content = output.getvalue()
    output.close()
    # 浏览器识别为文件下载，而非页面展示
    return Response(
        content=csv_content.encode("utf-8-sig"),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=students.csv"},
    )


@router.post("/add")  # 路由装饰器：注册POST新增接口
def add_student(data: StudentCreate):
    """新增学生"""
    # 如果指定的班级和教师不存在，则抛出异常
    if ClassModel().get_by_id(data.class_id) is None:
        raise HTTPException(status_code=404, detail="班级不存在")
    if TeacherModel().get_by_id(data.teacher_id) is None:
        raise HTTPException(status_code=404, detail="教师不存在")

    new_id = StudentModel().create(
        name=data.name,
        gender=data.gender,
        age=data.age,
        grade=data.grade,
        class_id=data.class_id,
        teacher_id=data.teacher_id,
        enrollment_date=data.enrollment_date,
    )
    logger.info("新增学生 id:%s 姓名:%s", new_id, data.name)
    return success({"id": new_id}, msg="新增成功")


@router.put("/update/{student_id}")  # 路由装饰器：注册PUT修改接口
def update_student(student_id: int, data: StudentUpdate):
    """修改学生基本信息"""
    if StudentModel().get_by_id(student_id) is None:
        raise HTTPException(status_code=404, detail="学生不存在")
    StudentModel().update(student_id, data.name, data.gender, data.age, data.grade)
    logger.info("修改学生 id:%s", student_id)
    return success(msg="修改成功")


@router.put("/assign-class/{student_id}")  # 路由装饰器：注册PUT修改接口
def assign_class(student_id: int, data: ClassAssign):
    """把学生安排到指定班级"""
    if StudentModel().get_by_id(student_id) is None:
        raise HTTPException(status_code=404, detail="学生不存在")
    if ClassModel().get_by_id(data.class_id) is None:
        raise HTTPException(status_code=404, detail="班级不存在")
    StudentModel().change_class(student_id, data.class_id)
    logger.info("学生分班 id:%s → 班级%s", student_id, data.class_id)
    return success(msg="分班成功")


@router.put("/assign-teacher/{student_id}")  # 路由装饰器：注册PUT修改接口
def assign_teacher(student_id: int, data: TeacherAssign):
    """选老师：把学生分配给指定教师"""
    if StudentModel().get_by_id(student_id) is None:
        raise HTTPException(status_code=404, detail="学生不存在")
    if TeacherModel().get_by_id(data.teacher_id) is None:
        raise HTTPException(status_code=404, detail="教师不存在")
    StudentModel().change_teacher(student_id, data.teacher_id)
    logger.info("学生选老师 id:%s → 教师%s", student_id, data.teacher_id)
    return success(msg="选老师成功")


@router.delete("/del/{student_id}")  # 路由装饰器：注册DELETE删除接口
def delete_student(student_id: int):
    """删除学生,级联删除选课记录和账号"""
    if StudentModel().get_by_id(student_id) is None:
        raise HTTPException(status_code=404, detail="学生不存在")
    StudentModel().delete(student_id)
    logger.info("删除学生 id:%s", student_id)
    return success(msg="删除成功")
