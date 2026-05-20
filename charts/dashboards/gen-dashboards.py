#!/usr/bin/env python3
"""Generates Grafana dashboard ConfigMap YAMLs for the homelab GitOps repo.

Conventions:
- Hosts and IPs live in HOSTS/IPS at the top so a portfolio extraction is just
  a matter of swapping those two dicts.
- Every panel helper accepts a ``ds=`` kwarg so Loki/Tempo panels can pin the
  datasource at panel level (per-target alone is overridden by Grafana).
- ``DASHBOARDS`` at the bottom is the single source of truth for what to emit.
"""
import copy
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

def row(id, title, y, description=""):
    return {"id": id, "title": title, "type": "row", "collapsed": False,
            "description": description,
            "gridPos": {"x": 0, "y": y, "w": 24, "h": 1}, "panels": []}

def stat(id, title, expr, unit, x, y, w, h, legend="", thresholds=None,
         color_mode="background", ds=None, description="", mappings=None):
    ds = ds or DS
    return {
        "id": id, "title": title, "type": "stat", "datasource": ds,
        "description": description,
        "gridPos": {"x": x, "y": y, "w": w, "h": h},
        "options": {
            "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
            "colorMode": color_mode, "graphMode": "none",
            "justifyMode": "auto", "orientation": "auto", "textMode": "auto"
        },
        "fieldConfig": {
            "defaults": {
                "unit": unit, "mappings": mappings or [],
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
               ds=None, description=""):
    return {
        "id": id, "title": title, "type": "timeseries", "datasource": ds or DS,
        "description": description,
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
             ds=None, description=""):
    return {
        "id": id, "title": title, "type": "bargauge", "datasource": ds or DS,
        "description": description,
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
          thresholds=None, ds=None, description=""):
    ds = ds or DS
    return {
        "id": id, "title": title, "type": "gauge", "datasource": ds,
        "description": description,
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

def text_panel(id, title, content, x, y, w, h, mode="markdown", description=""):
    return {
        "id": id, "title": title, "type": "text",
        "description": description,
        "gridPos": {"x": x, "y": y, "w": w, "h": h},
        "options": {"mode": mode, "content": content}
    }

def table(id, title, targets, x, y, w, h, ds=None, description=""):
    return {
        "id": id, "title": title, "type": "table", "datasource": ds or DS,
        "description": description,
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

# ── Firing-alert panels (ALERTS metric) ──────────────────────────────────────

def t_table(expr, ref="A"):
    """Instant target in table format — for the ALERTS metric."""
    return {"datasource": DS, "expr": expr, "instant": True,
            "format": "table", "legendFormat": "", "refId": ref}

# Noise columns to drop from an ALERTS table (rule-specific labels + internals).
_ALERT_HIDE = ["Time", "__name__", "Value", "alertstate", "namespace",
               "prometheus", "job", "endpoint", "container", "pod", "hostname",
               "device", "mountpoint", "attribute_name", "attribute_value_type",
               "fstype", "zpool", "model_name", "state", "name"]

WARN_THRESH = {"mode": "absolute",
               "steps": [{"color": "green", "value": None},
                         {"color": "orange", "value": 1}]}

def alerts_table(id, title, x, y, w, h, selector="", description=""):
    """Table of firing alerts over the ALERTS metric. ``selector`` is an extra
    label-matcher fragment, e.g. ``', service=~"plex|nas"'``."""
    expr = 'ALERTS{alertstate="firing"%s}' % selector
    return {
        "id": id, "title": title, "type": "table", "datasource": DS,
        "description": description,
        "gridPos": {"x": x, "y": y, "w": w, "h": h},
        "options": {"showHeader": True,
                    "sortBy": [{"displayName": "Severity", "desc": False}]},
        "targets": [t_table(expr)],
        "transformations": [{
            "id": "organize",
            "options": {
                "excludeByName": {n: True for n in _ALERT_HIDE},
                "renameByName": {"alertname": "Alert", "severity": "Severity",
                                 "service": "Service", "instance": "Host"},
                "indexByName": {"alertname": 0, "severity": 1,
                                "service": 2, "instance": 3},
            },
        }],
        "fieldConfig": {
            "defaults": {"custom": {"align": "auto", "filterable": True}},
            "overrides": [{
                "matcher": {"id": "byName", "options": "Severity"},
                "properties": [
                    {"id": "custom.cellOptions", "value": {"type": "color-text"}},
                    {"id": "mappings", "value": [{"type": "value", "options": {
                        "critical": {"color": "red", "text": "CRITICAL", "index": 0},
                        "warning": {"color": "orange", "text": "WARNING", "index": 1},
                    }}]},
                ],
            }],
        },
    }

def shift(panels, dy):
    """Return a copy of ``panels`` with every gridPos.y shifted down by ``dy``."""
    out = []
    for p in panels:
        p = copy.deepcopy(p)
        p["gridPos"]["y"] += dy
        out.append(p)
    return out

def with_alert_strip(panels, selector):
    """Prepend a firing-alerts row + table to a dashboard's panels."""
    strip = [
        row(900, "Active alerts — this dashboard's scope", 0),
        alerts_table(901, "Firing now", 0, 1, 24, 5, selector),
    ]
    return strip + shift(panels, 7)

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

def value_map(pairs):
    """pairs: {"0": ("DOWN","red"), "1": ("UP","green")} -> Grafana mapping list.

    Builds the ``fieldConfig.defaults.mappings`` structure so a numeric stat
    renders a word + colour instead of a bare 0/1. Threshold still drives the
    background; the mapping drives the displayed text."""
    return [{"type": "value", "options": {
        k: {"text": text, "color": color, "index": i}
        for i, (k, (text, color)) in enumerate(pairs.items())
    }}]

UP_DOWN     = value_map({"0": ("DOWN", "red"),     "1": ("UP", "green")})
ONLINE_DEG  = value_map({"0": ("DEGRADED", "red"), "1": ("ONLINE", "green")})
OK_FAIL     = value_map({"0": ("FAIL", "red"),     "1": ("OK", "green")})

def stat_with_target_color(id, title, expr, unit, x, y, w, h, target_pct,
                           description=""):
    """Stat panel: red below target, yellow within 0.1% of target, green above."""
    return stat(id, title, expr, unit, x, y, w, h, description=description,
                thresholds={
        "mode": "absolute",
        "steps": [
            {"color": "red", "value": None},
            {"color": "yellow", "value": target_pct - 0.1},
            {"color": "green", "value": target_pct},
        ]
    })

def stat_loki(id, title, expr, unit, x, y, w, h, thresholds=None,
              description="", mappings=None):
    """Loki-backed stat. Pins datasource at panel level (per-target is overridden)."""
    return stat(id, title, expr, unit, x, y, w, h,
                thresholds=thresholds, ds=LOKI_DS,
                description=description, mappings=mappings)

def loki_timeseries(id, title, targets, unit, x, y, w, h, fill=10,
                    description=""):
    return timeseries(id, title, targets, unit, x, y, w, h, fill=fill,
                      ds=LOKI_DS, description=description)

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

# node-exporter instance for the Proxmox host itself (host-level load/CPU/mem
# the pve exporter does not expose loadavg).
SRV_IP = IPS["srv"]
# Expected guest count: the six VMs/LXCs defined on the hypervisor (excludes the
# node and storage pseudo-entries).
PVE_GUEST_COUNT = 6

proxmox_panels = [
    row(1, f"{HOSTS['srv']} Host", 0),
    stat(2, "Host CPU",
         f'pve_cpu_usage_ratio{{id="node/{HOSTS["srv"]}"}} * 100',
         "percent", 0, 1, 6, 4,
         description="Hypervisor CPU utilisation across all cores. Normal "
                     "below 60%; yellow at 70%, red at 90% indicates the host "
                     "is CPU-constrained and guests may be throttled."),
    stat(3, "Host Memory",
         f'pve_memory_usage_bytes{{id="node/{HOSTS["srv"]}"}} / '
         f'pve_memory_size_bytes{{id="node/{HOSTS["srv"]}"}} * 100',
         "percent", 6, 1, 6, 4,
         description="Hypervisor RAM in use as a percentage of installed "
                     "memory. Normal below 70%; red at 90% risks the OOM "
                     "killer reaping a guest or ZFS ARC."),
    stat(4, "Host Uptime",
         f'pve_uptime_seconds{{id="node/{HOSTS["srv"]}"}}',
         "dtdurations", 12, 1, 6, 4, thresholds=GREEN_ONLY,
         description="Time since the hypervisor last booted. Informational, "
                     "no threshold; a sudden reset to near-zero means JBSRV01 "
                     "rebooted."),
    stat(5, f"Guests Running (of {PVE_GUEST_COUNT})",
         'count(pve_up{id!~"node/.*|storage/.*"} == 1)',
         "short", 18, 1, 6, 4, thresholds=GREEN_ONLY,
         description=f"Count of QEMU/LXC guests reporting pve_up==1. Expected "
                     f"{PVE_GUEST_COUNT} (all defined guests). A lower number "
                     f"means a guest is stopped or crashed."),

    row(6, "CPU & Memory Over Time", 5),
    timeseries(10, "Guest CPU %", [t(GUEST_CPU, "{{name}}")],
               "percent", 0, 6, 12, 8,
               description="Per-guest CPU utilisation over time. Each line is "
                           "one VM/LXC; sustained high lines flag a busy or "
                           "runaway guest."),
    timeseries(11, "Guest Memory Used", [t(GUEST_MEM, "{{name}}")],
               "bytes", 12, 6, 12, 8,
               description="Per-guest memory consumption over time. Watch for "
                           "a guest climbing steadily — a likely memory leak."),
    timeseries(20, "Hypervisor CPU & Memory over time",
               [t(f'pve_cpu_usage_ratio{{id="node/{HOSTS["srv"]}"}} * 100',
                  "Host CPU %"),
                t(f'pve_memory_usage_bytes{{id="node/{HOSTS["srv"]}"}} / '
                  f'pve_memory_size_bytes{{id="node/{HOSTS["srv"]}"}} * 100',
                  "Host Mem %", "B")],
               "percent", 0, 14, 12, 8,
               description="JBSRV01 host CPU and memory utilisation over time "
                           "(the history behind the instant Host CPU/Memory "
                           "stats). Both should track well below 90%."),
    timeseries(21, "Host load average",
               [t(f'node_load1{{instance="{SRV_IP}"}}',  "1m"),
                t(f'node_load5{{instance="{SRV_IP}"}}',  "5m",  "B"),
                t(f'node_load15{{instance="{SRV_IP}"}}', "15m", "C")],
               "short", 12, 14, 12, 8, fill=0,
               description="Run-queue load average for the hypervisor (1/5/15m "
                           "windows). Compare to the host vCPU count: load "
                           "near vCPUs means fully busy, well above means CPU "
                           "saturation and scheduling delay."),

    row(12, "Disk & Network I/O", 22),
    timeseries(13, "Disk Read",  [t(GUEST_DR,    "{{name}}")], "Bps", 0,  23, 12, 8,
               description="Per-guest disk read throughput (5m rate). Spikes "
                           "are normal during backups or boot."),
    timeseries(14, "Disk Write", [t(GUEST_DW,    "{{name}}")], "Bps", 12, 23, 12, 8,
               description="Per-guest disk write throughput (5m rate). "
                           "Sustained high write may indicate heavy logging "
                           "or a database workload."),
    timeseries(15, "Network Rx", [t(GUEST_NETRX, "{{name}}")], "Bps", 0,  31, 12, 8,
               description="Per-guest inbound network throughput (5m rate)."),
    timeseries(16, "Network Tx", [t(GUEST_NETTX, "{{name}}")], "Bps", 12, 31, 12, 8,
               description="Per-guest outbound network throughput (5m rate). "
                           "Plex streaming shows here as JBNAS01 Tx."),

    row(17, "Proxmox Storage", 39),
    bargauge(18, "Storage Disk Usage",
             [t('pve_disk_usage_bytes{id=~"storage/.*"} / '
                'pve_disk_size_bytes{id=~"storage/.*"} * 100',
                "{{id}}")],
             "percent", 0, 40, 12, 6,
             description="Percentage full of each Proxmox storage pool. Yellow "
                         "at 70%, red at 90% — a full storage pool blocks new "
                         "guest disks and snapshots."),
    bargauge(19, "Storage Free",
             [t('pve_disk_size_bytes{id=~"storage/.*"} - '
                'pve_disk_usage_bytes{id=~"storage/.*"}',
                "{{id}}")],
             "bytes", 12, 40, 12, 6, min_val=0, max_val=250 * 1024**3,
             description="Free space remaining per Proxmox storage pool. The "
                         "bar is scaled to a 250 GiB reference; the absolute "
                         "byte value is what matters."),
]

# ── Dashboard 2: NAS / ZFS ────────────────────────────────────────────────────

NAS = HOSTS["nas"]
NAS_IP = IPS["nas"]

# Pool-root datasets: their fill represents the whole pool's capacity.
ZFS_POOL_FS = 'fstype="zfs",device=~"JBNAS_SSD|JBNAS_MEDIA"'

zfs_panels = [
    row(1, "ZFS Pool Health", 0),
    stat(2, "JBNAS_SSD pool",   pool_state_online(NAS, "JBNAS_SSD"),
         "short", 0, 1, 6, 4, thresholds=ZERO_RED_ONE_GREEN,
         mappings=ONLINE_DEG,
         description="zpool health of JBNAS_SSD (mirror — SMB share + app "
                     "data). ONLINE = healthy; DEGRADED/other = zpool reports "
                     "a fault, investigate with `zpool status` on JBNAS01."),
    stat(3, "JBNAS_MEDIA pool", pool_state_online(NAS, "JBNAS_MEDIA"),
         "short", 6, 1, 6, 4, thresholds=ZERO_RED_ONE_GREEN,
         mappings=ONLINE_DEG,
         description="zpool health of JBNAS_MEDIA (the Plex library). This is "
                     "a stripe pool with no parity — DEGRADED here means data "
                     "loss is imminent, treat as a critical incident."),
    stat(4, "ARC Hit Ratio", arc_hit_ratio(NAS),
         "percent", 12, 1, 6, 4, thresholds=ARC_RATIO_THRESH,
         description="Fraction of ZFS reads served from the in-RAM ARC cache. "
                     "Normal above 90% (green); 70-90% yellow; below 70% red "
                     "means cache pressure and slower reads."),
    stat(5, "ARC Size", f'node_zfs_arc_size{{hostname="{NAS}"}}',
         "bytes", 18, 1, 6, 4, thresholds=GREEN_ONLY,
         description="Current size of the ZFS ARC cache in RAM. Informational, "
                     "no threshold; ARC grows to use spare memory and shrinks "
                     "under memory pressure."),

    row(6, "ZFS Pool Capacity", 5),
    bargauge(7, "Data pool capacity used %",
             [t(f'100 * (1 - node_filesystem_avail_bytes{{{ZFS_POOL_FS}}} / '
                f'node_filesystem_size_bytes{{{ZFS_POOL_FS}}})',
                "{{device}}")],
             "percent", 0, 6, 24, 6,
             description="Percentage full of each data pool (JBNAS_SSD, "
                         "JBNAS_MEDIA). Yellow at 70%, red at 90% — a full ZFS "
                         "pool degrades write performance and blocks "
                         "snapshots. boot-pool is excluded."),

    row(8, "ZFS ARC Detail", 12),
    timeseries(9, "ARC Size vs Max",
               [t(f'node_zfs_arc_size{{hostname="{NAS}"}}', "ARC Used"),
                t(f'node_zfs_arc_c_max{{hostname="{NAS}"}}', "ARC Max", "B"),
                t(f'node_zfs_arc_c_min{{hostname="{NAS}"}}', "ARC Min", "C")],
               "bytes", 0, 13, 24, 8,
               description="ZFS ARC size over time against its c_max ceiling "
                           "and c_min floor. ARC riding at c_max is healthy "
                           "(cache fully warmed); dropping toward c_min "
                           "indicates memory pressure on the NAS."),

    row(10, "ARC Hit/Miss Rate", 21),
    timeseries(11, "ARC Demand Hits / Misses",
               [t(f'rate(node_zfs_arc_demand_data_hits{{hostname="{NAS}"}}[5m])', "Data Hits"),
                t(f'rate(node_zfs_arc_demand_data_misses{{hostname="{NAS}"}}[5m])', "Data Misses", "B"),
                t(f'rate(node_zfs_arc_demand_metadata_hits{{hostname="{NAS}"}}[5m])', "Meta Hits", "C"),
                t(f'rate(node_zfs_arc_demand_metadata_misses{{hostname="{NAS}"}}[5m])', "Meta Misses", "D")],
               "ops", 0, 22, 24, 8,
               description="Per-second ARC demand hits vs misses for data and "
                           "metadata. A rising miss rate means the working "
                           "set no longer fits in ARC."),

    row(12, "NAS Host Resources", 30),
    timeseries(13, "NAS CPU %",
               [t(f'100 - (avg by (instance) (rate(node_cpu_seconds_total{{instance="{NAS_IP}",mode="idle"}}[5m])) * 100)',
                  "CPU %")],
               "percent", 0, 31, 12, 8,
               description="JBNAS01 CPU utilisation over time. Sustained high "
                           "values during scrubs or Plex transcodes are "
                           "expected; otherwise it should sit low."),
    timeseries(14, "NAS Memory",
               [t(f'node_memory_MemTotal_bytes{{instance="{NAS_IP}"}} - '
                  f'node_memory_MemAvailable_bytes{{instance="{NAS_IP}"}}', "Used"),
                t(f'node_memory_MemTotal_bytes{{instance="{NAS_IP}"}}', "Total", "B")],
               "bytes", 12, 31, 12, 8,
               description="JBNAS01 memory used vs total. Used tracking close "
                           "to Total is normal — ZFS ARC claims free RAM and "
                           "yields it on demand."),
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

# Backup-age tiles read backup_last_success_timestamp_seconds from each host's
# textfile_collector. Thresholds are per-job because cadences span 60x
# (1m mover vs 24h config backups); a uniform threshold would either flap on
# slow backups or hide a dead mover for hours.
# Entry: (label_selector, display_title, yellow_seconds, red_seconds)
BACKUP_JOBS = [
    ('name="jbsrv01-config-backup"',          "JBSRV01 config",     90000, 180000),
    ('name="jbdns01-config-backup"',          "JBDNS01 config",     90000, 180000),
    ('name="jbvm02-secrets-backup"',          "JBVM02 secrets",     90000, 180000),
    ('name="mc-world-backup",slot="daily"',   "MC world (daily)",   90000, 180000),
    ('name="mc-world-backup",slot="rolling"', "MC world (4h)",      18000,  36000),
    ('name="nas-dropbox-mover"',              "NAS dropbox mover",    180,    600),
]

def backup_age_stat(id, title, selector, x, y, w, h, yellow_s, red_s,
                    description=""):
    """Stat tile showing seconds since last backup heartbeat. Clamp guards
    against clock skew (TrueNAS time vs Prometheus time)."""
    return stat(id, title,
                f'clamp_min(time() - backup_last_success_timestamp_seconds{{{selector}}}, 0)',
                "dtdurations", x, y, w, h, description=description, thresholds={
                    "mode": "absolute",
                    "steps": [{"color": "green",  "value": None},
                              {"color": "yellow", "value": yellow_s},
                              {"color": "red",    "value": red_s}],
                })

CAP_BACKUP_GAPS = """
### Residual gaps not covered by heartbeats above

- **JBNAS_MEDIA** is a stripe pool (no parity, no snapshots). Single HDD failure loses 5 TB of Plex library.
- **`data` pool**: `_inbox` and `system-state` paths are single-copy (`mc-backups` is now covered via `mc-world-backup`).
- **JBVM01 credential store** is single-copy on local disk.

Tracked in `project_open_defects.md`.
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

    row(17, "Backup / DR Status: last successful heartbeat per job", 43),
    *[backup_age_stat(18 + i, title, selector,
                      (i % 6) * 4, 44, 4, 4, yellow_s, red_s)
      for i, (selector, title, yellow_s, red_s) in enumerate(BACKUP_JOBS)],
    # Meta-tile separates "textfile dir missing or unreadable" from "all
    # backups failed simultaneously". Without it the 6 tiles above light red
    # in unison and the real cause hides.
    stat(24, "Textfile scrape error (any host)",
         'max(node_textfile_scrape_error{job="node-exporter-external"})',
         "short", 0, 48, 6, 4, thresholds=ZERO_GREEN_ONE_RED),
    text_panel(25, "Residual gaps", CAP_BACKUP_GAPS, 6, 48, 18, 4),
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

    # Real user-facing DNS SLI — independent of pihole-exporter scrape.
    # probe_success is 0/1 (UDP/53 lookup of health.check.local).
    row(15, "Pi-hole DNS — Blackbox probe (real user-facing SLI)", 38),
    stat(16, "DNS probe status",
         'probe_success{module="dns_pihole"}',
         "short", 0, 39, 6, 4, thresholds=ZERO_RED_ONE_GREEN),
    timeseries(17, "Probe success (1 = OK, 0 = fail)",
               [t('probe_success{module="dns_pihole"}', "probe")],
               "short", 6, 39, 9, 4),
    timeseries(18, "DNS lookup time (s)",
               [t('probe_dns_lookup_time_seconds{module="dns_pihole"}', "lookup")],
               "s", 15, 39, 9, 4),

    row(19, "Network — Per-Host Throughput", 43),
    timeseries(20, "Receive (Bps)",
               [t('sum by (hostname) (rate(node_network_receive_bytes_total{device!~"lo|veth.*|tailscale.*"}[5m]))',
                  "{{hostname}}")],
               "Bps", 0, 44, 12, 8),
    timeseries(21, "Transmit (Bps)",
               [t('sum by (hostname) (rate(node_network_transmit_bytes_total{device!~"lo|veth.*|tailscale.*"}[5m]))',
                  "{{hostname}}")],
               "Bps", 12, 44, 12, 8),

    row(22, "Tailscale nodes (debug metrics)", 52),
    stat(23, "Nodes up", 'count(up{job="tailscale-nodes"} == 1)',
         "short", 0, 53, 6, 4, thresholds=GREEN_ONLY),
    stat(24, "Total dropped packets (since reboot)",
         'sum(netstack_dropped_packets)', "short", 6, 53, 6, 4,
         thresholds={"mode": "absolute",
                     "steps": [{"color": "green", "value": None},
                               {"color": "yellow", "value": 1000},
                               {"color": "red", "value": 100000}]}),
    timeseries(25, "Packet forward errors / sec",
               [t('sum by (hostname) (rate(netstack_ip_forward_errors[5m]))',
                  "{{hostname}}")],
               "ops", 12, 53, 12, 4),
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

# ── Alerts overview dashboard ────────────────────────────────────────────────

alerts_overview_panels = [
    row(900, "Active alerts", 0),
    stat(901, "Critical firing",
         'count(ALERTS{alertstate="firing",severity="critical"}) or vector(0)',
         "short", 0, 1, 8, 5, thresholds=ZERO_GREEN_ONE_RED),
    stat(902, "Warning firing",
         'count(ALERTS{alertstate="firing",severity="warning"}) or vector(0)',
         "short", 8, 1, 8, 5, thresholds=WARN_THRESH),
    stat(903, "Total firing",
         'count(ALERTS{alertstate="firing"}) or vector(0)',
         "short", 16, 1, 8, 5, thresholds=GREEN_ONLY),
    alerts_table(904, "All firing alerts", 0, 6, 24, 10),
    row(905, "History", 16),
    timeseries(906, "Firing alerts by severity",
               [t('count by (severity) (ALERTS{alertstate="firing"})', "{{severity}}")],
               "short", 0, 17, 24, 8),
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

# Single source of truth: (slug, title, panels, templating-extras, alert-selector)
# alert-selector is an extra ALERTS label matcher for the per-dashboard strip;
# None means no strip (the alerts-overview dashboard is itself the alert board).
DASHBOARDS = [
    ("proxmox-overview",     "Proxmox — Host & Guest Overview",   proxmox_panels,   None,                  ', service=~"storage|compute"'),
    ("nas-zfs",              "NAS — ZFS Pools & ARC",             zfs_panels,       None,                  ', alertname=~"Zfs.*|Smart.*|Nas.*"'),
    ("family-services-slo",  "Family Services — SLO Board",       slo_panels,       None,                  ', service=~"plex|minecraft|pihole|nas|tailscale"'),
    ("capacity-backup-dr",   "Capacity, Growth & Backup/DR",      capacity_panels,  None,                  ', service=~"storage|platform"'),
    ("logs-network-dns",     "Logs + Network/DNS Overview",       logs_panels,      None,                  ', service=~"loki|promtail|pihole"'),
    ("per-host-fleet",       "Per-Host Fleet Drill-Down",         per_host_panels,  [DS_VAR, HOSTNAME_VAR], ', hostname=~"$hostname"'),
    ("alerts-overview",      "Alerts — Fleet Overview",           alerts_overview_panels, None,            None),
]

for slug, title, panels, extra_vars, alert_sel in DASHBOARDS:
    if alert_sel is not None:
        panels = with_alert_strip(panels, alert_sel)
    db = dashboard(title, slug, panels, templating=extra_vars)
    with open(f"charts/dashboards/{slug}.yaml", "w") as f:
        f.write(configmap(f"grafana-dashboard-{slug}", f"{slug}.json", db))

print(f"Generated {len(DASHBOARDS)} dashboards.")
