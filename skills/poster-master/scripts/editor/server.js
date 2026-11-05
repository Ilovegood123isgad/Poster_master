#!/usr/bin/env node
"use strict";

/**
 * Poster Master — local component editor server.
 *
 * Node standard library only. No dependencies, no network access, no build step.
 * Binds to 127.0.0.1 and serves only the project folder it was pointed at.
 *
 *   node server.js --project "<project-dir>" [--port 41735]
 */

const http = require("http");
const fs = require("fs");
const fsp = require("fs/promises");
const path = require("path");
const crypto = require("crypto");
const { spawn } = require("child_process");

const PUBLIC_DIR = path.join(__dirname, "public");
const SKILL_DIR = path.resolve(__dirname, "..", "..");
const PSD_SCRIPT = path.join(SKILL_DIR, "scripts", "export_psd.py");

const MIME = {
  ".css": "text/css; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".webp": "image/webp",
  ".gif": "image/gif",
  ".svg": "image/svg+xml"
};

const ELEMENT_TYPES = ["image", "rect", "ellipse", "text", "line", "arc"];
const MAX_ELEMENTS = 200;
const MAX_BODY = 200 * 1024 * 1024;

function parseArgs(argv) {
  const args = { project: "", port: Number(process.env.POSTER_EDITOR_PORT || 41735), host: "127.0.0.1" };
  for (let i = 0; i < argv.length; i += 1) {
    const key = argv[i];
    if (key === "--project" || key === "-p") args.project = argv[++i] || "";
    else if (key === "--port") args.port = Number(argv[++i] || args.port);
    else if (key === "--host") args.host = argv[++i] || args.host;
    else if (key === "--help" || key === "-h") args.help = true;
  }
  return args;
}

function fail(message) {
  console.error("Poster Master 编辑器启动失败：" + message);
  console.error("");
  console.error("用法：node server.js --project \"<项目文件夹>\" [--port 41735]");
  process.exit(1);
}

function respond(res, status, body, type = "application/json; charset=utf-8") {
  res.writeHead(status, { "Content-Type": type, "Cache-Control": "no-store" });
  res.end(Buffer.isBuffer(body) ? body : typeof body === "string" ? body : JSON.stringify(body));
}

/** Resolve a path inside a root directory, refusing anything that escapes it. */
function safeChild(root, value) {
  const target = path.resolve(root, value);
  if (target !== root && !target.startsWith(root + path.sep)) throw new Error("非法文件路径");
  return target;
}

async function readBody(req, limit = MAX_BODY) {
  const chunks = [];
  let size = 0;
  for await (const chunk of req) {
    size += chunk.length;
    if (size > limit) throw new Error("请求内容超过 " + Math.round(limit / 1024 / 1024) + " MB 限制");
    chunks.push(chunk);
  }
  if (!chunks.length) return {};
  return JSON.parse(Buffer.concat(chunks).toString("utf8"));
}

function decodeDataUrl(data, allowed = ["image/png", "image/jpeg", "image/webp"]) {
  const matched = /^data:([^;]+);base64,([A-Za-z0-9+/=]+)$/.exec(data || "");
  if (!matched || !allowed.includes(matched[1])) throw new Error("只接受 PNG、JPEG 或 WebP 的 base64 数据");
  return { mime: matched[1], buffer: Buffer.from(matched[2], "base64") };
}

async function atomicWrite(file, data) {
  const temp = file + "." + process.pid + "." + Date.now() + ".tmp";
  await fsp.writeFile(temp, data);
  await fsp.rename(temp, file);
}

/** Validate a component source. Returns the normalised project. */
function validateProject(value) {
  if (!value || typeof value !== "object") throw new Error("源稿必须是 JSON 对象");
  if (value.schemaVersion !== 1) throw new Error("不支持的 schemaVersion：" + value.schemaVersion + "（当前支持 1）");

  const canvas = value.canvas;
  if (!canvas || !Number.isInteger(canvas.width) || !Number.isInteger(canvas.height)
    || canvas.width < 1 || canvas.height < 1 || canvas.width > 20000 || canvas.height > 20000) {
    throw new Error("画布宽高必须是 1–20000 之间的整数");
  }

  const elements = value.elements;
  if (!Array.isArray(elements) || elements.length < 1 || elements.length > MAX_ELEMENTS) {
    throw new Error("组件数量必须在 1–" + MAX_ELEMENTS + " 之间");
  }

  const ids = new Set();
  for (const item of elements) {
    if (!item || typeof item !== "object") throw new Error("存在无效的组件");
    if (typeof item.id !== "string" || !/^[a-z0-9-]{2,64}$/.test(item.id)) throw new Error("组件 ID 无效：" + item.id);
    if (ids.has(item.id)) throw new Error("组件 ID 重复：" + item.id);
    ids.add(item.id);

    if (!ELEMENT_TYPES.includes(item.type)) throw new Error("组件 " + item.id + " 的类型无效：" + item.type);
    for (const key of ["x", "y", "w", "h", "angle", "scaleX", "scaleY", "opacity", "radius", "strokeWidth", "fontSize", "start", "end"]) {
      if (item[key] !== undefined && (!Number.isFinite(item[key]) || Math.abs(item[key]) > 100000)) {
        throw new Error("组件 " + item.id + " 的 " + key + " 无效");
      }
    }
    if (item.type === "image") {
      const source = String(item.src || "");
      if (!source.startsWith("assets/")) throw new Error("图片必须引用 assets 目录：" + item.id);
      const name = source.slice(7);
      if (!name || name.includes("/") || name.includes("\\") || /[<>:"|?*\x00-\x1F]/.test(name)) {
        throw new Error("图片路径非法：" + source);
      }
    }
    if (item.type === "text" && typeof item.text !== "string") {
      throw new Error("文字组件缺少内容：" + item.id);
    }
  }
  return value;
}

async function findSourceFile(projectDir) {
  const entries = await fsp.readdir(projectDir, { withFileTypes: true });
  const candidates = [];
  for (const entry of entries) {
    if (!entry.isFile()) continue;
    if (entry.name.endsWith(".poster.json")) candidates.push(entry.name);
    else if (entry.name.endsWith(".json") && /组件源稿|source|poster/i.test(entry.name)) candidates.push(entry.name);
  }
  candidates.sort();
  if (!candidates.length) throw new Error("项目文件夹里没有找到组件源稿（*.poster.json）");
  return path.join(projectDir, candidates[0]);
}

async function listAssets(assetsDir) {
  try {
    const entries = await fsp.readdir(assetsDir, { withFileTypes: true });
    return entries.filter(entry => entry.isFile()).map(entry => "assets/" + entry.name);
  } catch {
    return [];
  }
}

let cachedPython = "";

/** Run a command and resolve with its stdout, rejecting on non-zero exit. */
function runCommand(command, argv, timeoutMs) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, argv, { windowsHide: true });
    let stdout = "";
    let stderr = "";
    const timer = timeoutMs ? setTimeout(() => {
      try { child.kill(); } catch { /* already gone */ }
      reject(new Error(`${command} 超时`));
    }, timeoutMs) : null;
    child.stdout.on("data", chunk => { stdout += chunk; });
    child.stderr.on("data", chunk => { stderr += chunk; });
    child.on("error", error => {
      if (timer) clearTimeout(timer);
      reject(error);
    });
    child.on("close", code => {
      if (timer) clearTimeout(timer);
      if (code === 0) resolve(stdout);
      else reject(new Error(stderr.trim() || `${command} 退出码 ${code}`));
    });
  });
}

/**
 * Find a working Python once.
 *
 * The old code called "python" and nothing else, so on a machine with only
 * python3 — or with the Windows Store stub that exits 9009 and prints nothing —
 * the PSD export failed with an empty error message.
 */
async function resolvePython() {
  if (cachedPython) return cachedPython;
  const candidates = [
    process.env.POSTER_EDITOR_PYTHON,
    process.platform === "win32" ? "python" : "python3",
    "python3",
    "python",
    "py"
  ].filter(Boolean);
  const failures = [];
  for (const candidate of candidates) {
    try {
      await runCommand(candidate, ["-c", "print(1)"], 15000);
      cachedPython = candidate;
      return candidate;
    } catch (error) {
      failures.push(candidate + ": " + error.message);
    }
  }
  throw new Error(
    "找不到可用的 Python 3，PSD 导出无法执行。请安装 Python 3 后设置环境变量 POSTER_EDITOR_PYTHON=python。" +
    "（已尝试：" + failures.join("；") + "）"
  );
}

const MAX_LAYERS = 400;

/** Turn the editor's layer tree into PNG files plus a manifest tree. */
async function writeLayerTree(nodes, tempDir, counter, depth) {
  if (depth > 4) throw new Error("图层组嵌套过深（最多 5 层）");
  const out = [];
  for (const node of nodes) {
    if (!node || typeof node.name !== "string") throw new Error("PSD 图层信息无效");
    const name = node.name.slice(0, 200);
    if (Array.isArray(node.children)) {
      if (!node.children.length) continue;
      out.push({ name, children: await writeLayerTree(node.children, tempDir, counter, depth + 1) });
      continue;
    }
    if (typeof node.data !== "string") continue;
    if (counter.value >= MAX_LAYERS) throw new Error("图层数超过 " + MAX_LAYERS + "，请改用「按组件分组」");
    const decoded = decodeDataUrl(node.data, ["image/png"]);
    const file = path.join(tempDir, String(counter.value).padStart(4, "0") + ".png");
    counter.value += 1;
    await fsp.writeFile(file, decoded.buffer);
    out.push({ name, path: file, visible: node.visible !== false });
  }
  return out;
}

async function runPsdExport(projectDir, outputName, layers, dpi) {
  const exportsDir = path.join(projectDir, "exports");
  const tempDir = path.join(exportsDir, "._psd_" + crypto.randomUUID());
  await fsp.mkdir(tempDir, { recursive: true });
  try {
    let canvas = { width: 0, height: 0 };
    try {
      const sourceFile = await findSourceFile(projectDir);
      const project = JSON.parse(await fsp.readFile(sourceFile, "utf8"));
      canvas = project.canvas || canvas;
    } catch {
      // A source without a canvas falls back to the layer size.
    }

    const tree = await writeLayerTree(layers, tempDir, { value: 0 }, 0);
    if (!tree.length) throw new Error("没有可写入的图层");

    const manifest = {
      width: Number(canvas.width) || 0,
      height: Number(canvas.height) || 0,
      dpi: Number(dpi) || 300,
      compression: "rle",
      output: path.join(exportsDir, outputName),
      layers: tree
    };
    const manifestPath = path.join(tempDir, "manifest.json");
    await fsp.writeFile(manifestPath, JSON.stringify(manifest), "utf8");

    const python = await resolvePython();
    await runCommand(python, [PSD_SCRIPT, manifestPath], 15 * 60 * 1000);
  } finally {
    await fsp.rm(tempDir, { recursive: true, force: true });
  }
}

function safeFileName(name, fallback) {
  const cleaned = String(name || "").replace(/[\\/:*?"<>|\x00-\x1F]/g, "-").trim();
  return cleaned || fallback;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) {
    console.log("用法：node server.js --project \"<项目文件夹>\" [--port 41735] [--host 127.0.0.1]");
    return;
  }
  if (!args.project) fail("缺少 --project 参数");

  const projectDir = path.resolve(args.project);
  if (!fs.existsSync(projectDir) || !fs.statSync(projectDir).isDirectory()) fail("项目文件夹不存在：" + projectDir);

  const assetsDir = path.join(projectDir, "assets");
  const exportsDir = path.join(projectDir, "exports");
  await fsp.mkdir(assetsDir, { recursive: true });
  await fsp.mkdir(exportsDir, { recursive: true });

  const sourceFile = await findSourceFile(projectDir);

  const server = http.createServer(async (req, res) => {
    try {
      const url = new URL(req.url, "http://" + args.host + ":" + args.port);

      if (req.method === "GET" && url.pathname === "/api/project") {
        const raw = await fsp.readFile(sourceFile, "utf8");
        return respond(res, 200, {
          file: path.basename(sourceFile),
          project: JSON.parse(raw),
          assets: await listAssets(assetsDir)
        });
      }

      if (req.method === "POST" && url.pathname === "/api/save") {
        const body = await readBody(req);
        const project = validateProject(body.project || body);
        await atomicWrite(sourceFile, JSON.stringify(project, null, 2) + "\n");
        return respond(res, 200, { ok: true, message: "组件源稿已保存" });
      }

      if (req.method === "POST" && url.pathname === "/api/assets/upload") {
        const body = await readBody(req, 20 * 1024 * 1024);
        const decoded = decodeDataUrl(body.data);
        const extension = decoded.mime === "image/png" ? ".png" : decoded.mime === "image/jpeg" ? ".jpg" : ".webp";
        const name = safeFileName(body.name, "替换素材-" + Date.now()) + extension;
        await fsp.writeFile(path.join(assetsDir, name), decoded.buffer);
        return respond(res, 200, { ok: true, src: "assets/" + name, name });
      }

      if (req.method === "POST" && url.pathname === "/api/export/png") {
        const body = await readBody(req);
        const decoded = decodeDataUrl(body.data, ["image/png"]);
        const output = path.join(exportsDir, safeFileName(body.filename, "海报导出.png"));
        await atomicWrite(output, decoded.buffer);
        return respond(res, 200, { ok: true, file: path.basename(output), path: output });
      }

      if (req.method === "POST" && url.pathname === "/api/export/svg") {
        const body = await readBody(req);
        if (typeof body.svg !== "string" || body.svg.length > 40 * 1024 * 1024 || !body.svg.trimStart().startsWith("<svg")) {
          throw new Error("SVG 内容无效");
        }
        const output = path.join(exportsDir, safeFileName(body.filename, "海报导出.svg"));
        await atomicWrite(output, body.svg);
        return respond(res, 200, { ok: true, file: path.basename(output), path: output });
      }

      if (req.method === "POST" && url.pathname === "/api/export/psd") {
        const body = await readBody(req);
        const tree = Array.isArray(body.tree) ? body.tree : body.layers;
        if (!Array.isArray(tree) || tree.length < 1 || tree.length > MAX_LAYERS) {
          throw new Error("PSD 图层数量无效（应为 1–" + MAX_LAYERS + " 个顶层图层/组）");
        }
        const output = safeFileName(body.filename, "海报分层版.psd");
        const dpi = Number(body.dpi) > 0 ? Number(body.dpi) : 300;
        await runPsdExport(projectDir, output, tree, dpi);
        return respond(res, 200, { ok: true, file: output, dpi });
      }

      if (req.method === "GET" && url.pathname.startsWith("/assets/")) {
        const name = decodeURIComponent(url.pathname.slice("/assets/".length));
        const file = safeChild(assetsDir, name);
        const content = await fsp.readFile(file);
        return respond(res, 200, content, MIME[path.extname(file).toLowerCase()] || "application/octet-stream");
      }

      if (req.method === "GET") {
        const requested = url.pathname === "/" ? "index.html" : url.pathname.slice(1);
        const file = safeChild(PUBLIC_DIR, requested);
        const content = await fsp.readFile(file);
        return respond(res, 200, content, MIME[path.extname(file).toLowerCase()] || "application/octet-stream");
      }

      return respond(res, 405, { error: "不支持的请求方式" });
    } catch (error) {
      const missing = error.code === "ENOENT";
      return respond(res, missing ? 404 : 400, { error: error.message || "请求处理失败" });
    }
  });

  server.listen(args.port, args.host, () => {
    const count = JSON.parse(fs.readFileSync(sourceFile, "utf8")).elements.length;
    console.log("Poster Master 编辑器已启动");
    console.log("  项目：" + projectDir);
    console.log("  源稿：" + path.basename(sourceFile) + "（" + count + " 个组件）");
    console.log("  地址：http://" + args.host + ":" + args.port + "/");
    console.log("  导出：" + exportsDir);
    console.log("  按 Ctrl+C 停止");
  });
}

main().catch(error => fail(error.message));

