# AI Factory compatibility pipeline

## Runtime

- Controller: `ai-factory.service`, loopback API `127.0.0.1:8100`.
- Dispatcher: `ai-factory-dispatcher.service`.
- State: `/srv/projects/ai-factory-state/runtime.db` (SQLite WAL).
- Project: `business-platform`.
- Active lanes: `pair`, `pair2`, `pair3`, `pair6` (hard global limit: four).
- Active project orchestrators: at most two, enforced transactionally by the Controller.

The dispatcher is an additive compatibility layer. It does not replace the established
`lane-run.sh` account rotation, filesystem account locks or role-specific worktrees. It
mirrors Git task papers into SQLite, acquires a durable logical worker lease and then invokes
the existing launcher. A restart loses neither the project queue nor run history. An expired
lease is released before the worker is reused.

## Task flow

```text
agents/<lane>/coder-inbox/*.md  -> coder (DEV)
agents/<lane>/review/*.md       -> tester (TEST)
agents/<lane>/rework/*.md       -> coder (REWORK -> DEV)
agents/<lane>/done/*.md         -> final orchestrator review (REVIEW)
```

`done` deliberately means the independent tester has passed the task; it does not grant an
automatic merge. The Project Orchestrator performs the final semantic review and merge. This
keeps the existing corruption/mutation acceptance gate and prevents an LLM self-report from
becoming merge authority.

## Operator commands

```bash
systemctl --user status ai-factory.service ai-factory-dispatcher.service
journalctl --user -u ai-factory-dispatcher.service -n 200 --no-pager
curl -fsS http://127.0.0.1:8100/api/v1/factory/status
curl -fsS 'http://127.0.0.1:8100/api/v1/factory/tasks?project_id=business-platform'
curl -fsS 'http://127.0.0.1:8100/api/v1/factory/dispatch-runs?project_id=business-platform&limit=25'
curl -fsS http://127.0.0.1:8100/api/v1/factory/projects/business-platform/bootstrap
```

Pause dispatch without touching Cockpit or provider processes:

```bash
systemctl --user stop ai-factory-dispatcher.service
```

Resume:

```bash
systemctl --user start ai-factory-dispatcher.service
```

## Recovery

The dispatcher is safe to restart. A worker process interrupted with the service remains in
the same Git/task-paper stage; after lease expiry the next cycle retries that stage. The
compatibility launcher still owns provider account selection and quota reset timestamps in
`/srv/projects/krona-accounts.tsv`.

Rollback is to stop and disable only `ai-factory-dispatcher.service`. The passive Controller,
Cockpit, Git repositories, Obsidian vault and original lane scripts remain intact.

## Security

- Both services listen or execute locally; no new public port is opened.
- Provider credentials remain in provider-local OS profiles and are never copied to SQLite.
- The dispatcher retains the server's existing narrowly scoped passwordless `sudo` path used
  by `lane-run.sh` to enter provider account profiles; the Controller API itself remains
  `NoNewPrivileges=true`.
- Stored output is limited to the final 12,000 characters and common credential forms are
  redacted.
- Lane names are allowlisted and subprocess arguments are passed without a shell.
