-- 1. 班委角色字典（班长/学习委员/团支书等）
CREATE TABLE class_committee_role (
    id INT PRIMARY KEY AUTO_INCREMENT,
    role_name VARCHAR(30) NOT NULL COMMENT '班委角色名称',
    role_desc VARCHAR(100) COMMENT '角色职责说明',
    create_time DATETIME DEFAULT NOW()
);

-- 2. 班级班委关联表（核心，绑定班级、学生、角色）
CREATE TABLE IF NOT EXISTS class_committee (
    -- 自增主键ID，本表唯一标识
    id INT PRIMARY KEY AUTO_INCREMENT,
    -- 班级编号，非空，关联classes班级表主键id
    class_id INT NOT NULL COMMENT '班级ID，关联classes表',
    -- 学生编号，非空，关联students学生表主键id
    student_id INT NOT NULL COMMENT '学生ID，关联students学生表',
    -- 班委角色编号，非空，关联class_committee_role角色表主键id
    role_id INT NOT NULL COMMENT '班委角色ID',
    -- 任职学期字段，非空，存储如2026秋季这类学期文本
    term VARCHAR(20) NOT NULL COMMENT '任职学期，例2026秋季',
    -- 创建时间，默认值为当前数据库时间
    create_time DATETIME DEFAULT NOW(),

    -- 外键约束：class_id绑定classes表id，班级删除时级联删除对应班委记录
    FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE,
    -- 外键约束：student_id绑定students表id，学生删除时级联删除对应班委记录
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    -- 外键约束：role_id绑定class_committee_role角色表id，角色不能随意删除，无级联
    FOREIGN KEY (role_id) REFERENCES class_committee_role(id),
    -- 唯一联合索引：同一个学生，同一学期，只能在一个班级担任一个班委，防止重复设置
    UNIQUE uk_class_student_term (class_id, student_id, term)
);

-- 初始化内置班委角色
INSERT INTO class_committee_role (role_name, role_desc)
VALUES
('班长','统筹班级全部事务'),
('学习委员','负责学习、作业、考勤'),
('团支书','团务活动、思想工作'),
('文体委员','运动会、文艺活动'),
('生活委员','后勤、班级物资');