---
name: kospi-mobile-web-design
description: Use when designing or editing KOSPI Monitor pages for phones, including mobile typography, responsive layouts, touch controls, daily reports, and shareable long images.
---

# KOSPI Monitor 手机页面设计

## 适用范围与依赖

设计或修改 KOSPI Monitor 的 `public/` 手机页面、`src/reporter/` 生成的移动版 HTML 或分享长图时使用。先在 **kospi-monitor 仓库根目录**阅读 `AGENTS.md` §7 和 `docs/reference/dashboard-design-system.md`；其中的颜色语义、数据诚实性、图表与交互契约优先于本 skill。下文的相对文件路径也都以该仓库根目录为准。桌面布局另见 `$kospi-desktop-dashboard-design`。

## 工作步骤

1. 确认页面用途、市场日、数据来源和状态字段；逐项找出必须在首屏出现的关键值。
2. 按下述阅读顺序重排内容，再选择字体、换行、触控目标和明细展开方式。
3. 在 320、390 和 760 CSS px 检查真实内容与缺失、估算、过期状态；如涉及分享长图，同时对账 HTML 与长图的数字。

## 阅读顺序

手机首屏先回答：看的是哪一天、数据是否新鲜、两只股票或三方资金的关键值是多少。按「状态 → 核心指标 → 趋势或近期对比 → 可展开明细 → 数据口径」排布。回购日报的整体进度从计划开始累计，近期 15 个交易日只是明细窗口；两个时间范围的标签必须分清。

## 字体与触控

| 内容           | 建议 CSS 字号                |
| -------------- | ---------------------------- |
| 页面标题       | 22–26 px                     |
| 区域标题       | 18–20 px                     |
| 核心数值       | 32–40 px，较长数值允许换行   |
| 正文、表格数值 | 15–16 px，行高约 1.5         |
| 状态、次级说明 | 13–14 px；重要限制不缩成脚注 |

全站沿用系统无衬线字体；日期、ticker 和精确数值用系统等宽字体。优先通过布局换行解决拥挤，不靠缩字。按钮、链接与 `<summary>` 尽量留出 44–48 px 的可点高度、可见焦点和相邻间距；不要让颜色成为状态的唯一线索。

## 重排与验收

- 在 320、390 和 760 CSS px 检查：页面单向纵滚，无整页横向滚动、裁切或数值碰撞。图表与卡片改为单列；长表可改成逐日卡片或仅在表格自身横滚。
- 保留桌面端的状态、单位、精确值与检查器。较长的逐股明细可默认收起，但展开后全部可读且可用键盘操作。
- 分享用长图以约 390 CSS px 的阅读宽度排版，标明日期、新鲜度、估算口径和缺失值；核对它与 HTML 的关键数字一致。

参考：[WCAG 2.2 Reflow](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html)、[Target Size](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum)、[web.dev Responsive Design](https://web.dev/articles/responsive-web-design-basics)。

## 应用示例

回购日报在 390 CSS px 下，把两只股票的当日回购量和状态放在首屏；计划开始以来的累计进度另标时间范围，近 15 个交易日放入可展开明细。某天数据缺失时显示 `N/A` 和原因，不用 0 填充；分享长图沿用同一日期、单位和数值。

## 常见错误

- 用缩小字号或整页横向滚动容纳宽表；先改为单列、换行或仅让表格自身滚动。
- 把累计进度误标为近 15 日进度，或让长图省略数据新鲜度和估算说明。
- 只用颜色表达涨跌或状态，或将重要限制压成难读的脚注。
