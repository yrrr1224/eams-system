from common.db import Database
import pymysql

class ClassModel:
    """班级表（分班）数据访问"""
    def get_all(self, keyword=''):
        """
        查询所有班级（关联班主任姓名），可按班级名模糊查询
        :param keyword: 班级名关键字（可选）
        :return: 班级行字典列表（含 head_teacher_name）
        """
        sql = (
            "SELECT c.*, t.name AS head_teacher_name "
            "FROM classes c LEFT JOIN teachers t ON c.head_teacher_id = t.id "
        )
        params = []
        if keyword:
            sql += "WHERE c.name LIKE %s "
            params.append(f"%{keyword}%")
        sql += "ORDER BY c.id"
        db = Database()
        try:
            return db.query_all(sql, tuple(params))
        finally:
            db.close()

    def get_by_id(self, class_id):
        """
        按 ID 查询班级
        :param class_id: 班级 ID
        :return: 班级行 dict；不存在返回 None
        """
        db = Database()
        try:
            return db.query_one("SELECT * FROM classes WHERE id = %s", (class_id,))
        finally:
            db.close()

    def get_class_student_stat(self, keyword='',grade=None):
        """
        统计每个班级学生总人数，关联 student 学生表
        :param keyword: 班级名称模糊搜索关键字
        :param grade: 年级筛选
        :return: list[dict] 包含 class_id、class_name、grade、head_teacher_name、student_count
        """
        sql = """
            SELECT 
                c.id class_id,
                c.name class_name,
                c.grade,
                t.name head_teacher_name,
                COUNT(s.id) student_count
            FROM classes c
            LEFT JOIN teachers t ON c.head_teacher_id = t.id
            LEFT JOIN students s ON c.id = s.class_id
        """
        params = []
        where_list = []
        if keyword:
            where_list.append("c.name LIKE %s")
            params.append(f"%{keyword}%")
        if grade:
            where_list.append("c.grade = %s")
            params.append(grade)
        if where_list:
            sql += " WHERE " + " AND ".join(where_list)
        sql += " GROUP BY c.id, c.name, c.grade, t.name ORDER BY c.id"
        db = Database()
        try:
            return db.query_all(sql, tuple(params))
        finally:
            db.close()

    def create(self, name, grade, head_teacher_id):
        """
        新增班级
        :return: 新班级自增 ID
        """
        db = Database()
        try:
            return db.insert(
                "INSERT INTO classes (name, grade, head_teacher_id) VALUES (%s, %s, %s)",
                (name, grade, head_teacher_id)
            )
        finally:
            db.close()

    def exists(self, name):
        """
        按班级名查是否已存在（重名校验）
        :param name: 班级名称
        :return: True=已存在，False=可用
        """
        db = Database()
        try:
            row = db.query_one(
                "SELECT id FROM classes WHERE name = %s LIMIT 1",
                (name,)
            )
            return row is not None
        finally:
            db.close()

    def update(self, class_id, name, grade, head_teacher_id):
        """
        修改班级
        :return: 受影响行数
        """
        db = Database()
        try:
            return db.execute(
                "UPDATE classes SET name=%s, grade=%s, head_teacher_id=%s WHERE id=%s",
                (name, grade, head_teacher_id, class_id)
            )
        finally:
            db.close()

    def delete(self, class_id):
        """
        删除单个班级，存在学生则禁止删除
        :param class_id: 班级ID
        :return: 受影响行数
        """
        db = Database()
        try:
            # 校验该班级下是否有学生
            check_sql = """
                  SELECT id FROM students WHERE class_id = %s LIMIT 1
              """
            student = db.query_one(check_sql, (class_id,))
            if student:
                raise Exception("该班级下存在学生，无法删除")
            # 无学生再执行删除
            return db.execute("DELETE FROM classes WHERE id = %s", (class_id,))
        finally:
            db.close()

    def batch_delete(self, id_list: list):
        """
        批量删除多个班级
        :param id_list: 班级ID数组 [1,2,3]
        :return: 成功删除行数
        """
        if not id_list:
            return 0
        db = Database()
        try:
            placeholders = ",".join(["%s"] * len(id_list))
            params_tuple = tuple(id_list)
            check_sql = f"""
                SELECT DISTINCT c.id, c.name
                FROM classes c
                LEFT JOIN students s ON c.id = s.class_id
                WHERE c.id IN ({placeholders}) AND s.id IS NOT NULL
            """
            conflict_rows = db.query_all(check_sql, params_tuple)
            if conflict_rows:
                conflict_names = [row["name"] for row in conflict_rows]
                msg = f"以下班级存在学生，禁止删除：{','.join(conflict_names)}"
                raise Exception(msg)
            del_sql = f"DELETE FROM classes WHERE id IN ({placeholders})"
            affect_rows = db.execute(del_sql, params_tuple)
            return affect_rows
        finally:
            db.close()
class CommitteeModel:
    """班委表数据访问（class_committee + class_committee_role）"""

    def list_roles(self):
        """全部班委角色（前端下拉）"""
        db = Database()
        try:
            return db.query_all(
                "SELECT id, role_name, role_desc FROM class_committee_role ORDER BY id"
            )
        finally:
            db.close()

    def list_class_students(self, class_id):
        """某班级的在册学生（班委弹窗的学生下拉用）"""
        db = Database()
        try:
            return db.query_all(
                "SELECT id, name FROM students WHERE class_id=%s ORDER BY id",
                (class_id,)
            )
        finally:
            db.close()

    def list_by_class(self, class_id, term=None):
        """班级班委名单，JOIN 学生名/角色名"""
        sql = (
            "SELECT cc.id, cc.class_id, cc.student_id, cc.role_id, cc.term, "
            "       s.name AS student_name, ccr.role_name "
            "FROM class_committee cc "
            "JOIN students s ON cc.student_id = s.id "
            "JOIN class_committee_role ccr ON cc.role_id = ccr.id "
            "WHERE cc.class_id = %s"
        )
        params = [class_id]
        if term:
            sql += " AND cc.term = %s"
            params.append(term)
        sql += " ORDER BY ccr.id"
        db = Database()
        try:
            return db.query_all(sql, tuple(params))
        finally:
            db.close()

    def create(self, class_id, student_id, role_id, term):
        db = Database()
        try:
            return db.insert(
                "INSERT INTO class_committee (class_id, student_id, role_id, term) "
                "VALUES (%s, %s, %s, %s)",
                (class_id, student_id, role_id, term)
            )
        finally:
            db.close()

    def update(self, committee_id, role_id, term):
        db = Database()
        try:
            return db.execute(
                "UPDATE class_committee SET role_id=%s, term=%s WHERE id=%s",
                (role_id, term, committee_id)
            )
        finally:
            db.close()

    def get_by_id(self, committee_id):
        db = Database()
        try:
            return db.query_one(
                "SELECT * FROM class_committee WHERE id=%s", (committee_id,)
            )
        finally:
            db.close()

    def delete(self, committee_id):
        db = Database()
        try:
            return db.execute(
                "DELETE FROM class_committee WHERE id=%s", (committee_id,)
            )
        finally:
            db.close()