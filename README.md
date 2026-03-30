# yousa-skills

A curated collection of [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skills for enhancing AI-assisted workflows.

## Skills

| Skill | Description |
|-------|-------------|
| [explaining-completed-work](skills/explaining-completed-work/) | Explain finished work with a Feynman-style walkthrough covering what changed, how it worked, why it was chosen, and where the boundaries are. |
| [tmux-dispatch](skills/tmux-dispatch/) | Orchestrate multiple Claude Code processes via tmux for parallel batch task processing. Supports work-stealing scheduling and built-in quality gates. |
| [social-strategist](skills/social-strategist/) | 首席社交策略顾问：分析对话记录/聊天截图中的潜台词、情绪和权力动态，提供多维度回复策略（高情商/设立边界/幽默/直击痛点）。 |

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
```

After copying, the skill will be available in your Claude Code sessions automatically.
