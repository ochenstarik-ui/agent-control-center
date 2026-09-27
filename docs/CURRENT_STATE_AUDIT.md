# AI Factory 2.0 — Current State Audit

Date: 2026-09-27. Scope: server `192.168.1.81`, Obsidian memory, Antigravity cockpit and `business-platform`. The audit was performed read-only before implementation.

## Existing components

- Canonical memory: `/srv/projects/AI-Memory`, Git-backed and opened by Obsidian.
- Project memory already separates current state, decisions, handoff, tasks and worklogs.
- Business Platform: `/srv/projects/Agent projects/business-platform`; the Forgejo repository is a working monorepo with API, admin UI, migrations, CI and tests.
- File pipeline: task papers move through inbox, in-progress, review, rework and done directories.
- Account rotation: cron invokes role-specific tick scripts; shared filesystem locks prevent simultaneous use of one account; quota reset data is persisted in TSV files.
- Antigravity cockpit: `/srv/projects/Agent projects/multiaccount`; contains a worker registry, state machine, health probes, leases, pipeline code and tests.
- Running services include `krona-cockpit.service` and `hermes-gateway.service`.

## Gaps against AI Factory 2.0

- Runtime state is split across process memory, task folders, TSV files and Git branches.
- Cockpit leases are in-memory and do not survive restart.
- There is no single authoritative Controller or atomic two-project admission limit.
- Provider, account, worker, model and role are not represented as separate persistent entities.
- Account pools and routing rules are embedded in shell/Python configuration.
- No standardized `factory.bootstrap(project_id)` contract exists.
- No common dynamic Model Registry or qualification workflow exists.
- Existing cron/tick execution is useful but is not reconciled against a durable runtime database.

## Components to preserve

- Obsidian project memory and its Git history.
- Existing working trees and agent role separation.
- Account OS identities, profile directories and account locks.
- Current tick scripts as a compatibility adapter during migration.
- Cockpit discovery and process-launch knowledge.
- Business Platform task papers, audits and test evidence.

## Immediate risks

- Replacing cron before the Controller can execute end-to-end would stop productive work.
- Reusing in-memory leases could assign one account to two projects after restart.
- Reading quota state only from CLI text is provider-version sensitive.
- The server contains many active worktrees; global cleanup would risk live work.
- Nextcloud on port 80 is at its initial setup screen and is not an authoritative storage service.

## Baseline decision

Extend Agent Control Center into the Controller. Keep `multiaccount` and existing tick scripts behind adapters. Introduce SQLite first, using Git for code and Obsidian for durable knowledge. Do not disable the old pipeline until equivalent end-to-end and rollback tests pass.
