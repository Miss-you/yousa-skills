# Agent Team 编排骨架

用 Task 工具并行派发 subagent 即可执行（同一条消息内多个 Task 调用即并行；有专用 Workflow 编排工具时也可用它）。下述骨架在 72k 字 / 2h49min / 17 标签的真实圆桌转录上验证过：15 agent、约 22 分钟、产出通过 Critic 验收（6 项中 5 项满分）。

## 目录

1. 编排结构
2. 各阶段 agent prompt 要点
3. JSON Schema 定义
4. 已知坑

## 1. 编排结构

```
phase 分段梳理:  parallel( N 个 Reader(chunk_i) )        # N=4~8，按自然边界切
   ↓ barrier（聚类需要全量话题块——这是少数合理的 barrier）
phase 聚合:      agent( Cluster, 输入=全部话题块 JSON )
phase 联网补充:  parallel( 每议题一个 Research agent )    ┐
phase 引语与案例: agent(引语评选) + agent(案例汇总)        ┘ 三者并行
phase 合成:      agent( Writer, 输入=全部结构化素材, 直接 Write 成稿文件 )
phase 验收:      agent( Critic, Read 成稿 + Grep 转录回查 ) → 不过则 agent( 修订, Edit 定向改 )
return { 成稿路径, 议题列表, 审计得分 }
```

切分方法：先运行 `scripts/speaker_stats.py <转录.md>`（输出说话人字数分布、称呼-接答配对、混人嫌疑、时间戳→行号映射），再按轮次/休息时间戳的行号区间分 chunk，传给各 Reader `offset/limit` 读取，不要把转录原文塞进 prompt。

**主流程必须先向用户收集的输入**：转录文件路径、活动背景一句话（场合/嘉宾角色/参与者构成）、发布范围（对内学习版 or 对外发布版——决定嘉宾是否署名与结构选择）。

**数据流约定**：各 agent 通过 schema 返回 JSON 给主流程（编排器内存中传递）；不依赖中间文件。只有 Writer 例外——直接 Write 成稿到约定路径并返回路径，Critic/修订 agent 对同一路径 Read/Edit。chunk 的"内容提示"来自 speaker_stats.py 输出的时间戳地图 + 主流程对各段首尾 20 行的快速抽look——不要凭空编造提示。`depth` 判定标准：浅=背景/事实陈述，中=有判断有理由，深=有判断+mindset+被反复争论。

## 2. 各阶段 agent prompt 要点

每个 agent prompt 必须包含共享上下文块 CTX：活动背景、说话人身份考证结论、标签噪音警告（"以内容判断身份，不要轻信标签"）、匿名化规则。

- **Reader**：给 chunk 的行号区间 + 该段内容提示（如"含第一轮：资本视角、监管"）；强调"宁可块多而碎，后面会聚合；纯寒暄/组织事务跳过不出块"
- **Cluster**：强调"聚合成 3-5 个反复出现的争论点，不是话题罗列"；要求输出 aha 自检字段（每个议题最反直觉的一点是什么）
- **Research**：传入议题的 guest_core_view/mindset/angles + 建议搜索方向；要求中英文都搜、优先一手来源（公司工程博客/研究报告/从业者复盘）；"禁止编造来源——搜不到就少写"
- **Writer**：传结构化 JSON 素材而非原文；给出完整目标结构；写作标准三条：不平庸（删掉"AI 很重要"式废话）、内外分区、读者是没到场的聪明人
- **Critic**：六条标准逐项打分（见 quality-standards.md）；要求用 Grep 在转录里实际回查抽样引语，不许凭印象打分

## 3. JSON Schema 定义

Reader 输出（SEG_SCHEMA）：

```json
{ "blocks": [ {
    "topic": "话题名10字内", "time_range": "42:12-49:30", "depth": "浅|中|深",
    "guest_judgments": ["嘉宾判断，每条一句话，保留锐度"],
    "mindset": "思维模型，没有则空串",
    "stories": [{"teller":"嘉宾 或 角色化描述","story":"发生了什么","lesson":"为什么成/不成","timestamp":""}],
    "others_views": ["其他参与者有价值视角（角色化署名）"],
    "quote_candidates": [{"speaker":"","quote":"贴原文","timestamp":"","why":"为什么值得记"}]
} ], "density": "高|中|低" }
```

Cluster 输出（CLUSTER_SCHEMA）：

```json
{ "themes": [ {
    "title": "", "one_line": "这个议题在争什么/答什么", "depth_rank": 1,
    "guest_core_view": "", "mindset": "", "angles": ["多角度论点，含支撑细节"],
    "source_topics": [""], "search_query_hint": "联网补充的搜索方向"
} ], "aha_check": "每个议题最反直觉的点分别是什么" }
```

Research 输出（ENRICH_SCHEMA）：

```json
{ "theme": "", "practices": [{"claim":"","source":"","url":"","relation":"支持|补充|矛盾"}],
  "methodology": "综合会场观点+外部实践的完整方法论，200-400字" }
```

Critic 输出（AUDIT_SCHEMA）：

```json
{ "pass": true, "scores": {"nontrivial":5,"three_layer":5,"authenticity":5,"separation":5,"anonymity":5,"progression":4},
  "issues": [{"severity":"blocker|major|minor","where":"","fix":""}] }
```

## 4. 已知坑

- **说话人标签噪音是最大坑**：真实案例中一个标签混了 3 个人。不做阶段 0 直接跑，归属会系统性错误
- **barrier 只用一次**：聚类前。其余阶段全部 pipeline/并行，否则浪费 1/3 墙钟时间
- **Writer 的输入用结构化 JSON**，不要让它重读转录——会被原文带跑、丢失提炼层
- **Critic 必须给 Grep 工具回查引语**，否则它会"看起来合理就放过"，引语编造逃逸
- **引语精选宁缺毋滥**：超过 5 条就开始稀释；候选可以几十条，终选 ≤5
- **闲聊段也要扫**：真实案例中开场前 36 分钟的寒暄里藏了嘉宾背景和两个有效话题块
- **时间戳常为双格式**：前 1 小时 `MM:SS`、之后 `H:MM:SS`——解析正则必须两者兼容，否则后半场整体漏切（真实案例差点丢掉最后 49 分钟）
- **匿名化规则不要现编**：CTX 中的匿名化规则直接引用 minutes-sensitive-scan 技能的口径（参与者角色化、对外版嘉宾也匿名）
