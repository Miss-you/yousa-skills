---
name: aligning-new-interface-fields
description: Use when an interface is being added or changed and the spec/design is settled but implementation has not started — naming an RPC method, its route alias, req/rsp message names, or choosing the name and type of any request/response param. Triggers on new proto/API endpoint, added fields on an existing message, or picking a type for an ID, status, reason, or enum value. 触发词：新增接口、接口变更、定义 proto、加字段、接口对账、字段对齐、命名对齐。
---

# Aligning New Interface Fields

## Overview

**新字段不是发明出来的，是对齐出来的。**

功能决定接口该有哪些字段；**既有代码决定这些字段叫什么、是什么类型**。跳过第二步，服务里就会长出 `orderId` 和 `order_id` 两种写法、`buyerId` 在 A proto 是 `int64` 在 B proto 是 `string`、明明有 `reason` 词表却又造一个 `code`。每一处单看都无害，攒够十个接口就没人敢动了。

这个 skill 是 **spec 定稿 → 写代码之间的一道闸口**。

## When to Use

**必须用：**
- 新增 RPC / HTTP endpoint / proto message
- 给既有 message 加字段（变更同样会引入不一致）
- 给既有接口改字段名或类型

**时机：** 功能语义已经想清楚、初版接口已经拟出来 **之后**，动手写代码 **之前**。太早做没有对齐对象，太晚做要返工 proto + 生成代码 + 调用方。

**不用：** 纯内部函数签名、不进 proto/API 契约的临时结构体。

## 顺序（不可颠倒）

1. **先按功能定稿初版** —— 想清楚要哪些字段、表达什么语义。这一步不要被既有命名绑住手脚。
2. **再对照局部代码对齐** —— 逐项检查初版的每个名字和类型，改成与既有一致。

先对齐再想功能，会把功能削足适履塞进旧结构。先想功能不对齐，就是本 skill 要防的那件事。

## 必须产出：对账表

**这一步的产物是一张表，不是"我看过了"。** 表填不出来 = 对账没做。

| 对象 | 初版 | 既有先例（file:line） | 定稿 | 说明 |
|---|---|---|---|---|
| RPC 名 | `OrderBatchConvertIds` | `OrderBatchGetSummaryByIds` order.proto:38 | `OrderBatchGetStatusByIds` | 本 proto 无 Convert 动词，范式是 Get...By... |
| alias | `/order/convertids` | `/order/batchgetsummarybyids` :39 | `/order/batchgetstatusbyids` | 全小写无分隔，跟方法名走 |
| req 消息 | — | `OrderBatchGetSummaryByIdsReq` :154 | `OrderBatchGetStatusByIdsReq` | 方法名 + Req |
| `orderIds` | `repeated string` | 同上 :155 | 不变 | — |
| `buyerId` | `int64` | `OrderSummary.buyerId` :121 | 不变 | 注意另一个服务的 proto 里同名字段为 string，需注释消歧 |
| `reason` | `code`（新造） | `ItemUnavailable.reason` catalog.proto:402 | `reason` | 词表已存在，不新造 |

**硬性要求：每一行的"既有先例"列必须是 `file:line`，或显式写「无先例」并说明为何必须新造。** 留空、写"参考了类似接口"、写"符合惯例"都不算。

## 五个对齐轴

### 1. 方法名

枚举同 service 的全部 RPC，归纳范式再命名。

```bash
grep -n "  rpc " proto/<svc>.proto
```

看动词集合（`Get` / `Check` / `Build` / `Sync`）、看 `Batch` 放在哪、看 `By<键>` 后缀怎么用。**你的新方法不该引入这个集合里没有的动词。**

### 2. alias / 路由路径

```bash
grep -nE "google.api.http|trpc.alias" proto/<svc>.proto
```

（按框架换成对应的路由别名选项，如 `google.api.http`、`trpc.alias`。）看大小写（通常全小写无分隔）、看前缀分段、看有没有例外。alias 常被当作方法名的机械小写，但**必须实际验证**——服务里往往有历史遗留的不同前缀。

### 3. req / rsp 消息名

看后缀范式（`Req`/`Rsp` vs `Request`/`Response`）、看是否存在多个 RPC **共享同一个 rsp** 的情况（共享时 rsp 名不带 `By<键>`）。

### 4. 字段名：同义词收敛 + 同名异型排查

**同义词收敛** —— 同一个概念在仓库里可能已有两种写法，找出区分规则再选：

```bash
grep -rn "string orderId\|string order_id" proto/*.proto
```

（例：一种写法用于请求键/回显，另一种用于镜像上游字段的数据模型。）

**同名异型排查（最容易漏，后果最重）** —— 拿字段名去 grep **全部** proto，不只是目标文件：

```bash
grep -rn "buyerId" proto/*.proto
```

同名不同型（`int64` vs `string`）说明跨域语义不同。此时**不要盲目跟随任一方**：确认你的字段属于哪个域，选对应类型，并在注释里点明与另一个同名字段的区别。

### 5. 取值词表：先查再造

**造任何 enum / status / reason / type 字符串之前**，先搜服务里有没有表达同一个轴的既有词表。

词表不写在字段名里，而是藏在**注释里的 `取值=含义` 枚举**中，所以要按这个形态搜：

```bash
grep -rnE "//.*[a-z_]+=[^ ]+ +[a-z_]+=" proto/*.proto
```

搜字段名（`grep reason`）是找不到词表的，只会命中一堆同名普通字段。必须专门按取值形态搜一次。

## Quick Reference

| 检查 | 命令 | 找什么 |
|---|---|---|
| 方法名范式 | `grep -n "  rpc " <svc>.proto` | 动词集合、Batch 位置、By 后缀 |
| alias 范式 | `grep -nE "google.api.http\|trpc.alias" <svc>.proto` | 大小写、前缀分段、例外 |
| 同义词 | `grep -rn "string <概念A>\|string <概念B>" *.proto` | 两种写法的区分规则 |
| 同名异型 | `grep -rn "<字段名>" *.proto` | 跨 proto 的类型冲突 |
| 既有词表 | `grep -rnE "//.*[a-z_]+=[^ ]+ +[a-z_]+=" *.proto` | 注释里的 `取值=含义` 枚举 |

## Common Mistakes

| 错误 | 后果 | 正确做法 |
|---|---|---|
| 只 grep 目标 proto | 漏掉跨 proto 的同名异型 | 全 proto 目录 grep 字段名 |
| 只对齐字段，不对齐方法名/alias | 接口名成为服务里的异类 | 五个轴逐个过 |
| 造新词表前不搜既有词表 | 同一语义两套词汇并存 | 搜注释里的取值说明 |
| 发现同名异型就跟着改类型 | 把另一个域的语义带进来 | 确认自己属于哪个域，加消歧注释 |
| 用"参考了类似接口"代替 file:line | 无法验证，等于没查 | 每行必须有可点击的 file:line |
| 对齐后不写消歧注释 | 下一个人重新踩同一个坑 | 冲突处在 proto 注释里点明 |

## 你可能跳过了对账的信号

- 你能说出新字段叫什么，但说不出它对齐的是哪一行代码
- 对账表里出现空的"既有先例"列
- 你为某个状态/原因/类型想了一个新词，但没搜过服务里已有什么词
- 你只看了要改的那个 proto 文件

**出现任意一条：回到五个对齐轴重跑一遍。**
