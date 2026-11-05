#!/usr/bin/env node
"use strict";

/**
 * Poster Master — scaffold a new poster project.
 *
 *   node new_project.js --project "<dir>" --name "<项目名>" --size <WxH> [--force]
 *
 * Copies the stage templates into the project folder and writes an empty
 * component source the editor can open. Existing files are never overwritten
 * unless --force is given.
 */

const fs = require("fs");
const fsp = require("fs/promises");
const path = require("path");

const TEMPLATES = path.resolve(__dirname, "..", "templates");

const FILES = [
  ["01-需求简报.md", "01-需求简报.md"],
  ["02-文案层级表.md", "02-文案层级表.md"],
  ["02-待确认问题.md", "02-待确认问题.md"],
  ["03-创意方向.md", "03-创意方向.md"],
  ["04-初稿说明.md", "04-初稿说明.md"],
  ["05-反馈记录.md", "05-反馈记录.md"],
  ["06-交付检查表.md", "06-交付检查表.md"],
  ["素材台账.md", "素材台账.md"],
  ["项目README.md", "README.md"]
];

function parseArgs(argv) {
  const args = { project: "", name: "", size: "1024x1536", force: false };
  for (let i = 0; i < argv.length; i += 1) {
    const key = argv[i];
    if (key === "--project" || key === "-p") args.project = argv[++i] || "";
    else if (key === "--name" || key === "-n") args.name = argv[++i] || "";
    else if (key === "--size" || key === "-s") args.size = argv[++i] || args.size;
    else if (key === "--force" || key === "-f") args.force = true;
    else if (key === "--help" || key === "-h") args.help = true;
  }
  return args;
}

function parseSize(value) {
  const matched = /^(\d{2,5})\s*[x×*]\s*(\d{2,5})$/.exec(String(value).trim());
  if (!matched) throw new Error("尺寸格式无效：" + value + "（应为 宽x高，例如 1024x1536）");
  return { width: Number(matched[1]), height: Number(matched[2]) };
}

function safeName(value) {
  return String(value).replace(/[\\/:*?"<>|]/g, "-").trim() || "海报项目";
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) {
    console.log("用法：node new_project.js --project \"<目录>\" --name \"<项目名>\" --size <宽x高> [--force]");
    return;
  }
  if (!args.project) throw new Error("缺少 --project 参数");
  if (!args.name) throw new Error("缺少 --name 参数");

  const size = parseSize(args.size);
  const projectDir = path.resolve(args.project);
  const name = safeName(args.name);

  await fsp.mkdir(projectDir, { recursive: true });
  await fsp.mkdir(path.join(projectDir, "assets"), { recursive: true });
  await fsp.mkdir(path.join(projectDir, "exports"), { recursive: true });

  const written = [];
  const skipped = [];

  for (const entry of FILES) {
    const target = path.join(projectDir, entry[1]);
    if (fs.existsSync(target) && !args.force) {
      skipped.push(entry[1]);
      continue;
    }
    const source = path.join(TEMPLATES, entry[0]);
    let text = await fsp.readFile(source, "utf8");
    text = text.replace(/<项目名称>/g, name).replace(/<项目名>/g, name);
    await fsp.writeFile(target, text, "utf8");
    written.push(entry[1]);
  }

  const sourceFile = path.join(projectDir, name + "-组件源稿.poster.json");
  if (!fs.existsSync(sourceFile) || args.force) {
    const template = await fsp.readFile(path.join(TEMPLATES, "poster-source.template.json"), "utf8");
    const project = JSON.parse(template);
    project.name = name;
    project.canvas.width = size.width;
    project.canvas.height = size.height;
    project.meta.carrier = size.width + " × " + size.height + " px";
    project.elements.forEach(item => {
      if (item.type === "rect" && item.id === "background") {
        item.w = size.width;
        item.h = size.height;
      }
      if (item.type === "text" && item.id === "main-title") {
        item.w = Math.round(size.width * 0.86);
        item.x = Math.round(size.width * 0.07);
        item.fontSize = Math.round(size.width * 0.094);
        item.text = name;
      }
    });
    await fsp.writeFile(sourceFile, JSON.stringify(project, null, 2) + "\n", "utf8");
    written.push(path.basename(sourceFile));
  } else {
    skipped.push(path.basename(sourceFile));
  }

  console.log("项目已创建：" + projectDir);
  console.log("  新建文件 " + written.length + " 个：");
  for (const file of written) console.log("    + " + file);
  if (skipped.length) {
    console.log("  已存在未覆盖 " + skipped.length + " 个：");
    for (const file of skipped) console.log("    = " + file);
  }
  console.log("");
  console.log("下一步：");
  console.log("  1. 按 01-需求简报.md 确认目标与渠道；");
  console.log("  2. 在 02-文案层级表.md 核对文案与优先级；");
  console.log("  3. 启动编辑器：node scripts/editor/server.js --project \"" + projectDir + "\"");
}

main().catch(error => {
  console.error("创建项目失败：" + error.message);
  process.exit(1);
});

