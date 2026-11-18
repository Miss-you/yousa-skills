# 例子（虚构场景，改编自真实重构）

每个例子对应 SKILL.md mindset 表的编号。场景和命名都是示意，只保留代码形状和判断过程。

## E1 · 主函数直线 / 数据不往返（#1 #2 #3）

内容服务里统计一条 feed 的赞数和踩数的函数（`item_vote.go`）。`voters` 来自投票记录表，赞踩明细在另一个异步同步的表里；`voters` 非空却统计出 0,0，说明明细还没同步过来，这时用 `fallbackItemVoteCnt` 按 itemID 哈希和两个经验比例估一个保底值。

**Before**：缓存未命中路径算出数字后拼成字符串，掉出 if 块，和命中路径共用一个 `Sscanf` 出口。读者要分别推两遍 `val` 从哪来，还要想「`up+down > 0` 在未命中路径什么时候为假」。

```go
val, err := rdb.Get(ctx, key).Result()
if err != nil {
    if up, down, err = countItemVotes(ctx, voters); err != nil {
        return fallbackItemVoteCnt(itemID, int32(len(voters)))
    }
    if up+down == 0 {
        up, down = fallbackItemVoteCnt(itemID, int32(len(voters)))
    }
    val = fmt.Sprintf("%d,%d", up, down)          // 拼出去
    go func() { /* SETEX val */ }()
}
if _, err = fmt.Sscanf(val, "%d,%d", &up, &down); err == nil && up+down > 0 {  // 再解析回来
    return up, down
}
return fallbackItemVoteCnt(itemID, int32(len(voters)))
```

**After**：三步直线；解析收进一个返回 `(up, down, ok)` 的 helper，调用方不知道值的格式和 0,0 约定。

```go
// 1. 读缓存
if up, down, ok := loadItemVoteCache(ctx, key); ok {
    return up, down
}
// 2. 现算；查不到就给保底值
up, down, err := countItemVotes(ctx, voters)
if err != nil {
    return fallbackItemVoteCnt(itemID, int32(len(voters)))
}
if up+down == 0 {
    up, down = fallbackItemVoteCnt(itemID, int32(len(voters)))
}
// 3. 异步回写
go func() { /* SETEX */ }()
return up, down
```

```go
// loadItemVoteCache 读缓存，值格式 "赞数,踩数"；未命中、格式不对、或 0,0 都按未命中处理
func loadItemVoteCache(ctx context.Context, key string) (up, down int32, ok bool)
```

汇报口径：「读者原来要分别推两条路径的 `val` 来源 → 现在主函数只有三步，格式细节在 helper 里」。

## E2 · helper 藏住了什么（#3、门槛）

同一个功能的第一版放在 `services/` 层，篇幅不小：`batchGetItemVoteCnt` → `getItemVoteCntCache`（MGET）/ `countItemVotes` / `setItemVoteCntCache`（pipeline），外加 `isItemWithoutVoteExt`、`buildItemVoteExt` 两个三行函数。调用方得先调批量函数拿 map，再逐条查 map，再调 build。

第二版只剩一个深接口：

```go
up, down := feed.GetItemVoteCnt(ctx, item.Id, item.GetVoters())
```

缓存、统计、保底全部在里面。判断标准：第一版的每个小函数接口和实现一样宽（`isItemWithoutVoteExt` 就是一行布尔表达式），读者仍要逐个跳进去；第二版一个函数藏住了三件事。

## E3 · 不同的要看得出来（#4）

E1 的 After 里 `err != nil` 和 `up+down == 0` 两个分支都走保底，看起来能合并。故意分开：前者不写缓存（下个请求重试），后者把保底值写进缓存（避免每次遍历投票记录）。合并了差异就藏起来了。函数 doc 注释里有一句说明这个差异。

## E4 · 按变更原因抽取（#6）

`list.go` 的 `LoadListByKind` 里，三处一模一样的赋值：

```go
list.Members[i].MemberType = pb.MEMBER_TYPE_VERIFIED
list.Members[i].BadgeId = primaryBadgeId
// … 创建者再来一遍 … 协作者再来一遍
```

「给成员挂上认证徽章」这件事如果要多设一个字段，三处必须一起改——同一个变更原因，抽：

```go
func bindBadge(m *pb.Member, badgeId int64) {
    m.MemberType = pb.MEMBER_TYPE_VERIFIED
    m.BadgeId = badgeId
}
```

反例：同文件里「收集 userId 列表再去重」的循环在多个函数里都长得像，但各自的过滤条件会独立演化，不抽。

## E5 · 名字代替魔数（#7）

`item_vote.go` `countItemVotes`：

```go
switch v.GetVote() {
case 1:
    up++
case 2:
    down++
}
```

先 grep：赞 / 踩已有常量（如 `VoteUp` / `VoteDown`），直接用，注释里的「1赞 2踩」可去掉。如果 grep 不到，不新加常量——在可读性 pass 里新加一个只用一次的常量是另一种噪音。

## E6 · 反例：一次改九处

对 E1 的 Before 做无 skill 的可读性 review，产出 9 项改动：拆命中/未命中、抽 `parseItemVoteCnt`、抽 `setItemVoteCntCacheAsync`、加格式常量、加两个比例常量、拆哈希算式成两行、换投票常量、加 `voterCount` 局部变量、加 redis.Nil 注释。每项单看都有道理，合起来几乎整个文件重写，reviewer 要从头看。

按门槛筛：#1 拆路径（成本最高）、#7 投票常量（零风险、有现成常量）两处即可；格式常量和比例常量是「给一个数字起名字」，算式拆行是口味，redis.Nil 是行为，都不在这轮。
