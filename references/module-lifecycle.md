# Module 4 — 内容库生命周期管理

Use this module only for the documented soft-archive sweep or an explicit lifecycle audit. It does not create creative candidates, tasks, storyboards, videos, or final-film records.

## Read for this module

Read the public gates in the parent `SKILL.md`, then read:

- [lifecycle-archive.md](lifecycle-archive.md) for archive locations, field semantics, and bottom-up rules.
- [configuration.md](configuration.md) for active limits and configuration provenance when task rotation is involved.
- `config/base-schema.json` and `config/lifecycle-policy.json` through their file paths; do not copy IDs into this module.

## Scope and order

The sweep covers only `内容库` → `内容策划任务` → `创意候选` → `内容母题`. It never archives `产品`, `主体资产库`, or `最终成片`; final films are read-only evidence.

Evaluate bottom-up. Use existing status fields, write `已归档`, and add `归档时间` and `归档原因`. Respect `归档保护=true` by reporting a deferred record without writing it. Never delete, move, copy, silently repair links, or create a replacement task as a side effect of a dry-run.

## Safe execution

1. Run `python scripts/lifecycle_sweeper.py --check-schema --json` first.
2. Run the default `--json` dry-run and retain its report locally.
3. Apply only when the user explicitly authorizes the write: `python scripts/lifecycle_sweeper.py --apply --json`.
4. Re-read every changed record and verify the status, timestamp, reason, and protected-record behavior. A single write failure must remain visible; do not rerun blindly to hide partial progress.

The sweep may archive a rejected content version when an updated replacement exists, a content version after a qualifying final film when policy says it is no longer active, an exhausted task only when an explicit active replacement points to it, a discarded/landed candidate, or a converged mother topic whose children are no longer active. It must not infer missing child links or invent a replacement direction.

Keep active/default views filtered to active states and use archive views for history. Lifecycle state is administrative; it never authorizes video generation.
