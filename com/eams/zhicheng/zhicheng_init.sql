# 建表 SQL：教师职称表（已有数据库升级时调用一次 init_db() 建表）
CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS teacher_titles (
    id          INT          PRIMARY KEY AUTO_INCREMENT COMMENT '职称记录ID',
    teacher_id  INT          NOT NULL                   COMMENT '教师ID（关联 teachers.id）',
    title       VARCHAR(50)  NOT NULL                   COMMENT '职称：助教/讲师/副教授/教授',
    level       INT          DEFAULT 1                  COMMENT '职称等级（1-4，越大越高）',
    obtain_date DATE                                     COMMENT '获得职称日期',
    remark      VARCHAR(200)                             COMMENT '备注',
    create_time DATETIME     DEFAULT CURRENT_TIMESTAMP   COMMENT '登记时间'
) COMMENT '教师职称表';
"""
