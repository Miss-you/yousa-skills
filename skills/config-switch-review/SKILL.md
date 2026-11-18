---
name: config-switch-review
description: Review-stage audit of runtime configuration added by a code change — feature flags, gray/canary switches, business config keys, env vars, YAML fields, config-center entries. Audits them from the point of view of whoever will actually set them (ops, PM, on-call), who has only the key names and one line of description, not the code. Builds the table of switch combinations a real operator would produce (nothing configured yet / all off / ALL ON / one-at-a-time rollout / 3am rollback), fills in what they would expect from the key names alone BEFORE reading the code, then diffs expectation against actual behavior. Catches switches that are secretly mutually exclusive, defaults that mean "fully on", names that don't predict behavior, sampling units that inflate a 1% ratio to 99%, and switches that can't be rolled back. Use during code review whenever a change adds or changes any runtime-configurable knob, and always before handing configuration instructions to ops.
---

# 配置开关的运维直觉审查

审查对象：本次改动新增或改动的**运行时可配项**——灰度开关、feature flag、业务配置 key、环境变量、YAML 字段、配置中心项。

审查视角不是「代码对不对」，是「**拿到这几个 key 的人会怎么配，配完会不会得到他以为的结果**」。配的人可能是运维、产品、值班同学，手上只有 key 名和一句说明，没有代码。

代码里自洽的状态机，在配置面板上经常是反直觉的。本 skill 只找这一类问题——不做通用 code review。

**跳过条件**：改动没引入任何运行时可配项。纯编译期常量、只在单测里改的值、部署脚本路径，都不算。

## 第一步：列清单

从本次 diff 里找出所有配置读取点，常见入口：`os.Getenv` / `viper.Get` / 配置结构体新字段 / `.yaml` 新增项 / 项目自己封装的开关读取函数。

| key | 值结构 | 未配置时 | 谁来配 | 生效时延 | 读取位置 |
|---|---|---|---|---|---|

「未配置时」这一列不要抄注释，要跟到函数实现里确认——**新开关复用既有读取函数时，缺省方向往往不是你要的那个**（见 C2）。

## 第二步：先写「运维以为会怎样」，再读代码

**顺序不能反。** 先只看 key 名 + 准备给运维的那句说明，把「预期」列填完；填完之后才去读代码填「实际」列。反过来做，你只会把代码逻辑抄两遍，一个问题都发现不了。

必填的组合行（N 个开关就这几类，不是 2^N 全排）：

| # | 组合 | 为什么必须有这行 |
|---|---|---|
| 1 | 全都还没建 key | 新环境、刚发版。这行的实际行为必须**严格等于改动前** |
| 2 | 全部 `0` | 运维理解的「关闭」 |
| 3 | **全部 `1`** | 新环境自测、联调环境的常态。**最容易暴雷的一行**，务必单独想清楚 |
| 4 | 按计划的放量顺序逐个打开 | 每一个中间态各写一行 |
| 5 | 半夜回滚：全部改回 `0` | 是否严格回到第 1/2 行 |
| 6 | 只开一个（每个开关各一行） | 单开是否有意义，还是静默无效 |

任何一行「预期 ≠ 实际」，就是一条 finding。

## 第三步：七条判定

### C1 全开是不是真全开（正交性）

把每个开关都打到最开，是不是每项能力都在生效？如果打开 A 会让 B **悄悄失效**，说明两件独立的事被塞进了同一个枚举的互斥状态里。

修法：拆成两个正交开关，不要做成三态枚举。判断依据是「这两件事在现实中会不会同时想要」——只要会，就必须能同时表达。

> 真实案例：消息下发出口从旧服务迁到新服务时，把「走旧出口 + 请求体对账」焊成一个 `shadow` 态。运维把四个 key 全配成 `{"mode":"on"}`（合理理解：全都打开），cutover 命中后所有用户进新出口，shadow 组为空，**对账静默消失**——放量期恰恰最需要盯请求体是否漂移。详见 [references/failure-modes.md](references/failure-modes.md)。

### C2 未配置是不是最保守的那个（缺省方向）

「key 还没建」必须等于「改动前的行为」。

重点查复用：新开关若复用了既有的开关读取函数，那个函数的缺省方向未必是你要的。存量业务开关的缺省常常是**全开**（为了给已上线功能做急停），迁移 / 新功能开关需要的恰好相反。

而且缺省错了是**静默**的：key 名打错一个字、新环境漏配、配置中心抖动返回空串——这三种在日志和监控上都表现为「开关看起来没配」，缺省若向开，就是 100% 流量一次性进入未验证路径。

> 真实案例：存量的 `flagOn` 未配置 = 全开，有多处存量调用依赖该语义不能改；迁移开关另起了 `migrationFlagOn`，共用同一份配置结构与命中判定，只反转缺省这一个语义。

### C3 名字能不能反推行为（命名）

把 key 名单独拿给一个没读过代码的人，他能不能说出 `=1` 时会发生什么？

高风险命名：
- 名词式能力名——`xxxCutover=1` 是「已经切了」还是「允许切」？
- 否定式——`disableX=1` 要在脑子里过两次否定。
- 缩写与内部黑话——`pushV2GrayExt` 里的 `Ext` 指什么，只有作者知道。

优先选「`1` = 这件事已经发生」的结果式表达。名字改不动时，至少让给运维的说明第一句就是「置 1 后：〈一句话结果〉」。

### C4 值域和采样单位符不符合直觉（语义）

- `percent` 是 0-100 还是 0-1？两种约定都常见，必须写死。
- 有没有隐藏档位（如 `mode` 除了 `off`/`on` 还有一档 `gray`，只有这一档才读 `percent` 和 `allowList`）？运维猜不到，说明里要列全枚举。
- **采样单位是什么**——这条最容易错也最难看出来。`percent` 是按用户采、按请求采、还是按批次采？

> 真实案例：`percent` 按 userId 逐个判，用在一条 500 人的群聊消息上，逻辑是「任一人命中就触发」，`percent=1` 的实际触发率 ≈ 99.3%。运维读到的是 1%。改成按这批接收者里的第一个人判定后，采样单位才与运维的理解一致。

### C5 配完看不看得见（可观测 + 时延）

- **生效时延写了没**：有本地缓存就写明「最长 X 秒生效」。否则运维配完立刻验、没反应、以为配错了，会反复改甚至改坏。
- **有没有一条日志 / 指标能回答「系统现在到底走哪条路」**：没有的话，运维只能靠「发一条试试」来确认配置有没有被读到。这条日志的级别要能在生产看到。
- 反过来，「未配置」是灰度未开启时的**正常稳态**，不能刷 Error——高频路径上会把真正的错误淹掉。

### C6 关掉能不能真回去（回滚）

把开关改回 `0`，是否严格恢复改动前的行为？留意不可逆副作用：以新格式写进库的数据、已经发出去的消息、建好的索引、已下发给客户端的字段。

回滚不完整不一定是缺陷，但**必须写进给运维的说明**：关掉之后还残留什么、要不要清、怎么清。

### C7 这几个 key 运维真的会分开配吗（粒度）

写出真实的放量步骤（第一天开什么、第三天开什么、灰度到多少再开下一个）：

- 任何一个步骤里**总是同开同关**的两个 key → 合并成一个。
- 一个 key 同时控着**风险等级差很远**的两件事（例如「低频通知」和「高频即时消息」）→ 拆开，运维需要把高风险的那件排到最后。

key 数量本身不是目标，「运维会不会在某一步只想动其中一个」才是判据。

## 输出

先给组合表（第二步的产物，保留预期与实际两列），再给发现表：

```
| # | 判定 | 严重度 | 问题 | 建议的配置形态 |
```

严重度：
- 🔴 会导致**静默**的错误配置——配了以为生效其实没生效，或缺省即全量切换
- 🟡 反直觉但有日志 / 报错兜底，运维能自己发现
- ⚪ 命名与文档问题

每条 finding 必须能指到具体代码行，并说清运维会怎么踩到它。指不出触发路径的不报。

最后写一段**给运维的配置说明草稿**：key 名、取值、配置顺序、生效时延、怎么确认生效、怎么回滚。这段本身就是审查结论的检验——写不清楚，说明开关设计还有问题，回到 C1~C7 找是哪一条。
