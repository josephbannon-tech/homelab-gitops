# radicale

**Status: DEPLOYED 2026-09-30** (`apps/radicale.yaml`; scaffolded 2026-09-14). Fill
checklist below kept as the record of what was decided at fill time. Plan doc: homelab
`docs/plans/personal-data-layer.md` (step 1 of the build order; Radicale goes
first because the phone's data must live in a standard store before any tool
layer reads it).

## What is already decided (do not re-litigate)

Source: `docs/plans/personal-data-layer.md`, `docs/plans/degoogle-plan.md`
Phase 4.

- **CalDAV / CardDAV / VTODO in one small server.** Phone: DAVx5 feeds the
  native Android calendar and contacts; Tasks.org for todos and the shared
  shopping list. Desktop: Thunderbird/KDE PIM. Later: the `pim-tools` server
  reads it for Open WebUI (chat) with the same htpasswd identity.
- **State is a file tree** (`/data/collections`), local-path PVC ~1 Gi.
  Backup: nightly tar to `JBNAS_SSD/data/backups/radicale/` with heartbeat,
  path added to the off-site seed, **before real data lands**.
- **Auth: htpasswd (bcrypt) from a Sealed Secret**, `rights = owner_only`.
  Exposure: LAN + tailnet only. The shared shopping list must sync from the
  supermarket, i.e. off-LAN, so the partner's phone carries Tailscale + DAVx5
  + Tasks.org (the only partner-facing install in the whole phase).
- Namespace `pim`, shared with syncthing.
- Plain YAML, tautulli pattern; no upstream chart worth wrapping.

## To fill before `apps/radicale.yaml` is added

- [x] Pin the image by digest (3.8.1.1, 2026-09-30) (`tomsquest/docker-radicale`, the maintained
      community image; tag below is unverified, check at fill time).
- [x] Sealed Secret `radicale-users` (operator user only for now; partner added at build step 4): bcrypt htpasswd with the operator user
      and the partner user. Generate with `htpasswd -B -c users <name>`.
- [x] NodePort 30232 (subnet router path); if the in-flight `tailscale-operator` lands first,
      consider a tailnet Service (`tailscale.com/expose`) instead so the
      partner phone does not depend on the subnet router.
- [ ] Blackbox probe (follow-up PR once the service answers, per the pre-merge validation rule) of `/.web/` (200) on the NodePort, `probe_success=1`
      verified **before** merge; alert warning-level.
- [x] Backup CronJob (`backup-cronjob.yaml`, 02:35, generic NAS receiver) + heartbeat; off-site seed path added NAS-side (see plan doc §storage).
      The Open WebUI backup CronJob does not exist yet either; design the
      pattern once and reuse it here.
- [ ] Google Calendar/Contacts `.ics`/`.vcf` export and import; run both for a
      few weeks before the Google surfaces go dead.
- [x] `apps/radicale.yaml` with `CreateNamespace=true` and operator-owned replicas.
