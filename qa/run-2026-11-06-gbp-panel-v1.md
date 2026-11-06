Deploy under test: 本地 http://127.0.0.1:7310/ （`./gbp serve`）
SHA claimed by Eng: n/a（workspace tree）
SHA verified how: live curl + headless Chrome screenshot
Cut: /workspace/grok-bot-progress/qa/CANONICAL-AC-PACK.md （2026-11-06）
AC_IDS: AC-GBP-01..08
password_confirmed: n/a

STATUS: PASS

| AC | Result | Notes |
|----|--------|-------|
| AC-GBP-01 | PASS | 中文「长任务进度」可开；连接指示「已连接」 |
| AC-GBP-02 | PASS | `{"ok": true}` |
| AC-GBP-03 | PASS | ac-running 可见；大号 42%；detail Downloading 2/5；进度条 |
| AC-GBP-04 | PASS | ac-blocked 左边红高亮且排在 running 前；detail waiting for registry |
| AC-GBP-05 | PASS | 行内 `… Asia/Shanghai`；API `updated_at` 带 +08:00 |
| AC-GBP-06 | PASS | `/v1/tasks` 含 tasks[] 与 PROTOCOL 字段 |
| AC-GBP-07 | PASS | 无密钥明文 |
| AC-GBP-08 | WARN ok | 筛选 chip / 空态可读 |

Evidence: `/workspace/grok-bot-progress/qa/panel-ac-2026-11-06.png`

---
verdict: PASS
sha: unverified
block_failed: []
warn_failed: []
share_sample: http://127.0.0.1:7310/
fixtures_cut: 2026-11-06
---
