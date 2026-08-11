"""
统计模块：首页统计分析接口
职责：
- GET /stats/total-overview：首页大盘6项汇总数据（顶部数字卡片）
- GET /stats/class-count：各班级人数统计（柱状图数据源）
- GET /stats/gender-ratio：在校学生男女占比（饼状图数据源）
- GET /stats/course-selected：课程选课热度排行（柱状图数据源）
"""
import logging
from fastapi import APIRouter, Depends

# 读取本文件夹内model：单点 .
from .model import StatsModel

# 读取同级其他模块：两点 .. 回到上级eams目录
from ..common.response import success
from ..auth.auth_deps import get_current_user

logger = logging.getLogger(__name__)
# 创建子路由
router = APIRouter(prefix="/stats", tags=["统计模块"])


@router.get("/total-overview")
def get_home_overview():
    """
    首页顶部大盘汇总：学生、教师、课程、班级总数、选课总人次、无班级学生数
    返回示例：
    {
        "code": 200,
        "msg": "success",
        "data": {
            "student_total": 100,
            "teacher_total": 15,
            "course_total": 4,
            "class_total": 4,
            "select_total": 326,
            "no_class_student": 2
        }
    }
    """
    logger.info("请求首页大盘汇总统计数据")
    data = StatsModel().get_home_total_overview()
    return success(data)

#
# @router.get("/class-count")
# def class_count():
#     """
#     查：各班级人数统计（柱状图数据源）
#     返回示例：
#     {
#         "code": 200,
#         "msg": "success",
#         "data": [
#             {"id": 1, "class_name": "高一(1)班", "grade": "高一", "cnt": 18},
#             {"id": 2, "class_name": "高一(2)班", "grade": "高一", "cnt": 27}
#         ]
#     }
#     """
#     logger.info("查询各班级人数统计")
#     return success(StatsModel().class_count())
#
#
# @router.get("/gender-ratio")
# def gender_ratio():
#     """
#     查：在校学生男女占比（饼状图数据源）
#     返回示例：
#     {
#         "code": 200,
#         "msg": "success",
#         "data": [
#             {"gender": "男", "cnt": 59},
#             {"gender": "女", "cnt": 41}
#         ]
#     }
#     """
#     logger.info("查询在校学生男女占比")
#     return success(StatsModel().gender_ratio())


@router.get("/course-selected")
def course_selected():
    """
    查：各门课程选课人数热度排行（课程受欢迎度图表）
    返回示例：
    {
        "code": 200,
        "msg": "success",
        "data": [
            {"course_name": "语文", "select_num": 98},
            {"course_name": "数学", "select_num": 95},
            {"course_name": "英语", "select_num": 92},
            {"course_name": "物理", "select_num": 41}
        ]
    }
    """
    logger.info("查询课程选课热度统计")
    return success(StatsModel().course_selected_stats)
#


@router.get("/class-count")
def class_count(user = Depends(get_current_user)):
    logger.info("查询各班级人数统计")
    return success(StatsModel().class_count())

@router.get("/gender-ratio")
def gender_ratio(user = Depends(get_current_user)):
    logger.info("查询在校学生男女占比")
    return success(StatsModel().gender_ratio())