# 文件名：teacher/router.py
"""
教师模块：教师增删改查

职责：定义 /teachers 前缀下端点，存在性校验后委托 TeacherModel
"""
import logging

from fastapi import APIRouter, HTTPException
from fastapi.params import Depends

from Group6.eams.auth.auth_deps import get_current_user, require_teacher
from Group6.eams.teacher.model import TeacherModel, TeacherRetireModel, TeacherBonusModel
from Group6.eams.teacher.vo import (
    TeacherCreate,
    TeacherUpdate,
    TeacherRetireCreate,
    TeacherRetireUpdate,
    TeacherBonusCreate,
    TeacherBonusUpdate,
)
from Group6.eams.common.response import success

logger = logging.getLogger(__name__)

# 创建子路由
router = APIRouter(prefix="/teachers", tags=["教师模块"])


def _ensure_teacher_exists(teacher_id):
    """教师存在性校验：退休/奖金登记等场景复用"""
    if TeacherModel().get_by_id(teacher_id) is None:
        raise HTTPException(status_code=404, detail=f"教师(id={teacher_id})不存在")


@router.get("/all")  # 路由装饰器：注册 GET 查询接口
def list_teachers(keyword: str = "", user = Depends(get_current_user)):
    """查：获取所有教师，可按姓名模糊查询"""
    return success(TeacherModel().get_all(keyword))


@router.get("/one/{teacher_id}")  # 路由装饰器：注册 GET 查询接口
def get_teacher(teacher_id: int, user = Depends(get_current_user)):
    """查：按 ID 获取单个教师"""
    teacher = TeacherModel().get_by_id(teacher_id)
    if teacher is None:
        raise HTTPException(status_code=404, detail="教师不存在")
    return success(teacher)


@router.post("/add")  # 路由装饰器：注册 POST 新增接口
def add_teacher(data: TeacherCreate, user = Depends(require_teacher)):
    """增：新增教师"""
    new_id = TeacherModel().create(
        name=data.name,
        gender=data.gender,
        age=data.age,
        subject=data.subject,
        phone=data.phone,
    )
    logger.info("新增教师 id:%s 姓名:%s", new_id, data.name)
    return success({"id": new_id}, msg="新增成功")


@router.put("/update/{teacher_id}")  # 路由装饰器：注册 PUT 修改接口
def update_teacher(teacher_id: int, data: TeacherUpdate, user = Depends(require_teacher)):
    """改：修改教师信息"""
    if TeacherModel().get_by_id(teacher_id) is None:
        raise HTTPException(status_code=404, detail="教师不存在")
    TeacherModel().update(
        teacher_id, data.name, data.gender, data.age, data.subject, data.phone
    )
    logger.info("修改教师 id:%s", teacher_id)
    return success(msg="修改成功")


@router.delete("/del/{teacher_id}")  # 路由装饰器：注册 DELETE 删除接口
def delete_teacher(teacher_id: int, user = Depends(require_teacher)):
    """删：删除教师"""
    if TeacherModel().get_by_id(teacher_id) is None:
        raise HTTPException(status_code=404, detail="教师不存在")
    TeacherModel().delete(teacher_id)
    logger.info("删除教师 id:%s", teacher_id)
    return success(msg="删除成功")


# ============================================================
# 教师退休管理（由原 teacher_extra.py 整合进教师模块，前缀 /teachers/retire）
# ============================================================
@router.post("/retire/add")
def add_retirement(data: TeacherRetireCreate, user = Depends(require_teacher)):
    """登记退休：校验教师存在后写入退休记录"""
    _ensure_teacher_exists(data.teacher_id)
    new_id = TeacherRetireModel().create(
        data.teacher_id, data.retire_date, data.reason, data.pension, data.remark
    )
    logger.info("登记教师退休 id:%s teacher_id:%s", new_id, data.teacher_id)
    return success({"id": new_id}, msg="退休登记成功")


@router.get("/retire/all")
def list_retirements(keyword: str = "",user = Depends(get_current_user)):
    """查询所有退休记录，可按教师姓名模糊查询"""
    return success(TeacherRetireModel().get_all(keyword))


@router.get("/retire/one/{retire_id}")
def get_retirement(retire_id: int,user = Depends(get_current_user)):
    """按退休记录ID查询"""
    record = TeacherRetireModel().get_by_id(retire_id)
    if record is None:
        raise HTTPException(status_code=404, detail="退休记录不存在")
    return success(record)


@router.get("/retire/by-teacher/{teacher_id}")
def list_retirements_by_teacher(teacher_id: int,user = Depends(get_current_user)):
    """按教师ID查询其退休记录"""
    _ensure_teacher_exists(teacher_id)
    return success(TeacherRetireModel().get_by_teacher(teacher_id))


@router.put("/retire/update/{retire_id}")
def update_retirement(retire_id: int, data: TeacherRetireUpdate, user = Depends(require_teacher)):
    """修改退休记录"""
    if TeacherRetireModel().get_by_id(retire_id) is None:
        raise HTTPException(status_code=404, detail="退休记录不存在")
    _ensure_teacher_exists(data.teacher_id)
    TeacherRetireModel().update(
        retire_id, data.teacher_id, data.retire_date, data.reason, data.pension, data.remark
    )
    logger.info("修改退休记录 id:%s", retire_id)
    return success(msg="修改成功")


@router.delete("/retire/del/{retire_id}")
def delete_retirement(retire_id: int, user = Depends(require_teacher)):
    """撤销（删除）退休记录"""
    if TeacherRetireModel().get_by_id(retire_id) is None:
        raise HTTPException(status_code=404, detail="退休记录不存在")
    TeacherRetireModel().delete(retire_id)
    logger.info("撤销退休记录 id:%s", retire_id)
    return success(msg="撤销成功")


# ============================================================
# 教师奖金管理（由原 teacher_extra.py 整合进教师模块，前缀 /teachers/bonus）
# ============================================================
@router.post("/bonus/add")
def add_bonus(data: TeacherBonusCreate, user = Depends(require_teacher)):
    """发放奖金：校验教师存在后写入奖金记录"""
    _ensure_teacher_exists(data.teacher_id)
    new_id = TeacherBonusModel().create(
        data.teacher_id, data.bonus_type, data.amount, data.bonus_date, data.remark
    )
    logger.info("发放教师奖金 id:%s teacher_id:%s 金额:%s", new_id, data.teacher_id, data.amount)
    return success({"id": new_id}, msg="奖金发放成功")


@router.get("/bonus/all")
def list_bonuses(keyword: str = "", user = Depends(require_teacher)):
    """查询所有奖金记录，可按教师姓名模糊查询"""
    return success(TeacherBonusModel().get_all(keyword))


@router.get("/bonus/one/{bonus_id}")  # 前端编辑奖金记录时预填详情
def get_bonus(bonus_id: int,user = Depends(require_teacher)):
    """按奖金记录ID查询"""
    record = TeacherBonusModel().get_by_id(bonus_id)
    if record is None:
        raise HTTPException(status_code=404, detail="奖金记录不存在")
    return success(record)


@router.get("/bonus/by-teacher/{teacher_id}")
def list_bonuses_by_teacher(teacher_id: int, user = Depends(require_teacher)):
    """按教师ID查询其奖金记录"""
    _ensure_teacher_exists(teacher_id)
    return success(TeacherBonusModel().get_by_teacher(teacher_id))


@router.get("/bonus/sum/{teacher_id}")
def sum_bonuses_by_teacher(teacher_id: int, user = Depends(require_teacher)):
    """某教师奖金总额"""
    _ensure_teacher_exists(teacher_id)
    total = TeacherBonusModel().sum_by_teacher(teacher_id)
    return success({"teacher_id": teacher_id, "total": total})


@router.get("/bonus/stat")
def stat_bonuses(user = Depends(require_teacher)):
    """按教师汇总统计奖金（发放次数 + 总额）"""
    return success(TeacherBonusModel().stat_by_teacher())


@router.put("/bonus/update/{bonus_id}")
def update_bonus(bonus_id: int, data: TeacherBonusUpdate, user = Depends(require_teacher)):
    """修改奖金记录"""
    if TeacherBonusModel().get_by_id(bonus_id) is None:
        raise HTTPException(status_code=404, detail="奖金记录不存在")
    _ensure_teacher_exists(data.teacher_id)
    TeacherBonusModel().update(
        bonus_id, data.teacher_id, data.bonus_type, data.amount, data.bonus_date, data.remark
    )
    logger.info("修改奖金记录 id:%s", bonus_id)
    return success(msg="修改成功")


@router.delete("/bonus/del/{bonus_id}")
def delete_bonus(bonus_id: int, user = Depends(require_teacher)):
    """删除奖金记录"""
    if TeacherBonusModel().get_by_id(bonus_id) is None:
        raise HTTPException(status_code=404, detail="奖金记录不存在")
    TeacherBonusModel().delete(bonus_id)
    logger.info("删除奖金记录 id:%s", bonus_id)
    return success(msg="删除成功")
