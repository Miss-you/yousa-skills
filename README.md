# yousa-skills

A curated collection of [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skills for enhancing AI-assisted workflows.

## Skills

| Skill | Description |
|-------|-------------|
| [explaining-completed-work](skills/explaining-completed-work/) | Explain finished work with a Feynman-style walkthrough covering what changed, how it worked, why it was chosen, and where the boundaries are. |
| [tmux-dispatch](skills/tmux-dispatch/) | Orchestrate multiple Claude Code processes via tmux for parallel batch task processing. Supports work-stealing scheduling and built-in quality gates. |
| [social-strategist](skills/social-strategist/) | 首席社交策略顾问：分析对话记录/聊天截图中的潜台词、情绪和权力动态，提供多维度回复策略（高情商/设立边界/幽默/直击痛点）。 |
| [structural-integrity-scan](skills/structural-integrity-scan/) | Use when an article compares multiple entities in parallel and you suspect the comparison may be artificial, unequal, or evidence-driven by narrative rather than fact. |
| [two-mirror-examples](skills/two-mirror-examples/) | 双镜例证法：为文章论点寻找高洞见力的例子。产出远镜（跨越百年的组织级案例）和近镜（身边司空见惯但点破即顿悟的例子），核心是「先找机制，再找故事」。 |
| [cdp-page-to-md](skills/cdp-page-to-md/) | Fetch authenticated or JS-rendered web pages via Chrome CDP and convert them to clean Markdown files. |
| [zh-proofreading](skills/zh-proofreading/) | 中文校对扫描：逐段扫描中文文章的错别字、语病、标点和中英混排问题，输出分级修复清单。支持三阶段流程（初扫→二次核查→汇总）。 |
| [secret-scan](skills/secret-scan/) | Scan staged/changed files for leaked secrets (API keys, tokens, passwords, credentials) before git commit, push, or PR creation. |

## Installation

Copy the desired skill directory into your local Claude Code skills folder:

```bash
# Clone the repo
git clone https://github.com/Miss-you/yousa-skills.git

# Copy a skill to your Claude Code skills directory
cp -r yousa-skills/skills/<skill-name> ~/.claude/skills/<skill-name>

# Examples:
cp -r yousa-skills/skills/explaining-completed-work ~/.claude/skills/explaining-completed-work
cp -r yousa-skills/skills/tmux-dispatch ~/.claude/skills/tmux-dispatch
cp -r yousa-skills/skills/social-strategist ~/.claude/skills/social-strategist
cp -r yousa-skills/skills/structural-integrity-scan ~/.claude/skills/structural-integrity-scan
cp -r yousa-skills/skills/two-mirror-examples ~/.claude/skills/two-mirror-examples
cp -r yousa-skills/skills/cdp-page-to-md ~/.claude/skills/cdp-page-to-md
cp -r yousa-skills/skills/zh-proofreading ~/.claude/skills/zh-proofreading
cp -r yousa-skills/skills/secret-scan ~/.claude/skills/secret-scan
```

After copying, the skill will be available in your Claude Code sessions automatically.
