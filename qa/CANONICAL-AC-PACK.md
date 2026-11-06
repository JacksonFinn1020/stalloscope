# gbp 本地面板 — Canonical AC Pack

Cut: 2026-11-06 Owner via Engineering Lead（Bot任务看板群）  
Deploy under test: 本地 `./gbp serve` → http://127.0.0.1:7310/（`web/index.html`）  
非 Canvas；不做多 bot LLM 刷新。

| AC id | Severity | Steps | Expected |
|-------|----------|-------|----------|
| AC-GBP-01 | BLOCK | `cd /workspace/grok-bot-progress && ./gbp serve`；打开 http://127.0.0.1:7310/ | 中文面板可开；非空白/非错误页；连接指示为通 |
| AC-GBP-02 | BLOCK | `curl -s http://127.0.0.1:7310/healthz` | `{"ok": true}`（或等价 ok） |
| AC-GBP-03 | BLOCK | `./gbp emit --task-id ac-running --bot-id qa --title 'docker pull demo' --state running --progress 42 --detail 'Downloading 2/5'`；刷新面板 | 出现该任务；进度条旁可见约 **42%**；detail 可见 |
| AC-GBP-04 | BLOCK | `./gbp emit --task-id ac-blocked --bot-id qa --title 'docker pull blocked' --state blocked --detail 'waiting for registry'`；看面板 | 阻塞卡左边高亮/优先排序；detail 非空；与 running 一眼可区分 |
| AC-GBP-05 | BLOCK | 对照 `updated_at` 展示（emit 带 `+08:00` 或默认） | 可读为 Asia/Shanghai（非裸 UTC/错区） |
| AC-GBP-06 | BLOCK | `curl -s http://127.0.0.1:7310/v1/tasks` | JSON 含 `tasks` 数组；含上述 task_id；字段对齐 PROTOCOL（task_id/bot_id/title/state/progress/detail/updated_at） |
| AC-GBP-07 | BLOCK | 扫面板与 API 响应 | 无密钥/token/密码明文 |
| AC-GBP-08 | WARN | 概览筛选 chip、空态文案、次要交互 | 可读即可；不挡船 |
| AC-GBP-09 | BLOCK | `./gbp serve` 已开；`./gbp wrap --task-id ac-wrap --bot-id qa --title 'fake docker pull' -- ./tests/fake_docker_pull.sh`；期间轮询 `GET /v1/tasks` / 面板 | 出现中间 `progress`（如 ≥1，冒烟常见约 20）；结束后 `state=done` 且 `progress=100`（或等价 done/100） |

Fixtures: 见同目录 `fixtures.json`。  
Out of scope：Canvas Page、多 bot 5 分钟例程、真实 `docker pull` 外网（本 cut 用 `tests/fake_docker_pull.sh`）。
