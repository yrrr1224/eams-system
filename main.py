# 文件名：main.py
"""
eams 学校教务管理系统 - 程序入口

功能：学生/教师管理、学生选课选老师、学生分班、学生自主注册登录
运行（Windows 本地）：
  开发：python main.py
"""
import os
#代码内启动 Uvicorn 短时间请求过载，uvicorn 阻塞
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse

# 统一导入前缀：eams
from eams.auth.router import router as auth_router
from eams.student.router import router as student_router
from eams.teacher.router import router as teacher_router
from eams.classes.router import router as classes_router
from eams.course.router import router as course_router
from eams.stats.router import router as stats_router

# 加载公共日志、全局异常
import eams.common.logging
from eams.common.exceptions import register_exception_handlers

# 实例化 FastAPI 主程序
app = FastAPI(
    title="eams 学校教务管理系统",
    description="学生/教师管理、选课选老师、分班、注册登录一体化 API",
    version="1.0.0",
)

# 项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ===================== 页面路由（单数页面地址：/student /teacher 等） =====================
def _serve_manage_page(page_file: str) -> FileResponse:
    return FileResponse(os.path.join(BASE_DIR, "static", page_file))

@app.get("/student")
def student_page():
    return _serve_manage_page("student.html")

@app.get("/teacher")
def teacher_page():
    return _serve_manage_page("teacher.html")

@app.get("/course")
def course_page():
    return _serve_manage_page("course.html")

@app.get("/classes")
def classes_page():
    return _serve_manage_page("classes.html")

@app.get("/dashboard")
def dashboard_page():
    return _serve_manage_page("index.html")

@app.get("/login")
def login_page():
    return _serve_manage_page("login.html")

@app.get("/")
def root():
    # 站点入口先进登录页，登录成功后由前端跳转 /dashboard 仪表盘
    return RedirectResponse(url="/login")

# ========== 1.优先全部API路由 ==========
app.include_router(auth_router)
app.include_router(student_router)
app.include_router(teacher_router)
app.include_router(classes_router)
app.include_router(course_router)
app.include_router(stats_router)

register_exception_handlers(app)

# ========== 2.静态文件挂载到 /static，不再挂载根路径！！ ==========
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# 本地直接运行入口，关闭reload！reload会加重根挂载bug
if __name__ == "__main__":
    uvicorn.run(
        app="main:app",
        host="127.0.0.1",
        port=8000,
        workers=2,  # 2个工作进程
        limit_concurrency=50,
        reload=True,  # 代码修改自动重启（开发环境开启；上线务必关掉）
        log_level="info"
    )