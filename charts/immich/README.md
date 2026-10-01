# immich

**Status: DEPLOYED 2026-10-01** (`apps/immich.yaml`, after `apps/cloudnative-pg.yaml` at
sync wave -1; scaffolded 2026-09-14). Platform rehearsal complete; the photo import
waits for the off-site photos tier (B2). Fill list below kept as the decision record. Plan doc: homelab `docs/plans/immich.md`
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
- [x] Originals pool: `JBNAS_SSD/immich`, NFS export to the node with `mapall=apps` (568).
- [x] Postgres: CNPG `Cluster` (`templates/postgres.yaml`, `cloudnative-vectorchord:17-0.4.3`); CNPG owns the app Secret; nightly `pg_dump` CronJob with heartbeat; **restore rehearsed 2026-10-01**.
- [x] Rendered clean; `charts/immich` in the CI helm-lint loop.
- [x] PVC capacity rules (`pvc-capacity` group in kube-prometheus-stack values). Caveat: local-path series report the node disk, only the NFS claim is per-volume.
- [x] ServiceMonitor on `:8081`/`:8082` (chart-provided, release label). Traces: none in v3.2, metrics only; the first OTLP trace emitter is pim-tools.
- [x] NodePort 30283; probe `blackbox-immich` on `/api/server/ping` (verified live).
- [x] `apps/immich.yaml`, wave 0 after the operator, operator-owned replicas.
- [ ] Import: Photos-only Takeout, cull screenshots, `immich-go`. Google copy
      stays until the restore rehearsal passes.

## Found at first boot (2026-10-01)

- The chart mounts the library PVC at `/data`, but the v3.2.0 image still
  defaults to `/usr/src/app/upload`; the first pod wrote its upload tree to the
  container overlay. Fixed by pinning `IMMICH_MEDIA_LOCATION=/data` and moving
  the thumbs/encoded-video mounts under `/data`. Never mount anything under the
  legacy path: a populated one wins.
- After the move, Immich's folder checks refused to start until `.immich`
  marker files existed in each `/data/<folder>`; created once by hand.
