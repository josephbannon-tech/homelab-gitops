# syncthing (SCAFFOLD, not deployed)

**Status: SCAFFOLD, 2026-09-14.** No `apps/syncthing.yaml` exists, so the root
Application does not see this directory. Plan doc: homelab
`docs/plans/personal-data-layer.md` (step 5 of the build order, after Radicale
and the tool server).

## What is already decided (do not re-litigate)

Source: `docs/plans/personal-data-layer.md`, `docs/plans/degoogle-plan.md`
Phase 4 (files lane).

- **The file vault:** Obsidian notes + recipe views + documents leaving Drive,
  as a private peer-to-peer mesh (phone, JBPC004, this always-on peer). The
  cluster node is the always-on introducer and the backup source; it holds no
  logic, just a full replica.
- **Storage:** config on a small local-path PVC, the vault on ~20 Gi
  local-path. Backup: nightly tar to `JBNAS_SSD/data/backups/syncthing-vault/`
  with heartbeat, path in the off-site seed, **before real data lands**.
  (The plan doc's JBVM02 replica for AI access rides the existing weekly NAS
  rsync separately; that is a Syncthing peer on JBVM02, not this chart.)
- **Auth:** Syncthing's own device-ID mutual TLS between peers; GUI behind its
  own user/password. Global discovery and relays OFF: peers find each other
  by static tailnet/LAN address, so nothing leaves the estate.
- Namespace `pim`, shared with radicale. Plain YAML, tautulli pattern.

## Found while scaffolding (2026-09-14)

- The **official Syncthing Android app is retired**; the maintained client is
  the Catfriend1 "Syncthing-Fork", whose maintainer is winding down their Play
  publishing, so the phone install path may become F-Droid/GitHub only. Fine
  for the operator; a consideration before asking anyone else to install it.
  (forum.syncthing.net "syncthing-android public archived";
  github.com/Catfriend1/syncthing-android.)

## To fill before `apps/syncthing.yaml` is added

- [ ] Pin the image by digest (`syncthing/syncthing`, 2.x line; tag below is
      unverified, check at fill time).
- [ ] Decide NodePorts for the GUI (8384) and the sync listener (22000/tcp+udp).
      The sync port must be reachable from the phone over the tailnet, so
      confirm the subnet router path or use the tailscale-operator if landed.
- [ ] First-boot: set the GUI user/password, record the device ID in the plan
      doc, add the JBPC004 and phone device IDs, share the vault folder. Then
      export `config.xml` and decide whether to seed it from a ConfigMap (the
      tautulli init-container pattern) for rebuildability.
- [ ] Blackbox probe of `/rest/noauth/health` (200 `{"status":"OK"}`),
      `probe_success=1` verified **before** merge.
- [ ] Backup CronJob + heartbeat + off-site seed path (same pattern as
      radicale; design once).
- [ ] `apps/syncthing.yaml` with `CreateNamespace=true`.
