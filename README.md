# yousa-skills

A curated collection of [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skills for enhancing AI-assisted workflows.

## Skills

| Skill | Description |
|-------|-------------|
| [tmux-dispatch](skills/tmux-dispatch/) | Orchestrate multiple Claude Code processes via tmux for parallel batch task processing. Supports work-stealing scheduling and built-in quality gates. |
| [social-strategist](skills/social-strategist/) | 首席社交策略顾问：分析对话记录/聊天截图中的潜台词、情绪和权力动态，提供多维度回复策略（高情商/设立边界/幽默/直击痛点）。 |
| [contribute-skill](skills/contribute-skill/) | 将 skill 或 skill 目录提交到 yousa-skills 项目：自动复制文件、更新 README、git commit 并创建 PR。 |

## Installation

Copy the desired skill directory into your local Claude Code skills folder:

```bash
# Clone the repo
git clone https://github.com/Miss-you/yousa-skills.git

# Copy a skill to your Claude Code skills directory
cp -r yousa-skills/skills/<skill-name> ~/.claude/skills/<skill-name>

# Examples:
cp -r yousa-skills/skills/tmux-dispatch ~/.claude/skills/tmux-dispatch
cp -r yousa-skills/skills/social-strategist ~/.claude/skills/social-strategist
cp -r yousa-skills/skills/contribute-skill ~/.claude/skills/contribute-skill
```

After copying, the skill will be available in your Claude Code sessions automatically.
