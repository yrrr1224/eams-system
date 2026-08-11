document.addEventListener('DOMContentLoaded', function () {
"use strict";

/* ---------- 内置 SVG 图标（Feather 风格线形，自包含） ---------- */
  function icon(inner) {
    return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' + inner + "</svg>";
  }
  var ICONS = {
    grad: icon('<path d="M22 10 12 5 2 10l10 5 10-5z"/><path d="M6 12v5c0 1.66 2.69 3 6 3s6-1.34 6-3v-5"/><path d="M22 10v6"/>'),
    home: icon('<path d="M3 9.5 12 3l9 6.5"/><path d="M5 8.5V21h14V8.5"/><path d="M9 21v-6h6v6"/>'),
    student: icon('<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>'),
    teacher: icon('<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>'),
    course: icon('<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>'),
    classes: icon('<polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/>'),
    bell: icon('<path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/>'),
    logout: icon('<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/>'),
    profile: icon('<circle cx="12" cy="8" r="4"/><path d="M4 21v-1a6 6 0 0 1 12 0v1"/><path d="M4 21h16"/>'),
    medal: icon('<circle cx="12" cy="9" r="6"/><path d="m9 14-1.5 7L12 18l4.5 3L15 14"/>')
  };

  /* ---------- 当前角色（auth.js 已先加载；无会话时守卫会踢回登录页） ---------- */
  var role = (window.EamsAuth && EamsAuth.getRole()) || 'teacher';
  var isStudent = role === 'student';
  var current = document.body.dataset.page;
  if (!current) current = 'home';

  /* 教师端页面配置（href 一律指向后端干净路径页面路由）：
     学生管理是单数 /student（页面），/students 是 API 前缀，勿混用。 */
  var PAGES = {
    home:    { href: "/dashboard", label: "首页",   crumb: "数据总览" },
    student: { href: "/student",   label: "学生管理", crumb: "学生列表" },
    teacher: { href: "/teacher",   label: "教师管理", crumb: "教师列表" },
    course:  { href: "/course",    label: "课程管理", crumb: "课程列表" },
    classes: { href: "/classes",   label: "班级管理", crumb: "班级列表" }
  };
  var NAV_ORDER = ["home", "student", "teacher", "course", "classes"];

  /* ---------- 侧边栏 ---------- */
  var sidebar = document.querySelector(".sidebar");
  var topbar = document.querySelector(".topbar");

  if (sidebar) {
    var brandHtml =
      '<a class="brand" href="' + (isStudent ? '#sec-profile' : "/dashboard") + '" title="回到首页">' +
        '<span class="brand-logo">' + ICONS.grad + "</span>" +
        '<span class="brand-text"><strong class="brand-name">eams</strong>' +
        '<span class="brand-sub">教务管理系统</span></span>' +
      "</a>";

    if (isStudent) {
      /* 学生端导航：同页锚点（个人信息 / 我的选课 / 我的成绩） */
      var stNav = [
        { href: "#sec-profile", key: "profile", label: "个人信息", icon: ICONS.profile },
        { href: "#sec-courses", key: "courses", label: "我的选课", icon: ICONS.course },
        { href: "#sec-scores",  key: "scores",  label: "我的成绩", icon: ICONS.medal }
      ];
      var stHtml = stNav.map(function (item, i) {
        return '<a class="nav-item' + (i === 0 ? " active" : "") + '" href="' + item.href + '" data-sec="' + item.key + '">' +
          item.icon + "<span>" + item.label + "</span></a>";
      }).join("");
      sidebar.innerHTML = brandHtml +
        '<nav class="nav" aria-label="学生导航"><div class="nav-title">学生中心</div>' + stHtml + "</nav>" +
        '<div class="sidebar-foot"><span class="dot"></span><span>v1.0.0 · 内部系统</span></div>';

      /* 点击锚点导航时高亮当前项 */
      sidebar.querySelectorAll('.nav-item').forEach(function (a) {
        a.addEventListener('click', function () {
          sidebar.querySelectorAll('.nav-item').forEach(function (x) { x.classList.remove('active'); });
          a.classList.add('active');
        });
      });
    } else {
      /* 教师端：完整管理导航，高亮当前页 */
      var navHtml = NAV_ORDER.map(function (key) {
        var p = PAGES[key];
        var active = key === current ? " active" : "";
        var currentAttr = key === current ? ' aria-current="page"' : "";
        return '<a class="nav-item' + active + '" href="' + p.href + '" data-page="' + key + '"' + currentAttr + ">" +
          ICONS[key] + "<span>" + p.label + "</span></a>";
      }).join("");
      sidebar.innerHTML = brandHtml +
        '<nav class="nav" aria-label="主导航"><div class="nav-title">主导航</div>' + navHtml + "</nav>" +
        '<div class="sidebar-foot"><span class="dot"></span><span>v1.0.0 · 内部系统</span></div>';
    }
  }

  /* ---------- 顶栏 ---------- */
  if (topbar) {
    var crumbLabel = isStudent ? "学生端" : PAGES[current].label;
    var crumbNow = isStudent ? "个人中心" : PAGES[current].crumb;
    var userName = isStudent ? "同学" : "教师";
    var userRole = isStudent ? "学生账号" : "教师账号";
    var avatar = isStudent ? "生" : "师";

    topbar.innerHTML =
      '<div class="topbar-left">' +
        '<span class="crumb">' + crumbLabel + "</span>" +
        '<span class="crumb-sep">/</span>' +
        '<span class="crumb crumb-now">' + crumbNow + "</span>" +
      "</div>" +
      '<div class="topbar-right">' +
        '<button class="notice" id="noticeBtn" aria-label="通知">' + ICONS.bell + '<span class="notice-dot"></span></button>' +
        '<div class="admin">' +
          '<span class="admin-avatar">' + avatar + '</span>' +
          '<span class="admin-meta"><span class="admin-name" id="topUserName">' + userName + '</span><span class="admin-role">' + userRole + '</span></span>' +
        "</div>" +
        '<a class="logout" href="/login" id="logoutBtn" title="退出登录">' + ICONS.logout + "<span>退出</span></a>" +
      "</div>";

    /* 退出登录：点击清除本地会话（access_token/role/student_id/user_id），再跳登录页 */
    var logoutBtn = topbar.querySelector('#logoutBtn');
    if (logoutBtn) {
      logoutBtn.addEventListener('click', function (e) {
        e.preventDefault();                        // 阻止默认跳转，先清会话
        if (window.EamsAuth) EamsAuth.clear();     // 清空全部会话字段
        window.location.href = '/login';           // 跳转登录页
      });
    }
  }
})
