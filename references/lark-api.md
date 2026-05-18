# Lark CLI And Feishu Base Notes

Use `lark-cli` as the execution layer when available. Prefer the modern `base` command group for record reads/searches:

```bash
lark-cli base +record-list --base-token <base_token> --table-id <table_id> --format json --as user
lark-cli base +record-search --base-token <base_token> --table-id <table_id> --json '{"keyword":"腾讯","search_fields":["公司"],"limit":20}' --format json --as user
```

The skill script still calls raw OpenAPI for operations that are stable there:

```bash
lark-cli api METHOD /open-apis/... --data '{"json":"body"}' --format json
```

Important concepts:

- A Feishu/Lark Base is called an `app` in older Bitable v1 APIs.
- `app_token` and `base_token` often refer to the token visible in `/base/<token>` or `/bitable/<token>` URLs.
- `table_id` identifies the data table inside the Base.
- Writing to an existing Base may require adding the app as a document application/collaborator with edit permission.

Common endpoints/commands used by the script:

| Operation | Endpoint |
| --- | --- |
| Create Base | `POST /open-apis/bitable/v1/apps` |
| Batch create tables | `POST /open-apis/bitable/v1/apps/{app_token}/tables/batch_create` |
| List tables | `GET /open-apis/bitable/v1/apps/{app_token}/tables` |
| List fields | `GET /open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields` |
| Create field | `POST /open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields` |
| Create record | `POST /open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records` |
| List records | `lark-cli base +record-list` |
| Search records | `lark-cli base +record-search` |
| Update record | `PUT /open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}` |

If a shortcut command exists in the installed CLI, it is fine to use it. Prefer the script interface for repeatability.
