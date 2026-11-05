# 安装

[English](en/installation.md) · [文档索引](README.md)

## 三种装法

### 1. Claude Code 插件市场

```text
/plugin marketplace add Ilovegood123isgad/Poster_master
/plugin install poster-master@poster-master
```

插件清单在 <code>.claude-plugin/marketplace.json</code>，技能本体在 <code>skills/poster-master/</code>。

### 2. Codex / 通用 Agent：下载解压

1. 下载 [poster-master-skill-v1.0.0.zip](../dist/poster-master-skill-v1.0.0.zip)。
2. 解压得到 <code>poster-master/</code> 目录。
3. 整个目录放进你的 skills 目录：
   - Windows：<code>%USERPROFILE%\.codex\skills\</code> 或 <code>%USERPROFILE%\.claude\skills\</code>
   - macOS / Linux：<code>~/.codex/skills/</code> 或 <code>~/.claude/skills/</code>

目录层级必须是这样（<code>SKILL.md</code> 在第一层）：

```text
skills/
└─ poster-master/
   ├─ SKILL.md
   ├─ agents/openai.yaml
   ├─ workflows/
   ├─ references/
   ├─ templates/
   └─ scripts/
```

### 3. Git 克隆

```bash
git clone https://github.com/Ilovegood123isgad/Poster_master.git
cp -R Poster_master/skills/poster-master ~/.codex/skills/
```

## 校验装好了

**不需要装依赖就能做的：**

```bash
node "<技能目录>/scripts/new_project.js" --help
node --check "<技能目录>/scripts/editor/server.js"
```

**需要 Python 依赖的脚本：**

```bash
pip install -r "<技能目录>/requirements.txt"
python "<技能目录>/scripts/check_delivery.py" --help
```

**校验技能结构：**

技能包里自带校验器不需要额外依赖：

```bash
python "<技能目录>/scripts/quick_validate.py" "<技能目录>"
```

## 依赖矩阵

| 能力 | 需要 | 备注 |
|---|---|---|
| 编辑器、项目脚手架 | Node.js 18+ | 纯标准库，零 npm 依赖 |
| 无头渲染、PSD 导出、交付检查 | Python 3.9+、Pillow | <code>pip install -r requirements.txt</code> |
| 二维码检测与重生成 | numpy、opencv-python | 随 requirements.txt 安装 |
| 抠图 | rembg（可选） | 首次运行会下载分割模型，体积大，按需装 |

## 环境变量

| 变量 | 作用 |
|---|---|
| <code>POSTER_EDITOR_PYTHON</code> | 指定编辑器调用 Python 的方式。默认 <code>python</code>。若你的机器上只有 <code>python3</code>，设成 <code>python3</code>。 |

## 常见安装问题

**Q：Windows 上 <code>python3</code> 一运行就退出、没有任何输出。**

这是 WindowsApps 的应用执行别名占位符，不是真正的 Python。直接改用 <code>python</code>，
或设置 <code>POSTER_EDITOR_PYTHON=python</code>。

**Q：编辑器提示端口被占用。**

换一个端口：<code>--port 41736</code>。默认 41735，只监听 127.0.0.1。

**Q：中文路径报错。**

技能包与项目目录都支持中文路径，但如果 Python 脚本报编码错误，先设
<code>set PYTHONUTF8=1</code>（PowerShell：<code>$env:PYTHONUTF8="1"</code>）。

**Q：编辑器里图片显示不出来。**

源稿里的 <code>src</code> 必须位于项目目录的 <code>assets/</code> 下，
且不能是绝对路径或外链——编辑器会直接拒绝这类源稿。

**Q：PSD 导出报错"图层尺寸不匹配"。**

每一层的位图必须和画布同尺寸。编辑器导出的层天然满足；
手工调用 <code>export_psd.py</code> 时，清单里没写宽高会自动按第一层推断。

## 升级

```bash
git -C ~/.codex/skills/poster-master pull
```

或者重新下载压缩包覆盖。技能包不写任何全局配置，升级不会影响其他技能。

## 卸载

删掉 skills 目录下的 <code>poster-master/</code> 即可。它不会在系统其他位置留下文件。
