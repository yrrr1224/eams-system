-- =============================================
-- EAMS教务管理系统 数据库初始化脚本
-- 数据库：school_db 字符集 utf8mb4
-- 文档版本：V1.0
-- =============================================
DROP DATABASE IF EXISTS school_db;
CREATE DATABASE school_db DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE school_db;

-- 1. 用户表 users
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '用户ID',
    username VARCHAR(50) NOT NULL UNIQUE COMMENT '登录账号',
    password VARCHAR(100) NOT NULL COMMENT '登录密码(明文教学使用)',
    role VARCHAR(20) DEFAULT 'student' COMMENT '角色：admin/student',
    student_id INT NULL COMMENT '关联学生ID，学生角色绑定',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统用户表';

-- 2. 教师表 teachers
CREATE TABLE teachers (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '教师ID',
    name VARCHAR(50) NOT NULL COMMENT '教师姓名',
    gender VARCHAR(10) COMMENT '性别',
    age INT COMMENT '年龄',
    subject VARCHAR(50) COMMENT '主讲科目',
    phone VARCHAR(20) COMMENT '联系电话',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='教师信息表';

-- 3. 班级表 classes
CREATE TABLE classes (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '班级ID',
    name VARCHAR(50) NOT NULL COMMENT '班级名称',
    grade VARCHAR(20) COMMENT '年级：高一/高二/高三',
    head_teacher_id INT NULL COMMENT '班主任教师ID',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (head_teacher_id) REFERENCES teachers(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='班级表';

-- 4. 学生表 students
CREATE TABLE students (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '学生ID',
    name VARCHAR(50) NOT NULL COMMENT '学生姓名',
    gender VARCHAR(10) COMMENT '性别',
    age INT COMMENT '年龄',
    grade VARCHAR(20) COMMENT '就读年级',
    class_id INT NULL COMMENT '所属班级ID',
    teacher_id INT NULL COMMENT '授课班主任ID',
    enrollment_date DATE COMMENT '入学日期',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE SET NULL,
    FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学生信息表';

-- 5. 课程表 courses
CREATE TABLE courses (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '课程ID',
    name VARCHAR(50) NOT NULL COMMENT '课程名称',
    credit INT DEFAULT 1 COMMENT '学分',
    teacher_id INT NULL COMMENT '授课教师ID',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='课程表';

-- 6. 选课中间表 student_course
CREATE TABLE student_course (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '选课记录ID',
    student_id INT NOT NULL COMMENT '学生ID',
    course_id INT NOT NULL COMMENT '课程ID',
    score DECIMAL(5,2) NULL COMMENT '考试成绩',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '选课时间',
    -- 联合唯一约束：同一个学生不能重复选同一门课
    UNIQUE KEY uk_stu_course (student_id, course_id),
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学生选课成绩中间表';

-- =============================================
-- 插入基础种子数据
-- =============================================
-- 管理员账号
INSERT INTO users(username, password, role, student_id)
VALUES ('admin', 'admin123', 'admin', NULL);

-- 15位教师数据
INSERT INTO teachers(name,gender,age,subject,phone) VALUES
('张建国','男',42,'数学','13800001101'),
('李淑芬','女',38,'语文','13800001102'),
('王海涛','男',45,'英语','13800001103'),
('赵雅丽','女',36,'物理','13800001104'),
('陈志强','男',40,'化学','13800001105'),
('刘美玲','女',35,'生物','13800001106'),
('周建军','男',43,'历史','13800001107'),
('吴小燕','女',37,'地理','13800001108'),
('郑光明','男',41,'政治','13800001109'),
('孙文静','女',34,'音乐','13800001110'),
('马洪亮','男',39,'体育','13800001111'),
('朱晓红','女',33,'美术','13800001112'),
('胡卫东','男',44,'信息技术','13800001113'),
('林秋月','女',32,'心理健康','13800001114'),
('方国华','男',46,'通用技术','13800001115');

-- 4个班级
INSERT INTO classes(name,grade,head_teacher_id) VALUES
('高一(1)班','高一',1),
('高一(2)班','高一',2),
('高二(1)班','高二',3),
('高三(1)班','高三',4);

-- 4门课程
INSERT INTO courses(name,credit,teacher_id) VALUES
('数学',4,1),
('语文',4,2),
('英语',4,3),
('物理',3,4);

-- =============================================
-- 存储过程：批量生成100名学生
-- =============================================
DELIMITER //
CREATE PROCEDURE batch_insert_student()
BEGIN
    DECLARE i INT DEFAULT 1;
    DECLARE rand_gender CHAR(2);
    DECLARE rand_grade VARCHAR(10);
    DECLARE rand_class INT;
    DECLARE rand_age INT;
    DECLARE rand_teacher INT;
    DECLARE enroll_date DATE;
    WHILE i <= 100 DO
        IF FLOOR(RAND()*2) = 0 THEN
            SET rand_gender = '男';
        ELSE
            SET rand_gender = '女';
        END IF;
        SET rand_grade = ELT(FLOOR(RAND()*3)+1,'高一','高二','高三');
        SET rand_class = FLOOR(RAND()*4)+1;
        SET rand_age = FLOOR(RAND()*5)+15;
        SET rand_teacher = FLOOR(RAND()*15)+1;
        SET enroll_date = DATE_ADD('2023-09-01',INTERVAL FLOOR(RAND()*730) DAY);

        INSERT INTO students(name,gender,age,grade,class_id,teacher_id,enrollment_date)
        VALUES(CONCAT('学生',i), rand_gender, rand_age, rand_grade, rand_class, rand_teacher, enroll_date);
        SET i = i + 1;
    END WHILE;
END //
DELIMITER ;

CALL batch_insert_student();
DROP PROCEDURE IF EXISTS batch_insert_student;

-- =============================================
-- 存储过程：随机批量选课+成绩
-- =============================================
DELIMITER //
CREATE PROCEDURE batch_student_course()
BEGIN
    DECLARE stu_id INT DEFAULT 1;
    DECLARE rand_course_num INT;
    DECLARE cid INT;
    DECLARE score_val DECIMAL(5,2);
    WHILE stu_id <= 100 DO
        SET rand_course_num = FLOOR(RAND()*4)+1;
        WHILE rand_course_num > 0 DO
            SET cid = FLOOR(RAND()*4)+1;
            SET score_val = ROUND(FLOOR(RAND()*61)+40 + RAND(),1);
            IF NOT EXISTS (SELECT 1 FROM student_course WHERE student_id=stu_id AND course_id=cid) THEN
                INSERT INTO student_course(student_id,course_id,score) VALUES(stu_id,cid,score_val);
                SET rand_course_num = rand_course_num - 1;
            END IF;
        END WHILE;
        SET stu_id = stu_id + 1;
    END WHILE;
END //
DELIMITER ;

CALL batch_student_course();
DROP PROCEDURE IF EXISTS batch_student_course;

-- =============================================
-- 存储过程：批量生成100个学生登录账号
-- =============================================
DELIMITER //
CREATE PROCEDURE batch_create_student_user()
BEGIN
    DECLARE sid INT DEFAULT 1;
    WHILE sid <= 100 DO
        INSERT INTO users(username,password,role,student_id)
        VALUES(CONCAT('stu',LPAD(sid,3,'0')),'123456','student',sid);
        SET sid = sid + 1;
    END WHILE;
END //
DELIMITER ;

CALL batch_create_student_user();
DROP PROCEDURE IF EXISTS batch_create_student_user;

-- 数据统计校验
SELECT '数据库初始化完成' AS 运行状态;
SELECT COUNT(*) AS 教师总数 FROM teachers;
SELECT COUNT(*) AS 班级总数 FROM classes;
SELECT COUNT(*) AS 课程总数 FROM courses;
SELECT COUNT(*) AS 学生总数 FROM students;
SELECT COUNT(*) AS 选课记录总数 FROM student_course;
SELECT COUNT(*) AS 用户总数 FROM users;

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