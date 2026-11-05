# Poster Master 文档

[English](en/README.md)

Poster Master 是一个 Agent 技能包。它把"做一张海报"拆成可执行、可检查、可归档的流程，
并附带一个零依赖的本地编辑器。

## 三分钟看懂

```text
需求 / 客户素材
   ↓  阶段 1 目标      受众、要什么效果、核心信息
   ↓  阶段 2 信息      文案层级 + 待确认问题
   ↓  阶段 3 方向      视觉关键词、配色、字体、主视觉
   ↓  阶段 4 初稿      至少一张可读的构图
   ↓  阶段 5 迭代      带决策的反馈记录
   ↓  阶段 6 交付      PNG / SVG / 分层 PSD + 交付检查
组件源稿（可再编辑） · 过程文档（可归档） · 交付报告
```

## 文档地图

| 文档 | 什么时候读 |
|---|---|
| [快速开始](getting-started.md) | 第一次用：一次完整的走查 |
| [安装](installation.md) | 装技能、装依赖、排错 |
| [工作流](workflow.md) | 想知道每一步到底做什么、卡在哪个门禁 |
| [编辑器](editor.md) | 要改源稿、导出多格式 |
| [常见问题](faq.md) | 遇到具体报错或不确定的行为 |
| [为什么这样设计](why-poster-master.md) | 想改技能包本身之前，先看边界 |

## 技能包内部文档

技能包自带 12 篇参考文档，供 Agent 在**选定路由之后**按需加载，不占用上下文：

| 参考文档 | 内容 |
|---|---|
| <code>references/six-stage-workflow.md</code> | 六阶段的完整程序、产物与模板映射 |
| <code>references/intake-and-brief.md</code> | 需求提问顺序、缺失事实 vs 设计假设 |
| <code>references/information-hierarchy.md</code> | 信息层级、P0/P1/P2 标注 |
| <code>references/audience-and-purpose.md</code> | 受众与投放目的如何决定视觉语言 |
| <code>references/creative-direction.md</code> | 方向单怎么写才算可执行 |
| <code>references/style-and-components.md</code> | 风格与组件的复用规则 |
| <code>references/formats-and-sizes.md</code> | 印刷 / 社交 / 数字屏的载体差异与尺寸 |
| <code>references/asset-intake.md</code> | 素材准入、授权状态、命名与台账 |
| <code>references/asset-processing.md</code> | 抠图、修图、扩展、生图的处理顺序 |
| <code>references/qr-and-brand-assets.md</code> | 二维码与品牌资产的红线 |
| <code>references/compliance-and-delivery.md</code> | 合规、字体授权、交付检查 |
| <code>references/editor-source-format.md</code> | 组件源稿格式与元素类型 |

## 一句话给 Agent

```text
$poster-master 用这个技能帮我做一张招新海报，素材在 ./assets，尺寸 A3，链接是 https://example.com/join
```

Agent 会自己读 <code>SKILL.md</code> 并选路由。你不需要记文档。
