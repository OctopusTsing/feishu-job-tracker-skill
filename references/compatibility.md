# Compatibility Notes

This skill is runtime-neutral. Any AI tool can use it if it can:

1. Read Markdown instructions.
2. Run shell commands.
3. Ask the user for confirmation before writes.

Recommended adapters:

| Runtime | Entry file |
| --- | --- |
| Codex | `SKILL.md` |
| Claude Code | `CLAUDE.md` |
| Gemini CLI | `GEMINI.md` |
| OpenClaw | `OPENCLAW.md` |
| Hermes | `HERMES.md` |
| Generic agents | `AGENTS.md` |

All adapters should delegate to:

```bash
python3 scripts/tracker.py
```

Do not fork separate implementations per runtime. Keep schemas, validation, and Lark CLI calls centralized in the script.
