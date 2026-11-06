# Progress Protocol

观察 bot **长任务堵塞进度**（尤其下载 %）的事件契约。不是多 bot LLM 轮询看板。

时区约定：`updated_at` 使用 ISO-8601，推荐带 `+08:00`（Asia/Shanghai）。

## Event schema

单条 JSON 事件（与 `schema/event.schema.json` 对齐）：

| 字段 | 类型 | 说明 |
|------|------|------|
| `task_id` | string | 任务稳定 id（upsert 主键） |
| `bot_id` | string | 上报方 bot / 包装器 id |
| `title` | string | 一句话标题 |
| `state` | string | `running` \| `blocked` \| `done` \| `failed` \| `idle` |
| `progress` | number \| null | `0`–`100`，未知时为 `null` |
| `detail` | string \| null | 细节行（层下载、阻塞原因等） |
| `updated_at` | string | ISO-8601 时间戳 |

示例：

```json
{
  "task_id": "pull-nginx-latest",
  "bot_id": "gbp-wrap",
  "title": "docker pull nginx:latest",
  "state": "running",
  "progress": 42,
  "detail": "Extracting 3/5",
  "updated_at": "2026-11-06T15:24:00+08:00"
}
```

```json
{
  "task_id": "pull-nginx-latest",
  "bot_id": "gbp-wrap",
  "title": "docker pull nginx:latest",
  "state": "blocked",
  "progress": null,
  "detail": "waiting for registry rate limit",
  "updated_at": "2026-11-06T15:25:10+08:00"
}
```

## HTTP endpoints

Daemon 默认绑定 `127.0.0.1:7310`。

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/v1/events` | 接收一条事件，按 `task_id` upsert |
| `GET` | `/v1/tasks` | 返回全部任务列表 |
| `GET` | `/v1/tasks/{task_id}` | 返回单个任务；不存在则 404 |
| `GET` | `/healthz` | 健康检查，返回 `{"ok": true}` |
| `GET` | `/` 及静态 | 挂载 `web/` 面板 |

`POST /v1/events` 请求体为单个 event JSON。成功响应：

```json
{"ok": true, "task_id": "..."}
```

校验失败返回 `400` + `{"ok": false, "error": "..."}`。

## 文件 drop 约定

可选：向 `inbox/` 写入 `*.json`（一个文件一条事件）。Daemon 轮询（约 1s）读取、upsert，成功后删除该文件；坏 JSON 移到 `inbox/bad/`（若可写）或留下并记日志。

持久化：聚合结果原子写入 `data/tasks.json`（写临时文件再 `rename`）。

## CLI（`gbp`）

- `gbp serve` — 启动 daemon
- `gbp emit --task-id ... --bot-id ... --title ... --state running --progress 42 --detail '...'` — POST 一条事件
- `gbp wrap -- <cmd...>` — 跑子进程并 emit；检测到 `docker pull`（或 `fake_docker_pull`）时走专用解析：按 `\n`/`\r` 切片段、维护 layer→progress、总体=各层平均，progress 变化≥1 或 phase 变才 emit；退出 0 → `done`/`100`
