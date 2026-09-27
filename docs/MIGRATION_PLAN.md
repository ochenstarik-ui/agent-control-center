# AI Factory 2.0 — Migration Plan

## Mapping

| Current | Target | Action |
|---|---|---|
| Task folders | Controller tasks + compatibility events | Keep and mirror |
| Cron role ticks | Scheduler adapter | Keep until cutover |
| TSV quota state | Provider/account records | Import, then replace |
| Filesystem account locks | Persistent leases plus compatibility lock | Keep both during migration |
| Multiaccount registry | Worker/provider adapter | Modify |
| In-memory supervisor leases | SQLite leases | Replace |
| Obsidian project notes | Memory API | Preserve and normalize incrementally |
| Git branches/worktrees | Git adapter | Preserve |

## Phases

1. Snapshot critical configuration, repositories and Obsidian.
2. Deploy a passive Controller with SQLite and status/bootstrap APIs.
3. Register Business Platform, workers and providers without dispatching work.
4. Mirror existing folder events into the database and reconcile discrepancies. **Implemented
   for the Business Platform coder/tester paper protocol.**
5. Add scheduler and provider adapters; enforce two active projects and worker leases.
   **Compatibility dispatcher implemented for four lanes; account selection remains in the
   proven `lane-run.sh` adapter during migration.**
6. Add DEV → TEST → REWORK/REVIEW → AUDIT → DONE execution.
7. Add Model Registry, discovery and qualification.
8. Run restart, quota rotation, orchestrator failover and two-project tests.
9. Cut over dispatch only after tests pass; retain rollback to cron/ticks.

## Rollback

Stop `ai-factory.service`; the old cron/tick pipeline remains untouched. Restore Controller code and memory from `/home/ochenstarik/backups/ai-factory-20260927-190000`. SQLite is additive and does not mutate Git or Obsidian content.

For the active compatibility layer, stop `ai-factory-dispatcher.service` first. This returns
execution control to the unchanged lane scripts without discarding queue or run history.
