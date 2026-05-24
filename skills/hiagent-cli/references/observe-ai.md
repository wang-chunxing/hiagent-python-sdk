# observe AI 模块

目标：使用 Observe 的 AI 分析能力对 trace / alert 做自动分析。

对应子命令：

- `<CMD>` 命令是 `cli-anything-hiagent`
- `observe trace-ai-process`
- `observe trace-ai-history`
- `observe alert-ai-process`

## 前置条件

与 `observe.md` 相同，需要 `VOLC_ACCESSKEY` / `VOLC_SECRETKEY` 或 `~/.volc/.env`。

## 设计要点

服务端 TOP gateway 同步代理硬性 60s timeout，AI 分析实测耗时 23-45s，**sync 模式必失败**。CLI 默认 `IsStream=True`，仅在调试场景使用 `--no-stream`。

## observe trace-ai-process

用途：对一个或多个 TraceID 触发 AI 分析。

必填参数：

- `--workspace-id <WORKSPACE_ID>`
- `--trace-id <TRACE_ID>`（可重复传入多个）

可选参数：

- `--tenant-id <TENANT_ID>`
- `--no-stream`（关闭 SSE，默认开启）

命令：

```bash
<CMD> --json observe trace-ai-process \
  --workspace-id <WORKSPACE_ID> \
  --trace-id <TRACE_ID_1> \
  --trace-id <TRACE_ID_2>
```

输出字段（JSON 模式 data 内）：

- `content`：AI 分析结论的 markdown 报告
- `reasoning_content`：推理过程
- `usage`：token 用量（服务端可能返回 None，不要假设非空）
- `latency`：耗时，单位毫秒
- `trace_id`：本次 AI 分析自身的 trace_id（用于排障）

## observe trace-ai-history

用途：查询某个 TraceID 历史的 AI 分析记录。

必填参数：

- `--workspace-id <WORKSPACE_ID>`
- `--trace-id <TRACE_ID>`

可选参数：

- `--page-size <N>`（默认 10）

命令：

```bash
<CMD> --json observe trace-ai-history \
  --workspace-id <WORKSPACE_ID> \
  --trace-id <TRACE_ID> \
  --page-size 10
```

输出：`data.items` 数组，每项是 trace span（含 `DocID` / `Context.TraceID` / `Status` 等）。

## observe alert-ai-process

用途：对一条告警规则触发 AI 分析。

必填参数：

- `--workspace-id <WORKSPACE_ID>`
- `--rule-id <RULE_ID>`

可选参数：

- `--tenant-id <TENANT_ID>`
- `--no-stream`

命令：

```bash
<CMD> --json observe alert-ai-process \
  --workspace-id <WORKSPACE_ID> \
  --rule-id <RULE_ID>
```

输出与 `trace-ai-process` 同结构。

## 典型工作流

1. 先用 `observe trace list` 找到要分析的 TraceID（看 items[].Context.TraceID）
2. 用 `observe trace-ai-process --trace-id <TRACE_ID>` 触发 AI 分析
3. 用 `observe trace-ai-history --trace-id <TRACE_ID>` 复看历史结果（避免重复触发）

## 排障清单

1. 鉴权错误：`Volcengine credentials not found.` → 见 troubleshooting.md
2. 60s 超时：若 `--no-stream` 模式失败，检查是否服务端代理超时；改为默认 stream
3. RuleID / TraceID 不存在：服务端会返回错误，看 `message` 字段
4. JSON 模式输出多块：报 bug，正常情况下 stdout 必须是单一 JSON 块
