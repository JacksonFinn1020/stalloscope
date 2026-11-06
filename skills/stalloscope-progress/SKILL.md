---
name: stalloscope-progress
description: Use when a bot runs a long-blocking task (docker pull/save/load, large download, multi-minute shell) and Owner’s stalloscope/gbp daemon is expected to show live progress on localhost.
---

# stalloscope progress reporting

Report long-blocking work to the local **stalloscope** daemon (CLI still named `gbp`). Do **not** wake LLMs to poll; emit structured events instead.

Repo: https://github.com/JacksonFinn1020/stalloscope  
Default daemon: `http://127.0.0.1:7310` (override with env `GBP_URL` only if the operator set it)  
Protocol: `PROTOCOL.md` in that repo.

## When to use

- Any command expected to take minutes or hide progress (especially `docker pull` / `docker save` / `docker load`, large file downloads).
- When stuck waiting on a registry, disk, or network → `blocked` + nonempty `detail`.
- Skip for trivial sub-second commands and chat-only updates.

### Hard rules

1. **Same long task → same `task_id`** (daemon upserts by `task_id`).
2. **Start**: at least one `running` emit (or start via `wrap`).
3. **End**: always emit a terminal state — `done` or `failed` — even if no mid-progress was available.
4. **State changes** (`blocked`↔`running`, or →`done`/`failed`) must emit again.
5. Never put secrets, tokens, passwords, or private keys in `title` / `detail` / event JSON.

## Preconditions

1. Work from the stalloscope checkout first:
   - Windows example: `cd C:\Users\20322\stalloscope` (or your local clone path)
   - Shared box example: `cd /workspace/grok-bot-progress` or the clone path
2. Confirm daemon: `GET http://127.0.0.1:7310/healthz` → `{"ok": true}`.
3. If healthz fails: **warn the operator once**, ask them to run `python gbp serve` (or `./gbp serve`) from that checkout — **do not invent a remote URL**. Then continue the real command; do **not** treat progress reporting as a hard dependency of the job.
4. If a later POST/`emit`/`wrap` upload fails: **warn once**, do **not** silently assume it was reported, and **do not abort** the underlying task because of reporting failure.

## Prefer `wrap` for docker pull

```bash
# after cd into checkout
python gbp wrap --task-id <stable-id> --bot-id <your-bot-id> --title '<one-line>' -- docker pull <image>
# Unix may use: ./gbp wrap ...
```

`wrap` parses layer progress (`\r`, MB/MB, Extracting %), truncates `detail` to ≤240 chars, emits when progress moves ≥1 or phase changes; exit 0 → `done` / `100`.

## Manual `emit`

```bash
python gbp emit \
  --task-id <stable-id> \
  --bot-id <your-bot-id> \
  --title '<one-line>' \
  --state running \
  --progress 42 \
  --detail '<short status>'
```

Or `POST http://127.0.0.1:7310/v1/events` with one JSON event.

`gbp emit` / `gbp wrap` **always send all seven keys**; if you omit `--progress` / `--detail` on the CLI they are sent as `null`. `updated_at` is filled automatically as Asia/Shanghai ISO-8601 (`+08:00`) when you use the CLI.

### Event fields (all keys required)

| Field | Rules |
|-------|--------|
| `task_id` | Stable upsert key for this job |
| `bot_id` | Your bot / wrapper id |
| `title` | One short sentence |
| `state` | `running` \| `blocked` \| `done` \| `failed` \| `idle` |
| `progress` | `0`–`100`, or `null` if unknown |
| `detail` | Status / blocker; prefer ≤240 chars; `null` ok if none; **nonempty when `blocked`** |
| `updated_at` | ISO-8601; prefer `+08:00` (CLI auto-fills) |

## Optional inbox drop

Write one event per `*.json` under the **running daemon’s** `inbox/` directory (relative to that daemon process cwd / checkout). Daemon upserts then deletes the file.

## Out of scope

- Do not rebuild Canvas multi-bot polling boards.
- Do not replace Engineering Lead task assignment.
- Do not change production infra while only reporting progress.
