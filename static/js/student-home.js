/* ==========================================================================
   eams 教务管理系统 · 学生个人主页逻辑
   个人信息（/students/one/{id}）+ 我的选课（已选 + 选课/退课）+ 我的成绩
   学生 id 来自登录会话（localStorage student_id），仅展示本人数据。
   依赖：auth.js（EamsAuth + 全局 fetch 令牌注入）
   ========================================================================== */
(function () {
  'use strict';

  var esc = function (s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  };

  /* 会话里没有学生 id 则退回登录页（守卫已兜底，这里双保险） */
  var studentId = EamsAuth.getStudentId();
  if (!studentId) {
    EamsAuth.toLogin();
    return;
  }

  var state = { profile: null, myCourses: [], allCourses: [] };

  /* ---------- API 封装（统一 envelope：code==0 成功，与后端一致） ---------- */
  function api(path, options) {
    options = options || {};
    return fetch(path, {
      method: options.method || 'GET',
      headers: options.body ? { 'Content-Type': 'application/json' } : undefined,
      body: options.body ? JSON.stringify(options.body) : undefined
    }).then(function (res) {
      return res.json().catch(function () { throw new Error('服务器响应异常'); });
    }).then(function (env) {
      if (!env || env.code !== 0) {
        var msg = (env && env.msg) || '操作失败';
        if (env && Array.isArray(env.data) && env.data[0] && env.data[0].msg) {
          msg = msg + '：' + env.data[0].msg;
        }
        var err = new Error(msg);
        err.code = env && env.code;
        throw err;
      }
      return env.data;
    });
  }

  /* ---------- Toast ---------- */
  var toastEl = document.getElementById('toastRoot');
  function toast(msg, type) {
    var el = toastEl.querySelector('.toast');
    if (!el) {
      el = document.createElement('div');
      el.className = 'toast';
      toastEl.appendChild(el);
    }
    el.innerHTML = '<span></span>';
    el.querySelector('span').textContent = msg;
    el.className = 'toast ' + (type || 'success');
    el.classList.add('show');
    clearTimeout(toast._t);
    toast._t = setTimeout(function () { el.classList.remove('show'); }, 2400);
  }

  /* ---------- DOM 引用 ---------- */
  var profileFields = document.getElementById('profileFields');
  var profileState = document.getElementById('profileState');
  var coursesTbody = document.querySelector('#coursesTable tbody');
  var scoresTbody = document.querySelector('#scoresTable tbody');
  var courseSelect = document.getElementById('courseSelect');
  var selectBtn = document.getElementById('selectBtn');
  var selectHint = document.getElementById('selectHint');

  /* ---------- 个人信息 ---------- */
  function loadProfile() {
    return api('/students/one/' + studentId).then(function (p) {
      state.profile = p;
      renderProfile();
      /* 把顶栏的学生姓名换成真实姓名 */
      var nm = document.querySelector('.admin-name');
      if (nm && p && p.name) nm.textContent = p.name;
    });
  }

  function renderProfile() {
    var p = state.profile || {};
    var items = [
      { k: '学号', v: p.id },
      { k: '姓名', v: p.name },
      { k: '性别', v: p.gender },
      { k: '年龄', v: p.age },
      { k: '年级', v: p.grade },
      { k: '班级', v: p.class_name || '<span class="muted">未分班</span>' },
      { k: '班主任', v: p.teacher_name || '<span class="muted">未分配</span>' },
      { k: '入学日期', v: p.enrollment_date }
    ];
    profileFields.innerHTML = items.map(function (it) {
      return '<div class="profile-item"><div class="k">' + esc(it.k) + '</div>' +
        '<div class="v">' + (it.v == null || it.v === '' ? '—' : it.v) + '</div></div>';
    }).join('');
    profileState.textContent = '已登录';
  }

  /* ---------- 我的选课 + 我的成绩（共用 /courses/student/{id} 数据） ---------- */
  function loadCourses() {
    return Promise.all([
      api('/courses/student/' + studentId),
      api('/courses/all')
    ]).then(function (rs) {
      state.myCourses = rs[0] || [];
      state.allCourses = rs[1] || [];
      renderCourses();
      renderScores();
    });
  }

  function renderCourses() {
    var rows = state.myCourses;
    if (rows.length) {
      coursesTbody.innerHTML = rows.map(function (c) {
        return '<tr>' +
          '<td>' + esc(c.course_name) + '</td>' +
          '<td>' + esc(c.credit) + '</td>' +
          '<td>' + esc(c.teacher_name || '—') + '</td>' +
          '<td>' + (c.score != null ? esc(c.score) : '<span class="chip">未登记</span>') + '</td>' +
          '<td><button type="button" class="btn-mini danger" data-unselect="' + esc(c.course_id) + '">退课</button></td>' +
        '</tr>';
      }).join('');
      coursesTbody.querySelectorAll('[data-unselect]').forEach(function (b) {
        b.addEventListener('click', function () { doUnselect(+b.getAttribute('data-unselect')); });
      });
    } else {
      coursesTbody.innerHTML = '<tr><td colspan="5">' +
        '<div class="empty"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-6l-2 3h-4l-2-3H2"/><path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/></svg><p>暂未选择任何课程，请在下方选择</p></div>' +
        '</td></tr>';
    }

    /* 可选课程下拉：过滤掉已选课程 */
    var selectedIds = state.myCourses.map(function (c) { return String(c.course_id); });
    var avail = state.allCourses.filter(function (c) { return selectedIds.indexOf(String(c.id)) === -1; });
    courseSelect.innerHTML = avail.map(function (c) {
      return '<option value="' + esc(c.id) + '">' + esc(c.name) + '（' + esc(c.credit) + ' 学分）</option>';
    }).join('') || '<option value="">—</option>';
    selectBtn.disabled = !avail.length;
    selectHint.textContent = avail.length ? '可选课程 ' + avail.length + ' 门' : '已选满，暂无可选课程';
  }

  function gradeOf(s) {
    if (s == null) return null;
    if (s >= 90) return '优';
    if (s >= 80) return '良';
    if (s >= 70) return '中';
    if (s >= 60) return '及格';
    return '不及格';
  }
  function scoreChip(s) {
    if (s == null) return '<span class="chip">未登记</span>';
    var g = gradeOf(s);
    var cls = g === '不及格' ? 'score-fail' : (g === '优' || g === '良' ? 'score-pass' : '');
    return '<span class="chip ' + cls + '">' + esc(s) + ' 分</span>';
  }

  function renderScores() {
    var rows = state.myCourses;
    if (rows.length) {
      scoresTbody.innerHTML = rows.map(function (c) {
        var g = gradeOf(c.score);
        return '<tr>' +
          '<td>' + esc(c.course_name) + '</td>' +
          '<td>' + esc(c.credit) + '</td>' +
          '<td>' + scoreChip(c.score) + '</td>' +
          '<td>' + (g ? esc(g) : '<span class="chip">未登记</span>') + '</td>' +
        '</tr>';
      }).join('');
    } else {
      scoresTbody.innerHTML = '<tr><td colspan="4">' +
        '<div class="empty"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg><p>暂无成绩记录</p></div>' +
        '</td></tr>';
    }
  }

  /* ---------- 选课 / 退课 ---------- */
  function doSelect() {
    var courseId = courseSelect.value;
    if (!courseId) return;
    selectBtn.disabled = true;
    api('/courses/select/' + studentId, { method: 'POST', body: { course_id: +courseId } })
      .then(function () {
        toast('选课成功');
        return loadCourses();
      })
      .catch(function (e) {
        toast(e.message, 'error');
        selectBtn.disabled = false;
      });
  }

  function doUnselect(courseId) {
    api('/courses/unselect/' + studentId, { method: 'DELETE', body: { course_id: courseId } })
      .then(function () {
        toast('退课成功');
        return loadCourses();
      })
      .catch(function (e) { toast(e.message, 'error'); });
  }

  /* ---------- 启动 ---------- */
  selectBtn.addEventListener('click', doSelect);

  loadProfile().catch(function () {
    profileState.textContent = '加载失败';
    toast('个人信息加载失败', 'error');
  });
  loadCourses().catch(function (e) { toast(e.message, 'error'); });
})();
