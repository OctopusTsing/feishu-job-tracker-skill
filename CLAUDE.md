# Claude Code Instructions

This file is a thin Claude Code entrypoint. The canonical workflow lives in `SKILL.md`; general agent rules live in `AGENTS.md`.

Read `SKILL.md` first, then run deterministic operations through:

```bash
python3 scripts/tracker.py <command>
```

Preview writes with `--dry-run` and confirm with the user before mutating Feishu/Lark Base records.
