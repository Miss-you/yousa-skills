# yousa-skills

A curated collection of [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skills for enhancing AI-assisted workflows.

## Skills

| Skill | Description |
|-------|-------------|
| [tmux-dispatch](skills/tmux-dispatch/) | Orchestrate multiple Claude Code processes via tmux for parallel batch task processing. Supports work-stealing scheduling and built-in quality gates. |

## Installation

Copy the desired skill directory into your local Claude Code skills folder:

```bash
# Clone the repo
git clone https://github.com/Miss-you/yousa-skills.git

# Copy a skill to your Claude Code skills directory
cp -r yousa-skills/skills/tmux-dispatch ~/.claude/skills/tmux-dispatch
```

After copying, the skill will be available in your Claude Code sessions automatically.
