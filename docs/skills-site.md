# Skills 目录维护

公开站点位于 [skills.yousali.com](https://skills.yousali.com/)。目录和双语 README 共用 `docs/readme/skills.json`。每项公开 skill 自动获得 `/skills/<name>/`、`/en/skills/<name>/` 和两种语言的 `?skill=<name>` 分享入口。首页列出全部简介，可直接复制安装提示或下载对应 ZIP。搜索同时匹配名称和中英文简介。

## 首页布局

- 浏览时直接读每行的名称和简介。目录默认展开全部条目，标题链接到详情。
- 搜索时就地缩小结果范围，显示命中数，清除后恢复全部列表。
- 安装时可直接复制该项的 Agent 安装提示，或下载仅包含该 Skill 的 ZIP。手机把操作放在对应简介下方，触控区至少 44 px 高。

顶栏、背景和正文宽度沿用 YDD 主页，列表分隔线参考 YDD 知识库，主操作样式参考 KOSPI Monitor。

## 新增或修改 Skill

1. 按仓库的 `contribute-skill` 流程整理 `skills/<name>/`。目录、`SKILL.md` 的 `name` 和公开链接使用同一个 kebab-case 名称。把该 skill 用到的文件一同提交。
2. 在 `docs/readme/skills.json` 新增或更新一条记录，提供简洁的中英文用途说明。现有名称是分享链接的一部分，改名时应一起处理旧链接。
3. 运行 `python3 scripts/render_readmes.py` 并提交改动。再运行下方预览命令，检查两种语言、安装提示和 ZIP 内容。
4. 合并到 `main` 后，在托管 Mac 上更新发布。详情页和安装指令链接到 GitHub 的 `main`。

只在本工作区使用的第三方 skill 通过本地发现目录和本地索引登记。工作区路径、别名和凭据保存在 Git 排除的本地配置里。

## 本地预览

```sh
preview=$(mktemp -d)
python3 scripts/render_readmes.py --check
python3 scripts/build_skill_site.py --output "$preview"
python3 scripts/serve_skill_site.py --directory "$preview" --port 8767
```

访问 `http://127.0.0.1:8767/`。生成目录包含 HTML、CSS、JavaScript 和 Skill ZIP。构建检查清单与 `skills/` 的一一对应关系。ZIP 由 Git 当前提交生成，保留每个 Skill 的完整目录和伴随文件。本地未提交的修改、未跟踪文件和工作区覆盖层不会进入 ZIP。构建需要 Git 和 Python 3.10 或更新版本。

## 在托管 Mac 发布

从更新到 `main` 的工作树执行。

```sh
site_home="$HOME/Library/Application Support/Yousa Skills"
python3 scripts/render_readmes.py --check
python3 scripts/build_skill_site.py --publish-to "$site_home"
curl -fsS https://skills.yousali.com/ >/dev/null
```

发布命令生成新的 `releases/site-…`，构建成功后原子切换 `current`。服务即时读取新版本。之前的版本保留在 `releases/`，可将 `current` 原子切回已知可用的版本。定期清理确认已过期的旧版本。

### 服务和自启

本机运行两个 macOS LaunchAgent。它们有 `RunAtLoad` 与 `KeepAlive`，在登录时启动并在进程退出后重启。

- `com.yousali.skills` 使用 Python 启动静态服务，监听 `127.0.0.1:8766`，只读取上述 `current` 目录。
- `com.yousali.skills-tunnel` 运行独立的 Cloudflare Tunnel。将 `skills.yousali.com` 路由至该回环端口，其余主机名返回 404。Tunnel 配置和凭据保存在本机应用目录，启动配置位于 `~/Library/LaunchAgents/`。

服务代码有改动时，更新本机运行副本并重启静态服务。

```sh
site_home="$HOME/Library/Application Support/Yousa Skills"
install -m 600 scripts/serve_skill_site.py "$site_home/serve_skill_site.py"
launchctl kickstart -k "gui/$(id -u)/com.yousali.skills"
curl -fsSL 'https://skills.yousali.com/?skill=zh-proofreading' >/dev/null
```

用 `launchctl print "gui/$(id -u)/com.yousali.skills"` 和 `launchctl print "gui/$(id -u)/com.yousali.skills-tunnel"` 分别检查两个进程。Mac 冷启动后需先解锁 FileVault 并登录，站点依赖这台机器联网且保持唤醒。
