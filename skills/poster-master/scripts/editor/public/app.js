"use strict";

/* Poster Master editor — front end.
   Renders a component source on a canvas, edits it, and exports PNG / SVG / PSD. */

const dom = {
  poster: document.getElementById("poster"),
  stage: document.getElementById("stage"),
  stageSurface: document.getElementById("stageSurface"),
  layerList: document.getElementById("layerList"),
  layerCount: document.getElementById("layerCount"),
  layerSearch: document.getElementById("layerSearch"),
  inspector: document.getElementById("inspector"),
  inspectorType: document.getElementById("inspectorType"),
  statusText: document.getElementById("statusText"),
  statusMeta: document.getElementById("statusMeta"),
  posterName: document.getElementById("posterName"),
  posterMeta: document.getElementById("posterMeta"),
  saveState: document.getElementById("saveState"),
  saveStateText: document.getElementById("saveStateText"),
  undoBtn: document.getElementById("undoBtn"),
  redoBtn: document.getElementById("redoBtn"),
  saveBtn: document.getElementById("saveBtn"),
  previewBtn: document.getElementById("previewBtn"),
  exportBtn: document.getElementById("exportBtn"),
  exportMenu: document.getElementById("exportMenu"),
  zoomLabel: document.getElementById("zoomLabel"),
  stageHint: document.getElementById("stageHint"),
  assetInput: document.getElementById("assetInput"),
  previewOverlay: document.getElementById("previewOverlay"),
  previewCanvas: document.getElementById("previewCanvas"),
  previewStage: document.getElementById("previewStage"),
  previewCaption: document.getElementById("previewCaption"),
  previewTitle: document.getElementById("previewTitle"),
  previewCloseBtn: document.getElementById("previewCloseBtn"),
  previewBackdropBtn: document.getElementById("previewBackdropBtn"),
  langBtn: document.getElementById("langBtn")
};

const ctx = dom.poster.getContext("2d");
const measureCtx = document.createElement("canvas").getContext("2d");

const state = {
  project: null,
  file: "",
  selectedId: null,
  zoom: 1,
  dirty: false,
  collapsedGroups: new Set(),
  search: "",
  history: [],
  future: [],
  drag: null,
  lang: "zh",
  previewBackdrop: "dark",
  replaceTargetId: null,
  images: new Map()
};

const TYPE_LABEL = {
  image: "图片", rect: "矩形", ellipse: "椭圆", text: "文字", line: "线", arc: "弧"
};
const TYPE_ICON = {
  image: "▣", rect: "▭", ellipse: "◯", text: "T", line: "╱", arc: "◠"
};

const I18N = {
  zh: {
    layers: "图层", properties: "属性", save: "保存", preview: "预览", export: "导出",
    synced: "已同步", unsaved: "未保存",
    emptyTitle: "未选中组件", emptyHint: "在画布或图层列表中选择一个组件后，这里会显示可编辑属性。",
    transform: "变换", appearance: "外观", text: "文字", image: "图片", meta: "组件信息",
    x: "X 位置", y: "Y 位置", w: "宽", h: "高", angle: "旋转", opacity: "不透明度",
    scaleX: "水平缩放", scaleY: "垂直缩放",
    fill: "填充色", stroke: "描边色", strokeWidth: "描边宽度", radius: "圆角",
    content: "文字内容", fontFamily: "字体", fontSize: "字号", fontWeight: "字重",
    lineHeight: "行高", align: "对齐", alignLeft: "左对齐", alignCenter: "居中", alignRight: "右对齐",
    weightRegular: "常规", weightBold: "粗体",
    replace: "替换图片", group: "分组", id: "组件 ID", visible: "可见", source: "源文件",
    replaceHint: "上传 PNG / JPEG / WebP，文件会保存到项目的 assets 目录。",
    fitHint: "拖动移动 · 角点缩放 · 顶部圆点旋转 · 方向键微调 · Ctrl+滚轮缩放",
    saved: "组件源稿已保存", loaded: "组件源稿已加载",
    canvasSize: "画布", elements: "个组件", selected: "已选中",
    exportPng1: "已导出 PNG（1×）", exportPng2: "已导出 PNG（2×）",
    exportSvg: "已导出 SVG", exportPsd: "已导出 PSD",
    previewTitle: "预览", previewExit: "退出预览", backdrop: "背景", layerName: "名称"
  },
  en: {
    layers: "Layers", properties: "Properties", save: "Save", preview: "Preview", export: "Export",
    synced: "Synced", unsaved: "Unsaved",
    emptyTitle: "Nothing selected", emptyHint: "Select a component on the canvas or in the layer list to edit it.",
    transform: "Transform", appearance: "Appearance", text: "Text", image: "Image", meta: "Component",
    x: "X", y: "Y", w: "Width", h: "Height", angle: "Rotation", opacity: "Opacity",
    scaleX: "Scale X", scaleY: "Scale Y",
    fill: "Fill", stroke: "Stroke", strokeWidth: "Stroke width", radius: "Corner radius",
    content: "Content", fontFamily: "Font", fontSize: "Size", fontWeight: "Weight",
    lineHeight: "Line height", align: "Align", alignLeft: "Left", alignCenter: "Center", alignRight: "Right",
    weightRegular: "Regular", weightBold: "Bold",
    replace: "Replace image", group: "Group", id: "Component ID", visible: "Visible", source: "Source file",
    replaceHint: "Upload PNG / JPEG / WebP. The file is stored in the project assets folder.",
    fitHint: "Drag to move · corner to scale · top dot to rotate · arrow keys to nudge · Ctrl+wheel to zoom",
    saved: "Component source saved", loaded: "Component source loaded",
    canvasSize: "Canvas", elements: "components", selected: "selected",
    exportPng1: "PNG exported (1x)", exportPng2: "PNG exported (2x)",
    exportSvg: "SVG exported", exportPsd: "PSD exported",
    previewTitle: "Preview", previewExit: "Exit preview", backdrop: "Backdrop", layerName: "Name"
  }
};

function t(key) {
  const dict = I18N[state.lang] || I18N.zh;
  return dict[key] !== undefined ? dict[key] : key;
}

function el(tag, className, textContent) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (textContent !== undefined) node.textContent = textContent;
  return node;
}

function setStatus(message, kind) {
  dom.statusText.textContent = message || "";
  dom.statusText.className = kind || "";
}

function selected() {
  if (!state.project || !state.selectedId) return null;
  return state.project.elements.find(item => item.id === state.selectedId) || null;
}

function groupOf(item) {
  return item.group || item.psdGroup || "";
}

/** Legacy sources anchored text by its centre; new sources use a top-left box. */
function isLegacy(item) {
  return Boolean(item && item.psdGroup && !item.group);
}

function fontSpec(item) {
  return (item.fontWeight || "400") + " " + (item.fontSize || 24) + "px " + (item.fontFamily || "sans-serif");
}

function textLayout(item) {
  const lines = String(item.text === undefined ? "" : item.text).split("\n");
  const fontSize = item.fontSize || 24;
  const lineHeight = fontSize * (item.lineHeight || 1.2);
  measureCtx.font = fontSpec(item);
  let width = 0;
  for (const line of lines) width = Math.max(width, measureCtx.measureText(line).width);
  const height = lines.length * lineHeight;
  let bx;
  let by;
  if (isLegacy(item)) {
    bx = item.align === "center" ? item.x - width / 2 : item.align === "right" ? item.x - width : item.x;
    by = item.y - height / 2;
  } else {
    bx = item.x;
    by = item.y;
  }
  return { lines: lines, width: width, height: height, lineHeight: lineHeight, bx: bx, by: by, fontSize: fontSize };
}

function itemBox(item) {
  if (item.type === "text") {
    const layout = textLayout(item);
    return { x: layout.bx, y: layout.by, w: layout.width, h: layout.height, layout: layout };
  }
  return { x: item.x || 0, y: item.y || 0, w: item.w || 0, h: item.h || 0 };
}

function centerOf(item) {
  const box = itemBox(item);
  return { x: box.x + box.w / 2, y: box.y + box.h / 2 };
}

function rotatePoint(point, degrees) {
  const rad = degrees * Math.PI / 180;
  const cos = Math.cos(rad);
  const sin = Math.sin(rad);
  return { x: point.x * cos - point.y * sin, y: point.x * sin + point.y * cos };
}

function localToCanvas(item, local) {
  const box = itemBox(item);
  const center = { x: box.x + box.w / 2, y: box.y + box.h / 2 };
  const scaled = { x: (local.x - box.w / 2) * (item.scaleX || 1), y: (local.y - box.h / 2) * (item.scaleY || 1) };
  const rotated = rotatePoint(scaled, item.angle || 0);
  return { x: center.x + rotated.x, y: center.y + rotated.y };
}

function canvasToLocal(item, point) {
  const box = itemBox(item);
  const center = { x: box.x + box.w / 2, y: box.y + box.h / 2 };
  const delta = rotatePoint({ x: point.x - center.x, y: point.y - center.y }, -(item.angle || 0));
  return {
    x: delta.x / (item.scaleX || 1) + box.w / 2,
    y: delta.y / (item.scaleY || 1) + box.h / 2
  };
}

/* ------------------------------------------------------------- rendering */

function drawShape(target, item, box) {
  if (item.type === "rect") {
    const radius = Math.min(item.radius || 0, box.w / 2, box.h / 2);
    target.beginPath();
    if (radius > 0 && target.roundRect) target.roundRect(0, 0, box.w, box.h, radius);
    else target.rect(0, 0, box.w, box.h);
    if (item.fill && item.fill !== "none") {
      target.fillStyle = item.fill;
      target.fill();
    }
    if (item.strokeWidth) {
      target.lineWidth = item.strokeWidth;
      target.strokeStyle = item.stroke || "#000";
      target.stroke();
    }
  }
  if (item.type === "ellipse") {
    target.beginPath();
    target.ellipse(box.w / 2, box.h / 2, box.w / 2, box.h / 2, 0, 0, Math.PI * 2);
    if (item.fill && item.fill !== "none") {
      target.fillStyle = item.fill;
      target.fill();
    }
    if (item.strokeWidth) {
      target.lineWidth = item.strokeWidth;
      target.strokeStyle = item.stroke || "#000";
      target.stroke();
    }
  }
  if (item.type === "line") {
    target.beginPath();
    target.moveTo(0, 0);
    target.lineTo(box.w, box.h);
    target.strokeStyle = item.stroke || "#000";
    target.lineWidth = item.strokeWidth || 1;
    target.lineCap = "round";
    target.stroke();
  }
  if (item.type === "arc") {
    const start = (item.start || 0) * Math.PI / 180;
    let end = (item.end === undefined ? 360 : item.end) * Math.PI / 180;
    while (end <= start) end += Math.PI * 2;
    target.beginPath();
    target.ellipse(box.w / 2, box.h / 2, box.w / 2, box.h / 2, 0, start, end);
    target.strokeStyle = item.stroke || "#000";
    target.lineWidth = item.strokeWidth || 1;
    target.lineCap = "round";
    target.stroke();
  }
  if (item.type === "image") {
    const image = state.images.get(item.src);
    if (image && image.complete && image.naturalWidth) {
      // A QR code must not be smoothed. Elements marked "resample": "nearest"
      // are scaled with hard pixels so the modules stay readable.
      const nearest = String(item.resample || "").toLowerCase() === "nearest";
      if (nearest) target.imageSmoothingEnabled = false;
      target.drawImage(image, 0, 0, box.w, box.h);
      if (nearest) target.imageSmoothingEnabled = true;
    } else {
      target.fillStyle = "rgba(91,156,255,0.08)";
      target.fillRect(0, 0, box.w, box.h);
      target.strokeStyle = "rgba(91,156,255,0.5)";
      target.setLineDash([8, 6]);
      target.strokeRect(1, 1, box.w - 2, box.h - 2);
      target.setLineDash([]);
    }
  }
  if (item.type === "text") {
    const layout = box.layout || textLayout(item);
    const align = item.align || "left";
    const textX = align === "center" ? box.w / 2 : align === "right" ? box.w : 0;
    target.textAlign = align === "center" ? "center" : align === "right" ? "right" : "left";
    target.textBaseline = "alphabetic";
    target.font = fontSpec(item);
    target.lineJoin = "round";
    layout.lines.forEach((line, index) => {
      const baseline = layout.fontSize * 0.8 + index * layout.lineHeight;
      if (item.strokeWidth) {
        target.lineWidth = item.strokeWidth;
        target.strokeStyle = item.stroke || "#000";
        target.strokeText(line, textX, baseline);
      }
      target.fillStyle = item.fill || "#000";
      target.fillText(line, textX, baseline);
    });
  }
}

function drawOnContext(target, item) {
  if (item.visible === false) return;
  const box = itemBox(item);
  const center = { x: box.x + box.w / 2, y: box.y + box.h / 2 };
  target.save();
  target.globalAlpha = item.opacity === undefined ? 1 : item.opacity;
  target.translate(center.x, center.y);
  if (item.angle) target.rotate(item.angle * Math.PI / 180);
  if (item.scaleX !== 1 || item.scaleY !== 1) target.scale(item.scaleX || 1, item.scaleY || 1);
  target.translate(-box.w / 2, -box.h / 2);
  drawShape(target, item, box);
  target.restore();
}

function visibleElements() {
  return state.project.elements.filter(item => item.visible !== false);
}

function render() {
  if (!state.project) return;
  const canvas = state.project.canvas;
  ctx.clearRect(0, 0, dom.poster.width, dom.poster.height);
  ctx.fillStyle = canvas.background || "#ffffff";
  ctx.fillRect(0, 0, dom.poster.width, dom.poster.height);
  for (const item of visibleElements()) drawOnContext(ctx, item);
  const item = selected();
  if (item) drawSelection(item);
}

const HANDLE_SIZE = 7;

function handleLocal(item, id) {
  const box = itemBox(item);
  const map = {
    nw: { x: 0, y: 0 }, n: { x: box.w / 2, y: 0 }, ne: { x: box.w, y: 0 },
    w: { x: 0, y: box.h / 2 }, e: { x: box.w, y: box.h / 2 },
    sw: { x: 0, y: box.h }, s: { x: box.w / 2, y: box.h }, se: { x: box.w, y: box.h }
  };
  return map[id];
}

function handlePositions(item) {
  const box = itemBox(item);
  return ["nw", "n", "ne", "w", "e", "sw", "s", "se"].map(id => ({
    id: id,
    local: handleLocal(item, id),
    canvas: localToCanvas(item, handleLocal(item, id))
  }));
}

function drawSelection(item) {
  const box = itemBox(item);
  const top = localToCanvas(item, { x: box.w / 2, y: -34 / state.zoom });
  const size = HANDLE_SIZE / state.zoom;

  ctx.save();
  ctx.save();
  const center = { x: box.x + box.w / 2, y: box.y + box.h / 2 };
  ctx.translate(center.x, center.y);
  if (item.angle) ctx.rotate(item.angle * Math.PI / 180);
  if (item.scaleX !== 1 || item.scaleY !== 1) ctx.scale(item.scaleX || 1, item.scaleY || 1);
  ctx.translate(-box.w / 2, -box.h / 2);
  ctx.setLineDash([6 / state.zoom, 4 / state.zoom]);
  ctx.strokeStyle = "#3d8bff";
  ctx.lineWidth = 1.5 / state.zoom;
  ctx.strokeRect(0, 0, box.w, box.h);
  ctx.restore();

  ctx.setLineDash([]);
  for (const handle of handlePositions(item)) {
    ctx.beginPath();
    ctx.rect(handle.canvas.x - size / 2, handle.canvas.y - size / 2, size, size);
    ctx.fillStyle = "#ffffff";
    ctx.fill();
    ctx.strokeStyle = "#3d8bff";
    ctx.lineWidth = 1.5 / state.zoom;
    ctx.stroke();
  }
  ctx.beginPath();
  ctx.moveTo(top.x, top.y + 10 / state.zoom);
  ctx.lineTo(top.x, top.y);
  ctx.strokeStyle = "#3d8bff";
  ctx.lineWidth = 1.5 / state.zoom;
  ctx.stroke();
  ctx.beginPath();
  ctx.arc(top.x, top.y, size / 1.6, 0, Math.PI * 2);
  ctx.fillStyle = "#ffffff";
  ctx.fill();
  ctx.stroke();
  ctx.restore();
}

/* ---------------------------------------------------------------- panels */

function renderLayers() {
  dom.layerList.innerHTML = "";
  if (!state.project) return;
  const keyword = state.search.trim().toLowerCase();
  const groups = new Map();
  for (const item of state.project.elements.slice().reverse()) {
    if (keyword && !String(item.label || item.id).toLowerCase().includes(keyword)) continue;
    const key = groupOf(item) || "_";
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(item);
  }
  dom.layerCount.textContent = state.project.elements.length;

  for (const [name, items] of groups) {
    const section = el("div", "layer-group");
    if (state.collapsedGroups.has(name)) section.classList.add("collapsed");
    const head = el("div", "layer-group-head");
    head.append(el("span", "twisty", "▾"), el("span", "", name === "_" ? t("layers") : name));
    head.addEventListener("click", () => {
      if (state.collapsedGroups.has(name)) state.collapsedGroups.delete(name);
      else state.collapsedGroups.add(name);
      renderLayers();
    });
    section.append(head);

    const list = el("div", "layer-items");
    for (const item of items) {
      const row = el("button", "layer" + (item.id === state.selectedId ? " active" : "") + (item.visible === false ? " hidden" : ""));
      row.title = item.label || item.id;
      const flag = el("span", "layer-flag" + (item.visible === false ? "" : " on"), item.visible === false ? "◌" : "◉");
      flag.title = t("visible");
      flag.addEventListener("click", event => {
        event.stopPropagation();
        pushHistory();
        item.visible = item.visible === false;
        markDirty();
        render();
        renderLayers();
      });
      row.append(el("span", "type-icon", TYPE_ICON[item.type] || "•"), el("span", "layer-name", item.label || item.id), flag);
      row.addEventListener("click", () => select(item.id));
      list.append(row);
    }
    section.append(list);
    dom.layerList.append(section);
  }

  if (!dom.layerList.children.length) {
    dom.layerList.append(el("div", "inspector-empty", keyword ? "没有匹配的组件" : "没有组件"));
  }
}

function numberField(label, key, value, options) {
  const settings = options || {};
  const wrap = el("div", "field");
  wrap.append(el("label", "", label));
  const input = el("input");
  input.type = "number";
  input.value = value === undefined || value === null ? "" : value;
  if (settings.step !== undefined) input.step = settings.step;
  if (settings.min !== undefined) input.min = settings.min;
  if (settings.max !== undefined) input.max = settings.max;
  input.addEventListener("change", () => {
    const item = selected();
    if (!item) return;
    const parsed = Number(input.value);
    if (!Number.isFinite(parsed)) return;
    pushHistory();
    item[key] = settings.integer ? Math.round(parsed) : parsed;
    markDirty();
    render();
  });
  wrap.append(input);
  return wrap;
}

function textField(label, key, value, options) {
  const settings = options || {};
  const wrap = el("div", "field");
  if (label) wrap.append(el("label", "", label));
  let input;
  if (settings.multiline) {
    input = el("textarea");
    input.value = value === undefined || value === null ? "" : value;
  } else {
    input = el("input");
    input.type = "text";
    input.value = value === undefined || value === null ? "" : value;
  }
  input.addEventListener("input", () => {
    const item = selected();
    if (!item) return;
    item[key] = input.value;
    markDirty();
    render();
    if (settings.relayout) renderInspector();
  });
  input.addEventListener("change", () => pushHistory());
  wrap.append(input);
  return wrap;
}

function normalizeHex(value) {
  const text = String(value || "").trim();
  if (/^#[0-9a-f]{6}$/i.test(text)) return text;
  if (/^#[0-9a-f]{3}$/i.test(text)) return "#" + text.slice(1).split("").map(char => char + char).join("");
  return "#000000";
}

function colorField(label, key, value) {
  const wrap = el("div", "field");
  wrap.append(el("label", "", label));
  const row = el("div", "swatch-row");
  const swatch = el("span", "swatch");
  const picker = el("input");
  picker.type = "color";
  picker.value = normalizeHex(value || "#000000");
  picker.addEventListener("input", () => {
    const item = selected();
    if (!item) return;
    item[key] = picker.value;
    markDirty();
    render();
  });
  picker.addEventListener("change", () => pushHistory());
  swatch.append(picker);
  const hex = el("input");
  hex.type = "text";
  hex.value = value || "";
  hex.addEventListener("change", () => {
    const item = selected();
    if (!item) return;
    pushHistory();
    item[key] = hex.value.trim();
    markDirty();
    render();
    renderInspector();
  });
  row.append(swatch, hex);
  wrap.append(row);
  return wrap;
}

function segmented(label, key, value, options) {
  const wrap = el("div", "field");
  wrap.append(el("label", "", label));
  const seg = el("div", "seg");
  for (const option of options) {
    const button = el("button", value === option.value ? "on" : "", option.label);
    button.addEventListener("click", () => {
      const item = selected();
      if (!item) return;
      pushHistory();
      item[key] = option.value;
      markDirty();
      render();
      renderInspector();
    });
    seg.append(button);
  }
  wrap.append(seg);
  return wrap;
}

function section(titleKey, build, open) {
  const node = el("div", "section");
  const head = el("button", "section-head");
  head.append(el("span", "", t(titleKey)), el("span", "twisty", "▾"));
  const body = el("div", "section-body");
  head.addEventListener("click", () => node.classList.toggle("collapsed"));
  if (open === false) node.classList.add("collapsed");
  build(body);
  node.append(head, body);
  return node;
}

function renderInspector() {
  dom.inspector.innerHTML = "";
  const item = selected();
  if (!item) {
    dom.inspectorType.textContent = "";
    const empty = el("div", "inspector-empty");
    empty.append(el("strong", "", t("emptyTitle")), document.createTextNode(t("emptyHint")));
    dom.inspector.append(empty);
    return;
  }
  dom.inspectorType.textContent = TYPE_LABEL[item.type] || item.type;

  dom.inspector.append(section("transform", body => {
    const grid = el("div", "grid-two");
    grid.append(numberField(t("x"), "x", Math.round(item.x || 0), { integer: true }), numberField(t("y"), "y", Math.round(item.y || 0), { integer: true }));
    body.append(grid);
    const grid2 = el("div", "grid-two");
    grid2.append(numberField(t("w"), "w", Math.round(item.w || 0), { integer: true }), numberField(t("h"), "h", Math.round(item.h || 0), { integer: true }));
    body.append(grid2);
    const grid3 = el("div", "grid-two");
    grid3.append(numberField(t("angle"), "angle", item.angle || 0, { step: 1 }), numberField(t("opacity"), "opacity", item.opacity === undefined ? 1 : item.opacity, { step: 0.05, min: 0, max: 1 }));
    body.append(grid3);
    const grid4 = el("div", "grid-two");
    grid4.append(numberField(t("scaleX"), "scaleX", item.scaleX === undefined ? 1 : item.scaleX, { step: 0.05 }), numberField(t("scaleY"), "scaleY", item.scaleY === undefined ? 1 : item.scaleY, { step: 0.05 }));
    body.append(grid4);
  }));

  if (item.type === "text") {
    dom.inspector.append(section("text", body => {
      body.append(textField(t("content"), "text", item.text, { multiline: true }));
      const grid = el("div", "grid-two");
      grid.append(textField(t("fontFamily"), "fontFamily", item.fontFamily || "Microsoft YaHei"), numberField(t("fontSize"), "fontSize", item.fontSize || 24, { integer: true, min: 1 }));
      body.append(grid);
      const grid2 = el("div", "grid-two");
      grid2.append(segmented(t("fontWeight"), "fontWeight", item.fontWeight || "400", [
        { value: "400", label: t("weightRegular") },
        { value: "700", label: t("weightBold") }
      ]), numberField(t("lineHeight"), "lineHeight", item.lineHeight || 1.2, { step: 0.05 }));
      body.append(grid2);
      body.append(segmented(t("align"), "align", item.align || "left", [
        { value: "left", label: t("alignLeft") },
        { value: "center", label: t("alignCenter") },
        { value: "right", label: t("alignRight") }
      ]));
    }));
  }

  if (item.type !== "image") {
    dom.inspector.append(section("appearance", body => {
      body.append(colorField(t("fill"), "fill", item.fill || "#000000"));
      if (item.type !== "text") body.append(colorField(t("stroke"), "stroke", item.stroke || "#000000"));
      const grid = el("div", "grid-two");
      grid.append(numberField(t("strokeWidth"), "strokeWidth", item.strokeWidth || 0, { step: 0.5, min: 0 }));
      if (item.type === "rect") grid.append(numberField(t("radius"), "radius", item.radius || 0, { integer: true, min: 0 }));
      body.append(grid);
      if (item.type === "arc") {
        const grid2 = el("div", "grid-two");
        grid2.append(numberField("起始角度", "start", item.start || 0, { integer: true }), numberField("结束角度", "end", item.end === undefined ? 360 : item.end, { integer: true }));
        body.append(grid2);
      }
    }));
  }

  if (item.type === "image") {
    dom.inspector.append(section("image", body => {
      const row = el("div", "btn-row");
      const button = el("button", "btn", t("replace"));
      button.addEventListener("click", () => {
        state.replaceTargetId = item.id;
        dom.assetInput.value = "";
        dom.assetInput.click();
      });
      row.append(button);
      body.append(row);
      body.append(el("p", "muted", t("replaceHint")));
      body.append(textField(t("source"), "src", item.src || ""));
    }));
  }

  dom.inspector.append(section("meta", body => {
    const lines = [[t("id"), item.id], [t("group"), groupOf(item) || "—"], [t("visible"), item.visible === false ? "否" : "是"]];
    for (const entry of lines) {
      const row = el("div", "meta-line");
      row.append(el("span", "", entry[0]), el("span", "", entry[1]));
      body.append(row);
    }
    body.append(textField(t("layerName"), "label", item.label || ""));
  }, false));
}

/* --------------------------------------------------------------- history */

function select(id) {
  state.selectedId = id;
  render();
  renderLayers();
  renderInspector();
  updateMeta();
}

function updateMeta() {
  if (!state.project) return;
  const canvas = state.project.canvas;
  const parts = [t("canvasSize") + " " + canvas.width + " × " + canvas.height, state.project.elements.length + " " + t("elements")];
  const item = selected();
  if (item) parts.push(t("selected") + ": " + (item.label || item.id));
  dom.statusMeta.textContent = parts.join("  ·  ");
}

function markDirty() {
  state.dirty = true;
  dom.saveState.classList.add("dirty");
  dom.saveStateText.textContent = t("unsaved");
  updateMeta();
}

function markClean() {
  state.dirty = false;
  dom.saveState.classList.remove("dirty");
  dom.saveStateText.textContent = t("synced");
}

function snapshot() {
  return JSON.stringify(state.project);
}

function pushHistory() {
  if (!state.project) return;
  state.history.push(snapshot());
  if (state.history.length > 80) state.history.shift();
  state.future.length = 0;
  updateHistoryButtons();
}

function updateHistoryButtons() {
  dom.undoBtn.disabled = state.history.length === 0;
  dom.redoBtn.disabled = state.future.length === 0;
}

function restore(text) {
  state.project = JSON.parse(text);
  if (!state.project.elements.some(item => item.id === state.selectedId)) state.selectedId = null;
  render();
  renderLayers();
  renderInspector();
  updateMeta();
}

function undo() {
  if (!state.history.length) return;
  state.future.push(snapshot());
  restore(state.history.pop());
  markDirty();
  updateHistoryButtons();
}

function redo() {
  if (!state.future.length) return;
  state.history.push(snapshot());
  restore(state.future.pop());
  markDirty();
  updateHistoryButtons();
}

/* ------------------------------------------------------------------- io */

async function api(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.error || "操作失败");
  return body;
}

async function save() {
  dom.saveBtn.disabled = true;
  setStatus("正在保存…");
  try {
    const result = await api("/api/save", { project: state.project });
    markClean();
    setStatus(result.message || t("saved"), "ok");
  } catch (error) {
    setStatus("保存失败：" + error.message, "err");
  } finally {
    dom.saveBtn.disabled = false;
  }
}

function setZoom(value) {
  const canvas = state.project ? state.project.canvas : { width: 1024, height: 1536 };
  state.zoom = Math.max(0.05, Math.min(8, value));
  dom.poster.style.width = Math.round(canvas.width * state.zoom) + "px";
  dom.poster.style.height = Math.round(canvas.height * state.zoom) + "px";
  dom.zoomLabel.textContent = Math.round(state.zoom * 100) + "%";
  render();
}

function fitToStage() {
  if (!state.project) return;
  const canvas = state.project.canvas;
  const available = {
    width: dom.stageSurface.clientWidth - 80,
    height: dom.stageSurface.clientHeight - 80
  };
  const scale = Math.min(available.width / canvas.width, available.height / canvas.height, 1.5);
  setZoom(scale);
}

function eventPoint(event) {
  const rect = dom.poster.getBoundingClientRect();
  return {
    x: (event.clientX - rect.left) * state.project.canvas.width / rect.width,
    y: (event.clientY - rect.top) * state.project.canvas.height / rect.height
  };
}

function hitTest(point) {
  for (const item of state.project.elements.slice().reverse()) {
    if (item.visible === false || item.locked) continue;
    const local = canvasToLocal(item, point);
    const box = itemBox(item);
    if (local.x >= -6 && local.x <= box.w + 6 && local.y >= -6 && local.y <= box.h + 6) return item;
  }
  return null;
}

function handleAt(item, point) {
  if (!item) return null;
  const tolerance = 9 / state.zoom;
  for (const handle of handlePositions(item)) {
    if (Math.abs(point.x - handle.canvas.x) <= tolerance && Math.abs(point.y - handle.canvas.y) <= tolerance) return handle;
  }
  const box = itemBox(item);
  const top = localToCanvas(item, { x: box.w / 2, y: -34 / state.zoom });
  if (Math.hypot(point.x - top.x, point.y - top.y) <= tolerance) return { id: "rotate" };
  return null;
}

function oppositeHandle(id) {
  const map = { nw: "se", se: "nw", ne: "sw", sw: "ne", n: "s", s: "n", e: "w", w: "e" };
  return map[id];
}

function resizeElement(item, handleId, pointer) {
  const box = itemBox(item);
  const anchorLocal = handleLocal(item, oppositeHandle(handleId));
  const anchorScreen = localToCanvas(item, anchorLocal);
  const delta = rotatePoint({ x: pointer.x - anchorScreen.x, y: pointer.y - anchorScreen.y }, -(item.angle || 0));

  const horizontal = handleId !== "n" && handleId !== "s";
  const vertical = handleId !== "e" && handleId !== "w";
  const newW = horizontal ? Math.max(1, Math.abs(delta.x)) : box.w;
  const newH = vertical ? Math.max(1, Math.abs(delta.y)) : box.h;

  if (item.type === "text") {
    const ratio = box.w > 0 ? newW / box.w : 1;
    pushHistory();
    item.fontSize = Math.max(4, Math.round((item.fontSize || 24) * ratio));
    markDirty();
    render();
    renderInspector();
    return;
  }

  const anchorRel = {
    x: box.w > 0 ? (anchorLocal.x / box.w) * 2 - 1 : -1,
    y: box.h > 0 ? (anchorLocal.y / box.h) * 2 - 1 : -1
  };
  const anchorStandard = { x: anchorRel.x < 0 ? 0 : newW, y: anchorRel.y < 0 ? 0 : newH };
  const offset = rotatePoint({ x: anchorStandard.x - newW / 2, y: anchorStandard.y - newH / 2 }, item.angle || 0);
  const center = { x: anchorScreen.x - offset.x, y: anchorScreen.y - offset.y };

  pushHistory();
  item.w = Math.round(newW);
  item.h = Math.round(newH);
  item.x = Math.round(center.x - newW / 2);
  item.y = Math.round(center.y - newH / 2);
  markDirty();
  render();
  renderInspector();
}

function duplicateSelected() {
  const item = selected();
  if (!item) return;
  pushHistory();
  const copy = JSON.parse(JSON.stringify(item));
  copy.id = item.id + "-copy-" + Math.random().toString(36).slice(2, 6);
  copy.label = (item.label || item.id) + " 副本";
  copy.x = (copy.x || 0) + 16;
  copy.y = (copy.y || 0) + 16;
  state.project.elements.push(copy);
  state.selectedId = copy.id;
  markDirty();
  render();
  renderLayers();
  renderInspector();
}

function deleteSelected() {
  if (!state.selectedId) return;
  pushHistory();
  state.project.elements = state.project.elements.filter(item => item.id !== state.selectedId);
  state.selectedId = null;
  markDirty();
  render();
  renderLayers();
  renderInspector();
}

function moveSelected(direction) {
  const item = selected();
  if (!item) return;
  const index = state.project.elements.indexOf(item);
  const target = index + direction;
  if (target < 0 || target >= state.project.elements.length) return;
  pushHistory();
  state.project.elements.splice(index, 1);
  state.project.elements.splice(target, 0, item);
  markDirty();
  render();
  renderLayers();
}

function nudge(dx, dy) {
  const item = selected();
  if (!item) return;
  item.x = Math.round((item.x || 0) + dx);
  item.y = Math.round((item.y || 0) + dy);
  markDirty();
  render();
}

/* ------------------------------------------------------------------ svg */

function escapeXml(value) {
  return String(value).replace(/[&<>"']/g, char => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&apos;"
  })[char]);
}

function imageDataUrl(image) {
  const offscreen = document.createElement("canvas");
  offscreen.width = image.naturalWidth;
  offscreen.height = image.naturalHeight;
  offscreen.getContext("2d").drawImage(image, 0, 0);
  return offscreen.toDataURL("image/png");
}

function transformAttribute(item, box) {
  const center = { x: box.x + box.w / 2, y: box.y + box.h / 2 };
  const transform = "rotate(" + (item.angle || 0) + " " + center.x + " " + center.y + ") "
    + "translate(" + center.x + " " + center.y + ") scale(" + (item.scaleX || 1) + " " + (item.scaleY || 1) + ") "
    + "translate(" + (-center.x) + " " + (-center.y) + ")";
  return "opacity=" + (item.opacity === undefined ? 1 : item.opacity) + " transform=" + JSON.stringify(transform);
}

function elementSvg(item) {
  const box = itemBox(item);
  const common = transformAttribute(item, box);
  if (item.type === "image") {
    const image = state.images.get(item.src);
    const data = image && image.complete ? imageDataUrl(image) : "";
    return "<image href=" + JSON.stringify(data) + " x=" + box.x + " y=" + box.y + " width=" + box.w + " height=" + box.h + " " + common + "/>";
  }
  if (item.type === "rect") {
    return "<rect x=" + box.x + " y=" + box.y + " width=" + box.w + " height=" + box.h + " rx=" + (item.radius || 0)
      + " fill=" + JSON.stringify(item.fill || "none") + " stroke=" + JSON.stringify(item.stroke || "none")
      + " stroke-width=" + (item.strokeWidth || 0) + " " + common + "/>";
  }
  if (item.type === "ellipse") {
    return "<ellipse cx=" + (box.x + box.w / 2) + " cy=" + (box.y + box.h / 2) + " rx=" + (box.w / 2) + " ry=" + (box.h / 2)
      + " fill=" + JSON.stringify(item.fill || "none") + " stroke=" + JSON.stringify(item.stroke || "none")
      + " stroke-width=" + (item.strokeWidth || 0) + " " + common + "/>";
  }
  if (item.type === "line") {
    return "<line x1=" + box.x + " y1=" + box.y + " x2=" + (box.x + box.w) + " y2=" + (box.y + box.h)
      + " stroke=" + JSON.stringify(item.stroke || "#000") + " stroke-width=" + (item.strokeWidth || 1)
      + " stroke-linecap=" + JSON.stringify("round") + " " + common + "/>";
  }
  if (item.type === "arc") {
    const start = (item.start || 0) * Math.PI / 180;
    let end = (item.end === undefined ? 360 : item.end) * Math.PI / 180;
    while (end <= start) end += Math.PI * 2;
    const rx = box.w / 2;
    const ry = box.h / 2;
    const cx = box.x + rx;
    const cy = box.y + ry;
    const sx = cx + rx * Math.cos(start);
    const sy = cy + ry * Math.sin(start);
    const ex = cx + rx * Math.cos(end);
    const ey = cy + ry * Math.sin(end);
    const large = end - start > Math.PI ? 1 : 0;
    return "<path d=" + JSON.stringify("M " + sx + " " + sy + " A " + rx + " " + ry + " 0 " + large + " 1 " + ex + " " + ey)
      + " fill=" + JSON.stringify("none") + " stroke=" + JSON.stringify(item.stroke || "#000")
      + " stroke-width=" + (item.strokeWidth || 1) + " stroke-linecap=" + JSON.stringify("round") + " " + common + "/>";
  }
  if (item.type === "text") {
    const layout = box.layout || textLayout(item);
    const align = item.align || "left";
    const textX = align === "center" ? box.x + box.w / 2 : align === "right" ? box.x + box.w : box.x;
    const anchor = align === "center" ? "middle" : align === "right" ? "end" : "start";
    return layout.lines.map((line, index) => {
      const baseline = box.y + layout.fontSize * 0.8 + index * layout.lineHeight;
      return "<text x=" + textX + " y=" + baseline + " text-anchor=" + JSON.stringify(anchor)
        + " font-family=" + JSON.stringify(item.fontFamily || "sans-serif") + " font-size=" + layout.fontSize
        + " font-weight=" + JSON.stringify(item.fontWeight || "400") + " fill=" + JSON.stringify(item.fill || "#000")
        + " stroke=" + JSON.stringify(item.stroke || "none") + " stroke-width=" + (item.strokeWidth || 0)
        + " paint-order=" + JSON.stringify("stroke") + " " + common + ">" + escapeXml(line) + "</text>";
    }).join("");
  }
  return "";
}

function buildSvg(elements) {
  const canvas = state.project.canvas;
  const body = elements.filter(item => item.visible !== false).map(elementSvg).join("");
  return "<svg xmlns=" + JSON.stringify("http://www.w3.org/2000/svg")
    + " width=" + canvas.width + " height=" + canvas.height
    + " viewBox=" + JSON.stringify("0 0 " + canvas.width + " " + canvas.height) + ">"
    + "<rect width=" + canvas.width + " height=" + canvas.height + " fill=" + JSON.stringify(canvas.background || "#ffffff") + "/>"
    + body + "</svg>";
}

/* --------------------------------------------------------------- export */

function renderToCanvas(scale) {
  const canvas = state.project.canvas;
  const target = document.createElement("canvas");
  target.width = canvas.width * scale;
  target.height = canvas.height * scale;
  const targetCtx = target.getContext("2d");
  targetCtx.scale(scale, scale);
  targetCtx.fillStyle = canvas.background || "#ffffff";
  targetCtx.fillRect(0, 0, canvas.width, canvas.height);
  for (const item of visibleElements()) drawOnContext(targetCtx, item);
  return target;
}

function baseName() {
  const name = (state.project.name || "poster").replace(/[\\/:*?"<>|]/g, "-");
  const version = (state.project.meta && state.project.meta.version) || "v1";
  return name + "-" + version;
}

function triggerDownload(dataUrl, filename) {
  const link = document.createElement("a");
  link.href = dataUrl;
  link.download = filename;
  document.body.append(link);
  link.click();
  link.remove();
}

async function exportPng(scale) {
  const data = renderToCanvas(scale).toDataURL("image/png");
  const filename = baseName() + "-" + scale + "x.png";
  const result = await api("/api/export/png", { data: data, filename: filename });
  triggerDownload(data, filename);
  setStatus(t(scale === 1 ? "exportPng1" : "exportPng2") + " · " + result.file, "ok");
}

async function exportSvg() {
  const svg = buildSvg(state.project.elements);
  const filename = baseName() + ".svg";
  const result = await api("/api/export/svg", { svg: svg, filename: filename });
  triggerDownload("data:image/svg+xml;charset=utf-8," + encodeURIComponent(svg), filename);
  setStatus(t("exportSvg") + " · " + result.file, "ok");
}

function rasterize(elements) {
  const canvas = state.project.canvas;
  const svg = buildSvg(elements);
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => {
      const target = document.createElement("canvas");
      target.width = canvas.width;
      target.height = canvas.height;
      target.getContext("2d").drawImage(image, 0, 0);
      resolve(target.toDataURL("image/png"));
    };
    image.onerror = () => reject(new Error("无法生成 PSD 图层快照"));
    image.src = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(svg);
  });
}

async function exportPsd() {
  setStatus("正在生成 PSD 图层…");
  const groups = new Map();
  for (const item of visibleElements()) {
    const name = groupOf(item) || item.label || item.id;
    if (!groups.has(name)) groups.set(name, []);
    groups.get(name).push(item);
  }
  const layers = [];
  for (const entry of groups) layers.push({ name: entry[0], data: await rasterize(entry[1]) });
  const filename = baseName() + "-分层版.psd";
  const result = await api("/api/export/psd", { layers: layers, filename: filename });
  setStatus(t("exportPsd") + " · " + result.file, "ok");
}

function openPreview() {
  const canvas = state.project.canvas;
  dom.previewCanvas.width = canvas.width;
  dom.previewCanvas.height = canvas.height;
  const targetCtx = dom.previewCanvas.getContext("2d");
  targetCtx.fillStyle = canvas.background || "#ffffff";
  targetCtx.fillRect(0, 0, canvas.width, canvas.height);
  for (const item of visibleElements()) drawOnContext(targetCtx, item);
  dom.previewOverlay.hidden = false;
  dom.previewStage.className = "preview-stage " + state.previewBackdrop;
  dom.previewCaption.textContent = canvas.width + " × " + canvas.height + " px  ·  "
    + state.project.elements.length + " " + t("elements") + "  ·  "
    + ((state.project.meta && state.project.meta.carrier) || "");
  dom.previewTitle.textContent = t("previewTitle");
  dom.previewCloseBtn.textContent = t("previewExit");
  dom.previewBackdropBtn.textContent = t("backdrop");
}

function closePreview() {
  dom.previewOverlay.hidden = true;
}

function applyLanguage() {
  document.documentElement.lang = state.lang === "zh" ? "zh-CN" : "en";
  dom.langBtn.textContent = state.lang === "zh" ? "EN" : "中";
  dom.saveBtn.textContent = t("save");
  dom.previewBtn.textContent = t("preview");
  dom.exportBtn.childNodes[0].textContent = t("export");
  dom.stageHint.textContent = t("fitHint");
  dom.saveStateText.textContent = state.dirty ? t("unsaved") : t("synced");
  renderLayers();
  renderInspector();
  updateMeta();
}

function loadImages(elements) {
  const tasks = [];
  for (const item of elements) {
    if (item.type !== "image" || !item.src || state.images.has(item.src)) continue;
    tasks.push(new Promise(resolve => {
      const image = new Image();
      image.onload = () => {
        state.images.set(item.src, image);
        resolve();
      };
      image.onerror = () => resolve();
      image.src = "/" + item.src;
    }));
  }
  return Promise.all(tasks);
}

async function load() {
  try {
    const response = await fetch("/api/project");
    const body = await response.json();
    if (!response.ok) throw new Error(body.error || "无法加载源稿");
    state.project = body.project;
    state.file = body.file;
    dom.poster.width = state.project.canvas.width;
    dom.poster.height = state.project.canvas.height;
    dom.posterName.textContent = state.project.name || body.file;
    const meta = state.project.meta || {};
    dom.posterMeta.textContent = [meta.version, meta.carrier, body.file].filter(Boolean).join(" · ");
    await loadImages(state.project.elements);
    state.selectedId = state.project.elements.length ? state.project.elements[state.project.elements.length - 1].id : null;
    fitToStage();
    render();
    renderLayers();
    renderInspector();
    updateMeta();
    updateHistoryButtons();
    setStatus(t("loaded"), "ok");
  } catch (error) {
    setStatus("无法加载源稿：" + error.message, "err");
  }
}

/* --------------------------------------------------------- interaction */

dom.poster.addEventListener("pointerdown", event => {
  if (!state.project) return;
  const point = eventPoint(event);
  const item = selected();
  if (item && !item.locked) {
    const handle = handleAt(item, point);
    if (handle) {
      pushHistory();
      state.drag = { kind: handle.id === "rotate" ? "rotate" : "resize", item: item, handle: handle.id };
      dom.poster.setPointerCapture(event.pointerId);
      return;
    }
  }
  const hit = hitTest(point);
  if (hit) {
    select(hit.id);
    if (!hit.locked) {
      pushHistory();
      state.drag = { kind: "move", item: hit, start: point, x: hit.x, y: hit.y };
      dom.poster.setPointerCapture(event.pointerId);
    }
  } else {
    select(null);
  }
});

dom.poster.addEventListener("pointermove", event => {
  const drag = state.drag;
  if (!drag || !state.project) return;
  const point = eventPoint(event);
  if (drag.kind === "move") {
    drag.item.x = Math.round(drag.x + point.x - drag.start.x);
    drag.item.y = Math.round(drag.y + point.y - drag.start.y);
  } else if (drag.kind === "rotate") {
    const center = centerOf(drag.item);
    const angle = Math.atan2(point.y - center.y, point.x - center.x) * 180 / Math.PI + 90;
    drag.item.angle = Math.round(angle * 10) / 10;
  } else if (drag.kind === "resize") {
    resizeElement(drag.item, drag.handle, point);
  }
  markDirty();
  render();
});

function endDrag() {
  if (!state.drag) return;
  state.drag = null;
  renderInspector();
}
dom.poster.addEventListener("pointerup", endDrag);
dom.poster.addEventListener("pointercancel", endDrag);

dom.stageSurface.addEventListener("wheel", event => {
  if (!state.project) return;
  if (!(event.ctrlKey || event.metaKey)) return;
  event.preventDefault();
  setZoom(state.zoom * (event.deltaY < 0 ? 1.1 : 0.9));
}, { passive: false });

document.addEventListener("keydown", event => {
  if (event.target.matches && event.target.matches("input, textarea, select")) return;
  const meta = event.ctrlKey || event.metaKey;
  const key = event.key.toLowerCase();
  if (meta && key === "s") {
    event.preventDefault();
    save();
    return;
  }
  if (meta && key === "z") {
    event.preventDefault();
    if (event.shiftKey) redo(); else undo();
    return;
  }
  if (meta && key === "y") {
    event.preventDefault();
    redo();
    return;
  }
  if (meta && key === "d") {
    event.preventDefault();
    duplicateSelected();
    return;
  }
  if (event.key === "Delete" || event.key === "Backspace") {
    if (state.selectedId) {
      event.preventDefault();
      deleteSelected();
    }
    return;
  }
  if (event.key === "Escape") {
    if (!dom.previewOverlay.hidden) closePreview();
    else select(null);
    return;
  }
  if (key === "p") {
    openPreview();
    return;
  }
  if (event.key === "0") {
    fitToStage();
    return;
  }
  const step = event.shiftKey ? 10 : 1;
  const moves = { ArrowLeft: [-step, 0], ArrowRight: [step, 0], ArrowUp: [0, -step], ArrowDown: [0, step] };
  if (moves[event.key]) {
    event.preventDefault();
    nudge(moves[event.key][0], moves[event.key][1]);
  }
});

dom.layerSearch.addEventListener("input", event => {
  state.search = event.target.value;
  renderLayers();
});

dom.undoBtn.addEventListener("click", undo);
dom.redoBtn.addEventListener("click", redo);
dom.saveBtn.addEventListener("click", save);
dom.previewBtn.addEventListener("click", openPreview);
dom.previewCloseBtn.addEventListener("click", closePreview);
dom.previewBackdropBtn.addEventListener("click", () => {
  state.previewBackdrop = state.previewBackdrop === "dark" ? "light" : "dark";
  dom.previewStage.className = "preview-stage " + state.previewBackdrop;
});

document.getElementById("groupUpBtn").addEventListener("click", () => moveSelected(1));
document.getElementById("groupDownBtn").addEventListener("click", () => moveSelected(-1));
document.getElementById("duplicateBtn").addEventListener("click", duplicateSelected);
document.getElementById("deleteBtn").addEventListener("click", deleteSelected);

dom.zoomIn.addEventListener("click", () => setZoom(state.zoom * 1.2));
dom.zoomOut.addEventListener("click", () => setZoom(state.zoom / 1.2));
dom.zoomFit.addEventListener("click", fitToStage);
dom.zoomLabel.addEventListener("click", () => setZoom(1));

dom.exportBtn.addEventListener("click", event => {
  event.stopPropagation();
  const open = dom.exportMenu.hidden;
  dom.exportMenu.hidden = !open;
  dom.exportBtn.setAttribute("aria-expanded", String(open));
});
document.addEventListener("click", event => {
  if (!dom.exportMenu.hidden && !dom.exportMenu.contains(event.target)) {
    dom.exportMenu.hidden = true;
    dom.exportBtn.setAttribute("aria-expanded", "false");
  }
});
dom.exportMenu.addEventListener("click", async event => {
  const button = event.target.closest("button[data-export]");
  if (!button) return;
  dom.exportMenu.hidden = true;
  const kind = button.dataset.export;
  try {
    if (kind === "png1") await exportPng(1);
    else if (kind === "png2") await exportPng(2);
    else if (kind === "svg") await exportSvg();
    else if (kind === "psd") await exportPsd();
  } catch (error) {
    setStatus("导出失败：" + error.message, "err");
  }
});

dom.assetInput.addEventListener("change", async () => {
  const file = dom.assetInput.files[0];
  if (!file) return;
  const targetId = state.replaceTargetId;
  state.replaceTargetId = null;
  const reader = new FileReader();
  reader.onload = async () => {
    try {
      const result = await api("/api/assets/upload", { data: reader.result, name: file.name.replace(/\.[^.]+$/, "") });
      const image = new Image();
      await new Promise(resolve => {
        image.onload = resolve;
        image.onerror = resolve;
        image.src = "/" + result.src;
      });
      state.images.set(result.src, image);
      const item = targetId ? state.project.elements.find(entry => entry.id === targetId) : null;
      if (item) {
        pushHistory();
        item.src = result.src;
        markDirty();
        render();
        renderInspector();
        setStatus("已替换图片，请保存源稿。", "ok");
      }
    } catch (error) {
      setStatus("上传失败：" + error.message, "err");
    }
  };
  reader.readAsDataURL(file);
});

dom.langBtn.addEventListener("click", () => {
  state.lang = state.lang === "zh" ? "en" : "zh";
  applyLanguage();
});

window.addEventListener("resize", () => {
  if (!state.project) return;
  const canvas = state.project.canvas;
  const available = {
    width: dom.stageSurface.clientWidth - 80,
    height: dom.stageSurface.clientHeight - 80
  };
  const scale = Math.min(available.width / canvas.width, available.height / canvas.height, 1.5);
  if (Math.abs(scale - state.zoom) < 0.02) setZoom(scale);
});

applyLanguage();
load();

