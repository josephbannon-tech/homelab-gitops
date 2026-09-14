# radicale (SCAFFOLD, not deployed)

**Status: SCAFFOLD, 2026-09-14.** No `apps/radicale.yaml` exists, so the root
Application does not see this directory. Plan doc: homelab
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

- [ ] Pin the image by digest (`tomsquest/docker-radicale`, the maintained
      community image; tag below is unverified, check at fill time).
- [ ] Sealed Secret `radicale-users`: bcrypt htpasswd with the operator user
      and the partner user. Generate with `htpasswd -B -c users <name>`.
- [ ] Decide the NodePort; if the in-flight `tailscale-operator` lands first,
      consider a tailnet Service (`tailscale.com/expose`) instead so the
      partner phone does not depend on the subnet router.
- [ ] Blackbox probe of `/.web/` (200) on the NodePort, `probe_success=1`
      verified **before** merge; alert warning-level.
- [ ] Backup CronJob + heartbeat + off-site seed path (see plan doc §storage).
      The Open WebUI backup CronJob does not exist yet either; design the
      pattern once and reuse it here.
- [ ] Google Calendar/Contacts `.ics`/`.vcf` export and import; run both for a
      few weeks before the Google surfaces go dead.
- [ ] `apps/radicale.yaml` with `CreateNamespace=true`.
