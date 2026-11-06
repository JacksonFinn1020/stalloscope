# stalloscope

Local progress protocol + daemon + panel for long-blocking bot tasks.

CLI binary remains `gbp`.

观察 bot **长任务堵塞进度**（尤其下载百分比）的开源小工具：本地 daemon + 简单 Web 面板 + CLI 包装器。

**不是**多 bot LLM 轮询看板；不依赖 Canvas / 云端刷新例程。

## 目标

- 统一 **Progress protocol**（JSON 事件：`task_id / bot_id / title / state / progress / detail / updated_at`）
- 本地 **daemon** 收 HTTP POST 与可选文件 drop，聚合到 `data/tasks.json`
- **localhost Web** 一眼看到进度、阻塞高亮
- **`gbp wrap`** 试点：包一层命令（如 `docker pull`），启发式解析进度并上报

## 快速开始

```bash
cd /workspace/grok-bot-progress   # 或你的 clone 路径

# 1) 起本地 daemon（127.0.0.1:7310）
./gbp serve

# 2) 另开终端：上报一条进度
./gbp emit \
  --task-id demo-pull \
  --bot-id local \
  --title 'docker pull nginx' \
  --state running \
  --progress 37 \
  --detail 'Downloading layer'

# 上报阻塞（progress 可省略 → null）
./gbp emit \
  --task-id demo-pull \
  --bot-id local \
  --title 'docker pull nginx' \
  --state blocked \
  --detail 'waiting on registry'

# 3) 打开面板
# 浏览器打开 http://127.0.0.1:7310/
# 或：curl -s http://127.0.0.1:7310/v1/tasks | python3 -m json.tool
```

包装器试点（`docker pull` 专用解析：按层 `Downloading MB/MB` / `Extracting %` / `Pull complete`，总体 progress=各层平均；兼容 `\r` 刷新）：

```bash
./gbp wrap --task-id pull-nginx --bot-id local --title 'pull nginx' -- docker pull nginx:latest

# 无真实 docker 时可用模拟脚本自测
./gbp wrap --task-id pull-demo --bot-id test --title 'fake pull' -- ./tests/fake_docker_pull.sh
```

## 目录说明

| 路径 | 说明 |
|------|------|
| `PROTOCOL.md` | 事件 schema、HTTP 端点、inbox drop 约定 |
| `schema/event.schema.json` | JSON Schema |
| `daemon/server.py` | Python3 标准库 daemon |
| `web/index.html` | vanilla JS 面板（约 2s 轮询） |
| `gbp` | CLI：`serve` / `emit` / `wrap` |
| `data/tasks.json` | 运行时持久化（gitignore） |
| `inbox/*.json` | 可选文件 drop（gitignore） |
| `LICENSE` | MIT |

## 协议摘要

- `state`: `running` \| `blocked` \| `done` \| `failed` \| `idle`
- `progress`: `0`–`100` 或 `null`
- 详见 `PROTOCOL.md`

## 许可

MIT — Copyright (c) 2026 Grok Bot Progress Contributors

## Bot skill

Shared recipe for bots: [skills/stalloscope-progress/SKILL.md](skills/stalloscope-progress/SKILL.md).

