Deploy under test: 本地 http://127.0.0.1:7310/ + `./gbp wrap -- ./tests/fake_docker_pull.sh`
SHA claimed by Eng: n/a
SHA verified how: live poll GET /v1/tasks during wrap
Cut: /workspace/grok-bot-progress/qa/CANONICAL-AC-PACK.md （EL 补 AC-GBP-09）
AC_IDS: AC-GBP-09
password_confirmed: n/a

STATUS: PASS

| AC | Result | Notes |
|----|--------|-------|
| AC-GBP-09 | PASS | wrap 期间 API 见 running progress 5→20→…；终态 done / progress 100 / detail exit 0（task_id ac-wrap2） |

Panel pack AC-GBP-01…08 此前 PASS 不变。

---
verdict: PASS
sha: unverified
block_failed: []
warn_failed: []
share_sample: http://127.0.0.1:7310/
fixtures_cut: 2026-11-06
---
