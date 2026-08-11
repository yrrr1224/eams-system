/* ==========================================================================
   eams 教务管理系统 · 登录页逻辑（双角色：教师 / 学生）
   流程：表单校验 → POST /auth/login（JSON）→ 按返回角色写入会话 →
         teacher 跳 /dashboard，student 跳 /static/student-home.html
   另含学生注册弹窗：POST /auth/register（仅学生可注册）
   依赖：auth.js（EamsAuth）
   ========================================================================== */
(function () {
  'use strict';

  var form = document.getElementById('loginForm');
  var userEl = document.getElementById('loginUser');
  var passEl = document.getElementById('loginPass');
  var errEl = document.getElementById('loginError');
  var btn = document.getElementById('loginBtn');

  /* 已登录则直接进入各自首页（教师→仪表盘，学生→学生主页） */
  if (EamsAuth.isLoggedIn()) {
    window.location.href = EamsAuth.roleHome();
    return;
  }

  function showError(msg) {
    errEl.textContent = msg;
    errEl.hidden = false;
  }
  function hideError() { errEl.hidden = true; }

  /* 解析后端统一 envelope：{code, msg, data}，成功 code==0 */
  function parseEnvelope(res) {
    return res.json().catch(function () {
      throw new Error('服务器响应异常，请稍后重试');
    });
  }

  /* 登录提交 */
  form.addEventListener('submit', function (e) {
    e.preventDefault();
    var username = userEl.value.trim();
    var password = passEl.value;

    if (!username) { showError('请输入用户名'); userEl.focus(); return; }
    if (!password) { showError('请输入密码'); passEl.focus(); return; }

    btn.disabled = true;
    btn.textContent = '登录中…';

    fetch('/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: username, password: password })
    }).then(parseEnvelope).then(function (env) {
      if (!env || env.code !== 0 || !env.data || !env.data.access_token) {
        throw new Error((env && env.msg) || '登录失败');
      }
      /* 写入真实会话：access_token / role / student_id / user_id */
      EamsAuth.set(env.data);
      /* 按角色跳转各自首页 */
      window.location.href = EamsAuth.roleHome();
    }).catch(function (err) {
      btn.disabled = false;
      btn.textContent = '登 录';
      showError(err && err.message ? err.message : '登录失败，请稍后重试');
      passEl.select();
    });
  });

  /* 输入时清除错误提示 */
  [userEl, passEl].forEach(function (el) {
    el.addEventListener('input', hideError);
  });

  /* ===================== 学生注册弹窗 ===================== */
  var regBtn = document.getElementById('regBtn');
  var regMask = document.getElementById('regMask');
  var regForm = document.getElementById('regForm');
  var regErr = document.getElementById('regErr');
  var regSubmit = document.getElementById('regSubmit');
  var regClose = document.getElementById('regClose');
  var regCancel = document.getElementById('regCancel');

  function regOpen() {
    regErr.hidden = true;
    regMask.classList.add('show');
    var first = document.getElementById('regUsername');
    if (first) first.focus();
  }
  function regCloseModal() {
    regMask.classList.remove('show');
  }
  function regShowErr(msg) {
    regErr.textContent = msg;
    regErr.hidden = false;
  }
  function regToast(msg) {
    var t = document.getElementById('regToast');
    t.textContent = msg;
    t.classList.add('show');
    clearTimeout(regToast._t);
    regToast._t = setTimeout(function () { t.classList.remove('show'); }, 2400);
  }

  if (regBtn && regMask) {
    regBtn.addEventListener('click', regOpen);
    regClose.addEventListener('click', regCloseModal);
    regCancel.addEventListener('click', regCloseModal);
    /* 点击遮罩空白处关闭 */
    regMask.addEventListener('click', function (e) {
      if (e.target === regMask) regCloseModal();
    });

    regForm.addEventListener('submit', function (e) {
      e.preventDefault();
      var u = document.getElementById('regUsername').value.trim();
      var p = document.getElementById('regPassword').value;
      var n = document.getElementById('regName').value.trim();
      var g = document.getElementById('regGender').value;
      var a = document.getElementById('regAge').value.trim();

      /* 前端校验与后端 VO 规则一致（后端仍会二次校验） */
      if (u.length < 3 || u.length > 20) { regShowErr('用户名需为 3-20 位'); return; }
      if (p.length < 6 || p.length > 20) { regShowErr('密码需为 6-20 位'); return; }
      if (!n) { regShowErr('请输入真实姓名'); return; }
      if (!a || isNaN(+a) || +a < 10 || +a > 100 || Math.floor(+a) !== +a) {
        regShowErr('年龄需为 10-100 的整数'); return;
      }

      regSubmit.disabled = true;
      regSubmit.textContent = '注册中…';

      fetch('/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: u, password: p, name: n, gender: g, age: +a })
      }).then(parseEnvelope).then(function (env) {
        if (!env || env.code !== 0) {
          var msg = (env && env.msg) || '注册失败';
          if (env && Array.isArray(env.data) && env.data[0] && env.data[0].msg) {
            msg = msg + '：' + env.data[0].msg;   // 422 参数校验明细
          }
          throw new Error(msg);
        }
        /* 注册成功：提示后关闭弹窗，留在登录页 */
        regCloseModal();
        regToast('注册成功，请登录');
        regForm.reset();
      }).catch(function (err) {
        regShowErr(err && err.message ? err.message : '注册失败，请稍后重试');
      }).then(function () {
        regSubmit.disabled = false;
        regSubmit.textContent = '注 册';
      });
    });
  }
})();
