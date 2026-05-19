# Compatibility Notes

This skill is runtime-neutral. Any AI tool can use it if it can:

1. Read Markdown instructions.
2. Run shell commands.
3. Ask the user for confirmation before writes.

Recommended entrypoints:

| Runtime | Entry file |
| --- | --- |
| Codex | `SKILL.md` |
| Claude Code | `CLAUDE.md` |
| Gemini CLI | `SKILL.md` and `AGENTS.md` |
| OpenClaw | `SKILL.md` and `AGENTS.md` |
| Hermes | `SKILL.md` and `AGENTS.md` |
| Generic agents | `SKILL.md` and `AGENTS.md` |

All adapters should delegate to:

```bash
python3 scripts/tracker.py
```

Do not fork separate Markdown instructions or implementations per runtime unless a runtime has a real discovery requirement. Keep schemas, validation, and Lark CLI calls centralized in the script.
