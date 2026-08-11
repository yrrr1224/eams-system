/* ==========================================================================
   eams 教务管理系统 · 管理页共享逻辑（学生 / 教师 / 课程 / 班级）
   按 <body data-page="..."> 选择配置，四个页面共用同一套 CRUD / 分页 / 搜索 /
   弹窗 / toast / 确认框逻辑；学生页额外包含「分班 / 选老师 / 选课管理」。
   纯前端：只调后端 JSON API，自包含，无外部依赖。
   ========================================================================== */
(function () {
  'use strict';

  /* ---------- 工具 ---------- */
  var enc = encodeURIComponent;

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  // 由姓名/课程名稳定取一个马卡龙色，用作迷你头像底色
  var HUES = ['#59a5e8', '#3fa583', '#e2872e', '#e57ca5', '#9a82e6', '#dfaa3e'];
  function hueFor(s) {
    var n = 0, str = String(s || '');
    for (var i = 0; i < str.length; i++) n = (n * 31 + str.charCodeAt(i)) >>> 0;
    return HUES[n % HUES.length];
  }

  function today() {
    var d = new Date();
    return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
  }

  /* ---------- 内联图标 ---------- */
  var ICONS = {
    edit: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 3a2.83 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"/></svg>',
    trash: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>',
    cls: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/></svg>',
    user: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>',
    book: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>',
    check: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>',
    alert: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.3 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
    info: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>',
    empty: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-6l-2 3h-4l-2-3H2"/><path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/></svg>'
  };

  /* ---------- API 封装（统一 envelope：code==0 成功） ---------- */
  var api = {
    call: function (path, options) {
      options = options || {};
      return fetch(path, {
        method: options.method || 'GET',
        headers: options.body ? { 'Content-Type': 'application/json' } : undefined,
        body: options.body ? JSON.stringify(options.body) : undefined
      }).then(function (res) {
        return res.json().catch(function () {
          throw new Error('服务器响应异常');
        });
      }).then(function (env) {
        if (!env || env.code !== 0) {
          var msg = (env && env.msg) || '操作失败';
          if (env && Array.isArray(env.data) && env.data.length) {
            var first = env.data[0];
            if (first && first.msg) msg = msg + '：' + first.msg;
            else if (first && first.loc && first.loc.length) msg = msg + '：' + first.loc[first.loc.length - 1] + ' 不合法';
          }
          var err = new Error(msg);
          err.code = env && env.code;
          throw err;
        }
        return env.data;
      });
    },
    get: function (p) { return this.call(p); },
    post: function (p, body) { return this.call(p, { method: 'POST', body: body }); },
    put: function (p, body) { return this.call(p, { method: 'PUT', body: body }); },
    del: function (p, body) { return this.call(p, { method: 'DELETE', body: body }); }
  };

  /* ---------- Toast ---------- */
  var Toast = {
    _timer: null,
    show: function (msg, type) {
      var root = document.getElementById('toastRoot');
      if (!root) {
        root = document.createElement('div');
        root.id = 'toastRoot';
        document.body.appendChild(root);
      }
      var el = root.querySelector('.toast');
      if (!el) {
        el = document.createElement('div');
        el.className = 'toast';
        root.appendChild(el);
      }
      var icon = type === 'success' ? ICONS.check : type === 'error' ? ICONS.alert : ICONS.info;
      el.innerHTML = icon + '<span></span>';
      el.querySelector('span').textContent = msg;
      el.className = 'toast ' + (type || 'info');
      el.classList.add('show');
      clearTimeout(Toast._timer);
      Toast._timer = setTimeout(function () { el.classList.remove('show'); }, 2400);
    },
    success: function (m) { Toast.show(m, 'success'); },
    error: function (m) { Toast.show(m, 'error'); },
    info: function (m) { Toast.show(m, 'info'); }
  };

  /* ---------- 模态框 ---------- */
  var openMasks = [];

  var Modal = {
    build: function (opts) {
      var root = document.getElementById('modalRoot');
      if (!root) {
        root = document.createElement('div');
        root.id = 'modalRoot';
        document.body.appendChild(root);
      }
      var mask = document.createElement('div');
      mask.className = 'modal-mask';
      mask.innerHTML =
        '<div class="modal"' + (opts.width ? ' style="width:min(' + opts.width + 'px,100%)"' : '') + '>' +
          (opts.hideHead ? '' : '<div class="modal-head"><h3>' + esc(opts.title) + '</h3><button type="button" class="modal-close" aria-label="关闭">✕</button></div>') +
          '<div class="modal-body">' + (opts.bodyHTML || '') + '</div>' +
          (opts.footHTML ? '<div class="modal-foot">' + opts.footHTML + '</div>' : '') +
        '</div>';
      root.appendChild(mask);
      requestAnimationFrame(function () { mask.classList.add('show'); });
      openMasks.push(mask);

      var closed = false;
      var close = function () {
        if (closed) return;
        closed = true;
        var idx = openMasks.indexOf(mask);
        if (idx > -1) openMasks.splice(idx, 1);
        mask.classList.remove('show');
        setTimeout(function () { if (mask.parentNode) mask.parentNode.removeChild(mask); }, 260);
        if (opts.onClose) opts.onClose();
      };

      mask.addEventListener('click', function (e) { if (e.target === mask) close(); });
      var closeBtn = mask.querySelector('.modal-close');
      if (closeBtn) closeBtn.addEventListener('click', close);
      mask._modalClose = close; // 供 ESC 等统一走正式关闭（会触发 onClose/确认框 resolve）

      return {
        mask: mask,
        modal: mask.querySelector('.modal'),
        close: close,
        $: function (sel) { return mask.querySelector(sel); },
        $$: function (sel) { return Array.prototype.slice.call(mask.querySelectorAll(sel)); }
      };
    }
  };

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && openMasks.length) {
      // 统一走正式 close：触发 onClose（确认框 resolve(false)、清理节点）
      var m = openMasks[openMasks.length - 1];
      if (m._modalClose) m._modalClose();
    }
  });

  /* ---------- 确认框 ---------- */
  function confirmDialog(opts) {
    return new Promise(function (resolve) {
      var M = Modal.build({
        title: opts.title,
        bodyHTML:
          '<div class="confirm-icon">' + ICONS.alert + '</div>' +
          '<div class="confirm-title">' + esc(opts.title) + '</div>' +
          '<div class="confirm-text">' + esc(opts.text || '确定执行该操作吗？') + '</div>',
        footHTML:
          '<button type="button" class="btn-secondary" data-act="cancel">取消</button>' +
          '<button type="button" class="btn-primary" data-act="ok">确定</button>',
        width: 420,
        hideHead: true,
        onClose: function () { resolve(false); }
      });
      M.modal.classList.add('confirm');
      M.$('[data-act="cancel"]').addEventListener('click', function () { resolve(false); M.close(); });
      M.$('[data-act="ok"]').addEventListener('click', function () { resolve(true); M.close(); });
    });
  }

  /* ---------- 表单弹窗 ---------- */
  function fieldHTML(f) {
    var required = f.required ? '<span class="req">*</span>' : '';
    var attrs = 'id="f-' + f.name + '"';
    var control = '';
    if (f.type === 'select') {
      var opts = '<option value="">请选择</option>';
      (f.options || []).forEach(function (o) { opts += '<option value="' + String(o.value) + '">' + esc(o.label) + '</option>'; });
      control = '<select class="form-control" ' + attrs + '>' + opts + '</select>';
    } else if (f.type === 'textarea') {
      control = '<textarea class="form-control" ' + attrs + ' rows="3"></textarea>';
    } else {
      control = '<input class="form-control" ' + attrs + ' type="' + (f.type || 'text') + '"' +
        (f.placeholder ? ' placeholder="' + esc(f.placeholder) + '"' : '') +
        (f.min !== undefined ? ' min="' + f.min + '"' : '') +
        (f.max !== undefined ? ' max="' + f.max + '"' : '') + '>';
    }
    return '<div class="form-field' + (f.full ? ' full' : '') + '" data-field="' + f.name + '">' +
      '<label class="form-label" for="f-' + f.name + '">' + esc(f.label) + required + '</label>' +
      control +
      '<div class="field-err"></div>' +
    '</div>';
  }

  /**
   * 通用表单弹窗
   * fields: [{name,label,type,options,required,min,max,placeholder,full}]
   * submit(data) -> Promise<提示文案>；失败抛 Error（弹窗保留）
   */
  function openFormModal(opts) {
    var M = Modal.build({
      title: opts.title,
      bodyHTML: '<div class="form-grid">' + opts.fields.map(fieldHTML).join('') + '</div>',
      footHTML:
        '<button type="button" class="btn-secondary" data-act="cancel">取消</button>' +
        '<button type="button" class="btn-primary" data-act="ok">保存</button>',
      width: 620
    });

    // 回填默认值
    opts.fields.forEach(function (f) {
      var el = M.$('#f-' + f.name);
      if (!el) return;
      var v = opts.values ? opts.values[f.name] : undefined;
      if (v === undefined || v === null) v = f['default'];
      if (v !== undefined && v !== null) el.value = String(v);
    });

    function clearErr(el) {
      var fw = el.closest('.form-field');
      if (fw) fw.classList.remove('invalid');
    }
    M.$$('input,select,textarea').forEach(function (el) {
      el.addEventListener('input', function () { clearErr(el); });
    });

    function showErr(name, msg) {
      var fw = M.mask.querySelector('.form-field[data-field="' + name + '"]');
      if (fw) {
        fw.classList.add('invalid');
        fw.querySelector('.field-err').textContent = msg;
      }
    }

    function collect() {
      var out = {};
      for (var i = 0; i < opts.fields.length; i++) {
        var f = opts.fields[i];
        var el = M.$('#f-' + f.name);
        if (!el) continue;
        var v = el.value.trim();
        if (f.required && v === '') {
          showErr(f.name, (f.type === 'select' ? '请选择' : '请输入') + f.label);
          return null;
        }
        if (f.type === 'number' && v !== '') {
          var n = Number(v);
          if (!isFinite(n)) { showErr(f.name, '请输入有效数字'); return null; }
          if (f.min !== undefined && n < f.min) { showErr(f.name, f.label + '需 ≥ ' + f.min); return null; }
          if (f.max !== undefined && n > f.max) { showErr(f.name, f.label + '需 ≤ ' + f.max); return null; }
        }
        if (f.type === 'select') {
          var opt = (f.options || []).filter(function (o) { return String(o.value) === el.value; })[0];
          out[f.name] = el.value ? (opt ? opt.value : el.value) : null;
        } else if (f.type === 'number') {
          out[f.name] = v === '' ? null : Number(v);
        } else {
          out[f.name] = v;
        }
      }
      return out;
    }

    M.$('[data-act="cancel"]').addEventListener('click', M.close);
    M.$('[data-act="ok"]').addEventListener('click', function () {
      var data = collect();
      if (!data) return;
      var btn = M.$('[data-act="ok"]');
      btn.disabled = true;
      btn.textContent = '保存中…';
      Promise.resolve(opts.submit(data)).then(function (msg) {
        M.close();
        if (msg) Toast.success(msg);
      }).catch(function (e) {
        btn.disabled = false;
        btn.textContent = '保存';
        Toast.error(e.message || '保存失败');
      });
    });
  }

  /* ---------- 公共渲染片段 ---------- */
  var GRADES = ['高一', '高二', '高三'].map(function (g) { return { value: g, label: g }; });

  function nameCell(r, field) {
    var v = r[field || 'name'];
    if (v == null || v === '') v = '—';
    return '<span class="cell-name">' +
      '<span class="mini-avatar" style="background:' + hueFor(v) + '">' + esc(String(v)[0]) + '</span>' +
      esc(v) + '</span>';
  }

  function genderChip(g) {
    if (g === '女') return '<span class="chip" style="background:var(--pink-tint);color:#d75f8d">女</span>';
    return '<span class="chip" style="background:var(--sky-tint);color:#3a8bd6">' + esc(g || '男') + '</span>';
  }

  function classChip(cn) {
    if (!cn) return '<span style="color:var(--text-3)">未分班</span>';
    return '<span class="chip" style="background:var(--mint-tint);color:#2f8f6c">' + esc(cn) + '</span>';
  }

  function teacherOrDash(name) {
    return name ? esc(name) : '<span style="color:var(--text-3)">未安排</span>';
  }

  /* ---------- 各模块配置 ---------- */
  var CONFIG = {
    student: {
      addTitle: '新增学生',
      editTitle: '编辑学生',
      addMsg: '新增成功',
      editMsg: '修改成功',
      addDefaults: { gender: '男', grade: '高一', enrollment_date: today() },
      getList: function (kw) { return api.get('/students/all?keyword=' + enc(kw)); },
      addFields: function () {
        return Promise.all([api.get('/classes/all'), api.get('/teachers/all')]).then(function (rs) {
          return [
            { name: 'name', label: '姓名', type: 'text', required: true, placeholder: '请输入学生姓名' },
            { name: 'gender', label: '性别', type: 'select', options: [{ value: '男', label: '男' }, { value: '女', label: '女' }] },
            { name: 'age', label: '年龄', type: 'number', required: true, min: 10, max: 100, placeholder: '10-100' },
            { name: 'grade', label: '年级', type: 'select', options: GRADES },
            { name: 'class_id', label: '班级（可稍后分班）', type: 'select', options: rs[0].map(function (c) { return { value: c.id, label: c.name }; }) },
            { name: 'teacher_id', label: '负责教师（可稍后选老师）', type: 'select', options: rs[1].map(function (t) { return { value: t.id, label: t.name }; }) },
            { name: 'enrollment_date', label: '入学日期', type: 'date' }
          ];
        });
      },
      addSubmit: function (data) { return api.post('/students/add', data); },
      editFields: [
        { name: 'name', label: '姓名', type: 'text', required: true },
        { name: 'gender', label: '性别', type: 'select', options: [{ value: '男', label: '男' }, { value: '女', label: '女' }] },
        { name: 'age', label: '年龄', type: 'number', required: true, min: 10, max: 100 },
        { name: 'grade', label: '年级', type: 'select', options: GRADES }
      ],
      editValues: function (r) { return { name: r.name, gender: r.gender, age: r.age, grade: r.grade }; },
      editSubmit: function (id, data) { return api.put('/students/update/' + id, data); },
      deleteText: function (r) { return '确定删除学生「' + r.name + '」吗？其选课记录与登录账号将一并删除。'; },
      deleteApi: function (id) { return api.del('/students/del/' + id); },
      extraActions: function (row) {
        return [
          { act: 'assign-class', label: '分班', cls: 'primary', icon: ICONS.cls, onClick: function () { openAssignModal(row, 'class'); } },
          { act: 'assign-teacher', label: '选老师', cls: 'mint', icon: ICONS.user, onClick: function () { openAssignModal(row, 'teacher'); } },
          { act: 'select-course', label: '选课管理', cls: 'purple', icon: ICONS.book, onClick: function () { openSelectionModal(row); } }
        ];
      },
      columns: [
        { key: 'id', label: 'ID' },
        { key: 'name', label: '姓名', render: function (r) { return nameCell(r); } },
        { key: 'gender', label: '性别', render: function (r) { return genderChip(r.gender); } },
        { key: 'age', label: '年龄' },
        { key: 'grade', label: '年级' },
        { key: 'class_name', label: '班级', render: function (r) { return classChip(r.class_name); } },
        { key: 'teacher_name', label: '负责教师', render: function (r) { return teacherOrDash(r.teacher_name); } },
        { key: 'course_count', label: '选课', render: function (r) { return (r.course_count || 0) + ' 门'; } },
        { key: 'enrollment_date', label: '入学日期', render: function (r) { return esc(r.enrollment_date || '—'); } }
      ]
    },

    teacher: {
      addTitle: '新增教师',
      editTitle: '编辑教师',
      addMsg: '新增成功',
      editMsg: '修改成功',
      getList: function (kw) { return api.get('/teachers/all?keyword=' + enc(kw)); },
      addFields: [
        { name: 'name', label: '姓名', type: 'text', required: true, placeholder: '请输入教师姓名' },
        { name: 'gender', label: '性别', type: 'select', options: [{ value: '男', label: '男' }, { value: '女', label: '女' }] },
        { name: 'age', label: '年龄', type: 'number', required: true, min: 20, max: 70, placeholder: '20-70' },
        { name: 'subject', label: '教授科目', type: 'text', required: true, placeholder: '如：语文' },
        { name: 'phone', label: '联系电话', type: 'text', placeholder: '选填', full: true }
      ],
      addSubmit: function (data) { return api.post('/teachers/add', data); },
      editFields: [
        { name: 'name', label: '姓名', type: 'text', required: true },
        { name: 'gender', label: '性别', type: 'select', options: [{ value: '男', label: '男' }, { value: '女', label: '女' }] },
        { name: 'age', label: '年龄', type: 'number', required: true, min: 20, max: 70 },
        { name: 'subject', label: '教授科目', type: 'text', required: true },
        { name: 'phone', label: '联系电话', type: 'text', full: true }
      ],
      editValues: function (r) { return { name: r.name, gender: r.gender, age: r.age, subject: r.subject, phone: r.phone }; },
      editSubmit: function (id, data) { return api.put('/teachers/update/' + id, data); },
      deleteText: function (r) { return '确定删除教师「' + r.name + '」吗？'; },
      deleteApi: function (id) { return api.del('/teachers/del/' + id); },
      columns: [
        { key: 'id', label: 'ID' },
        { key: 'name', label: '姓名', render: function (r) { return nameCell(r); } },
        { key: 'gender', label: '性别', render: function (r) { return genderChip(r.gender); } },
        { key: 'age', label: '年龄' },
        { key: 'subject', label: '教授科目', render: function (r) { return '<span class="chip" style="background:var(--sky-tint);color:#3a8bd6">' + esc(r.subject || '—') + '</span>'; } },
        { key: 'phone', label: '联系电话', render: function (r) { return esc(r.phone || '—'); } }
      ]
    },

    course: {
      addTitle: '新增课程',
      editTitle: '编辑课程',
      addMsg: '新增成功',
      editMsg: '修改成功',
      /* 选课人数：后端 /courses/all 已自带 student_count（见 course/model.py），
         优先直接使用该字段填入「选课人数」列；个别字段缺失时，
         再用 /stats/course-selected 的 select_num 按课程名兜底映射。 */
//      getList: function (kw) {
//        return Promise.all([
//          api.get('/courses/all?keyword=' + enc(kw)),
//          api.get('/stats/course-selected').catch(function () { return []; })
//        ]).then(function (rs) {
//          var map = {};
//          (Array.isArray(rs[1]) ? rs[1] : []).forEach(function (s) { map[s.course_name] = s.select_num; });
//          return (Array.isArray(rs[0]) ? rs[0] : []).map(function (c) {
//            c.select_num = c.student_count != null ? c.student_count : (map[c.name] || 0);
//            return c;
//          });
//        });
//      },
      getList: function (kw) {
  // 后端 /courses/all 已经自带 student_count，不需要再调用stats接口
        return api.get('/courses/all?keyword=' + enc(kw)).then(function(list){
         return (Array.isArray(list) ? list : []).map(function (c) {
      // 直接把后端 student_count 赋值给渲染要用的 select_num
          c.select_num = c.student_count ?? 0;
          return c;
    });
  });
},
      addFields: function () {
        return api.get('/teachers/all').then(function (teachers) {
          return [
            { name: 'name', label: '课程名称', type: 'text', required: true, placeholder: '如：高等数学' },
            { name: 'credit', label: '学分', type: 'number', required: true, min: 1, max: 10, placeholder: '1-10' },
            { name: 'teacher_id', label: '授课教师（可稍后安排）', type: 'select', options: teachers.map(function (t) { return { value: t.id, label: t.name }; }) }
          ];
        });
      },
      addSubmit: function (data) { return api.post('/courses/add', data); },
      editFields: function () {
        return api.get('/teachers/all').then(function (teachers) {
          return [
            { name: 'name', label: '课程名称', type: 'text', required: true },
            { name: 'credit', label: '学分', type: 'number', required: true, min: 1, max: 10 },
            { name: 'teacher_id', label: '授课教师', type: 'select', options: teachers.map(function (t) { return { value: t.id, label: t.name }; }) }
          ];
        });
      },
      editValues: function (r) { return { name: r.name, credit: r.credit, teacher_id: r.teacher_id }; },
      editSubmit: function (id, data) { return api.put('/courses/update/' + id, data); },
      deleteText: function (r) { return '确定删除课程「' + r.name + '」吗？相关选课记录将一并删除。'; },
      deleteApi: function (id) { return api.del('/courses/del/' + id); },
      columns: [
        { key: 'id', label: 'ID' },
        { key: 'name', label: '课程名', render: function (r) { return nameCell(r); } },
        { key: 'credit', label: '学分', render: function (r) { return '<span class="chip" style="background:var(--cream-tint);color:#b4831d">' + (r.credit || 0) + ' 分</span>'; } },
        { key: 'teacher_name', label: '授课教师', render: function (r) { return teacherOrDash(r.teacher_name); } },
        { key: 'student_count', label: '选课人数', render: function (r) { return '<span class="chip" style="background:var(--sky-tint);color:#3a8bd6">' + (r.select_num || 0) + ' 人</span>'; } }
      ]
    },

    classes: {
      addTitle: '新增班级',
      editTitle: '编辑班级',
      addMsg: '新增成功',
      editMsg: '修改成功',
      getList: function (kw) { return api.get('/classes/all?keyword=' + enc(kw)); },
      addFields: function () {
        return api.get('/teachers/all').then(function (teachers) {
          return [
            { name: 'name', label: '班级名称', type: 'text', required: true, placeholder: '如：高一(1)班' },
            { name: 'grade', label: '年级', type: 'select', options: GRADES },
            { name: 'head_teacher_id', label: '班主任（可稍后安排）', type: 'select', options: teachers.map(function (t) { return { value: t.id, label: t.name }; }) }
          ];
        });
      },
      addSubmit: function (data) { return api.post('/classes/add', data); },
      editFields: function () {
        return api.get('/teachers/all').then(function (teachers) {
          return [
            { name: 'name', label: '班级名称', type: 'text', required: true },
            { name: 'grade', label: '年级', type: 'select', options: GRADES },
            { name: 'head_teacher_id', label: '班主任', type: 'select', options: teachers.map(function (t) { return { value: t.id, label: t.name }; }) }
          ];
        });
      },
      editValues: function (r) { return { name: r.name, grade: r.grade, head_teacher_id: r.head_teacher_id }; },
      editSubmit: function (id, data) { return api.put('/classes/update/' + id, data); },
      deleteText: function (r) { return '确定删除班级「' + r.name + '」吗？'; },
      deleteApi: function (id) { return api.del('/classes/del/' + id); },
      columns: [
        { key: 'id', label: 'ID' },
        { key: 'name', label: '班级名', render: function (r) { return nameCell(r); } },
        { key: 'grade', label: '年级', render: function (r) { return '<span class="chip" style="background:var(--purple-tint);color:#6f58cf">' + esc(r.grade || '—') + '</span>'; } },
        { key: 'head_teacher_name', label: '班主任', render: function (r) { return teacherOrDash(r.head_teacher_name); } }
      ]
    }
  };

  /* ---------- 列表状态与渲染 ---------- */
  var cfg = null;
  var state = { keyword: '', page: 1, pageSize: 8, data: [] };
  var pendingPage = 0; // 非 0 时，下次 loadList 跳转到该页（新增后定位到末页）

  function loadList() {
    var tbody = document.querySelector('#dataTable tbody');
    var cols = (cfg.columns.length + 1);
    tbody.innerHTML = '<tr class="loading-row"><td colspan="' + cols + '"><div class="spinner"></div>加载中…</td></tr>';
    cfg.getList(state.keyword).then(function (data) {
      state.data = Array.isArray(data) ? data : [];
      if (pendingPage) { state.page = pendingPage; pendingPage = 0; }
      render();
    }).catch(function (e) {
      tbody.innerHTML = '<tr class="loading-row"><td colspan="' + cols + '">' +
        '<div class="empty">' + ICONS.empty + '<div>加载失败：' + esc(e.message) + '</div></div></td></tr>';
    });
  }

  function render() {
    var table = document.querySelector('#dataTable');
    var thead = table.querySelector('thead');
    var tbody = table.querySelector('tbody');

    thead.innerHTML = '<tr>' + cfg.columns.map(function (c) {
      return '<th' + (c.className ? ' class="' + c.className + '"' : '') + '>' + esc(c.label) + '</th>';
    }).join('') + '<th class="td-right">操作</th></tr>';

    var total = state.data.length;
    var pages = Math.max(1, Math.ceil(total / state.pageSize));
    if (state.page > pages) { state.page = pages; }

    var start = (state.page - 1) * state.pageSize;
    var rows = state.data.slice(start, start + state.pageSize);

    if (!rows.length) {
      tbody.innerHTML = '<tr><td colspan="' + (cfg.columns.length + 1) + '">' +
        '<div class="empty">' + ICONS.empty + '<div>' + (state.keyword ? '没有匹配「' + esc(state.keyword) + '」的记录' : '暂无数据') + '</div></div></td></tr>';
    } else {
      tbody.innerHTML = rows.map(function (row) {
        var tds = cfg.columns.map(function (c) {
          var v = c.render ? c.render(row) : esc(row[c.key] == null ? '' : row[c.key]);
          return '<td' + (c.className ? ' class="' + c.className + '"' : '') + '>' + v + '</td>';
        }).join('');
        return '<tr data-id="' + row.id + '">' + tds + '<td class="td-right"><div class="td-actions">' + renderActions(row) + '</div></td></tr>';
      }).join('');
    }
    renderPagination();
  }

  function renderActions(row) {
    var btns = [
      '<button class="btn-mini primary" data-act="edit">' + ICONS.edit + '<span>编辑</span></button>'
    ];
    (cfg.extraActions ? cfg.extraActions(row) : []).forEach(function (a) {
      btns.push('<button class="btn-mini ' + a.cls + '" data-act="' + a.act + '">' + (a.icon || '') + '<span>' + a.label + '</span></button>');
    });
    btns.push('<button class="btn-mini danger" data-act="del">' + ICONS.trash + '<span>删除</span></button>');
    return btns.join('');
  }

  function pageRange(cur, max) {
    if (max <= 7) return Array.apply(null, { length: max }).map(function (_, i) { return i + 1; });
    var arr = [1];
    if (cur > 3) arr.push('…');
    for (var p = Math.max(2, cur - 1); p <= Math.min(max - 1, cur + 1); p++) arr.push(p);
    if (cur < max - 2) arr.push('…');
    arr.push(max);
    return arr;
  }

  function renderPagination() {
    var box = document.getElementById('pagination');
    var total = state.data.length;
    if (!total) { box.innerHTML = ''; return; }
    var pages = Math.max(1, Math.ceil(total / state.pageSize));
    var html = '<span class="pg-info">共 ' + total + ' 条 · 第 ' + state.page + '/' + pages + ' 页</span>' +
      '<button class="pg-btn" data-nav="prev"' + (state.page <= 1 ? ' disabled' : '') + '>‹</button>';
    pageRange(state.page, pages).forEach(function (p) {
      if (p === '…') {
        html += '<span class="pg-btn" style="background:transparent;border:none;color:var(--text-3);cursor:default">…</span>';
      } else {
        html += '<button class="pg-btn' + (p === state.page ? ' active' : '') + '" data-p="' + p + '">' + p + '</button>';
      }
    });
    html += '<button class="pg-btn" data-nav="next"' + (state.page >= pages ? ' disabled' : '') + '>›</button>';
    box.innerHTML = html;

    Array.prototype.forEach.call(box.querySelectorAll('button[data-p]'), function (b) {
      b.addEventListener('click', function () { state.page = Number(b.dataset.p); render(); });
    });
    var prev = box.querySelector('[data-nav="prev"]');
    var next = box.querySelector('[data-nav="next"]');
    if (prev) prev.addEventListener('click', function () { if (state.page > 1) { state.page--; render(); } });
    if (next) next.addEventListener('click', function () { if (state.page < pages) { state.page++; render(); } });
  }

  function onRowAction(e) {
    var btn = e.target.closest('button[data-act]');
    if (!btn) return;
    var tr = btn.closest('tr[data-id]');
    if (!tr) return;
    var row = null;
    for (var i = 0; i < state.data.length; i++) {
      if (String(state.data[i].id) === tr.dataset.id) { row = state.data[i]; break; }
    }
    if (!row) return;
    var act = btn.dataset.act;
    if (act === 'edit') { openEditModal(cfg, row); return; }
    if (act === 'del') { onDelete(row); return; }
    var extras = cfg.extraActions ? cfg.extraActions(row) : [];
    for (var j = 0; j < extras.length; j++) {
      if (extras[j].act === act) { extras[j].onClick(row); return; }
    }
  }

  function reload() { loadList(); }

  /* ---------- 新增 / 编辑 / 删除 ---------- */
  function openAddModal(c) {
    Promise.resolve(typeof c.addFields === 'function' ? c.addFields() : c.addFields).then(function (fields) {
      openFormModal({
        title: c.addTitle,
        fields: fields,
        values: c.addDefaults || {},
        submit: function (data) {
          return c.addSubmit(data).then(function () {
            pendingPage = Number.MAX_SAFE_INTEGER; // 跳转末页，新纪录立即可见
            reload();
            return c.addMsg;
          });
        }
      });
    }).catch(function (e) { Toast.error(e.message || '加载表单数据失败'); });
  }

  function openEditModal(c, row) {
    Promise.resolve(typeof c.editFields === 'function' ? c.editFields() : c.editFields).then(function (fields) {
      openFormModal({
        title: c.editTitle,
        fields: fields,
        values: c.editValues(row),
        submit: function (data) {
          return c.editSubmit(row.id, data).then(function () { reload(); return c.editMsg; });
        }
      });
    }).catch(function (e) { Toast.error(e.message || '加载表单数据失败'); });
  }

  function onDelete(row) {
    confirmDialog({ title: '删除确认', text: cfg.deleteText(row) }).then(function (ok) {
      if (!ok) return;
      cfg.deleteApi(row.id).then(function () {
        Toast.success('删除成功');
        reload();
      }).catch(function (e) { Toast.error(e.message || '删除失败'); });
    });
  }

  /* ---------- 学生：分班 / 选老师 ---------- */
  function openAssignModal(row, kind) {
    var isClass = kind === 'class';
    var key = isClass ? 'class_id' : 'teacher_id';
    var title = isClass ? '学生分班' : '选择负责教师';
    var label = isClass ? '目标班级' : '负责教师';
    var url = isClass ? '/classes/all' : '/teachers/all';
    api.get(url).then(function (all) {
      var cur = isClass ? row.class_id : row.teacher_id;
      var values = {};
      if (cur != null) values[key] = cur;
      openFormModal({
        title: title,
        fields: [
          { name: key, label: label, type: 'select', required: true, full: true,
            options: all.map(function (x) { return { value: x.id, label: x.name }; }) }
        ],
        values: values,
        submit: function (data) {
          var body = {};
          body[key] = data[key];
          var p = isClass
            ? api.put('/students/assign-class/' + row.id, body)
            : api.put('/students/assign-teacher/' + row.id, body);
          return p.then(function () { reload(); return isClass ? '分班成功' : '已指定负责教师'; });
        }
      });
    }).catch(function (e) { Toast.error(e.message || '加载选项失败'); });
  }

  /* ---------- 学生：选课管理弹窗 ---------- */
  function renderSelItems(courses) {
    if (!courses.length) {
      return '<div class="empty">' + ICONS.empty + '<div>该学生暂未选课，可从上方下拉框添加</div></div>';
    }
    return courses.map(function (c) {
      var hasScore = c.score !== null && c.score !== undefined && c.score !== '';
      var scoreBox = hasScore
        ? '<span class="score-val">' + Number(c.score) + '</span><button class="btn-mini primary" data-act="edit-score">改分</button>'
        : '<input class="score-input" type="number" min="0" max="100" placeholder="成绩"><button class="btn-mini primary" data-act="save-score">登记</button>';
      return '<div class="sel-item" data-cid="' + c.course_id + '">' +
        '<span class="mini-avatar" style="background:' + hueFor(c.course_name) + '">' + esc(String(c.course_name)[0]) + '</span>' +
        '<div class="sel-info">' +
          '<div class="sel-name">' + esc(c.course_name) + '</div>' +
          '<div class="sel-sub">' + esc(c.teacher_name || '未安排教师') + ' · ' + c.credit + ' 学分</div>' +
        '</div>' +
        '<div class="score-box">' + scoreBox + '</div>' +
        '<button class="btn-mini danger" data-act="unselect">退课</button>' +
      '</div>';
    }).join('');
  }

  function openSelectionModal(student) {
    var M = Modal.build({
      title: '选课管理',
      bodyHTML:
        '<div class="sel-meta">' +
          '<span class="mini-avatar" style="background:' + hueFor(student.name) + '">' + esc(String(student.name)[0]) + '</span>' +
          '<span>为 <b>' + esc(student.name) + '</b> 管理已选课程与成绩</span>' +
        '</div>' +
        '<div class="sel-add">' +
          '<select class="form-control" id="sel-course"></select>' +
          '<button type="button" class="btn-mini mint" id="sel-add-btn">＋ 选课</button>' +
        '</div>' +
        '<div class="sel-list" id="sel-list"></div>',
      footHTML: '<button type="button" class="btn-secondary" data-act="close">关闭</button>',
      width: 660
    });
    var listEl = M.$('#sel-list');
    var selEl = M.$('#sel-course');
    M.$('[data-act="close"]').addEventListener('click', M.close);

    var load = function () {
      return Promise.all([
        api.get('/courses/student/' + student.id),
        api.get('/courses/all')
      ]).then(function (rs) {
        return {
          courses: Array.isArray(rs[0]) ? rs[0] : [],
          all: Array.isArray(rs[1]) ? rs[1] : []
        };
      });
    };

    var data = null;
    var render = function () {
      var selected = {};
      data.courses.forEach(function (c) { selected[c.course_id] = true; });
      var available = data.all.filter(function (c) { return !selected[c.id]; });
      listEl.innerHTML = renderSelItems(data.courses);
      selEl.innerHTML =
        '<option value="">选择要添加的课程…</option>' +
        available.map(function (c) {
          return '<option value="' + c.id + '">' + esc(c.name) + '（' + c.credit + ' 学分' +
            (c.teacher_name ? ' · ' + esc(c.teacher_name) : '') + '）</option>';
        }).join('') +
        (available.length ? '' : '<option value="" disabled>暂无可添加的课程</option>');
    };

    var refresh = function (msg) {
      return load().then(function (d) {
        data = d;
        render();
        if (msg) Toast.success(msg);
      }).catch(function (e) { Toast.error(e.message || '操作失败'); });
    };

    refresh().then(function () {
      // 选课
      M.$('#sel-add-btn').addEventListener('click', function () {
        var cid = selEl.value;
        if (!cid) { Toast.info('请先选择课程'); return; }
        api.post('/courses/select/' + student.id, { course_id: Number(cid) })
          .then(function () { return refresh('选课成功'); })
          .catch(function (e) { Toast.error(e.message); });
      });

      // 列表内：登记成绩 / 改分 / 退课
      listEl.addEventListener('click', function (e) {
        var btn = e.target.closest('button[data-act]');
        if (!btn) return;
        var item = btn.closest('.sel-item');
        if (!item) return;
        var cid = Number(item.dataset.cid);
        var act = btn.dataset.act;

        if (act === 'save-score') {
          var input = item.querySelector('.score-input');
          var v = Number(input.value);
          if (!input.value || !isFinite(v) || v < 0 || v > 100) {
            Toast.error('成绩需在 0-100 之间');
            return;
          }
          api.put('/courses/score/' + student.id, { course_id: cid, score: v })
            .then(function () { return refresh('成绩登记成功'); })
            .catch(function (err) { Toast.error(err.message); });
        } else if (act === 'edit-score') {
          var cur = Number(item.querySelector('.score-val').textContent);
          item.querySelector('.score-box').innerHTML =
            '<input class="score-input" type="number" min="0" max="100" value="' + cur + '">' +
            '<button class="btn-mini primary" data-act="save-score">保存</button>';
        } else if (act === 'unselect') {
          confirmDialog({ title: '确认退课', text: '确定退掉这门课程吗？' }).then(function (ok) {
            if (!ok) return;
            api.del('/courses/unselect/' + student.id, { course_id: cid })
              .then(function () { return refresh('退课成功'); })
              .catch(function (err) { Toast.error(err.message); });
          });
        }
      });
    });
  }

  /* ---------- 启动 ---------- */
  function boot() {
    var page = document.body.dataset.page || 'home';
    cfg = CONFIG[page];
    if (!cfg) return; // 非管理页（如首页仪表盘）不初始化

    var addBtn = document.getElementById('addBtn');
    var searchInput = document.getElementById('searchInput');
    var searchBtn = document.getElementById('searchBtn');

    if (addBtn) addBtn.addEventListener('click', function () { openAddModal(cfg); });

    function doSearch() {
      state.keyword = (searchInput ? searchInput.value : '').trim();
      state.page = 1;
      loadList();
    }
    if (searchBtn) searchBtn.addEventListener('click', doSearch);
    if (searchInput) searchInput.addEventListener('keydown', function (e) { if (e.key === 'Enter') doSearch(); });

    var tbody = document.querySelector('#dataTable tbody');
    if (tbody) tbody.addEventListener('click', onRowAction);

    loadList();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
