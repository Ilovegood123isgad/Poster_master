#!/usr/bin/env node
"use strict";

/**
 * Start the component editor if it is not already running, then print its URL.
 *
 *   node open.js --project "<project-dir>" [--port 41735] [--open] [--stop]
 *
 * Why this exists: `server.js` runs in the foreground and holds the terminal, so
 * the common failure is "I clicked the link and got ERR_CONNECTION_REFUSED" —
 * the server was never started, or the window it lived in was closed. This
 * wrapper starts it detached, waits until it actually answers, and only then
 * prints the address. Running it twice for the same project reuses the instance
 * instead of starting a second one.
 *
 * Node standard library only.
 */

const http = require("http");
const net = require("net");
const path = require("path");
const fs = require("fs");
const os = require("os");
const crypto = require("crypto");
const { spawn } = require("child_process");

const SERVER = path.join(__dirname, "server.js");
const DEFAULT_PORT = 41735;
const PORT_RANGE = 10;
const START_TIMEOUT_MS = 30000;

function parseArgs(argv) {
  const args = { project: "", port: DEFAULT_PORT, open: false, stop: false };
  for (let i = 0; i < argv.length; i += 1) {
    const key = argv[i];
    if (key === "--project" || key === "-p") args.project = argv[++i] || "";
    else if (key === "--port") args.port = Number(argv[++i]) || DEFAULT_PORT;
    else if (key === "--open") args.open = true;
    else if (key === "--stop") args.stop = true;
    else if (key === "--help" || key === "-h") args.help = true;
  }
  return args;
}

/**
 * Where the running instance is recorded. Kept out of the project folder on
 * purpose: a project folder is something people zip, archive and hand over, and
 * a stray pid file has no business being in it.
 */
function pidFile(project) {
  const digest = crypto.createHash("sha1").update(project).digest("hex").slice(0, 12);
  return path.join(os.tmpdir(), `poster-master-editor-${digest}.pid`);
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/** GET /api/project; resolves with the payload, or null when nothing answers. */
function probe(port) {
  return new Promise(resolve => {
    const request = http.get(
      { host: "127.0.0.1", port, path: "/api/project", timeout: 1500 },
      response => {
        let body = "";
        response.setEncoding("utf8");
        response.on("data", chunk => { body += chunk; });
        response.on("end", () => {
          if (response.statusCode !== 200) return resolve(null);
          try {
            resolve(JSON.parse(body));
          } catch {
            resolve(null);
          }
        });
      }
    );
    request.on("timeout", () => { request.destroy(); resolve(null); });
    request.on("error", () => resolve(null));
  });
}

function portIsFree(port) {
  return new Promise(resolve => {
    const tester = net.createServer();
    tester.once("error", () => resolve(false));
    tester.once("listening", () => tester.close(() => resolve(true)));
    tester.listen(port, "127.0.0.1");
  });
}

async function waitForServer(port, project, timeoutMs) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const payload = await probe(port);
    if (payload && payload.project) {
      const samePath = payload.file
        ? path.basename(payload.file) === path.basename(findSource(project) || "")
        : false;
      if (samePath || payload.project.name === readProjectName(project)) return payload;
    }
    await sleep(400);
  }
  return null;
}

function findSource(project) {
  try {
    const entries = fs.readdirSync(project).filter(name => name.endsWith(".poster.json"));
    return entries.length ? entries.sort()[0] : null;
  } catch {
    return null;
  }
}

function readProjectName(project) {
  const source = findSource(project);
  if (!source) return "";
  try {
    return JSON.parse(fs.readFileSync(path.join(project, source), "utf8")).name || "";
  } catch {
    return "";
  }
}

function launch(url) {
  const command = process.platform === "win32"
    ? ["cmd", ["/c", "start", "", url]]
    : process.platform === "darwin"
      ? ["open", [url]]
      : ["xdg-open", [url]];
  try {
    spawn(command[0], command[1], { detached: true, stdio: "ignore" }).unref();
  } catch {
    /* opening a browser is a convenience; never fail on it */
  }
}

async function stop(project) {
  const file = pidFile(project);
  if (!fs.existsSync(file)) {
    console.log("没有找到运行记录（.editor.pid）；编辑器可能不是由 open.js 启动的。");
    return 1;
  }
  const pid = Number(fs.readFileSync(file, "utf8").trim());
  try {
    process.kill(pid);
    console.log(`已停止编辑器进程 ${pid}`);
  } catch (error) {
    console.log(`进程 ${pid} 已经不在了（${error.code || error.message}）`);
  }
  try { fs.unlinkSync(file); } catch { /* ignore */ }
  return 0;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) {
    console.log(
      '用法：node open.js --project "<项目文件夹>" [--port 41735] [--open] [--stop]\n' +
      "  不给 --open 就只打印地址（方便在 DSH 侧边栏浏览器里打开）。"
    );
    return 0;
  }
  if (!args.project) {
    console.error('缺少 --project。用法：node open.js --project "<项目文件夹>"');
    return 2;
  }

  const project = path.resolve(args.project);
  if (!fs.existsSync(project) || !fs.statSync(project).isDirectory()) {
    console.error(`项目文件夹不存在：${project}`);
    return 2;
  }
  if (!findSource(project)) {
    console.error(`这个文件夹里没有 *.poster.json：${project}`);
    return 2;
  }

  if (args.stop) return stop(project);

  const wanted = readProjectName(project);

  // Already serving this project? Reuse it, do not start a second one.
  const existing = await probe(args.port);
  if (existing && existing.project && existing.project.name === wanted) {
    const url = `http://127.0.0.1:${args.port}/`;
    console.log(`编辑器已在运行：${url}`);
    console.log(`  项目：${existing.project.name}（${existing.project.elements.length} 个组件）`);
    if (args.open) launch(url);
    return 0;
  }

  // Pick a free port instead of dying on EADDRINUSE.
  let port = args.port;
  let found = false;
  for (let offset = 0; offset < PORT_RANGE; offset += 1) {
    const candidate = args.port + offset;
    if (await portIsFree(candidate)) {
      port = candidate;
      found = true;
      break;
    }
  }
  if (!found) {
    console.error(
      `端口 ${args.port}–${args.port + PORT_RANGE - 1} 都被占用了。` +
      "用 --port 指定一个空闲端口。"
    );
    return 1;
  }
  if (port !== args.port) {
    console.log(`端口 ${args.port} 已被占用，改用 ${port}。`);
  }

  const child = spawn(
    process.execPath,
    [SERVER, "--project", project, "--port", String(port)],
    { detached: true, stdio: "ignore", windowsHide: true }
  );
  child.unref();
  fs.writeFileSync(pidFile(project), String(child.pid), "utf8");

  const payload = await waitForServer(port, project, START_TIMEOUT_MS);
  if (!payload) {
    console.error(
      `启动失败：${START_TIMEOUT_MS / 1000} 秒内 ${port} 端口没有响应。\n` +
      "手动跑一次看报错：\n" +
      `  node "${SERVER}" --project "${project}" --port ${port}`
    );
    return 1;
  }

  const url = `http://127.0.0.1:${port}/`;
  console.log(`编辑器已启动：${url}`);
  console.log(`  项目：${payload.project.name}（${payload.project.elements.length} 个组件）`);
  console.log(`  停止：node open.js --project "${project}" --stop`);
  if (args.open) launch(url);
  return 0;
}

main().then(code => process.exit(code)).catch(error => {
  console.error(error && error.stack ? error.stack : String(error));
  process.exit(1);
});
