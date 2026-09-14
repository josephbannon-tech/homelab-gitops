# navidrome (SCAFFOLD, not deployed)

**Status: SCAFFOLD, 2026-09-14.** No `apps/navidrome.yaml` exists, so the root
Application does not see this directory and nothing here is applied. Turning it
on is one deliberate act: add the Application manifest after the fill list
below is done. Plan doc: homelab `docs/plans/navidrome.md` (de-Google Phase 3,
the Spotify cut, behind a family go/no-go gate).

## What is already decided (do not re-litigate)

Source: homelab `docs/plans/2026-09-post-window-layout.md` (MEDIA section and
validation table) and `docs/plans/degoogle-plan.md` Phase 3.

- **Library on JBNAS_MEDIA over NFS, read-only.** Navidrome never writes to the
  music folder. Same `nfs:` volume shape the media-integrity scanner Job uses
  (`192.168.0.201:/mnt/JBNAS_MEDIA/plex`, `readOnly: true`), against a new
  `music/` path that needs its own NFS export on the NAS.
- **Data dir (SQLite + cache) on a local-path PVC, never on the share.** A
  documented case shows a 3K-album scan taking >24 h with the DB on NFS versus
  minutes local.
- **No filesystem watcher, scheduled scans instead.** The watcher does not work
  over NFS/SMB. Navidrome's internal `ND_SCANSCHEDULE` is set to `0` (off) and
  scans are driven by the `scan-cronjob.yaml` here.
- **Mount guard on every scan, not just at pod start.** If the share drops
  mid-scan Navidrome can read the library as deleted and purge entries. The
  CronJob asserts the NFS mount (`.navidrome-library` marker file present)
  before calling the scan API. An initContainer would only cover pod start,
  which is the wrong window.
- **Exposure:** NodePort on the LAN, tailnet via the subnet router, never
  public. Subsonic API clients (Symfonium, DSub, Feishin) point at that port.
- **Footprint:** ~200 MB RAM, single Go binary. Does not touch the
  Immich/Odysseus RAM budget.
- Plain YAML, tautulli pattern (no upstream chart worth wrapping).

## To fill before `apps/navidrome.yaml` is added

- [ ] NAS: create `JBNAS_MEDIA/music` (or `plex/Music`, decide in the plan doc)
      and a read-only NFS export to JBK8S01 with `mapall nasuser`, mirroring
      the `plex` export. Drop a `.navidrome-library` marker file at its root.
      Update `NFS_PATH` in `deployment.yaml` and `scan-cronjob.yaml`.
- [ ] Pin the image by digest: `ghcr.io/navidrome/navidrome:0.64.0@sha256:...`
      (0.64.0 released 2026-09-12; check for newer at fill time).
- [ ] Sealed Secret `navidrome-admin` (first-run admin user) if headless
      bootstrap is wanted; otherwise first-visit UI setup and note it.
- [ ] Scan CronJob: create the API user/token the CronJob authenticates with
      and store it in a Sealed Secret; confirm the scan endpoint for the pinned
      version (`POST /api/scanner/scan` in 0.5x, verify).
- [ ] Blackbox probe of `/ping` on the NodePort (real-SLI convention,
      `probe_success=1` verified in Prometheus **before** merge).
- [ ] Alert: probe failure, warning until the family gate passes, then the
      family-services severity.
- [ ] Backup CronJob: nightly copy of the data PVC (SQLite + playlists) to
      `JBNAS_SSD/data/backups/navidrome/` with a heartbeat metric; add the
      path to the off-site seed. Small, but the play counts and playlists
      are the only state that is not re-derivable.
- [ ] Dashboard tile in `family-services-slo` once it is family-facing.
- [ ] Library build itself is out of scope for this chart (Bandcamp/Lidarr
      acquisitions, M3U playlist regeneration; see the plan doc).
