#!/usr/bin/env node
"use strict";

/**
 * Build the demo poster component source shipped with the skill.
 *
 *   node build-demo.js
 *
 * The demo uses only shapes and text, plus one generated QR code, so the example
 * carries no third-party artwork and no personal data. It exists to show the
 * component format and to give the editor something to open.
 */

const fs = require("fs");
const path = require("path");

const W = 1080;
const H = 1440;

const INK = "#0A0E1C";
const DEEP = "#121A30";
const NIGHT = "#0E1428";
const LINE = "#26324F";
const CORAL = "#FF6B4A";
const GOLD = "#F7C948";
const PAPER = "#EAF0FF";
const MUTED = "#8C9CC4";

const elements = [];
let counter = 0;

function push(element) {
  counter += 1;
  elements.push(Object.assign({ id: "e" + String(counter).padStart(2, "0"), scaleX: 1, scaleY: 1, angle: 0, opacity: 1 }, element));
  return elements[elements.length - 1];
}

function rect(label, group, x, y, w, h, fill, extra) {
  return push(Object.assign({ label: label, group: group, type: "rect", x: x, y: y, w: w, h: h, fill: fill }, extra || {}));
}

function ellipse(label, group, x, y, w, h, fill, extra) {
  return push(Object.assign({ label: label, group: group, type: "ellipse", x: x, y: y, w: w, h: h, fill: fill }, extra || {}));
}

function line(label, group, x, y, w, h, stroke, width) {
  return push({ label: label, group: group, type: "line", x: x, y: y, w: w, h: h, stroke: stroke, strokeWidth: width });
}

function arc(label, group, x, y, w, h, start, end, stroke, width) {
  return push({ label: label, group: group, type: "arc", x: x, y: y, w: w, h: h, start: start, end: end, stroke: stroke, strokeWidth: width });
}

function text(label, group, x, y, w, content, size, fill, options) {
  const settings = options || {};
  return push(Object.assign({
    label: label, group: group, type: "text", x: x, y: y, w: w,
    text: content, fontFamily: settings.font || "Microsoft YaHei",
    fontSize: size, fontWeight: settings.weight || "400",
    lineHeight: settings.lineHeight || 1.2, align: settings.align || "left",
    fill: fill, strokeWidth: 0
  }, settings.extra || {}));
}

/* --- 背景层 ------------------------------------------------------------- */
rect("底色", "01 背景", 0, 0, W, H, INK);
ellipse("夜色光晕", "01 背景", -180, -260, 1440, 1180, "#16203C");
ellipse("地面辉光", "01 背景", 120, 1080, 840, 420, "#101A33");

/* --- 月亮与环形装饰 ------------------------------------------------------ */
ellipse("月亮", "02 主视觉", 762, 128, 176, 176, GOLD);
ellipse("月面阴影", "02 主视觉", 812, 150, 150, 150, "#E0AE3B");
arc("外环", "02 主视觉", 706, 72, 288, 288, 150, 380, CORAL, 3);
arc("内环", "02 主视觉", 736, 102, 228, 228, 165, 360, LINE, 2);

/* --- 城市剪影 ------------------------------------------------------------ */
const skyline = [
  [0, 980, 150], [140, 1060, 96], [230, 920, 128], [352, 1040, 84],
  [430, 860, 150], [574, 1010, 110], [678, 940, 142], [814, 1060, 92],
  [900, 990, 180]
];
for (const entry of skyline) {
  rect("楼体 " + entry[0], "03 城市剪影", entry[0], entry[1], entry[2], H - entry[1], NIGHT);
}
const windows = [
  [30, 1030, GOLD], [80, 1090, MUTED], [170, 1110, GOLD], [268, 970, MUTED],
  [318, 1020, GOLD], [470, 910, GOLD], [516, 980, MUTED], [620, 1060, GOLD],
  [716, 990, GOLD], [860, 1040, MUTED], [950, 1050, GOLD], [1000, 1110, MUTED]
];
for (const entry of windows) {
  ellipse("窗光 " + entry[0], "03 城市剪影", entry[0], entry[1], 12, 12, entry[2]);
}

/* --- 主标题 -------------------------------------------------------------- */
text("主标题", "04 标题", 90, 372, 900, "城市夜跑", 148, PAPER, {
  weight: "700", align: "center", lineHeight: 1.05
});
text("英文副标", "04 标题", 90, 540, 900, "CITY  NIGHT  RUN", 34, GOLD, {
  weight: "700", align: "center", font: "Arial"
});
rect("标题装饰条", "04 标题", 486, 604, 108, 6, CORAL);
text("一句话主张", "04 标题", 90, 648, 900, "沿着城市的光，跑向下一个路口", 38, MUTED, {
  align: "center"
});

/* --- 信息卡 -------------------------------------------------------------- */
rect("信息卡底", "05 信息", 90, 782, 900, 330, DEEP, { radius: 34, stroke: LINE, strokeWidth: 2 });

const rows = [
  ["时间", "10 月 26 日（周日）19:00 — 21:30"],
  ["地点", "滨江体育公园 东门集合"],
  ["名额", "限 60 人，报满即止"],
  ["装备", "荧光手环 + 反光背心，现场提供"]
];
rows.forEach((row, index) => {
  const y = 838 + index * 66;
  text("标签 " + row[0], "05 信息", 134, y, 90, row[0], 26, CORAL, { weight: "700" });
  text("内容 " + row[0], "05 信息", 240, y, 600, row[1], 30, PAPER);
});

/* --- 二维码 -------------------------------------------------------------- */
push({
  id: "qr-code", label: "报名二维码", group: "06 行动入口", type: "image",
  // 148 px = 37 modules × 4 px, so the code is placed 1:1 and never resampled.
  src: "assets/城市夜跑-报名二维码.png", x: 812, y: 812, w: 148, h: 148,
  resample: "nearest"
});
text("二维码说明", "06 行动入口", 801, 968, 170, "扫码报名", 24, MUTED, { align: "center" });

/* --- 行动按钮 ------------------------------------------------------------ */
rect("报名按钮底", "06 行动入口", 90, 1152, 900, 96, CORAL, { radius: 48 });
text("报名按钮文字", "06 行动入口", 90, 1180, 900, "扫码报名 · 领取夜跑路线图", 34, "#1A0E0A", {
  weight: "700", align: "center"
});

/* --- 页脚 ---------------------------------------------------------------- */
line("页脚分隔线", "07 页脚", 90, 1296, 900, 0, LINE, 1);
text("主办信息", "07 页脚", 90, 1322, 900, "示例项目 · 素材与文案均为演示数据，不代表任何真实活动", 22, "#5C6A8C", {
  align: "center"
});

const project = {
  schemaVersion: 1,
  name: "城市夜跑",
  canvas: { width: W, height: H, background: INK },
  meta: {
    version: "v1",
    carrier: "1080 × 1440 px（3:4 社交媒体）/ 印刷放大至 600×800 mm",
    notes: "演示项目：所有文案为示例数据，二维码指向 example.com 占位地址。"
  },
  elements: elements
};

const target = path.join(__dirname, "城市夜跑-组件源稿.poster.json");
fs.writeFileSync(target, JSON.stringify(project, null, 2) + "\n", "utf8");
console.log("示例源稿已生成：" + target + "（" + elements.length + " 个组件）");

// The demo project keeps its own copy so the folder can be opened, rendered
// and delivered on its own.
const projectCopy = path.join(__dirname, "城市夜跑", "城市夜跑-组件源稿.poster.json");
fs.mkdirSync(path.dirname(projectCopy), { recursive: true });
fs.writeFileSync(projectCopy, JSON.stringify(project, null, 2) + "\n", "utf8");
console.log("示例工程源稿已同步：" + projectCopy);

