# ============================================================
# 教师退休 + 教师奖金扩展（由原 teacher_extra.py 整合进本模块）
# 新增两张独立扩展表：teacher_retirements / teacher_bonuses
# 与 teachers 表互不影响；已有数据库升级时调用一次 init_db() 建表
# ============================================================
CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS teacher_retirements (
    id          INT          PRIMARY KEY AUTO_INCREMENT COMMENT '退休记录ID',
    teacher_id  INT          NOT NULL                   COMMENT '教师ID（关联 teachers.id）',
    retire_date DATE                                     COMMENT '退休日期',
    reason      VARCHAR(100) DEFAULT '正常退休'          COMMENT '退休原因',
    pension     DECIMAL(10,2) DEFAULT 0.00              COMMENT '月退休金（养老金）',
    remark      VARCHAR(200)                             COMMENT '备注',
    create_time DATETIME     DEFAULT CURRENT_TIMESTAMP   COMMENT '登记时间'
) COMMENT '教师退休记录表';

CREATE TABLE IF NOT EXISTS teacher_bonuses (
    id          INT          PRIMARY KEY AUTO_INCREMENT COMMENT '奖金记录ID',
    teacher_id  INT          NOT NULL                   COMMENT '教师ID（关联 teachers.id）',
    bonus_type  VARCHAR(50)  NOT NULL                   COMMENT '奖金类型：年终奖/绩效奖/优秀教师奖等',
    amount      DECIMAL(10,2) NOT NULL                  COMMENT '奖金金额',
    bonus_date  DATE                                     COMMENT '发放日期',
    remark      VARCHAR(200)                             COMMENT '备注',
    create_time DATETIME     DEFAULT CURRENT_TIMESTAMP   COMMENT '发放时间'
) COMMENT '教师奖金记录表';

"""