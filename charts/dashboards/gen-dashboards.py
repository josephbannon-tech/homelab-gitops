#!/usr/bin/env python3
"""Generates Grafana dashboard ConfigMap YAMLs for the homelab GitOps repo.

Conventions:
- Hosts and IPs live in HOSTS/IPS at the top so a portfolio extraction is just
  a matter of swapping those two dicts.
- Every panel helper accepts a ``ds=`` kwarg so Loki/Tempo panels can pin the
  datasource at panel level (per-target alone is overridden by Grafana).
- ``DASHBOARDS`` at the bottom is the single source of truth for what to emit.
"""
import json

# ── Datasources ──────────────────────────────────────────────────────────────

DS = {"type": "prometheus", "uid": "${datasource}"}
LOKI_DS = {"type": "loki", "uid": "loki"}

DS_VAR = {
    "name": "datasource", "type": "datasource", "query": "prometheus",
    "current": {}, "hide": 0, "includeAll": False, "label": "Datasource", "refresh": 1
}

# ── Estate identity (swap these dicts for portfolio extraction) ──────────────

HOSTS = {
    "srv":  "JBSRV01",   # Proxmox hypervisor
    "nas":  "JBNAS01",   # TrueNAS SCALE
    "vm01": "JBVM01",    # Debian XFCE jumpbox
    "vm02": "JBVM02",    # Claude Code + code-server
    "vm03": "JBVM03",    # Minecraft
    "dns":  "JBDNS01",   # Pi-hole + Tailscale subnet router
    "k8s":  "JBK8S01",   # k3s + observability
}

# IPs are not secrets but they bind the dashboards to this estate; centralise
# them so a sanitised export is mechanical.
IPS = {
    "srv": "192.168.0.200",
    "nas": "192.168.0.201",
    "shield": "192.168.0.202",
    "vm01": "192.168.0.206",
    "vm02": "192.168.0.203",
    "vm03": "192.168.0.204",
    "dns": "192.168.0.205",
    "k8s": "192.168.0.207",
}

# ── Dashboard skeleton + base panels ─────────────────────────────────────────

def dashboard(title, uid, panels, templating=None, refresh="30s",
              time_from="now-6h"):
    return {
        "title": title, "uid": uid, "schemaVersion": 38, "version": 1,
        "refresh": refresh, "time": {"from": time_from, "to": "now"},
        "timezone": "Europe/London",
        "templating": {"list": templating or [DS_VAR]},
        "panels": panels, "links": []
    }

def row(id, title, y):
    return {"id": id, "title": title, "type": "row", "collapsed": False,
            "gridPos": {"x": 0, "y": y, "w": 24, "h": 1}, "panels": []}

def stat(id, title, expr, unit, x, y, w, h, legend="", thresholds=None,
         color_mode="background", ds=None):
    ds = ds or DS
    return {
        "id": id, "title": title, "type": "stat", "datasource": ds,
        "gridPos": {"x": x, "y": y, "w": w, "h": h},
        "options": {
            "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
            "colorMode": color_mode, "graphMode": "none",
            "justifyMode": "auto", "orientation": "auto", "textMode": "auto"
        },
        "fieldConfig": {
            "defaults": {
                "unit": unit, "mappings": [],
                "thresholds": thresholds or {
                    "mode": "absolute",
                    "steps": [{"color": "green", "value": None},
                              {"color": "yellow", "value": 70},
                              {"color": "red", "value": 90}]
                }
            },
            "overrides": []
        },
        "targets": [{"datasource": ds, "expr": expr, "instant": True,
                     "legendFormat": legend, "refId": "A"}]
    }

def timeseries(id, title, targets, unit, x, y, w, h, fill=10, stacking="none",
               ds=None):
    return {
        "id": id, "title": title, "type": "timeseries", "datasource": ds or DS,
        "gridPos": {"x": x, "y": y, "w": w, "h": h},
        "options": {
            "tooltip": {"mode": "multi", "sort": "desc"},
            "legend": {"displayMode": "table", "placement": "bottom",
                       "calcs": ["max", "mean", "lastNotNull"]},
            "stacking": {"mode": stacking}
        },
        "fieldConfig": {
            "defaults": {
                "unit": unit,
                "custom": {"lineWidth": 1, "fillOpacity": fill, "gradientMode": "opacity"}
            },
            "overrides": []
        },
        "targets": targets
    }

def bargauge(id, title, targets, unit, x, y, w, h, min_val=0, max_val=100,
             ds=None):
    return {
        "id": id, "title": title, "type": "bargauge", "datasource": ds or DS,
        "gridPos": {"x": x, "y": y, "w": w, "h": h},
        "options": {
            "reduceOptions": {"calcs": ["lastNotNull"]},
            "orientation": "horizontal", "displayMode": "gradient",
            "valueMode": "color"
        },
        "fieldConfig": {
            "defaults": {
                "unit": unit, "min": min_val, "max": max_val, "mappings": [],
                "thresholds": {
                    "mode": "percentage",
                    "steps": [{"color": "green", "value": None},
                              {"color": "yellow", "value": 70},
                              {"color": "red", "value": 90}]
                }
            },
            "overrides": []
        },
        "targets": targets
    }

def gauge(id, title, expr, unit, x, y, w, h, min_val=0, max_val=100,
          thresholds=None, ds=None):
    ds = ds or DS
    return {
        "id": id, "title": title, "type": "gauge", "datasource": ds,
        "gridPos": {"x": x, "y": y, "w": w, "h": h},
        "options": {
            "reduceOptions": {"calcs": ["lastNotNull"]},
            "showThresholdLabels": False, "showThresholdMarkers": True
        },
        "fieldConfig": {
            "defaults": {
                "unit": unit, "min": min_val, "max": max_val, "mappings": [],
                "thresholds": thresholds or {
                    "mode": "percentage",
                    "steps": [{"color": "green", "value": None},
                              {"color": "yellow", "value": 70},
                              {"color": "red", "value": 90}]
                }
            },
            "overrides": []
        },
        "targets": [{"datasource": ds, "expr": expr, "instant": True,
                     "legendFormat": "", "refId": "A"}]
    }

def text_panel(id, title, content, x, y, w, h, mode="markdown"):
    return {
        "id": id, "title": title, "type": "text",
        "gridPos": {"x": x, "y": y, "w": w, "h": h},
        "options": {"mode": mode, "content": content}
    }

def table(id, title, targets, x, y, w, h, ds=None):
    return {
        "id": id, "title": title, "type": "table", "datasource": ds or DS,
        "gridPos": {"x": x, "y": y, "w": w, "h": h},
        "options": {"showHeader": True},
        "fieldConfig": {"defaults": {"custom": {"align": "auto"}}, "overrides": []},
        "targets": targets,
    }

# Shorthand target builders. Pass ds=LOKI_DS for Loki targets.
def t(expr, legend, ref="A", ds=None):
    return {"datasource": ds or DS, "expr": expr, "legendFormat": legend,
            "refId": ref}

def t_loki(expr, legend, ref="A"):
    return {"datasource": LOKI_DS, "expr": expr, "legendFormat": legend,
            "refId": ref, "queryType": "range"}

# ── Reusable panel/threshold idioms ──────────────────────────────────────────

NO_THRESH  = {"mode": "absolute", "steps": [{"color": "text",  "value": None}]}
GREEN_ONLY = {"mode": "absolute", "steps": [{"color": "green", "value": None}]}
ZERO_GREEN_ONE_RED = {
    "mode": "absolute",
    "steps": [{"color": "green", "value": None}, {"color": "red", "value": 1}],
}
ZERO_RED_ONE_GREEN = {
    "mode": "absolute",
    "steps": [{"color": "red", "value": None}, {"color": "green", "value": 1}],
}
ARC_RATIO_THRESH = {
    "mode": "absolute",
    "steps": [{"color": "red",    "value": None},
              {"color": "yellow", "value": 70},
              {"color": "green",  "value": 90}],
}

def stat_with_target_color(id, title, expr, unit, x, y, w, h, target_pct):
    """Stat panel: red below target, yellow within 0.1% of target, green above."""
    return stat(id, title, expr, unit, x, y, w, h, thresholds={
        "mode": "absolute",
        "steps": [
            {"color": "red", "value": None},
            {"color": "yellow", "value": target_pct - 0.1},
            {"color": "green", "value": target_pct},
        ]
    })

def stat_loki(id, title, expr, unit, x, y, w, h, thresholds=None):
    """Loki-backed stat. Pins datasource at panel level (per-target is overridden)."""
    return stat(id, title, expr, unit, x, y, w, h,
                thresholds=thresholds, ds=LOKI_DS)

def loki_timeseries(id, title, targets, unit, x, y, w, h, fill=10):
    return timeseries(id, title, targets, unit, x, y, w, h, fill=fill, ds=LOKI_DS)

# ── Reusable query helpers ───────────────────────────────────────────────────

def arc_hit_ratio(host=HOSTS["nas"]):
    """ZFS ARC hit ratio (%) for the given host."""
    return (
        f'node_zfs_arc_hits{{hostname="{host}"}} / '
        f'(node_zfs_arc_hits{{hostname="{host}"}} + '
        f'node_zfs_arc_misses{{hostname="{host}"}}) * 100'
    )

def pool_state_online(host, pool):
    return (f'node_zfs_zpool_state{{hostname="{host}", zpool="{pool}", '
            f'state="online"}}')

def smart_warning_count(ip=IPS["srv"]):
    """Drives reporting smartctl exit_status > 0 on the given host."""
    return (f'count(smartctl_device_smartctl_exit_status{{instance="{ip}"}} '
            f'> 0) or vector(0)')

# ── Dashboard 1: Proxmox Overview ────────────────────────────────────────────

# All guest metrics join pve_guest_info on `id` to expose the VM `name` label.
# The id-filter excludes the host (node/*) and storage entries; for rate
# queries it must live INSIDE the metric selector (Prometheus rejects label
# matchers placed after a function call).
GUEST_CPU   = 'pve_cpu_usage_ratio{id!~"node/.*"} * on(id) group_left(name) pve_guest_info * 100'
GUEST_MEM   = 'pve_memory_usage_bytes{id!~"node/.*"} * on(id) group_left(name) pve_guest_info'
GUEST_NETRX = 'rate(pve_network_receive_bytes{id!~"node/.*|storage/.*"}[5m]) * on(id) group_left(name) pve_guest_info'
GUEST_NETTX = 'rate(pve_network_transmit_bytes{id!~"node/.*|storage/.*"}[5m]) * on(id) group_left(name) pve_guest_info'
GUEST_DR    = 'rate(pve_disk_read_bytes{id!~"node/.*|storage/.*"}[5m]) * on(id) group_left(name) pve_guest_info'
GUEST_DW    = 'rate(pve_disk_write_bytes{id!~"node/.*|storage/.*"}[5m]) * on(id) group_left(name) pve_guest_info'

proxmox_panels = [
    row(1, f"{HOSTS['srv']} Host", 0),
    stat(2, "Host CPU",
         f'pve_cpu_usage_ratio{{id="node/{HOSTS["srv"]}"}} * 100',
         "percent", 0, 1, 6, 4),
    stat(3, "Host Memory",
         f'pve_memory_usage_bytes{{id="node/{HOSTS["srv"]}"}} / '
         f'pve_memory_size_bytes{{id="node/{HOSTS["srv"]}"}} * 100',
         "percent", 6, 1, 6, 4),
    stat(4, "Host Uptime",
         f'pve_uptime_seconds{{id="node/{HOSTS["srv"]}"}}',
         "dtdurations", 12, 1, 6, 4, thresholds=GREEN_ONLY),
    stat(5, "Guests Online",
         'count(pve_up{id!~"node/.*|storage/.*"} == 1)',
         "short", 18, 1, 6, 4, thresholds=GREEN_ONLY),

    row(6, "Guest Status", 5),
    bargauge(7, "Guest CPU %", [t(GUEST_CPU, "{{name}}")],
             "percent", 0, 6, 12, 8),
    bargauge(8, "Guest Memory Used", [t(GUEST_MEM, "{{name}}")],
             "bytes", 12, 6, 12, 8, min_val=0, max_val=16 * 1024**3),

    row(9, "CPU & Memory Over Time", 14),
    timeseries(10, "Guest CPU %", [t(GUEST_CPU, "{{name}}")],
               "percent", 0, 15, 12, 8),
    timeseries(11, "Guest Memory Used", [t(GUEST_MEM, "{{name}}")],
               "bytes", 12, 15, 12, 8),

    row(12, "Disk & Network I/O", 23),
    timeseries(13, "Disk Read",  [t(GUEST_DR,    "{{name}}")], "Bps", 0,  24, 12, 8),
    timeseries(14, "Disk Write", [t(GUEST_DW,    "{{name}}")], "Bps", 12, 24, 12, 8),
    timeseries(15, "Network Rx", [t(GUEST_NETRX, "{{name}}")], "Bps", 0,  32, 12, 8),
    timeseries(16, "Network Tx", [t(GUEST_NETTX, "{{name}}")], "Bps", 12, 32, 12, 8),

    row(17, "Proxmox Storage", 40),
    bargauge(18, "Storage Disk Usage",
             [t('pve_disk_usage_bytes{id=~"storage/.*"} / '
                'pve_disk_size_bytes{id=~"storage/.*"} * 100',
                "{{id}}")],
             "percent", 0, 41, 12, 6),
    bargauge(19, "Storage Free",
             [t('pve_disk_size_bytes{id=~"storage/.*"} - '
                'pve_disk_usage_bytes{id=~"storage/.*"}',
                "{{id}}")],
             "bytes", 12, 41, 12, 6, min_val=0, max_val=250 * 1024**3),
]

# ── Dashboard 2: NAS / ZFS ────────────────────────────────────────────────────

NAS = HOSTS["nas"]
NAS_IP = IPS["nas"]

zfs_panels = [
    row(1, "ZFS Pool Health", 0),
    stat(2, "JBNAS_SSD",   pool_state_online(NAS, "JBNAS_SSD"),
         "short", 0, 1, 6, 4, thresholds=ZERO_RED_ONE_GREEN),
    stat(3, "JBNAS_MEDIA", pool_state_online(NAS, "JBNAS_MEDIA"),
         "short", 6, 1, 6, 4, thresholds=ZERO_RED_ONE_GREEN),
    stat(4, "ARC Hit Ratio", arc_hit_ratio(NAS),
         "percent", 12, 1, 6, 4, thresholds=ARC_RATIO_THRESH),
    stat(5, "ARC Size", f'node_zfs_arc_size{{hostname="{NAS}"}}',
         "bytes", 18, 1, 6, 4, thresholds=GREEN_ONLY),

    row(6, "ZFS ARC Detail", 5),
    gauge(7, "ARC Utilisation",
          f'node_zfs_arc_size{{hostname="{NAS}"}} / '
          f'node_zfs_arc_c_max{{hostname="{NAS}"}} * 100',
          "percent", 0, 6, 8, 8),
    timeseries(8, "ARC Size vs Max",
               [t(f'node_zfs_arc_size{{hostname="{NAS}"}}', "ARC Used"),
                t(f'node_zfs_arc_c_max{{hostname="{NAS}"}}', "ARC Max", "B"),
                t(f'node_zfs_arc_c_min{{hostname="{NAS}"}}', "ARC Min", "C")],
               "bytes", 8, 6, 16, 8),

    row(9, "ARC Hit/Miss Rate", 14),
    timeseries(10, "ARC Demand Hits / Misses",
               [t(f'rate(node_zfs_arc_demand_data_hits{{hostname="{NAS}"}}[5m])', "Data Hits"),
                t(f'rate(node_zfs_arc_demand_data_misses{{hostname="{NAS}"}}[5m])', "Data Misses", "B"),
                t(f'rate(node_zfs_arc_demand_metadata_hits{{hostname="{NAS}"}}[5m])', "Meta Hits", "C"),
                t(f'rate(node_zfs_arc_demand_metadata_misses{{hostname="{NAS}"}}[5m])', "Meta Misses", "D")],
               "ops", 0, 15, 24, 8),

    row(11, "NAS Host Resources", 23),
    timeseries(12, "NAS CPU %",
               [t(f'100 - (avg by (instance) (rate(node_cpu_seconds_total{{instance="{NAS_IP}",mode="idle"}}[5m])) * 100)',
                  "CPU %")],
               "percent", 0, 24, 12, 8),
    timeseries(13, "NAS Memory",
               [t(f'node_memory_MemTotal_bytes{{instance="{NAS_IP}"}} - '
                  f'node_memory_MemAvailable_bytes{{instance="{NAS_IP}"}}', "Used"),
                t(f'node_memory_MemTotal_bytes{{instance="{NAS_IP}"}}', "Total", "B")],
               "bytes", 12, 24, 12, 8),
]

# ── Dashboard 3: Family Services SLO ─────────────────────────────────────────

slo_panels = [
    row(1, "30-Day SLO Compliance (target lines: red=below, green=above)", 0),
    stat_with_target_color(2, "Plex (target 99.5%)",
        "slo:plex:availability:ratio_30d * 100", "percent", 0, 1, 6, 4, 99.5),
    stat_with_target_color(3, "Minecraft (target 99.0%)",
        "slo:minecraft:availability:ratio_30d * 100", "percent", 6, 1, 6, 4, 99.0),
    stat_with_target_color(4, "Pi-hole DNS (target 99.9%)",
        "slo:pihole:availability:ratio_30d * 100", "percent", 12, 1, 6, 4, 99.9),
    stat_with_target_color(5, "NAS reachable (target 99.9%)",
        "slo:nas:availability:ratio_30d * 100", "percent", 18, 1, 6, 4, 99.9),

    row(6, "Burn Rate (1.0 = on budget; >14.4 = critical, >6 = warning)", 5),
    timeseries(7, "Plex burn rate",
               [t("slo:plex:burn_rate:5m", "5m"),
                t("slo:plex:burn_rate:1h", "1h", "B"),
                t("slo:plex:burn_rate:6h", "6h", "C")],
               "short", 0, 6, 8, 7, fill=0),
    timeseries(8, "Minecraft burn rate",
               [t("slo:minecraft:burn_rate:5m", "5m"),
                t("slo:minecraft:burn_rate:1h", "1h", "B"),
                t("slo:minecraft:burn_rate:6h", "6h", "C")],
               "short", 8, 6, 8, 7, fill=0),
    timeseries(9, "Pi-hole burn rate",
               [t("slo:pihole:burn_rate:5m", "5m"),
                t("slo:pihole:burn_rate:1h", "1h", "B"),
                t("slo:pihole:burn_rate:6h", "6h", "C")],
               "short", 16, 6, 8, 7, fill=0),

    row(10, "Plex", 13),
    stat(11, "Server up", 'up{job="plex"}', "short", 0, 14, 6, 4,
         thresholds=ZERO_RED_ONE_GREEN),
    stat(12, "Library size",
         'sum(library_storage_total{server_type="plex"})', "bytes", 6, 14, 6, 4,
         thresholds=GREEN_ONLY),
    timeseries(13, "Estimated bandwidth out (5m rate)",
               [t('rate(estimated_transmit_bytes_total{server_type="plex"}[5m])',
                  "{{server}}")],
               "Bps", 12, 14, 12, 4),

    row(15, "Minecraft", 18),
    stat(16, "Server healthy", "minecraft_status_healthy", "short", 0, 19, 4, 4,
         thresholds=ZERO_RED_ONE_GREEN),
    stat(17, "Players online", "minecraft_status_players_online_count",
         "short", 4, 19, 4, 4, thresholds=GREEN_ONLY),
    stat(18, "Max players", "minecraft_status_players_max_count",
         "short", 8, 19, 4, 4, thresholds=NO_THRESH),
    timeseries(19, "Server response time",
               [t("minecraft_status_response_time_seconds", "ping")],
               "s", 12, 19, 12, 4),

    row(20, "Pi-hole DNS", 23),
    stat(21, "DNS up (scrape)", 'up{job="pihole"}', "short", 0, 24, 4, 4,
         thresholds=ZERO_RED_ONE_GREEN),
    stat(22, "Queries today", "sum(pihole_dns_queries_today)",
         "short", 4, 24, 4, 4, thresholds=GREEN_ONLY),
    stat(23, "Blocked %", "avg(pihole_ads_percentage_today)",
         "percent", 8, 24, 4, 4, thresholds=NO_THRESH),
    timeseries(24, "Queries/sec (5m rate)",
               [t("rate(pihole_dns_queries_all_types[5m])", "qps")],
               "ops", 12, 24, 12, 4),

    row(25, "NAS / Storage Health", 28),
    stat(26, "NAS reachable",
         f'up{{job="node-exporter-external", hostname="{NAS}"}}',
         "short", 0, 29, 4, 4, thresholds=ZERO_RED_ONE_GREEN),
    # Filter boot-pool out — only data pools (JBNAS_SSD, JBNAS_MEDIA) count.
    stat(27, "Data pools online",
         f'count(node_zfs_zpool_state{{hostname="{NAS}", state="online", '
         f'zpool!="boot-pool"}} == 1)',
         "short", 4, 29, 4, 4,
         thresholds={"mode": "absolute",
                     "steps": [{"color": "red", "value": None},
                               {"color": "yellow", "value": 1},
                               {"color": "green", "value": 2}]}),
    stat(28, "ARC hit ratio", arc_hit_ratio(NAS),
         "percent", 8, 29, 4, 4, thresholds=ARC_RATIO_THRESH),
    # Drives with smartctl exit_status > 0 are flagged. Exit 64 means
    # "DISK FAILING" per smartctl's bitmask. Real signal even at value 1+.
    stat(29, "Drives with SMART warning (red = action needed)",
         smart_warning_count(),
         "short", 12, 29, 6, 4, thresholds=ZERO_GREEN_ONE_RED),
    stat(30, "Tailscale nodes up",
         'count(up{job="tailscale-nodes"} == 1)', "short", 18, 29, 6, 4,
         thresholds=GREEN_ONLY),
]

# ── Dashboard 4: Capacity / Growth / Backup-DR ───────────────────────────────

CAP_BACKUP_GAPS = """
### Open backup / DR gaps (from `project_open_defects`)

- **JBSRV01** has no scheduled config backup. Loss of `/etc/pve` is reconstructable but slow.
- **JBDNS01** has no backup at all. Pi-hole rebuild is doc-driven; gravity list, custom DNS, DHCP leases all rebuild from code.
- **JBNAS_MEDIA** is a stripe pool (no parity, no snapshots). Single HDD failure loses 5 TB of Plex library.
- **`data` pool** rsync targets back up project data, but `_inbox`, `mc-backups`, and `system-state` are single-copy.
- **JBVM01 credential store** is single-copy on local disk.

These are tracked in `project_open_defects.md` (memory). When a textfile-collector
backup-status pipeline lands, the panels above this one will populate with
last-success timestamps and replace this static list.
"""

FS_FILTER = ('fstype!~"tmpfs|overlay|squashfs|devtmpfs|fuse.*|ramfs|autofs|'
             'nsfs|tracefs|securityfs|cgroup.*|bpf|debugfs|configfs|hugetlbfs|'
             'mqueue|pstore|sysfs|proc|none",mountpoint!~"/var/lib/kubelet.*|'
             '/var/lib/docker.*|/run.*|/snap.*|/boot/efi"')

# Days-to-full per filesystem via predict_linear (positive value = days remaining
# under current fill rate; absent series = filesystem stable or growing slowly).
DAYS_TO_FULL = (
    f'(node_filesystem_avail_bytes{{{FS_FILTER}}} / '
    f' (-deriv(node_filesystem_avail_bytes{{{FS_FILTER}}}[7d]) > 0) ) / 86400'
)

capacity_panels = [
    row(1, "Filesystem Free Space (%) — across all hosts", 0),
    bargauge(2, "Free %",
             [t(f'100 * node_filesystem_avail_bytes{{{FS_FILTER}}} / '
                f'node_filesystem_size_bytes{{{FS_FILTER}}}',
                '{{hostname}}: {{mountpoint}}')],
             "percent", 0, 1, 24, 10),

    row(3, "Filesystem Days-to-Full (linear projection from last 7d)", 11),
    bargauge(4, "Days remaining (positive = filling; absent = stable/growing slowly)",
             [t(DAYS_TO_FULL, '{{hostname}}: {{mountpoint}}')],
             "d", 0, 12, 24, 8, min_val=0, max_val=180),

    row(5, "ZFS Pools (NAS)", 20),
    stat(6, "JBNAS_SSD pool state",   pool_state_online(NAS, "JBNAS_SSD"),
         "short", 0, 21, 6, 4, thresholds=ZERO_RED_ONE_GREEN),
    stat(7, "JBNAS_MEDIA pool state", pool_state_online(NAS, "JBNAS_MEDIA"),
         "short", 6, 21, 6, 4, thresholds=ZERO_RED_ONE_GREEN),
    stat(8, "ARC hit ratio", arc_hit_ratio(NAS),
         "percent", 12, 21, 6, 4, thresholds=ARC_RATIO_THRESH),
    stat(9, "ARC size", f'node_zfs_arc_size{{hostname="{NAS}"}}',
         "bytes", 18, 21, 6, 4, thresholds=GREEN_ONLY),

    row(10, "Estate Headroom — RAM & CPU per Host", 25),
    # avg by (hostname) drops the noisy {namespace, endpoint, ...} labels so
    # the legend reads as just the hostname.
    timeseries(11, "Free memory (%)",
               [t('100 * avg by (hostname) (node_memory_MemAvailable_bytes / '
                  'node_memory_MemTotal_bytes)', "{{hostname}}")],
               "percent", 0, 26, 12, 8),
    timeseries(12, "CPU idle (%)",
               [t('100 * avg by (hostname) (rate(node_cpu_seconds_total{mode="idle"}[5m]))',
                  "{{hostname}}")],
               "percent", 12, 26, 12, 8),

    row(13, f"SMART — Power-on time + warnings ({HOSTS['srv']} = all physical drives)", 34),
    timeseries(14, "Power-on hours per drive",
               [t(f'smartctl_device_power_on_seconds{{instance="{IPS["srv"]}"}} / 3600',
                  "{{device}} {{model_name}}")],
               "h", 0, 35, 16, 8),
    stat(15, "Drives with SMART warning (exit_status > 0)",
         smart_warning_count(),
         "short", 16, 35, 8, 4, thresholds=ZERO_GREEN_ONE_RED),
    stat(16, "Drives with SMART status FAILED",
         f'count(smartctl_device_smart_status{{instance="{IPS["srv"]}"}} == 0) '
         f'or vector(0)',
         "short", 16, 39, 8, 4, thresholds=ZERO_GREEN_ONE_RED),

    row(17, "Backup / DR Status", 43),
    text_panel(18, "Open gaps", CAP_BACKUP_GAPS, 0, 44, 24, 9),
]

# ── Dashboard 5: Logs + Network / DNS Overview ──────────────────────────────

LOG_RATE_BY_HOST  = 'sum by (hostname) (rate({job="systemd-journal"}[5m]))'
ERR_RATE_BY_HOST  = 'sum by (hostname) (rate({job="systemd-journal"} |~ "(?i)error"[5m]))'
WARN_RATE_BY_HOST = 'sum by (hostname) (rate({job="systemd-journal"} |~ "(?i)warn"[5m]))'
SSHD_FAILS        = 'sum by (hostname) (count_over_time({job="systemd-journal", unit="ssh.service"} |~ "Failed password"[24h]))'
TOP_NOISY_UNITS   = 'topk(10, sum by (hostname, unit) (rate({job="systemd-journal"}[5m])))'

logs_panels = [
    row(1, "Loki — Log Activity (last 5m)", 0),
    loki_timeseries(2, "Log rate per host (lines/sec)",
               [t_loki(LOG_RATE_BY_HOST, "{{hostname}}")],
               "ops", 0, 1, 12, 8),
    loki_timeseries(3, "Error rate per host (lines/sec)",
               [t_loki(ERR_RATE_BY_HOST, "{{hostname}}")],
               "ops", 12, 1, 12, 8),
    loki_timeseries(4, "Warning rate per host (lines/sec)",
               [t_loki(WARN_RATE_BY_HOST, "{{hostname}}")],
               "ops", 0, 9, 12, 8),
    loki_timeseries(5, "Top 10 noisy systemd units (lines/sec)",
               [t_loki(TOP_NOISY_UNITS, "{{hostname}} / {{unit}}")],
               "ops", 12, 9, 12, 8),

    row(6, "SSH auth failures (last 24h, journal)", 17),
    loki_timeseries(7, "Failed SSH password attempts",
               [t_loki(SSHD_FAILS, "{{hostname}}")],
               "short", 0, 18, 24, 8),

    row(8, "Pi-hole DNS — Live", 26),
    stat(9,  "Queries (today)", "sum(pihole_dns_queries_today)",
         "short", 0, 27, 6, 4, thresholds=GREEN_ONLY),
    stat(10, "Blocked (today)", "sum(pihole_ads_blocked_today)",
         "short", 6, 27, 6, 4, thresholds=GREEN_ONLY),
    stat(11, "Blocked %", "avg(pihole_ads_percentage_today)",
         "percent", 12, 27, 6, 4, thresholds=NO_THRESH),
    stat(12, "Domains in blocklist", "max(pihole_domains_being_blocked)",
         "short", 18, 27, 6, 4, thresholds=NO_THRESH),
    timeseries(13, "DNS queries/sec (5m rate)",
               [t("rate(pihole_dns_queries_all_types[5m])", "queries/s")],
               "ops", 0, 31, 12, 7),
    timeseries(14, "Cache vs forwarded (1h rate)",
               [t("rate(pihole_queries_cached[1h])", "cached"),
                t("rate(pihole_queries_forwarded[1h])", "forwarded", "B")],
               "ops", 12, 31, 12, 7),

    row(15, "Network — Per-Host Throughput", 38),
    timeseries(16, "Receive (Bps)",
               [t('sum by (hostname) (rate(node_network_receive_bytes_total{device!~"lo|veth.*|tailscale.*"}[5m]))',
                  "{{hostname}}")],
               "Bps", 0, 39, 12, 8),
    timeseries(17, "Transmit (Bps)",
               [t('sum by (hostname) (rate(node_network_transmit_bytes_total{device!~"lo|veth.*|tailscale.*"}[5m]))',
                  "{{hostname}}")],
               "Bps", 12, 39, 12, 8),

    row(18, "Tailscale nodes (debug metrics)", 47),
    stat(19, "Nodes up", 'count(up{job="tailscale-nodes"} == 1)',
         "short", 0, 48, 6, 4, thresholds=GREEN_ONLY),
    stat(20, "Total dropped packets (since reboot)",
         'sum(netstack_dropped_packets)', "short", 6, 48, 6, 4,
         thresholds={"mode": "absolute",
                     "steps": [{"color": "green", "value": None},
                               {"color": "yellow", "value": 1000},
                               {"color": "red", "value": 100000}]}),
    timeseries(21, "Packet forward errors / sec",
               [t('sum by (hostname) (rate(netstack_ip_forward_errors[5m]))',
                  "{{hostname}}")],
               "ops", 12, 48, 12, 4),
]

# ── Dashboard 6: Per-Host Fleet Drill-Down ───────────────────────────────────
#
# A single dashboard for any host. Drives every panel from a `$hostname`
# Prometheus variable so swapping hosts is a dropdown change. Loki panels
# inherit by joining on the same hostname label.

HOSTNAME_VAR = {
    "name": "hostname",
    "type": "query",
    "datasource": DS,
    "query": "label_values(node_uname_info, nodename)",
    "current": {}, "refresh": 1, "includeAll": False, "multi": False,
    "label": "Host", "hide": 0, "sort": 1,
}

per_host_panels = [
    row(1, "Snapshot", 0),
    stat(2, "Uptime",
         'time() - node_boot_time_seconds{hostname="$hostname"}',
         "dtdurations", 0, 1, 5, 4, thresholds=GREEN_ONLY),
    stat(3, "Load (1m)",
         'node_load1{hostname="$hostname"}',
         "short", 5, 1, 5, 4, thresholds=NO_THRESH),
    stat(4, "CPU busy %",
         '100 - (avg by (hostname) (rate(node_cpu_seconds_total{hostname="$hostname",mode="idle"}[5m])) * 100)',
         "percent", 10, 1, 5, 4),
    stat(5, "Free RAM %",
         '100 * node_memory_MemAvailable_bytes{hostname="$hostname"} / node_memory_MemTotal_bytes{hostname="$hostname"}',
         "percent", 15, 1, 5, 4,
         thresholds={"mode": "absolute",
                     "steps": [{"color": "red", "value": None},
                               {"color": "yellow", "value": 10},
                               {"color": "green", "value": 25}]}),
    stat(6, "Root FS free %",
         '100 * node_filesystem_avail_bytes{hostname="$hostname",mountpoint="/"} / '
         'node_filesystem_size_bytes{hostname="$hostname",mountpoint="/"}',
         "percent", 20, 1, 4, 4,
         thresholds={"mode": "absolute",
                     "steps": [{"color": "red", "value": None},
                               {"color": "yellow", "value": 10},
                               {"color": "green", "value": 20}]}),

    row(7, "CPU & Memory", 5),
    timeseries(8, "CPU usage by mode",
               [t('sum by (mode) (rate(node_cpu_seconds_total{hostname="$hostname",mode!="idle"}[5m])) '
                  '/ on() group_left scalar(count(node_cpu_seconds_total{hostname="$hostname",mode="idle"}))',
                  "{{mode}}")],
               "percentunit", 0, 6, 12, 8, stacking="normal"),
    timeseries(9, "Memory breakdown",
               [t('node_memory_MemTotal_bytes{hostname="$hostname"} - '
                  'node_memory_MemAvailable_bytes{hostname="$hostname"}', "Used"),
                t('node_memory_Cached_bytes{hostname="$hostname"} + '
                  'node_memory_Buffers_bytes{hostname="$hostname"}', "Cache+Buffers", "B"),
                t('node_memory_MemFree_bytes{hostname="$hostname"}', "Free", "C")],
               "bytes", 12, 6, 12, 8),

    row(10, "Disk & Network", 14),
    timeseries(11, "Disk I/O (Bps)",
               [t('rate(node_disk_read_bytes_total{hostname="$hostname",device!~"loop.*|dm-.*"}[5m])',
                  "read {{device}}"),
                t('rate(node_disk_written_bytes_total{hostname="$hostname",device!~"loop.*|dm-.*"}[5m])',
                  "write {{device}}", "B")],
               "Bps", 0, 15, 12, 8),
    timeseries(12, "Network rx/tx (Bps)",
               [t('rate(node_network_receive_bytes_total{hostname="$hostname",device!~"lo|veth.*|tailscale.*|cni.*|cali.*"}[5m])',
                  "rx {{device}}"),
                t('rate(node_network_transmit_bytes_total{hostname="$hostname",device!~"lo|veth.*|tailscale.*|cni.*|cali.*"}[5m])',
                  "tx {{device}}", "B")],
               "Bps", 12, 15, 12, 8),
    bargauge(13, "Filesystem usage % (per mountpoint)",
             [t(f'100 - (100 * node_filesystem_avail_bytes{{hostname="$hostname",{FS_FILTER}}} / '
                f'node_filesystem_size_bytes{{hostname="$hostname",{FS_FILTER}}})',
                "{{mountpoint}}")],
             "percent", 0, 23, 24, 6),

    row(14, "Logs (Loki, journal)", 29),
    loki_timeseries(15, "Top 10 noisy units (lines/sec)",
                    [t_loki('topk(10, sum by (unit) (rate({hostname="$hostname",job="systemd-journal"}[5m])))',
                            "{{unit}}")],
                    "ops", 0, 30, 12, 8),
    loki_timeseries(16, "Error / warn rate",
                    [t_loki('sum(rate({hostname="$hostname",job="systemd-journal"} |~ "(?i)error"[5m]))',
                            "errors"),
                     t_loki('sum(rate({hostname="$hostname",job="systemd-journal"} |~ "(?i)warn"[5m]))',
                            "warnings", "B")],
                    "ops", 12, 30, 12, 8),
    loki_timeseries(17, "SSH failed-password attempts (24h count)",
                    [t_loki('sum(count_over_time({hostname="$hostname",job="systemd-journal",unit="ssh.service"} '
                            '|~ "Failed password"[24h]))', "fails")],
                    "short", 0, 38, 24, 6),
]

# ── Emit ConfigMap YAMLs ──────────────────────────────────────────────────────

def configmap(name, filename, db):
    db_json = json.dumps(db, indent=2)
    lines = [
        "apiVersion: v1",
        "kind: ConfigMap",
        "metadata:",
        f"  name: {name}",
        "  namespace: monitoring",
        "  labels:",
        '    grafana_dashboard: "1"',
        "data:",
        f"  {filename}: |",
    ]
    for line in db_json.splitlines():
        lines.append("    " + line)
    return "\n".join(lines) + "\n"

# Single source of truth: (slug, title, panels, templating-extras)
DASHBOARDS = [
    ("proxmox-overview",     "Proxmox — Host & Guest Overview",   proxmox_panels,   None),
    ("nas-zfs",              "NAS — ZFS Pools & ARC",             zfs_panels,       None),
    ("family-services-slo",  "Family Services — SLO Board",       slo_panels,       None),
    ("capacity-backup-dr",   "Capacity, Growth & Backup/DR",      capacity_panels,  None),
    ("logs-network-dns",     "Logs + Network/DNS Overview",       logs_panels,      None),
    ("per-host-fleet",       "Per-Host Fleet Drill-Down",         per_host_panels,  [DS_VAR, HOSTNAME_VAR]),
]

for slug, title, panels, extra_vars in DASHBOARDS:
    db = dashboard(title, slug, panels, templating=extra_vars)
    with open(f"charts/dashboards/{slug}.yaml", "w") as f:
        f.write(configmap(f"grafana-dashboard-{slug}", f"{slug}.json", db))

print(f"Generated {len(DASHBOARDS)} dashboards.")
