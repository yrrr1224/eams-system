/* ==========================================================================
   eams 教务管理系统 · 会话管理 + 全局路由守卫 + 请求令牌注入
   双角色：teacher（教师/管理员）与 student（学生）。
   会话以 localStorage 顶层键存储：access_token / role / student_id / user_id
   （后端真实鉴权：登录接口返回 JWT，写接口按角色校验；前端守卫只做界面拦截，
   不能替代后端鉴权，故所有请求统一带上 Authorization: Bearer）。
   由 login.html 与所有页面（首页/管理页/学生主页）共享。
   ========================================================================== */
(function () {
  'use strict';

  /* ---------- 会话键名（顶层 localStorage） ---------- */
  var KEY_ACCESS = 'access_token';
  var KEY_ROLE = 'role';
  var KEY_STUDENT_ID = 'student_id';
  var KEY_USER_ID = 'user_id';

  var EamsAuth = {
    LOGIN_URL: '/login',                       // 登录页（后端干净路径）
    HOME_URL: '/dashboard',                    // 教师端首页（后端干净路径）
    STUDENT_HOME_URL: '/static/student-home.html', // 学生主页（静态页，随 /static 挂载）

    /* 读取当前会话；未登录返回 null */
    get: function () {
      var token = localStorage.getItem(KEY_ACCESS);
      if (!token) return null;
      return {
        access_token: token,
        role: localStorage.getItem(KEY_ROLE) || '',
        student_id: localStorage.getItem(KEY_STUDENT_ID) || null,
        user_id: localStorage.getItem(KEY_USER_ID) || null
      };
    },

    /* 是否已登录（存在 access_token 即视为已登录） */
    isLoggedIn: function () {
      return !!localStorage.getItem(KEY_ACCESS);
    },

    /* 当前角色：'teacher' | 'student' | '' */
    getRole: function () {
      return localStorage.getItem(KEY_ROLE) || '';
    },

    /* 当前学生 id（学生端使用，teacher 返回 null） */
    getStudentId: function () {
      return localStorage.getItem(KEY_STUDENT_ID);
    },

    /* 登录成功后写入会话（写入登录接口返回的 data 字段） */
    set: function (session) {
      session = session || {};
      localStorage.setItem(KEY_ACCESS, session.access_token || '');
      localStorage.setItem(KEY_ROLE, session.role || '');
      if (session.student_id != null) localStorage.setItem(KEY_STUDENT_ID, session.student_id);
      if (session.user_id != null) localStorage.setItem(KEY_USER_ID, session.user_id);
    },

    /* 退出登录：清空全部会话字段 */
    clear: function () {
      localStorage.removeItem(KEY_ACCESS);
      localStorage.removeItem(KEY_ROLE);
      localStorage.removeItem(KEY_STUDENT_ID);
      localStorage.removeItem(KEY_USER_ID);
    },

    /* 按角色返回各自首页地址 */
    roleHome: function () {
      return EamsAuth.getRole() === 'student' ? EamsAuth.STUDENT_HOME_URL : EamsAuth.HOME_URL;
    },

    /* 跳转登录页（用 replace 替换历史记录，避免「返回」键退回受保护页） */
    toLogin: function () {
      window.location.replace(EamsAuth.LOGIN_URL);
    }
  };

  window.EamsAuth = EamsAuth;

  /* 一次性清理旧版单键会话（早期版本存的 eams_session），避免与新键并存 */
  try { localStorage.removeItem('eams_session'); } catch (e) { /* ignore */ }

  /* ---------- 全局 fetch 包装：自动注入 Authorization: Bearer ----------
     只对同源/相对路径请求加令牌；不改动业务代码（manage.js/dashboard.js 等
     调 fetch 处零改动），让后端鉴权依赖能拿到身份。 */
  var origFetch = window.fetch;
  if (typeof origFetch === 'function') {
    window.fetch = function (input, init) {
      init = init || {};
      var token = localStorage.getItem(KEY_ACCESS);
      var url = typeof input === 'string' ? input : (input && input.url) || '';
      var isSameOrigin = !/^(https?:)?\/\//i.test(url);
      if (token && url && isSameOrigin) {
        var src = init.headers || {};
        var headers = {};
        if (typeof Headers !== 'undefined' && src instanceof Headers) {
          src.forEach(function (v, k) { headers[k] = v; });
        } else if (Array.isArray(src)) {
          for (var i = 0; i < src.length; i++) headers[src[i][0]] = src[i][1];
        } else if (src && typeof src === 'object') {
          for (var k in src) {
            if (Object.prototype.hasOwnProperty.call(src, k)) headers[k] = src[k];
          }
        }
        if (!headers.Authorization && !headers.authorization) {
          headers.Authorization = 'Bearer ' + token;
        }
        init.headers = headers;
      }
      return origFetch.call(this, input, init);
    };
  }

  /* ---------- 全局路由守卫：按角色/登录态跳转 ---------- */
  var ADMIN_PAGES = ['home', 'student', 'teacher', 'course', 'classes']; // 教师端受保护页

  function guard() {
    var page = document.body ? document.body.dataset.page : '';

    /* 登录页：已登录者直接进入各自首页（避免重复登录） */
    if (page === 'login') {
      if (EamsAuth.isLoggedIn()) window.location.href = EamsAuth.roleHome();
      return;
    }

    /* 学生主页：未登录→登录页；教师误入→教师首页 */
    if (page === 'student-home') {
      if (!EamsAuth.isLoggedIn()) { EamsAuth.toLogin(); return; }
      if (EamsAuth.getRole() !== 'student') window.location.href = EamsAuth.HOME_URL;
      return;
    }

    /* 教师端受保护页：未登录→登录页；学生访问→踢回学生主页 */
    if (ADMIN_PAGES.indexOf(page) > -1) {
      if (!EamsAuth.isLoggedIn()) { EamsAuth.toLogin(); return; }
      if (EamsAuth.getRole() === 'student') window.location.href = EamsAuth.STUDENT_HOME_URL;
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', guard);
  } else {
    guard();
  }
})();
