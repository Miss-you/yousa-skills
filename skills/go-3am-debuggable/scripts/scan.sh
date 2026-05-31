#!/usr/bin/env bash
# scan.sh — 启发式扫描 Go 代码中的"3 点钟难调试"反模式
#
# 用法:
#   bash scan.sh <go-dir-or-file>        # 扫描目录或单文件
#   bash scan.sh                          # 扫描当前目录
#
# 输出: 命中行 + 提示
# 退出码: 始终 0，结果仅供参考，不作为 gate
#
# 检测的反模式（T1=必清，T2=应修；按 Tier 排序输出）:
#   A. [T1] 测试间接函数变量    var xxxFunc = pkg.RealFn
#   B. [T1] 函数类型参数        func foo(... cb func() T ...)
#   C. [T1] 嵌套匿名 func       func(){... func(){...} ...}  ← 闭包套闭包直接信号
#   D. [T2] 单 caller helper    包内函数只有 1 处调用点
#   E. [T2] 函数内局部闭包变量  xxx := func(...) {...}
#         ※ 同一函数内 ≥2 处 → 必须排查闭包链调用（升级为 T1）
#   F. [Inspect] 异步边界检查点  go func / trpc.Go / errgroup.Go
#   G. [Inspect] context.Background/TODO  切断 trace/cancel/deadline 的线索

set -u

TARGET="${1:-.}"
if [ ! -e "$TARGET" ]; then
    echo "usage: $0 <go-dir-or-file>" >&2
    exit 2
fi

if command -v rg >/dev/null 2>&1; then
    GREP() { rg -n --type go --no-heading --color never "$@"; }
    GREP_MULTI() { rg -n --type go --no-heading --color never --multiline --multiline-dotall "$@"; }
else
    GREP() {
        local pattern="$1"; shift
        find "${1:-.}" -type f -name '*.go' -print0 2>/dev/null \
            | xargs -0 grep -nE "$pattern" 2>/dev/null
    }
    GREP_MULTI() { GREP "$@"; }
fi

bold()   { printf '\033[1m%s\033[0m\n' "$*"; }
yellow() { printf '\033[33m%s\033[0m\n' "$*"; }
cyan()   { printf '\033[36m%s\033[0m\n' "$*"; }
dim()    { printf '\033[2m%s\033[0m\n' "$*"; }

HITS_TOTAL=0
section() {
    bold ""
    bold "── $1 ──"
    dim "  $2"
}
tally() {
    local n="$1"
    HITS_TOTAL=$((HITS_TOTAL + n))
    if [ "$n" -eq 0 ]; then dim "  ✓ 未发现"; else dim "  共 $n 处命中"; fi
}

# ─── A. 测试间接函数变量 ──────────────────────────────────────────
section "A. 测试间接函数变量 (T1)" "形如 var xxxFunc = pkg.RealFn — mockey 可以直接 patch 原函数"

A_RAW=$(GREP '^\s*(var\s+)?[a-z][a-zA-Z0-9_]*(Func|Fn)\s*=\s*[a-zA-Z_][a-zA-Z0-9_.]*\s*$' "$TARGET" 2>/dev/null | grep -v '_test\.go:' || true)
A_COUNT=0
if [ -n "$A_RAW" ]; then
    echo "$A_RAW" | while IFS= read -r line; do yellow "  $line"; done
    A_COUNT=$(echo "$A_RAW" | grep -c '' || true)
fi
tally "$A_COUNT"

# ─── B. 函数类型参数 ──────────────────────────────────────────────
section "B. 函数类型参数 (T1, callback inversion)" "形如 func foo(..., cb func() T) — 优先传数据；大小写函数和 method 都检查"

B_RAW=$(GREP 'func\s+(\([^)]+\)\s+)?[a-zA-Z_][a-zA-Z0-9_]*\s*\([^)]*\b[a-zA-Z_][a-zA-Z0-9_]*\s+func\s*\(' "$TARGET" 2>/dev/null | grep -v '_test\.go:' || true)
B_COUNT=0
if [ -n "$B_RAW" ]; then
    echo "$B_RAW" | while IFS= read -r line; do yellow "  $line"; done
    B_COUNT=$(echo "$B_RAW" | grep -c '' || true)
fi
tally "$B_COUNT"

# ─── C. 嵌套匿名 func ─────────────────────────────────────────────
section "C. 嵌套匿名 func (T1, 闭包套闭包)" "panic 栈会显示 func1.func2 — 凌晨调试天书；属于必清反模式"

C_RAW=$(GREP_MULTI 'func\s*\([^)]*\)\s*[^{]{0,40}\{\s*[^}]{0,300}\bfunc\s*\(' "$TARGET" 2>/dev/null | grep -v '_test\.go:' | head -30 || true)
C_COUNT=0
if [ -n "$C_RAW" ]; then
    echo "$C_RAW" | while IFS= read -r line; do yellow "  $line"; done
    C_COUNT=$(echo "$C_RAW" | grep -c '' || true)
fi
tally "$C_COUNT"

# ─── D. 单 caller helper ──────────────────────────────────────────
section "D. 单 caller helper (T2)" "包内函数仅 1 个调用点 — 考虑 inline，等真有第二个 caller 再抽"

D_COUNT=0
if [ -d "$TARGET" ]; then
    if command -v rg >/dev/null 2>&1; then
        FUNCS=$(rg --type go --no-heading --no-filename '^func\s+(\([^)]+\)\s+)?[a-z][a-zA-Z0-9_]+\s*\(' "$TARGET" 2>/dev/null \
            | sed -E 's/^func[[:space:]]+(\([^)]+\)[[:space:]]+)?([a-z][a-zA-Z0-9_]+)[[:space:]]*\(.*/\2/' | sort -u)
    else
        FUNCS=$(find "$TARGET" -name '*.go' -exec grep -hE '^func\s+(\([^)]+\)\s+)?[a-z][a-zA-Z0-9_]+\s*\(' {} \; 2>/dev/null \
            | sed -E 's/^func[[:space:]]+(\([^)]+\)[[:space:]]+)?([a-z][a-zA-Z0-9_]+).*$/\2/' | sort -u)
    fi
    D_SHOWN=0
    for fn in $FUNCS; do
        case "$fn" in
            init|main|new*|TestMain) continue ;;
        esac
        N=$(GREP "\\b${fn}\\(" "$TARGET" 2>/dev/null | grep -v '_test\.go:' | grep -c '' || true)
        # 2 = 声明那行 + 1 个 caller
        if [ "$N" = "2" ]; then
            DECL=$(GREP "^func[[:space:]]+(\\([^)]+\\)[[:space:]]+)?${fn}[[:space:]]*\\(" "$TARGET" 2>/dev/null | head -1 || true)
            if [ -n "$DECL" ] && [ "$D_SHOWN" -lt 30 ]; then
                yellow "  $DECL"
                D_SHOWN=$((D_SHOWN + 1))
            fi
            D_COUNT=$((D_COUNT + 1))
        fi
    done
fi
tally "$D_COUNT"

# ─── E. 函数内局部闭包变量 ─────────────────────────────────────────
section "E. 函数内局部闭包变量 (T2，可升级 T1)" "形如 xxx := func(...) — 失名为 .func1/.func2；扫描器只做文件级粗略提示，同函数互调才升级 T1。修法顺序：统一控制流 → 提具名函数 → 抽 struct method"

E_RAW=$(GREP '^\s+[a-zA-Z_][a-zA-Z0-9_]*\s*:=\s*func\s*\(' "$TARGET" 2>/dev/null | grep -v '_test\.go:' || true)
E_COUNT=0
if [ -n "$E_RAW" ]; then
    echo "$E_RAW" | while IFS= read -r line; do yellow "  $line"; done
    E_COUNT=$(echo "$E_RAW" | grep -c '' || true)
    # 同一 file 内若 ≥2 处局部闭包变量，粗略提示人工检查；真正升级条件是同一函数内 closure 互调。
    SUSPECT_FILES=$(echo "$E_RAW" | awk -F: '{print $1}' | sort | uniq -c | awk '$1>=2 {print $2}')
    if [ -n "$SUSPECT_FILES" ]; then
        bold "  ⚠  以下文件含 ≥2 处局部闭包变量，需人工核查是否在同一函数形成闭包链（互调才升级为 T1 #1）:"
        echo "$SUSPECT_FILES" | while IFS= read -r f; do yellow "    $f"; done
    fi
fi
tally "$E_COUNT"

# ─── F. 异步边界检查点 ───────────────────────────────────────────
section "F. 异步边界检查点 (Inspect)" "这些不是自动违规；用于人工确认 caller 是否看得见异步边界，以及 error/panic/cancel/lifecycle 是否有归属"

F_RAW=$(GREP '\bgo\s+func\b|trpc\.Go\b|errgroup\.Go\b|\.Go\s*\(' "$TARGET" 2>/dev/null | grep -v '_test\.go:' | head -30 || true)
if [ -n "$F_RAW" ]; then
    echo "$F_RAW" | while IFS= read -r line; do yellow "  $line"; done
    F_COUNT=$(echo "$F_RAW" | grep -c '' || true)
    dim "  共 $F_COUNT 处检查点（不计入命中总数）"
else
    dim "  ✓ 未发现检查点"
fi

# ─── G. context.Background/TODO 线索 ─────────────────────────────
section "G. context.Background/TODO near async (Inspect)" "request-scoped 异步路径里出现 Background/TODO 时，确认是否故意 detach，并有 owner/timeout"

G_RAW=$(GREP 'context\.(Background|TODO)\s*\(' "$TARGET" 2>/dev/null | grep -v '_test\.go:' | head -30 || true)
if [ -n "$G_RAW" ]; then
    echo "$G_RAW" | while IFS= read -r line; do yellow "  $line"; done
    G_COUNT=$(echo "$G_RAW" | grep -c '' || true)
    dim "  共 $G_COUNT 处检查点（不计入命中总数）"
else
    dim "  ✓ 未发现检查点"
fi

# ─── 总结 ────────────────────────────────────────────────────────
bold ""
bold "═══ 总结 ═══"
if [ "$HITS_TOTAL" -eq 0 ]; then
    cyan "  ✓ 所有检测均未命中"
else
    cyan "  共 $HITS_TOTAL 处可疑模式。修复顺序: T1（A/B/C）必清 → T2（D/E）应清；F/G 为人工检查点。"
    echo ""
    echo "  对 T1 命中：问'修法成本'，不问'是否要修'。"
    echo "  对 T2 命中：问三个问题——"
    echo "    1. 这层间接的真实目的是什么？(mock / 延迟 / 复用 / 还是只是'灵活')"
    echo "    2. inline / 命名 / 去间接 后会损失什么？"
    echo "    3. panic 栈帧名字会是什么？如果是 func1.func2 → 自动升级为 T1。"
fi

exit 0
