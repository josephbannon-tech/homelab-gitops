# immich (SCAFFOLD, not deployed)

**Status: SCAFFOLD, 2026-09-14.** No `apps/immich.yaml` exists, so the root
Application does not see this directory. Plan doc: homelab `docs/plans/immich.md`
(the stateful-workload rehearsal). Standing gate: **Backblaze B2 account** for
photo-class off-site capacity, an operator action, still open.

## What is already decided (do not re-litigate)

Source: `docs/plans/immich.md`, `docs/plans/2026-09-post-window-layout.md`
(validation table), memory `project_service_roadmap`.

- Framed as a **rehearsal of four patterns the cluster has never solved**: a
  real storage class, a Postgres that is backed up **and restore-rehearsed**,
  PVC capacity alerting, a first real telemetry emitter. Not a family service
  on day one (~8 GB library, mostly screenshots).
- Official chart via the app-of-apps, wrapper-chart pattern (open-webui).
- **DB, thumbnails, encoded video, ML cache: local** (`templates/local-pvcs.yaml`).
  Immich docs forbid the DB on any network share; community practice keeps
  thumbs/encoded video local because the timeline UI hammers them.
- **Originals: NFS from the NAS** as a static PV so the pod fails closed on a
  missing mount (`templates/library.yaml`).
- Exposure NodePort + subnet router, never public. Blackbox probe of the web
  UI, info-level until the family uses it.
- Keep the Google copy until the restore rehearsal has passed.

## Found while scaffolding (2026-09-14)

- **Chart 0.13.2 bundles no Postgres.** It expects an external vectorchord-
  capable instance (`DB_*` env). Decision at fill time: CNPG operator + Cluster
  CR (chart maintainers' path, one more Application) vs a plain StatefulSet on
  `ghcr.io/immich-app/postgres`. `immich.md` says "simplest that can be backed
  up"; `post-window-layout.md` leans CNPG. Not a contradiction, but pick one.
- **Pool for originals is contradicted across the two plan docs**
  (`JBNAS_MEDIA/immich` in immich.md vs `JBNAS_SSD` in the later, validated
  layout doc, which also says "decide finally at Immich time"). The PV here
  carries the SSD path as the validated proposal; the plan doc must settle it.
- **"First OTel emitter" needs verifying.** Immich publishes Prometheus
  metrics through the OTel SDK; a documented OTLP *trace* export was not found
  for v3.2. If it is not there, the pim-tools server is the better candidate
  for the first Tempo emitter and this step drops to metrics-only.

## To fill before `apps/immich.yaml` is added

- [ ] B2 account + bucket + scoped application key (operator). Second restic
      repo (photos tier) on JBNAS01 with heartbeat and `BackupHeartbeatStale`.
- [ ] Settle the originals pool in `docs/plans/immich.md`; update
      `templates/library.yaml` path + the NAS dataset/export/UID mapping.
- [ ] Postgres: choose CNPG vs StatefulSet; add `templates/postgres.yaml`;
      Sealed Secret `immich-postgres-app`; nightly `pg_dump` CronJob to
      `JBNAS_SSD/data/backups/immich-db/` with heartbeat; **restore rehearsal
      is part of done, not a follow-up**.
- [ ] `helm dependency update` locally (OCI pull), confirm values keys against
      the pulled chart (`bjw-s common` 5.1.0 conventions), `helm template` clean.
      Add `charts/immich` to the `helm-lint` loop in `.github/workflows/ci.yaml`.
- [ ] PVC capacity alert rules for the four PVCs (the pattern the cluster lacks).
- [ ] ServiceMonitor for `:8081`/`:8082`; verify/decide the trace question.
- [ ] Pick the NodePort, blackbox probe of `/api/server/ping`,
      `probe_success=1` verified in Prometheus **before** merge.
- [ ] `apps/immich.yaml` with `CreateNamespace=true` and, if CNPG, a sync-wave
      after the operator.
- [ ] Import: Photos-only Takeout, cull screenshots, `immich-go`. Google copy
      stays until the restore rehearsal passes.
