# 飞书求职进度跟踪 Skill

[English](README-EN.md) | 中文

求职者常常同时投递几十个岗位：链接散在 Boss 直聘、牛客、实习僧、公司官网和内推消息里，状态更新靠手动表格维护，几天后就很容易忘记哪个岗位投过、哪个要跟进、哪个已经进入面试。这个 skill 让 AI Agent 帮你把“看到岗位 -> 记录投递 -> 更新进展 -> 复盘下一步”沉淀到飞书多维表格里。

用户只需要自然语言告诉 Agent“我刚投了这个岗位”“腾讯进一面了”“总结这周进展”，Agent 会调用 `lark-cli` 把信息写入你的飞书求职进度表。当前模板主要面向中国实习、校招、春招、秋招场景。

## 功能点

- 🧩 **一键创建求职进度表**：自动创建 `求职进度跟踪` 飞书多维表格，只保留一张清爽的 `投递记录` 表，避免用户从零设计字段。
- 📝 **自然语言记录投递**：用户可以说“我刚投了字节 AI 产品实习”，Agent 抽取公司、岗位、链接、状态、优先级、下一步动作并写入表格。
- 🔎 **投递查重**：保存前按岗位链接、公司、岗位名称搜索疑似重复记录，减少“同一个岗位到底投没投过”的混乱。
- 🔄 **状态更新归一**：把“进一面了”“OC 了”“拿 offer 了”“挂了”等说法映射到标准状态：已投递、测评/笔试、AI 面试、一面、二面、HR 面、OC、Offer、拒绝等。
- 📅 **下一步跟踪**：自动维护下一步动作和下一步日期，例如“7 天后检查反馈”“下周三参加一面”。
- 📊 **周报复盘**：读取表格生成投递总数、状态分布、面试中岗位、过期待办和长期无响应岗位。
- 🛠️ **预检与修复**：检查 `lark-cli`、用户授权、Base 权限和模板字段，支持修复已有表。
- 🤖 **多 Agent 入口**：支持 Codex、Claude Code、Gemini CLI、OpenClaw、Hermes 和通用 shell-capable Agent。

## 用户怎么说

你可以这样对 Agent 说：

```text
使用 Feishu Job Tracker，帮我初始化一个求职进度跟踪表。
```

```text
我刚投了字节 AI 产品实习，岗位链接是 https://example.com/job/123，上海，状态记为已投递，备注：内推人是 Alex。
```

```text
帮我看看这个岗位是不是已经记录过了：腾讯 产品实习 https://example.com/tencent-pm-intern
```

```text
腾讯那个产品实习进一面了，下周三下午三点，帮我更新一下。
```

```text
总结一下这周求职进展，看看哪些岗位该跟进。
```

## Agent 快速开始

如果你是正在阅读本文档的 AI coding agent，请按这个顺序执行。

### 1. 判断运行环境

- **Codex**：把 skill 安装到 `~/.codex/skills`。
- **Claude Code**：保留本目录，并读取 `CLAUDE.md`。
- **Gemini CLI**：保留本目录，并读取 `GEMINI.md`。
- **OpenClaw**：保留本目录，并读取 `OPENCLAW.md`。
- **Hermes**：保留本目录，并读取 `HERMES.md`。
- **通用 Agent**：读取 `AGENTS.md` 和 `SKILL.md`。

### 2. 为 Codex 安装

在本仓库根目录运行：

```bash
python3 scripts/install_skill.py --target codex
```

这会把 skill 软链到：

```text
~/.codex/skills/feishu-job-tracker
```

如果不适合使用软链，可以复制安装：

```bash
python3 scripts/install_skill.py --target codex --mode copy
```

安装后，提示用户重启或刷新 Codex，让 Codex 发现这个 skill。

### 3. 检查依赖

```bash
python3 scripts/tracker.py check
```

如果 `lark-cli` 缺失或版本过旧，安装/更新：

```bash
npm install -g @larksuite/cli
lark-cli auth login --recommend
```

### 4. 初始化用户的求职跟踪表

当用户要求初始化时，执行：

```bash
python3 scripts/tracker.py bootstrap --dry-run
python3 scripts/tracker.py bootstrap
```

`bootstrap` 是幂等的：如果没有配置，它会创建新的求职进度表；如果已经配置过，它会检查并补全模板字段。

### 5. 处理用户请求

把自然语言映射到确定性命令：

| 用户意图 | Agent 动作 |
| --- | --- |
| “帮我初始化求职跟踪表” | `python3 scripts/tracker.py bootstrap` |
| “我刚投了这个岗位” | 抽取 JSON -> `search-duplicates` -> `add-record` |
| “我是不是已经保存过了？” | `search-duplicates --from-json application.json` |
| “腾讯进一面了” | `normalize-status` -> 找到记录 -> `update-status` |
| “总结这周求职进展” | `list-records` -> `weekly-review` |
| “删掉这条记录” | `delete-record --record-id <record_id>` |

所有写操作前，都要先展示预览并等待用户确认。

## 内置表格模板

默认必填字段：

- 公司
- 岗位名称
- 投递状态
- 最近更新时间：由脚本自动填充，用户通常不需要手动输入

默认字段顺序：

- 公司
- 岗位名称
- 投递状态
- 岗位链接
- 平台来源
- 岗位类型
- 方向
- 城市
- 优先级
- 匹配度
- 投递日期
- 最近更新时间
- 下一步动作
- 下一步日期
- 工作模式
- 简历版本
- 联系人/HR
- JD 摘要
- JD 原文
- 风险信号
- AI 备注
- 结果原因
- 备注

完整 schema 见 [`references/template-schema.json`](references/template-schema.json)。

## 环境要求

- Python 3.9+
- [`lark-cli`](https://github.com/larksuite/cli) 1.0.32 或更新版本
- 已在 `lark-cli` 中授权的飞书/Lark 账号

安装或更新 Lark CLI：

```bash
npm install -g @larksuite/cli
lark-cli auth login --recommend
```

检查状态：

```bash
lark-cli --version
lark-cli auth status
```

## 安装 Skill

如果使用 Codex，可以一键安装：

```bash
python3 scripts/install_skill.py --target codex
```

这会在下面的位置创建软链：

```text
~/.codex/skills/feishu-job-tracker
```

如果你希望复制一份，而不是软链：

```bash
python3 scripts/install_skill.py --target codex --mode copy
```

如果使用 Claude Code、Gemini CLI、OpenClaw、Hermes 或其他通用 Agent，可以让 Agent 读取本目录下对应入口文件：

- `CLAUDE.md`
- `GEMINI.md`
- `OPENCLAW.md`
- `HERMES.md`
- `AGENTS.md`

真正执行确定性操作的始终是：

```bash
python3 scripts/tracker.py <command>
```

## 首次初始化

理想的用户体验不是让用户自己敲命令，而是用户对 Agent 说：

```text
使用 Feishu Job Tracker skill，帮我初始化求职进度跟踪表。
```

Agent 应该执行：

```bash
python3 scripts/tracker.py bootstrap --dry-run
python3 scripts/tracker.py bootstrap
```

`bootstrap` 会自动判断：如果本地没有配置，就创建新的求职进度表；如果已经配置过，就检查并补全表格模板字段。

下面的命令主要给开发者调试和审计用，普通用户不需要自己输入。

## 手动快速开始

在本目录下运行：

```bash
python3 scripts/tracker.py check
python3 scripts/tracker.py init-template --dry-run
python3 scripts/tracker.py init-template
```

创建成功后，本地配置会保存到：

```text
~/.feishu-job-tracker.json
```

如果你已经有飞书多维表格，可以接入已有表：

```bash
python3 scripts/tracker.py configure --base-token <base_token> --table-id <table_id>
python3 scripts/tracker.py repair-template
```

## 常见用法

### 新增投递记录

创建 `application.json`：

```json
{
  "company": "字节跳动",
  "role": "AI产品实习生",
  "job_url": "https://example.com/job/123",
  "source": "公司官网",
  "job_type": "日常实习",
  "track": "产品",
  "city": "上海",
  "status": "已投递",
  "priority": "高",
  "fit_score": 86,
  "work_mode": "混合",
  "risk_signals": ["实习时长过长"],
  "resume_version": "product_ai_v1.pdf",
  "jd_summary": "负责 AI 产品需求分析、用户反馈整理和效果评估。",
  "ai_notes": "建议准备 AI 产品指标和用户反馈闭环案例。",
  "user_notes": "用户自定义备注，例如内推人、个人判断、后续想法。"
}
```

先查重：

```bash
python3 scripts/tracker.py search-duplicates --from-json application.json
```

确认后写入：

```bash
python3 scripts/tracker.py add-record --from-json application.json
```

### 更新状态

当用户说：

```text
腾讯那个产品实习进一面了，下周三下午三点。
```

Agent 应该先归一状态，再更新选中的记录：

```bash
python3 scripts/tracker.py normalize-status "腾讯那个产品实习进一面了"
python3 scripts/tracker.py update-status \
  --record-id <record_id> \
  --company 腾讯 \
  --role-keyword 产品 \
  --status 一面 \
  --next-date 2026-05-20 \
  --next-action "参加一面"
```

如果还没有确定是哪条记录，先 dry-run 并让用户选择：

```bash
python3 scripts/tracker.py update-status --company 腾讯 --role-keyword 产品 --status 一面 --dry-run
```

### 生成周报

```bash
python3 scripts/tracker.py list-records > /tmp/job-records.json
python3 scripts/tracker.py weekly-review --records-json /tmp/job-records.json
```

### 删除记录

```bash
python3 scripts/tracker.py delete-record --record-id <record_id>
```

## AI Agent 集成方式

本项目尽量保持运行时中立。

入口文件：

- `SKILL.md`：Codex 和通用 skill loader
- `CLAUDE.md`：Claude Code
- `GEMINI.md`：Gemini CLI
- `OPENCLAW.md`：OpenClaw
- `HERMES.md`：Hermes
- `AGENTS.md`：通用 Agent

所有 Agent 都应把确定性操作交给：

```bash
python3 scripts/tracker.py <command>
```

推荐交互流程：

1. 从用户自然语言或 JD 中抽取结构化字段。
2. 先查重。
3. 展示写入预览。
4. 让用户确认。
5. 写入飞书多维表格。

## 身份与权限模型

工具默认使用：

- 读操作：`user`
- 写操作：`bot`

这是基于真实飞书 Base 测试后的默认值：新版 `lark-cli base +record-list/+record-search` 用 user 读取更自然，而 CLI 创建的 Base 用 bot 写入更稳定。

可以通过环境变量覆盖：

```bash
FEISHU_JOB_TRACKER_READ_AS=user python3 scripts/tracker.py list-records
FEISHU_JOB_TRACKER_WRITE_AS=bot python3 scripts/tracker.py add-record --from-json application.json
```

旧式统一覆盖也可用：

```bash
FEISHU_JOB_TRACKER_AS=user python3 scripts/tracker.py ...
```

### 所有者与权限

如果用 bot/app 身份创建 Base，飞书客户端里可能会显示机器人是所有者。现在初始化逻辑已改为使用新版 `lark-cli base +base-create`，因为它在 bot 模式创建后会尝试给当前 CLI 用户授予可管理权限。

如果某张 Base 是旧版本工具或原始 Bitable API 创建的，可以先检查当前用户权限：

```bash
python3 scripts/tracker.py check-permissions
```

如果用户只有阅读权限，可以把所有者转移给当前 Lark CLI 用户，同时给原所有者/机器人保留编辑权限：

```bash
python3 scripts/tracker.py transfer-owner-to-user --dry-run
python3 scripts/tracker.py transfer-owner-to-user
```

真实转移所有者前，Agent 必须先获得用户明确确认。

## 已验证流程

以下流程已经在真实飞书多维表格中完整测试：

- `check`
- `init-template`
- 清理飞书自动创建的默认空表
- `repair-template`
- `add-record`
- `search-duplicates`
- `normalize-status`
- `update-status`
- `list-records`
- `weekly-review`
- `delete-record`

测试记录已在验证结束后删除。

## 隐私与安全

- 不爬取招聘网站。
- 只写入用户或 Agent 明确提供的数据。
- 默认不存储简历文件。
- 本地只保存 Base 配置到 `~/.feishu-job-tracker.json`。
- Agent 在写入前应先展示预览并等待用户确认。

## 开源协议

MIT。详见 [`LICENSE`](LICENSE)。

## 常见问题

检查授权：

```bash
lark-cli auth status
lark-cli auth scopes | rg 'base:record|bitable:app'
```

更新 CLI：

```bash
npm install -g @larksuite/cli
lark-cli auth login --recommend
```

如果旧版 `bitable/v1` 记录读取接口报权限错误，使用新版 Base 命令：

```bash
lark-cli base +record-list --base-token <base_token> --table-id <table_id> --format json --as user
lark-cli base +record-search --base-token <base_token> --table-id <table_id> --json '{"keyword":"腾讯","search_fields":["公司"],"limit":20}' --format json --as user
```

如果 user 写入失败，使用默认的 bot 写入身份，或设置：

```bash
FEISHU_JOB_TRACKER_WRITE_AS=bot
```
