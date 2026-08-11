/* ==========================================================================
   eams 教务管理系统 · 后台首页仪表盘
   模块一：欢迎区 / 统计卡片生成 / 数字滚动动画
   ========================================================================== */
(function () {
  "use strict";

  /* ---------- 内置 SVG 图标（Feather 风格线形图标，自包含，无外链） ---------- */
  var ICONS = {
    users: '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
    user: '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
    book: '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>',
    layers: '<polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/>',
    calendar: '<rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/><path d="m9 16 2 2 4-4"/>',
    userPlus: '<path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="8.5" cy="7" r="4"/><line x1="20" y1="8" x2="20" y2="14"/><line x1="23" y1="11" x2="17" y2="11"/>',
    arrowUp: '<polyline points="17 11 12 6 7 11"/><line x1="12" y1="6" x2="12" y2="18"/>'
  };

  function svgWrap(inner, cls) {
    return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="' + (cls || "") + '">' + inner + "</svg>";
  }

  /* ---------- 统计卡片数据（先用合理静态示例数据，结构与后端 /stats/total-overview 对齐） ---------- */
  var COLORS = {
    sky:    { hue: "var(--sky)",    tint: "var(--sky-tint)" },
    mint:   { hue: "var(--mint)",   tint: "var(--mint-tint)" },
    orange: { hue: "var(--orange)", tint: "var(--orange-tint)" },
    pink:   { hue: "var(--pink)",   tint: "var(--pink-tint)" },
    purple: { hue: "var(--purple)", tint: "var(--purple-tint)" },
    cream:  { hue: "var(--cream)",  tint: "var(--cream-tint)" }
  };

  var STATS = [
    { key: "student_total", icon: "users",    label: "学生总数", count: 1286, href: "/student", color: "sky",    trend: "+3.2% 较上月" },
    { key: "teacher_total", icon: "user",     label: "教师总数", count: 128,  href: "/teacher", color: "orange", trend: "+2 本月新入职" },
    { key: "course_total",  icon: "book",     label: "课程总数", count: 96,   href: "/course",  color: "mint",   trend: "+6 本学期新增" },
    { key: "class_total",   icon: "layers",   label: "班级总数", count: 42,   href: "/classes", color: "pink",   trend: "+1 本月新设班" },
    { key: "today_select",  icon: "calendar", label: "今日选课", count: 268,  href: "/course",  color: "purple", trend: "较昨日 +18" },
    { key: "today_register",icon: "userPlus", label: "今日注册", count: 46,   href: "/student", color: "cream",  trend: "较昨日 +7" }
  ];

  /* ---------- 渲染统计卡片 ---------- */
  var grid = document.getElementById("statsGrid");

  STATS.forEach(function (s, i) {
    var c = COLORS[s.color];
    var card = document.createElement("a");
    card.className = "stat-card";
    card.href = s.href;
    card.style.setProperty("--hue", c.hue);
    card.style.setProperty("--tint", c.tint);
    card.style.setProperty("--i", i);
    card.setAttribute("aria-label", s.label + "：" + s.count + "，点击进入" + s.label + "页面");

    card.innerHTML =
      '<span class="stat-icon">' + svgWrap(ICONS[s.icon]) + "</span>" +
      '<span class="stat-body">' +
        '<span class="stat-num" data-count="' + s.count + '">0</span>' +
        '<span class="stat-label">' + s.label + "</span>" +
        '<span class="stat-trend">' + svgWrap(ICONS.arrowUp, "trend-arrow") + s.trend + "</span>" +
      "</span>";

    grid.appendChild(card);
  });

  /* ---------- 数字滚动动画（与卡片进场动画错峰） ---------- */
  function animateCount(el, target, duration) {
    var start = null;
    var t0 = performance.now();
    var delay = 500; // 等卡片浮起后再滚动，节奏更舒服
    function easeOut(k) { return 1 - Math.pow(1 - k, 3); }
    function step(now) {
      if (start === null) start = now;
      var p = Math.min((now - start) / duration, 1);
      if (p < 0) { requestAnimationFrame(step); return; }
      el.textContent = Math.round(easeOut(p) * target).toLocaleString("en-US");
      if (p < 1) requestAnimationFrame(step);
    }
    setTimeout(function () { requestAnimationFrame(step); }, delay);
  }

  var nums = grid.querySelectorAll(".stat-num");
  Array.prototype.forEach.call(nums, function (el) {
    animateCount(el, parseInt(el.getAttribute("data-count"), 10), 1100);
  });

  /* ---------- 欢迎语 / 日期（按当前时间实时生成） ---------- */
  var now = new Date();
  var h = now.getHours();
  var greet = h < 6 ? "夜深了" : h < 12 ? "早上好" : h < 14 ? "中午好" : h < 18 ? "下午好" : "晚上好";

  document.getElementById("welcomeTitle").textContent = greet + "，管理员 👋";

  var week = ["日", "一", "二", "三", "四", "五", "六"];
  var dateStr =
    now.getFullYear() + "年" + (now.getMonth() + 1) + "月" + now.getDate() + "日 " +
    "星期" + week[now.getDay()];
  document.getElementById("welcomeDate").textContent = dateStr;

  /* ---------- 图表面板进场错峰（--i 序号） ---------- */
  var panels = document.querySelectorAll(".charts-grid .panel");
  Array.prototype.forEach.call(panels, function (p, i) {
    p.style.setProperty("--i", i);
  });
})();
