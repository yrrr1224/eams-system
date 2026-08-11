/* ==========================================================================
   eams 教务管理系统 · 后台首页仪表盘
   模块二：SVG 图表（趋势 / 班级人数 / 课程热度 / 男女占比）
   纯前端实现，无 ECharts / 无外链 CDN；数据为合理静态示例，结构对齐后端 /stats 接口
   ========================================================================== */
(function () {
  "use strict";

  var NS = "http://www.w3.org/2000/svg";

  /* ---------- 马卡龙色板（与 dashboard.css 中的六色一致） ---------- */
  var C = {
    sky: "#59a5e8", mint: "#3fa583", orange: "#e2872e", pink: "#e57ca5",
    text1: "#2c3154", text2: "#687099", text3: "#a4abc9",
    grid: "#eef0f7", surface: "#ffffff"
  };

  function S(tag, attrs, parent) {
    var e = document.createElementNS(NS, tag);
    for (var k in attrs) {
      if (attrs.hasOwnProperty(k)) e.setAttribute(k, attrs[k]);
    }
    if (parent) parent.appendChild(e);
    return e;
  }

  /* ---------- 悬浮提示层 ---------- */
  var tip = document.getElementById("chartTip");

  function showTip(html, cx, cy) {
    if (!tip) return;
    tip.innerHTML = html;
    tip.classList.remove("show");
    var w = tip.offsetWidth;
    var h = tip.offsetHeight;
    var x = cx + 16, y = cy - h - 14;
    if (x + w > window.innerWidth - 12) x = cx - w - 16;
    if (y < 12) y = cy + 18;
    tip.style.left = x + "px";
    tip.style.top = y + "px";
    tip.setAttribute("aria-hidden", "false");
    // 强制回流后开启动画
    void tip.offsetWidth;
    tip.classList.add("show");
  }
  function hideTip() {
    if (!tip) return;
    tip.classList.remove("show");
    tip.setAttribute("aria-hidden", "true");
  }

  /* ---------- 基础工具 ---------- */
  function easeOut(k) { return 1 - Math.pow(1 - k, 3); }

  function tween(dur, fn, done) {
    var start = null;
    function step(now) {
      if (start === null) start = now;
      var p = Math.min((now - start) / dur, 1);
      fn(easeOut(p));
      if (p < 1) requestAnimationFrame(step);
      else if (done) done();
    }
    requestAnimationFrame(step);
  }

  function niceScale(max, targetTicks) {
    if (max <= 0) max = 1;
    var rough = max / targetTicks;
    var mag = Math.pow(10, Math.floor(Math.log10(rough)));
    var norm = rough / mag;
    var f = norm > 5 ? 10 : norm > 2 ? 5 : norm > 1 ? 2 : 1;
    var step = f * mag;
    return { step: step, max: Math.ceil(max / step) * step };
  }

  function pad2(n) { return (n < 10 ? "0" : "") + n; }

  /* 平滑曲线：Catmull-Rom → 三次贝塞尔 */
  function smoothPath(pts) {
    if (pts.length < 2) return "";
    var d = "M" + pts[0][0] + " " + pts[0][1];
    for (var i = 0; i < pts.length - 1; i++) {
      var p0 = pts[Math.max(i - 1, 0)], p1 = pts[i], p2 = pts[i + 1], p3 = pts[Math.min(i + 2, pts.length - 1)];
      var c1x = p1[0] + (p2[0] - p0[0]) / 6, c1y = p1[1] + (p2[1] - p0[1]) / 6;
      var c2x = p2[0] - (p3[0] - p1[0]) / 6, c2y = p2[1] - (p3[1] - p1[1]) / 6;
      d += " C" + c1x + " " + c1y + "," + c2x + " " + c2y + "," + p2[0] + " " + p2[1];
    }
    return d;
  }

  /* 顶部圆角、底部直角（柱体） */
  function roundTop(x, y, w, h, r) {
    r = Math.min(r, w / 2, h);
    return "M" + x + " " + (y + h) +
      " L" + x + " " + (y + r) +
      " Q" + x + " " + y + " " + (x + r) + " " + y +
      " L" + (x + w - r) + " " + y +
      " Q" + (x + w) + " " + y + " " + (x + w) + " " + (y + r) +
      " L" + (x + w) + " " + (y + h) + " Z";
  }

  /* 右侧圆角、左侧直角（横向柱体） */
  function roundRight(x, y, w, h, r) {
    r = Math.min(r, w / 2, h);
    return "M" + x + " " + y +
      " L" + (x + w - r) + " " + y +
      " Q" + (x + w) + " " + y + " " + (x + w) + " " + (y + r) +
      " L" + (x + w) + " " + (y + h - r) +
      " Q" + (x + w) + " " + (y + h) + " " + (x + w - r) + " " + (y + h) +
      " L" + x + " " + (y + h) + " Z";
  }

  /* ---------- 静态示例数据（结构对齐后端 /stats 接口） ---------- */
  var TREND_VALUES = [28, 32, 30, 41, 52, 48, 63];
  var CLASS_DATA = [
    { name: "高一(1)班", v: 28 }, { name: "高一(2)班", v: 32 },
    { name: "高一(3)班", v: 26 }, { name: "高二(1)班", v: 38 },
    { name: "高二(2)班", v: 29 }, { name: "高三(1)班", v: 31 }
  ];
  var COURSE_DATA = [
    { name: "语文", v: 98 }, { name: "数学", v: 95 }, { name: "英语", v: 92 },
    { name: "物理", v: 64 }, { name: "化学", v: 58 }, { name: "生物", v: 47 }
  ];
  var GENDER_DATA = [
    { name: "男", v: 742, color: C.sky },
    { name: "女", v: 544, color: C.pink }
  ];

  /* 近 7 日选课日期标签（相对今天生成，保证日期鲜活） */
  function trendLabels() {
    var out = [], today = new Date();
    for (var i = 6; i >= 0; i--) {
      var d = new Date(today.getTime());
      d.setDate(today.getDate() - i);
      out.push(pad2(d.getMonth() + 1) + "-" + pad2(d.getDate()));
    }
    return out;
  }

  /* ======================================================================
     ① 近 7 日选课趋势（面积折线图 · 天蓝）
     ====================================================================== */
  function renderTrend(container) {
    container.innerHTML = "";
    var W = container.clientWidth || 520, H = container.clientHeight || 268;
    var L = 38, R = 20, T = 16, B = 26;
    var labels = trendLabels(), values = TREND_VALUES;
    var sc = niceScale(Math.max.apply(null, values), 4);
    var plotW = W - L - R, plotH = H - T - B;
    var xFor = function (i) { return L + (plotW * i) / (values.length - 1); };
    var yFor = function (v) { return T + plotH * (1 - v / sc.max); };
    var svg = S("svg", { width: W, height: H, viewBox: "0 0 " + W + " " + H }, container);

    /* 渐变填充 */
    var defs = S("defs", {}, svg);
    var grad = S("linearGradient", { id: "trendArea", x1: 0, y1: 0, x2: 0, y2: 1 }, defs);
    S("stop", { offset: "0%", "stop-color": C.sky, "stop-opacity": 0.26 }, grad);
    S("stop", { offset: "100%", "stop-color": C.sky, "stop-opacity": 0.02 }, grad);

    /* 网格 + Y 轴刻度 */
    for (var v = 0; v <= sc.max; v += sc.step) {
      var gy = yFor(v);
      S("line", { x1: L, y1: gy, x2: W - R, y2: gy, stroke: C.grid, "stroke-width": 1 }, svg);
      S("text", { x: L - 9, y: gy + 4, "text-anchor": "end", "font-size": 11, fill: C.text3 }, svg)
        .textContent = v;
    }

    /* X 轴日期 */
    labels.forEach(function (d, i) {
      S("text", { x: xFor(i), y: H - B + 18, "text-anchor": "middle", "font-size": 11, fill: C.text3 }, svg)
        .textContent = d;
    });

    var pts = values.map(function (v, i) { return [xFor(i), yFor(v)]; });
    var linePath = smoothPath(pts);

    /* 面积 + 折线 + 数据点 */
    var area = S("path", {
      d: linePath + " L" + xFor(values.length - 1) + " " + (T + plotH) +
         " L" + xFor(0) + " " + (T + plotH) + " Z",
      fill: "url(#trendArea)", stroke: "none"
    }, svg);

    var line = S("path", {
      d: linePath, fill: "none", stroke: C.sky, "stroke-width": 2.5,
      "stroke-linecap": "round", "stroke-linejoin": "round"
    }, svg);

    var dots = [];
    pts.forEach(function (p, i) {
      var c = S("circle", {
        cx: p[0], cy: p[1], r: i === pts.length - 1 ? 5 : 4,
        fill: C.sky, stroke: C.surface, "stroke-width": 2.5
      }, svg);
      c.style.opacity = 0;
      dots.push(c);
    });

    /* 末点直接标注 */
    var lp = pts[pts.length - 1];
    var endLabel = S("text", {
      x: lp[0], y: lp[1] - 12, "text-anchor": "middle",
      "font-size": 13, "font-weight": 700, fill: C.sky,
      "paint-order": "stroke", stroke: C.surface, "stroke-width": 4
    }, svg);
    endLabel.textContent = values[values.length - 1];

    /* 悬浮十字线 + 焦点 */
    var fg = S("g", { opacity: 0 }, svg);
    var vline = S("line", { y1: T, y2: T + plotH, stroke: C.sky, "stroke-width": 1, "stroke-dasharray": "3 3", opacity: 0.6 }, fg);
    var fdot = S("circle", { r: 6, fill: C.surface, stroke: C.sky, "stroke-width": 2.5 }, fg);

    var hit = S("rect", { x: L, y: T, width: plotW, height: plotH, fill: "transparent" }, svg);
    hit.addEventListener("mousemove", function (ev) {
      var rect = container.getBoundingClientRect();
      var mx = ev.clientX - rect.left;
      var i = Math.round((mx - L) / plotW * (values.length - 1));
      i = Math.max(0, Math.min(values.length - 1, i));
      var p = pts[i];
      vline.setAttribute("x1", p[0]); vline.setAttribute("x2", p[0]);
      fdot.setAttribute("cx", p[0]); fdot.setAttribute("cy", p[1]);
      fg.setAttribute("opacity", 1);
      showTip("<div class=\"tip-title\">" + labels[i] + "</div>" +
        "<div class=\"tip-val\">选课 " + values[i] + " 人次</div>", ev.clientX, ev.clientY);
    });
    hit.addEventListener("mouseleave", function () { fg.setAttribute("opacity", 0); hideTip(); });

    /* 动画：折线描边绘制 → 面积淡入 → 数据点依次浮现 */
    var len = line.getTotalLength();
    line.style.strokeDasharray = len;
    line.style.strokeDashoffset = len;
    area.style.opacity = 0;
    void line.getBoundingClientRect();
    tween(1150, function (p) { line.style.strokeDashoffset = len * (1 - p); },
      function () {
        dots.forEach(function (c, i) {
          setTimeout(function () { tween(240, function (k) { c.style.opacity = k; }); }, i * 60);
        });
      });
    tween(900, function (p) { area.style.opacity = p * 0.95; });
  }

  /* ======================================================================
     ② 各班级人数分布（柱状图 · 薄荷绿）
     ====================================================================== */
  function renderClassCount(container) {
    container.innerHTML = "";
    var W = container.clientWidth || 520, H = container.clientHeight || 268;
    var L = 38, R = 12, T = 18, B = 30;
    var data = CLASS_DATA;
    var sc = niceScale(Math.max.apply(null, data.map(function (d) { return d.v; })), 4);
    var plotW = W - L - R, plotH = H - T - B;
    var baseY = T + plotH;
    var n = data.length, band = plotW / n, bw = Math.min(band * 0.52, 26);
    var svg = S("svg", { width: W, height: H, viewBox: "0 0 " + W + " " + H }, container);

    /* 网格 + Y 轴刻度 */
    for (var v = 0; v <= sc.max; v += sc.step) {
      var gy = T + plotH * (1 - v / sc.max);
      S("line", { x1: L, y1: gy, x2: W - R, y2: gy, stroke: C.grid, "stroke-width": 1 }, svg);
      S("text", { x: L - 9, y: gy + 4, "text-anchor": "end", "font-size": 11, fill: C.text3 }, svg)
        .textContent = v;
    }

    /* 班级名（横轴） */
    data.forEach(function (d, i) {
      S("text", { x: L + band * i + band / 2, y: H - B + 18, "text-anchor": "middle", "font-size": 11, fill: C.text3 }, svg)
        .textContent = d.name;
    });

    /* 柱体（初始为 0 高，进场生长） */
    var bars = [], vlabels = [];
    data.forEach(function (d, i) {
      var x = L + band * i + (band - bw) / 2;
      var h = (d.v / sc.max) * plotH;
      var bar = S("path", { d: roundTop(x, baseY, bw, 0.001, 7), fill: C.mint }, svg);
      bars.push({ bar: bar, x: x, h: h });

      var t = S("text", {
        x: L + band * i + band / 2, y: baseY - h - 7,
        "text-anchor": "middle", "font-size": 12, "font-weight": 600, fill: C.text2
      }, svg);
      t.textContent = d.v;
      t.style.opacity = 0;
      vlabels.push(t);
    });

    /* 悬浮高亮 */
    function highlight(i, on) {
      bars.forEach(function (b, j) {
        b.bar.style.opacity = on && j !== i ? 0.4 : 1;
        b.bar.style.filter = on && j === i ? "brightness(1.06)" : "none";
      });
      vlabels.forEach(function (t, j) { t.style.opacity = on && j !== i ? 0.3 : 1; });
    }
    data.forEach(function (d, i) {
      var hit = S("rect", { x: L + band * i, y: T, width: band, height: plotH, fill: "transparent" }, svg);
      hit.addEventListener("mouseenter", function (ev) {
        highlight(i, true);
        showTip("<div class=\"tip-title\">" + d.name + "</div><div class=\"tip-val\">" + d.v + " 人</div>", ev.clientX, ev.clientY);
      });
      hit.addEventListener("mousemove", function (ev) {
        showTip("<div class=\"tip-title\">" + d.name + "</div><div class=\"tip-val\">" + d.v + " 人</div>", ev.clientX, ev.clientY);
      });
      hit.addEventListener("mouseleave", function () { highlight(i, false); hideTip(); });
    });

    /* 柱体生长动画（错峰） */
    bars.forEach(function (b, i) {
      setTimeout(function () {
        tween(680, function (p) {
          var h = b.h * p;
          b.bar.setAttribute("d", roundTop(b.x, baseY - h, bw, Math.max(h, 0.5), 7));
        }, function () { vlabels[i].style.opacity = 1; });
      }, i * 80);
    });
  }

  /* ======================================================================
     ③ 课程选课热度排行（横向条形图 · 浅橙）
     ====================================================================== */
  function renderCourseHot(container) {
    container.innerHTML = "";
    var W = container.clientWidth || 520, H = container.clientHeight || 268;
    var L = 56, R = 12, T = 12, B = 28;
    var data = COURSE_DATA;
    var sc = niceScale(Math.max.apply(null, data.map(function (d) { return d.v; })), 5);
    var plotW = W - L - R, plotH = H - T - B;
    var n = data.length, barH = 16, gap = (plotH - n * barH) / (n + 1);
    var xFor = function (v) { return L + (v / sc.max) * plotW; };
    var svg = S("svg", { width: W, height: H, viewBox: "0 0 " + W + " " + H }, container);

    /* 纵向网格 + 底部刻度 */
    for (var v = 0; v <= sc.max; v += sc.step) {
      var gx = xFor(v);
      S("line", { x1: gx, y1: T, x2: gx, y2: T + plotH, stroke: C.grid, "stroke-width": 1 }, svg);
      S("text", { x: gx, y: H - B + 18, "text-anchor": "middle", "font-size": 11, fill: C.text3 }, svg)
        .textContent = v;
    }

    /* 课程名 */
    data.forEach(function (d, i) {
      S("text", { x: L - 10, y: T + gap + i * (barH + gap) + barH / 2 + 4, "text-anchor": "end", "font-size": 12, fill: C.text2 }, svg)
        .textContent = d.name;
    });

    /* 条形（初始宽度 0） */
    var bars = [], vlabels = [];
    data.forEach(function (d, i) {
      var y = T + gap + i * (barH + gap);
      var w = (d.v / sc.max) * plotW;
      var bar = S("path", { d: roundRight(L, y, 0.001, barH, 8), fill: C.orange }, svg);
      bars.push({ bar: bar, y: y, w: w });

      var t = S("text", {
        x: L + w + 7, y: y + barH / 2 + 4,
        "text-anchor": "start", "font-size": 12, "font-weight": 600, fill: C.text2
      }, svg);
      t.textContent = d.v;
      t.style.opacity = 0;
      vlabels.push(t);
    });

    /* 悬浮高亮 */
    function highlight(i, on) {
      bars.forEach(function (b, j) {
        b.bar.style.opacity = on && j !== i ? 0.4 : 1;
        b.bar.style.filter = on && j === i ? "brightness(1.06)" : "none";
      });
      vlabels.forEach(function (t, j) { t.style.opacity = on && j !== i ? 0.3 : 1; });
    }
    data.forEach(function (d, i) {
      var y = T + gap + i * (barH + gap);
      var hit = S("rect", { x: L, y: y, width: plotW, height: barH + gap, fill: "transparent" }, svg);
      hit.addEventListener("mouseenter", function (ev) {
        highlight(i, true);
        showTip("<div class=\"tip-title\">" + d.name + "</div><div class=\"tip-val\">选课 " + d.v + " 人次</div>", ev.clientX, ev.clientY);
      });
      hit.addEventListener("mousemove", function (ev) {
        showTip("<div class=\"tip-title\">" + d.name + "</div><div class=\"tip-val\">选课 " + d.v + " 人次</div>", ev.clientX, ev.clientY);
      });
      hit.addEventListener("mouseleave", function () { highlight(i, false); hideTip(); });
    });

    /* 条形生长动画（错峰） */
    bars.forEach(function (b, i) {
      setTimeout(function () {
        tween(650, function (p) {
          var w = b.w * p;
          b.bar.setAttribute("d", roundRight(L, b.y, Math.max(w, 0.5), barH, 8));
        }, function () { vlabels[i].style.opacity = 1; });
      }, i * 70);
    });
  }

  /* ======================================================================
     ④ 在校学生性别占比（环形图 · 天蓝 / 淡粉）
     ====================================================================== */
  function renderGender(container) {
    container.innerHTML = "";
    var W = container.clientWidth || 520, H = container.clientHeight || 268;
    var LEG_H = 46;
    var svgH = Math.max(H - LEG_H, 160);
    var svg = S("svg", { width: W, height: svgH, viewBox: "0 0 " + W + " " + svgH }, container);
    var cx = W / 2, cy = svgH / 2;
    var R = Math.max(Math.min(cx, cy) - 30, 40);
    var sw = 30;
    var Ccirc = 2 * Math.PI * R;
    var data = GENDER_DATA;
    var total = data[0].v + data[1].v;

    var angles = [], a = -90;
    data.forEach(function (d) {
      var frac = d.v / total;
      angles.push({ start: a, frac: frac, mid: a + frac * 360 / 2 });
      a += frac * 360;
    });

    /* 底色轨道 */
    S("circle", { cx: cx, cy: cy, r: R, fill: "none", stroke: "#f0f1f8", "stroke-width": sw }, svg);

    /* 分段（初始隐藏，扫入） */
    var segs = [];
    data.forEach(function (d, i) {
      var seg = S("circle", {
        cx: cx, cy: cy, r: R, fill: "none", stroke: d.color, "stroke-width": sw,
        transform: "rotate(" + angles[i].start + " " + cx + " " + cy + ")",
        "stroke-dasharray": "0.001 " + Ccirc
      }, svg);
      segs.push(seg);
    });

    /* 中心数字 */
    var t1 = S("text", { x: cx, y: cy - 5, "text-anchor": "middle", "font-size": 28, "font-weight": 800, fill: C.text1 }, svg);
    t1.textContent = total.toLocaleString("en-US");
    var t2 = S("text", { x: cx, y: cy + 20, "text-anchor": "middle", "font-size": 12, fill: C.text3 }, svg);
    t2.textContent = "在校学生";

    /* 百分比直接标注（悬停判定用的坐标也基于此角标） */
    var percentTexts = [];
    angles.forEach(function (an, i) {
      var rad = an.mid * Math.PI / 180;
      var px = cx + Math.cos(rad) * (R + sw / 2 + 18);
      var py = cy + Math.sin(rad) * (R + sw / 2 + 18);
      var t = S("text", {
        x: px, y: py + 4, "text-anchor": "middle", "font-size": 13, "font-weight": 700,
        fill: C.text2, "paint-order": "stroke", stroke: "#ffffff", "stroke-width": 4
      }, svg);
      t.textContent = Math.round(an.frac * 100) + "%";
      percentTexts.push(t);
    });

    /* 图例 */
    var legend = document.createElement("div");
    legend.className = "donut-legend";
    data.forEach(function (d) {
      var item = document.createElement("span");
      item.className = "dl-item";
      item.innerHTML =
        "<span class=\"dl-swatch\" style=\"background:" + d.color + "\"></span>" +
        d.name + " <b>" + d.v.toLocaleString("en-US") + "</b><em>" +
        Math.round(d.v / total * 100) + "%</em>";
      legend.appendChild(item);
    });
    container.appendChild(legend);

    /* 悬浮：按角度判定分段 */
    function findSegment(beta) {
      var idx = -1;
      data.forEach(function (d, i) {
        var st = ((angles[i].start % 360) + 360) % 360;
        var en = st + angles[i].frac * 360;
        if (en <= 360) { if (beta >= st && beta <= en) idx = i; }
        else if (beta >= st || beta <= en - 360) idx = i;
      });
      return idx;
    }
    function resetHover() {
      segs.forEach(function (s) { s.setAttribute("stroke-width", sw); s.style.opacity = 1; });
      percentTexts.forEach(function (t) { t.style.opacity = 1; });
    }
    var hit = S("circle", { cx: cx, cy: cy, r: R + sw / 2 + 10, fill: "transparent" }, svg);
    hit.addEventListener("mousemove", function (ev) {
      var rect = container.getBoundingClientRect();
      var dx = ev.clientX - rect.left - cx, dy = ev.clientY - rect.top - cy;
      var beta = Math.atan2(dy, dx) * 180 / Math.PI;
      if (beta < 0) beta += 360;
      var i = findSegment(beta);
      if (i >= 0) {
        segs.forEach(function (s, j) {
          s.setAttribute("stroke-width", j === i ? sw + 7 : sw);
          s.style.opacity = j === i ? 1 : 0.35;
        });
        percentTexts.forEach(function (t, j) { t.style.opacity = j === i ? 1 : 0.35; });
        showTip("<div class=\"tip-title\">" + data[i].name + "生</div>" +
          "<div class=\"tip-val\">" + data[i].v + " 人</div>" +
          "<div class=\"tip-sub\">占比 " + Math.round(data[i].v / total * 100) + "%</div>", ev.clientX, ev.clientY);
      } else {
        resetHover();
      }
    });
    hit.addEventListener("mouseleave", function () { resetHover(); hideTip(); });

    /* 扫入动画 */
    segs.forEach(function (seg, i) {
      var segLen = Ccirc * angles[i].frac;
      setTimeout(function () {
        tween(950, function (p) {
          seg.setAttribute("stroke-dasharray", (segLen * p) + " " + Ccirc);
        }, function () {
          seg.setAttribute("stroke-linecap", "round");
          seg.setAttribute("stroke-dasharray", segLen + " " + (Ccirc - segLen));
        });
      }, 200 + i * 160);
    });
  }

  /* ---------- 入口 ---------- */
  function init() {
    var el;
    if ((el = document.querySelector('[data-render="trend"]'))) renderTrend(el);
    if ((el = document.querySelector('[data-render="classCount"]'))) renderClassCount(el);
    if ((el = document.querySelector('[data-render="courseHot"]'))) renderCourseHot(el);
    if ((el = document.querySelector('[data-render="gender"]'))) renderGender(el);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  /* 窗口缩放重绘（防抖） */
  var resizeTimer;
  window.addEventListener("resize", function () {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(init, 180);
  });
})();
