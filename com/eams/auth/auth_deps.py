from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from ..common.security import decode_token

# 登录接口地址 /auth/login
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# 获取当前登录用户（所有接口通用）
def get_current_user(token: str = Depends(oauth2_scheme)):
    return decode_token(token)

# 仅教师可访问：增删改接口专用依赖
def require_teacher(user = Depends(get_current_user)):
    if user["role"] != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足：仅教师可执行新增/编辑/删除操作"
        )
    return user