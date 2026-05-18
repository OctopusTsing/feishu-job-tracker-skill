# OpenClaw Instructions

Use `SKILL.md` as the source of truth for the Feishu job tracker workflow. Use `scripts/tracker.py` for deterministic schema, status normalization, and Lark CLI calls.

OpenClaw API Caller integrations may call Feishu OpenAPI directly, but should keep the same field schema from `references/template-schema.json`.
