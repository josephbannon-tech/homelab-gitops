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
             ds=None, description="", thresholds=None):
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
                "thresholds": thresholds or {
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
        alerts_table(901, "Firing now", 0, 1, 24, 5, selector,
                     description="Alerts firing right now that fall within "
                                 "this dashboard's scope. Empty is good — any "
                                 "row is a live incident for these services."),
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

# The data-holding child datasets. The pool-root datasets (JBNAS_SSD,
# JBNAS_MEDIA) report near-zero fill because the data lives in child datasets,
# so capacity panels must query the datasets that actually hold data.
ZFS_DATA_FS = 'fstype="zfs",mountpoint=~"/mnt/JBNAS_SSD/data|/mnt/JBNAS_MEDIA/plex"'

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
    bargauge(7, "Data dataset usage %",
             [t(f'100 * (1 - node_filesystem_avail_bytes{{{ZFS_DATA_FS}}} / '
                f'node_filesystem_size_bytes{{{ZFS_DATA_FS}}})',
                "{{mountpoint}}")],
             "percent", 0, 6, 24, 6,
             description="Space used by the data-holding ZFS datasets "
                         "(JBNAS_SSD/data, JBNAS_MEDIA/plex) as a percentage of "
                         "used + pool-free. Yellow 70%, red 90% — a near-full "
                         "pool degrades ZFS write performance."),

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

_BURN_DESC = ("SLO error-budget burn rate over 5m/1h/6h windows. 1.0 = "
              "consuming budget exactly on pace; above 6 is a warning, above "
              "14.4 is critical and the 30-day SLO is at risk.")

slo_panels = [
    row(1, "30-Day SLO Compliance (target lines: red=below, green=above)", 0),
    stat_with_target_color(2, "Plex (target 99.5%)",
        "slo:plex:availability:ratio_30d * 100", "percent", 0, 1, 5, 4, 99.5,
        description="Plex availability over the trailing 30 days against the "
                    "99.5% target. Green = meeting SLO, yellow = within 0.1% "
                    "of the line, red = SLO breached."),
    stat_with_target_color(3, "Minecraft (target 99.0%)",
        "slo:minecraft:availability:ratio_30d * 100", "percent", 5, 1, 5, 4, 99.0,
        description="Minecraft server availability over the trailing 30 days "
                    "against the 99.0% target. Red = the 30-day SLO is "
                    "breached."),
    stat_with_target_color(4, "Pi-hole DNS (real probe, 99.9%)",
        "slo:pihole_dns:availability:ratio_30d * 100", "percent", 10, 1, 5, 4, 99.9,
        description="Pi-hole DNS availability from the blackbox UDP/53 probe "
                    "(real user-facing resolution), trailing 30 days vs the "
                    "99.9% target — not the exporter-scrape signal."),
    stat_with_target_color(5, "NAS reachable (target 99.9%)",
        "slo:nas:availability:ratio_30d * 100", "percent", 15, 1, 5, 4, 99.9,
        description="JBNAS01 reachability over the trailing 30 days against "
                    "the 99.9% target. Red = the NAS missed its SLO."),
    stat_with_target_color(6, "Tailscale (target 99.0%)",
        "slo:tailscale:availability:ratio_30d * 100", "percent", 20, 1, 4, 4, 99.0,
        description="Tailscale mesh availability over the trailing 30 days "
                    "against the 99.0% target — covers remote access to the "
                    "estate."),

    row(7, "Burn Rate (1.0 = on budget; >14.4 = critical, >6 = warning)", 5),
    timeseries(8, "Plex burn rate",
               [t("slo:plex:burn_rate:5m", "5m"),
                t("slo:plex:burn_rate:1h", "1h", "B"),
                t("slo:plex:burn_rate:6h", "6h", "C")],
               "short", 0, 6, 6, 7, fill=0, description=_BURN_DESC),
    timeseries(9, "Minecraft burn rate",
               [t("slo:minecraft:burn_rate:5m", "5m"),
                t("slo:minecraft:burn_rate:1h", "1h", "B"),
                t("slo:minecraft:burn_rate:6h", "6h", "C")],
               "short", 6, 6, 6, 7, fill=0, description=_BURN_DESC),
    timeseries(10, "Pi-hole DNS burn rate",
               [t("slo:pihole_dns:burn_rate:5m", "5m"),
                t("slo:pihole_dns:burn_rate:1h", "1h", "B"),
                t("slo:pihole_dns:burn_rate:6h", "6h", "C")],
               "short", 12, 6, 6, 7, fill=0, description=_BURN_DESC),
    timeseries(11, "Tailscale burn rate",
               [t("slo:tailscale:burn_rate:5m", "5m"),
                t("slo:tailscale:burn_rate:1h", "1h", "B"),
                t("slo:tailscale:burn_rate:6h", "6h", "C")],
               "short", 18, 6, 6, 7, fill=0, description=_BURN_DESC),

    row(12, "Plex", 13),
    stat(13, "Plex server", 'up{job="plex"}', "short", 0, 14, 6, 4,
         thresholds=ZERO_RED_ONE_GREEN, mappings=UP_DOWN,
         description="UP = the plex-exporter scrape succeeded (the Plex Media "
                     "Server process is responding). DOWN = Plex is "
                     "unreachable."),
    stat(14, "Library size",
         'sum(library_storage_total{server_type="plex"})', "bytes", 6, 14, 6, 4,
         thresholds=GREEN_ONLY,
         description="Total size of the Plex media library. Informational, "
                     "no threshold; it should only grow."),
    timeseries(15, "Estimated bandwidth out (5m rate)",
               [t('rate(estimated_transmit_bytes_total{server_type="plex"}[5m])',
                  "{{server}}")],
               "Bps", 12, 14, 12, 4,
               description="Outbound bandwidth Plex is serving (5m rate) — a "
                           "proxy for active streaming load."),

    row(16, "Minecraft", 18),
    stat(17, "Minecraft server", "minecraft_status_healthy", "short", 0, 19, 6, 4,
         thresholds=ZERO_RED_ONE_GREEN, mappings=OK_FAIL,
         description="OK = the Minecraft server responded to a status ping. "
                     "FAIL = the server is down or not accepting connections."),
    stat(18, "Players online", "minecraft_status_players_online_count",
         "short", 6, 19, 6, 4, thresholds=GREEN_ONLY,
         description="Players currently connected to the Minecraft server. "
                     "Informational; the server is capped at "
                     "minecraft_status_players_max_count slots."),
    timeseries(19, "Server response time",
               [t("minecraft_status_response_time_seconds", "ping")],
               "s", 12, 19, 12, 4,
               description="Server status-ping round-trip time. Rising "
                           "latency points to CPU pressure or world lag on "
                           "JBVM03."),

    row(20, "Pi-hole DNS", 23),
    stat(21, "Pi-hole exporter", 'up{job="pihole"}', "short", 0, 24, 6, 4,
         thresholds=ZERO_RED_ONE_GREEN, mappings=UP_DOWN,
         description="UP = the pihole-exporter scrape succeeded. This is the "
                     "exporter-scrape signal, NOT real DNS resolution — the "
                     "real probe drives the SLO tile above."),
    stat(22, "Queries today", "sum(pihole_dns_queries_today)",
         "short", 6, 24, 3, 4, thresholds=GREEN_ONLY,
         description="Total DNS queries Pi-hole has handled today. "
                     "Informational; resets at midnight."),
    stat(23, "Blocked %", "avg(pihole_ads_percentage_today)",
         "percent", 9, 24, 3, 4, thresholds=NO_THRESH,
         description="Share of today's DNS queries blocked as ads/trackers. "
                     "Informational, no threshold; typically 10-25% for this "
                     "estate's blocklists."),
    timeseries(24, "Queries/sec (5m rate)",
               [t("rate(pihole_dns_queries_all_types[5m])", "qps")],
               "ops", 12, 24, 12, 4,
               description="DNS query rate Pi-hole is serving (5m rate). A "
                           "drop to zero with the exporter UP means clients "
                           "stopped querying."),

    row(25, "NAS / Storage Health", 28),
    stat(26, "NAS reachable",
         f'up{{job="node-exporter-external", hostname="{NAS}"}}',
         "short", 0, 29, 4, 4, thresholds=ZERO_RED_ONE_GREEN, mappings=UP_DOWN,
         description="UP = the node-exporter on JBNAS01 is being scraped — the "
                     "NAS is up and on the network. DOWN = NAS unreachable."),
    # Filter boot-pool out — only data pools (JBNAS_SSD, JBNAS_MEDIA) count.
    stat(27, "Data pools online",
         f'count(node_zfs_zpool_state{{hostname="{NAS}", state="online", '
         f'zpool!="boot-pool"}} == 1)',
         "short", 4, 29, 4, 4,
         thresholds={"mode": "absolute",
                     "steps": [{"color": "red", "value": None},
                               {"color": "yellow", "value": 1},
                               {"color": "green", "value": 2}]},
         description="Count of data pools (JBNAS_SSD, JBNAS_MEDIA) reporting "
                     "ONLINE. Expect 2; anything less means a pool is "
                     "degraded or faulted."),
    stat(28, "ARC hit ratio", arc_hit_ratio(NAS),
         "percent", 8, 29, 4, 4, thresholds=ARC_RATIO_THRESH,
         description="ZFS ARC cache hit ratio on the NAS. Normal above 90%; "
                     "below 70% (red) means reads are missing cache."),
    # Drives with smartctl exit_status > 0 are flagged. Exit 64 means
    # "DISK FAILING" per smartctl's bitmask. Real signal even at value 1+.
    stat(29, "Drives with SMART warning",
         smart_warning_count(),
         "short", 12, 29, 6, 4, thresholds=ZERO_GREEN_ONE_RED,
         description="Count of drives where smartctl exit_status > 0. The "
                     "exit status is a bitfield — 0 is the only clean value, "
                     "any non-zero means SMART flagged the drive: investigate."),
    stat(30, "Tailscale nodes up",
         'count(up{job="tailscale-nodes"} == 1)', "short", 18, 29, 6, 4,
         thresholds=GREEN_ONLY,
         description="Count of Tailscale nodes currently reporting up. "
                     "Informational; a drop means a node left the mesh."),
]

# ── Dashboard 4: Capacity / Growth / Backup-DR ───────────────────────────────

# Backup-age tiles read backup_last_success_timestamp_seconds from each host's
# textfile_collector. Thresholds are per-job because cadences span 60x
# (1m mover vs 24h config backups); a uniform threshold would either flap on
# slow backups or hide a dead mover for hours.
# Entry: (label_selector, display_title, yellow_seconds, red_seconds, description)
BACKUP_JOBS = [
    ('name="jbsrv01-config-backup"',          "JBSRV01 config",     90000, 180000,
     "Time since the last successful Proxmox host config backup. Expected "
     "daily — yellow at ~25h, red at ~50h means the backup job is failing."),
    ('name="jbdns01-config-backup"',          "JBDNS01 config",     90000, 180000,
     "Time since the last successful Pi-hole/JBDNS01 config backup. Expected "
     "daily — red at ~50h means DNS/DHCP config is no longer being captured."),
    ('name="jbvm02-secrets-backup"',          "JBVM02 secrets",     90000, 180000,
     "Time since the last successful JBVM02 secrets backup. Expected daily — "
     "red at ~50h means credential material is not being protected."),
    ('name="mc-world-backup",slot="daily"',   "MC world (daily)",   90000, 180000,
     "Time since the last successful daily Minecraft world snapshot. Red at "
     "~50h means a day's worth of world progress is unprotected."),
    ('name="mc-world-backup",slot="rolling"', "MC world (4h)",      18000,  36000,
     "Time since the last 4-hourly rolling Minecraft world snapshot. Yellow "
     "at ~5h, red at ~10h means the short-cadence backup has stalled."),
    ('name="nas-dropbox-mover"',              "NAS dropbox mover",    180,    600,
     "Time since the NAS dropbox mover last ran. Expected every minute — "
     "yellow at 3m, red at 10m means the mover is stuck and inbound files "
     "are piling up."),
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
             "percent", 0, 1, 24, 10,
             description="Free space remaining as a percentage of each "
                         "filesystem, all hosts. Thresholds are inverted from "
                         "fill: red below 15% free, green above 30%.",
             thresholds={"mode": "absolute", "steps": [
                 {"color": "red", "value": None},
                 {"color": "yellow", "value": 15},
                 {"color": "green", "value": 30}]}),

    row(3, "Filesystem Days-to-Full (linear projection from last 7d)", 11),
    bargauge(4, "Days remaining (positive = filling; absent = stable/growing slowly)",
             [t(DAYS_TO_FULL, '{{hostname}}: {{mountpoint}}')],
             "d", 0, 12, 24, 8, min_val=0, max_val=180,
             description="Linear projection of days until each filesystem "
                         "fills, from the last 7d trend. A filesystem that is "
                         "stable or shrinking has no series here — an absent "
                         "bar is good, not an error. Red below 7 days.",
             thresholds={"mode": "absolute", "steps": [
                 {"color": "red", "value": None},
                 {"color": "yellow", "value": 7},
                 {"color": "green", "value": 30}]}),

    row(5, "ZFS Pools (NAS)", 20),
    stat(6, "JBNAS_SSD pool state",   pool_state_online(NAS, "JBNAS_SSD"),
         "short", 0, 21, 6, 4, thresholds=ZERO_RED_ONE_GREEN,
         mappings=ONLINE_DEG,
         description="zpool health of JBNAS_SSD. ONLINE = healthy; DEGRADED "
                     "is a DR concern — a degraded pool may lose redundancy "
                     "or capacity."),
    stat(7, "JBNAS_MEDIA pool state", pool_state_online(NAS, "JBNAS_MEDIA"),
         "short", 6, 21, 6, 4, thresholds=ZERO_RED_ONE_GREEN,
         mappings=ONLINE_DEG,
         description="zpool health of JBNAS_MEDIA — a stripe pool with no "
                     "parity. DEGRADED means imminent data loss; treat as a "
                     "critical DR incident."),
    bargauge(8, "Data dataset usage %",
             [t(f'100 * (1 - node_filesystem_avail_bytes{{{ZFS_DATA_FS}}} / '
                f'node_filesystem_size_bytes{{{ZFS_DATA_FS}}})',
                "{{mountpoint}}")],
             "percent", 12, 21, 12, 4,
             description="Space used by the data-holding ZFS datasets "
                         "(JBNAS_SSD/data, JBNAS_MEDIA/plex) as a percentage of "
                         "used + pool-free. Yellow 70%, red 90% — a near-full "
                         "pool is a capacity incident."),

    row(9, "Estate Headroom — RAM & CPU per Host", 25),
    # avg by (hostname) drops the noisy {namespace, endpoint, ...} labels so
    # the legend reads as just the hostname.
    timeseries(10, "Free memory (%)",
               [t('100 * avg by (hostname) (node_memory_MemAvailable_bytes / '
                  'node_memory_MemTotal_bytes)', "{{hostname}}")],
               "percent", 0, 26, 12, 8,
               description="Free memory as a percentage of total, per host. "
                           "Sustained low free memory on any host risks the "
                           "OOM killer."),
    timeseries(11, "CPU idle (%)",
               [t('100 * avg by (hostname) (rate(node_cpu_seconds_total{mode="idle"}[5m]))',
                  "{{hostname}}")],
               "percent", 12, 26, 12, 8,
               description="CPU idle percentage per host. Low idle = the host "
                           "is CPU-bound; this is the spare-capacity view for "
                           "the estate."),

    row(12, f"SMART — Power-on time + warnings ({HOSTS['srv']} = all physical drives)", 34),
    timeseries(13, "Power-on hours per drive",
               [t(f'smartctl_device_power_on_seconds{{instance="{IPS["srv"]}"}} / 3600',
                  "{{device}} {{model_name}}")],
               "h", 0, 35, 16, 8,
               description="Cumulative power-on hours per physical drive. "
                           "Used to gauge drive age — consumer drives drift "
                           "into the failure-rate climb past ~40-50k hours."),
    stat(14, "Drives with SMART warning (exit_status > 0)",
         smart_warning_count(),
         "short", 16, 35, 8, 4, thresholds=ZERO_GREEN_ONE_RED,
         description="Count of drives where smartctl exit_status > 0. The "
                     "exit status is a bitfield — 0 is the only clean value; "
                     "any non-zero means SMART flagged the drive."),
    stat(15, "Drives with SMART status FAILED",
         f'count(smartctl_device_smart_status{{instance="{IPS["srv"]}"}} == 0) '
         f'or vector(0)',
         "short", 16, 39, 8, 4, thresholds=ZERO_GREEN_ONE_RED,
         description="Count of drives whose SMART overall-health "
                     "self-assessment reports FAILED. Expected 0 — any "
                     "non-zero means a drive is dying, see the "
                     "SmartDriveStatusFailed alert."),

    row(16, "Backup / DR Status: last successful heartbeat per job", 43),
    *[backup_age_stat(17 + i, title, selector,
                      (i % 6) * 4, 44, 4, 4, yellow_s, red_s,
                      description=desc)
      for i, (selector, title, yellow_s, red_s, desc) in enumerate(BACKUP_JOBS)],
    # Meta-tile separates "textfile dir missing or unreadable" from "all
    # backups failed simultaneously". Without it the 6 tiles above light red
    # in unison and the real cause hides.
    stat(23, "Textfile scrape error (any host)",
         'max(node_textfile_scrape_error{job="node-exporter-external"})',
         "short", 0, 48, 6, 4, thresholds=ZERO_GREEN_ONE_RED,
         description="1 if any host's node-exporter textfile collector is "
                     "broken or unreadable. Disambiguates 'textfile dir "
                     "missing' from 'all backups genuinely failed' — the "
                     "former lights every backup tile red at once."),
    text_panel(24, "Residual gaps", CAP_BACKUP_GAPS, 6, 48, 18, 4,
               description="Backup/DR coverage gaps not visible in the "
                           "heartbeat tiles above — single-copy paths and "
                           "no-parity pools, tracked in project_open_defects."),
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
               "ops", 0, 1, 12, 8,
               description="Total journal lines/sec per host from the "
                           "systemd journal. A sudden spike flags a chatty "
                           "or failing unit."),
    loki_timeseries(3, "Error rate per host (lines/sec)",
               [t_loki(ERR_RATE_BY_HOST, "{{hostname}}")],
               "ops", 12, 1, 12, 8,
               description="Journal lines matching 'error' (case-insensitive) "
                           "per host. Should sit near zero; a rising line "
                           "means a host is logging errors."),
    loki_timeseries(4, "Warning rate per host (lines/sec)",
               [t_loki(WARN_RATE_BY_HOST, "{{hostname}}")],
               "ops", 0, 9, 12, 8,
               description="Journal lines matching 'warn' (case-insensitive) "
                           "per host. Useful as an early signal before "
                           "warnings escalate to errors."),
    loki_timeseries(5, "Top 10 noisy systemd units (lines/sec)",
               [t_loki(TOP_NOISY_UNITS, "{{hostname}} / {{unit}}")],
               "ops", 12, 9, 12, 8,
               description="The 10 systemd units producing the most log lines "
                           "right now. Identifies which unit is responsible "
                           "for a log-volume spike."),

    row(6, "SSH auth failures (last 24h, journal)", 17),
    loki_timeseries(7, "Failed SSH password attempts",
               [t_loki(SSHD_FAILS, "{{hostname}}")],
               "short", 0, 18, 24, 8,
               description="Count of 'Failed password' lines from sshd over "
                           "the last 24h, per host. A sustained climb "
                           "indicates a brute-force attempt."),

    row(8, "Pi-hole DNS — Live", 26),
    stat(9,  "Queries (today)", "sum(pihole_dns_queries_today)",
         "short", 0, 27, 6, 4, thresholds=GREEN_ONLY,
         description="Total DNS queries Pi-hole has handled today. "
                     "Informational; resets at midnight."),
    stat(10, "Blocked (today)", "sum(pihole_ads_blocked_today)",
         "short", 6, 27, 6, 4, thresholds=GREEN_ONLY,
         description="DNS queries blocked as ads/trackers today. "
                     "Informational; resets at midnight."),
    stat(11, "Blocked %", "avg(pihole_ads_percentage_today)",
         "percent", 12, 27, 6, 4, thresholds=NO_THRESH,
         description="Share of today's queries blocked. Informational, no "
                     "threshold; typically 10-25% for this estate."),
    stat(12, "Domains in blocklist", "max(pihole_domains_being_blocked)",
         "short", 18, 27, 6, 4, thresholds=NO_THRESH,
         description="Number of domains on Pi-hole's active blocklists. "
                     "Informational; a drop to zero means a gravity update "
                     "failed."),
    timeseries(13, "DNS queries/sec (5m rate)",
               [t("rate(pihole_dns_queries_all_types[5m])", "queries/s")],
               "ops", 0, 31, 12, 7,
               description="DNS query rate Pi-hole is serving (5m rate). A "
                           "drop to zero while clients are active points to "
                           "a DNS outage."),
    timeseries(14, "Cache vs forwarded (1h rate)",
               [t("rate(pihole_queries_cached[1h])", "cached"),
                t("rate(pihole_queries_forwarded[1h])", "forwarded", "B")],
               "ops", 12, 31, 12, 7,
               description="Queries answered from Pi-hole's cache vs forwarded "
                           "upstream (1h rate). A high cache share means fast "
                           "local resolution."),

    # Real user-facing DNS SLI — independent of pihole-exporter scrape.
    # probe_success is 0/1 from the blackbox dns_pihole module (UDP/53 lookup).
    # The series carries job=, not module=, so select on job.
    row(15, "Pi-hole DNS — Blackbox probe (real user-facing SLI)", 38),
    stat(16, "DNS probe",
         'probe_success{job="blackbox-dns-pihole"}',
         "short", 0, 39, 6, 4, thresholds=ZERO_RED_ONE_GREEN, mappings=UP_DOWN,
         description="Result of a real UDP/53 DNS lookup against "
                     "192.168.0.205. UP = the LAN can resolve names — the "
                     "actual user-facing signal, independent of the "
                     "pihole-exporter scrape."),
    timeseries(18, "DNS lookup time (s)",
               [t('probe_dns_lookup_time_seconds{job="blackbox-dns-pihole"}', "lookup")],
               "s", 6, 39, 18, 4,
               description="Round-trip time of the blackbox DNS probe. Rising "
                           "lookup time means Pi-hole is slow to answer even "
                           "when the probe still succeeds."),

    row(19, "Network — Per-Host Throughput", 43),
    timeseries(20, "Receive (Bps)",
               [t('sum by (hostname) (rate(node_network_receive_bytes_total{device!~"lo|veth.*|tailscale.*"}[5m]))',
                  "{{hostname}}")],
               "Bps", 0, 44, 12, 8,
               description="Inbound network throughput per host (5m rate), "
                           "excluding loopback and virtual interfaces."),
    timeseries(21, "Transmit (Bps)",
               [t('sum by (hostname) (rate(node_network_transmit_bytes_total{device!~"lo|veth.*|tailscale.*"}[5m]))',
                  "{{hostname}}")],
               "Bps", 12, 44, 12, 8,
               description="Outbound network throughput per host (5m rate), "
                           "excluding loopback and virtual interfaces."),

    row(22, "Tailscale nodes (debug metrics)", 52),
    stat(23, "Nodes up", 'count(up{job="tailscale-nodes"} == 1)',
         "short", 0, 53, 6, 4, thresholds=GREEN_ONLY,
         description="Count of Tailscale nodes currently reporting up. "
                     "Informational; a drop means a node left the mesh."),
    stat(24, "Total dropped packets (since reboot)",
         'sum(netstack_dropped_packets)', "short", 6, 53, 6, 4,
         thresholds={"mode": "absolute",
                     "steps": [{"color": "green", "value": None},
                               {"color": "yellow", "value": 1000},
                               {"color": "red", "value": 100000}]},
         description="Cumulative Tailscale netstack packet drops since each "
                     "node booted. This is a counter, not a rate — it only "
                     "grows; watch the trend. Thresholds 1k/100k are rough."),
    timeseries(25, "Packet forward errors / sec",
               [t('sum by (hostname) (rate(netstack_ip_forward_errors[5m]))',
                  "{{hostname}}")],
               "ops", 12, 53, 12, 4,
               description="Tailscale packet-forwarding errors per second. "
                           "Sustained non-zero values point to a subnet-"
                           "router routing problem."),
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
         "dtdurations", 0, 1, 4, 4, thresholds=GREEN_ONLY,
         description="Time since the selected host last booted. "
                     "Informational; a reset to near-zero means the host "
                     "rebooted."),
    stat(3, "Load average (1m)",
         'node_load1{hostname="$hostname"}',
         "short", 4, 1, 4, 4, thresholds=NO_THRESH,
         description="1-minute kernel load average. Compare to the host's "
                     "vCPU count (see CPU cores): load near the core count "
                     "means fully busy, well above means CPU saturation and "
                     "run-queue queueing."),
    stat(4, "CPU cores",
         'count(node_cpu_seconds_total{hostname="$hostname",mode="idle"})',
         "short", 8, 1, 4, 4, thresholds=GREEN_ONLY,
         description="Number of vCPUs on the selected host — the denominator "
                     "for the load-average figures. Load above this number "
                     "means the CPU is oversubscribed."),
    stat(5, "CPU busy %",
         '100 - (avg by (hostname) (rate(node_cpu_seconds_total{hostname="$hostname",mode="idle"}[5m])) * 100)',
         "percent", 12, 1, 4, 4,
         description="CPU utilisation across all cores (5m average). Normal "
                     "below 70%; red at 90% means the host is CPU-bound."),
    stat(6, "Free RAM %",
         '100 * node_memory_MemAvailable_bytes{hostname="$hostname"} / node_memory_MemTotal_bytes{hostname="$hostname"}',
         "percent", 16, 1, 4, 4,
         thresholds={"mode": "absolute",
                     "steps": [{"color": "red", "value": None},
                               {"color": "yellow", "value": 10},
                               {"color": "green", "value": 25}]},
         description="Available memory as a percentage of total. Green above "
                     "25%; below 10% (red) the host is close to OOM."),
    stat(7, "Root FS free %",
         '100 * node_filesystem_avail_bytes{hostname="$hostname",mountpoint="/"} / '
         'node_filesystem_size_bytes{hostname="$hostname",mountpoint="/"}',
         "percent", 20, 1, 4, 4,
         thresholds={"mode": "absolute",
                     "steps": [{"color": "red", "value": None},
                               {"color": "yellow", "value": 10},
                               {"color": "green", "value": 20}]},
         description="Free space on the root filesystem. Green above 20%; "
                     "below 10% (red) risks the host filling its disk."),

    row(8, "CPU & Memory", 5),
    timeseries(9, "CPU usage by mode",
               [t('sum by (mode) (rate(node_cpu_seconds_total{hostname="$hostname",mode!="idle"}[5m])) '
                  '/ on() group_left scalar(count(node_cpu_seconds_total{hostname="$hostname",mode="idle"}))',
                  "{{mode}}")],
               "percentunit", 0, 6, 8, 8, stacking="normal",
               description="CPU time by mode (user/system/iowait/...), "
                           "normalised per core and stacked. A tall iowait "
                           "band points to disk pressure, not CPU."),
    timeseries(10, "Memory breakdown",
               [t('node_memory_MemTotal_bytes{hostname="$hostname"} - '
                  'node_memory_MemAvailable_bytes{hostname="$hostname"}', "Used"),
                t('node_memory_Cached_bytes{hostname="$hostname"} + '
                  'node_memory_Buffers_bytes{hostname="$hostname"}', "Cache+Buffers", "B"),
                t('node_memory_MemFree_bytes{hostname="$hostname"}', "Free", "C")],
               "bytes", 8, 6, 8, 8,
               description="Memory split into used, cache/buffers and free. "
                           "Cache+Buffers is reclaimable — only sustained "
                           "high Used with low Free is real pressure."),
    timeseries(11, "Load average (1m/5m/15m)",
               [t('node_load1{hostname="$hostname"}',  "1m"),
                t('node_load5{hostname="$hostname"}',  "5m",  "B"),
                t('node_load15{hostname="$hostname"}', "15m", "C")],
               "short", 16, 6, 8, 8, fill=0,
               description="Kernel load average over 1/5/15m windows. "
                           "Compare against the host's vCPU count: lines "
                           "riding above the core count mean sustained CPU "
                           "saturation."),

    row(12, "Disk & Network", 14),
    timeseries(13, "Disk I/O (Bps)",
               [t('rate(node_disk_read_bytes_total{hostname="$hostname",device!~"loop.*|dm-.*"}[5m])',
                  "read {{device}}"),
                t('rate(node_disk_written_bytes_total{hostname="$hostname",device!~"loop.*|dm-.*"}[5m])',
                  "write {{device}}", "B")],
               "Bps", 0, 15, 12, 8,
               description="Per-device disk read and write throughput (5m "
                           "rate). Loop and device-mapper devices are "
                           "excluded."),
    timeseries(14, "Network rx/tx (Bps)",
               [t('rate(node_network_receive_bytes_total{hostname="$hostname",device!~"lo|veth.*|tailscale.*|cni.*|cali.*"}[5m])',
                  "rx {{device}}"),
                t('rate(node_network_transmit_bytes_total{hostname="$hostname",device!~"lo|veth.*|tailscale.*|cni.*|cali.*"}[5m])',
                  "tx {{device}}", "B")],
               "Bps", 12, 15, 12, 8,
               description="Per-interface network receive and transmit "
                           "throughput (5m rate). Loopback and virtual/CNI "
                           "interfaces are excluded."),
    bargauge(15, "Filesystem usage % (per mountpoint)",
             [t(f'100 - (100 * node_filesystem_avail_bytes{{hostname="$hostname",{FS_FILTER}}} / '
                f'node_filesystem_size_bytes{{hostname="$hostname",{FS_FILTER}}})',
                "{{mountpoint}}")],
             "percent", 0, 23, 24, 6,
             description="Percentage used per mountpoint on the selected "
                         "host. Yellow at 70%, red at 90% — a full filesystem "
                         "blocks writes."),

    row(16, "Logs (Loki, journal)", 29),
    loki_timeseries(17, "Top 10 noisy units (lines/sec)",
                    [t_loki('topk(10, sum by (unit) (rate({hostname="$hostname",job="systemd-journal"}[5m])))',
                            "{{unit}}")],
                    "ops", 0, 30, 12, 8,
                    description="The 10 systemd units logging the most on the "
                                "selected host. Identifies the source of a "
                                "log-volume spike."),
    loki_timeseries(18, "Error / warn rate",
                    [t_loki('sum(rate({hostname="$hostname",job="systemd-journal"} |~ "(?i)error"[5m]))',
                            "errors"),
                     t_loki('sum(rate({hostname="$hostname",job="systemd-journal"} |~ "(?i)warn"[5m]))',
                            "warnings", "B")],
                    "ops", 12, 30, 12, 8,
                    description="Journal lines matching 'error' and 'warn' "
                                "per second on the selected host. Should sit "
                                "near zero."),
    loki_timeseries(19, "SSH failed-password attempts (24h count)",
                    [t_loki('sum(count_over_time({hostname="$hostname",job="systemd-journal",unit="ssh.service"} '
                            '|~ "Failed password"[24h]))', "fails")],
                    "short", 0, 38, 24, 6,
                    description="Count of sshd 'Failed password' lines over "
                                "the last 24h on the selected host. A "
                                "sustained climb indicates a brute-force "
                                "attempt."),
]

# ── Alerts overview dashboard ────────────────────────────────────────────────

alerts_overview_panels = [
    row(900, "Active alerts", 0),
    stat(901, "Critical firing",
         'count(ALERTS{alertstate="firing",severity="critical"}) or vector(0)',
         "short", 0, 1, 8, 5, thresholds=ZERO_GREEN_ONE_RED,
         description="Count of critical-severity alerts firing right now. "
                     "Expected 0 — any non-zero is a page-worthy incident."),
    stat(902, "Warning firing",
         'count(ALERTS{alertstate="firing",severity="warning"}) or vector(0)',
         "short", 8, 1, 8, 5, thresholds=WARN_THRESH,
         description="Count of warning-severity alerts firing right now. "
                     "Non-zero is amber — investigate, but not an emergency."),
    stat(903, "Total firing",
         'count(ALERTS{alertstate="firing"}) or vector(0)',
         "short", 16, 1, 8, 5, thresholds=GREEN_ONLY,
         description="Total alerts firing across all severities. "
                     "Informational; the headline number for estate health."),
    alerts_table(904, "All firing alerts", 0, 6, 24, 10,
                 description="Every alert currently firing, with severity, "
                             "service and host. Sorted by severity — the "
                             "live incident queue for the estate."),
    row(905, "History", 16),
    timeseries(906, "Firing alerts by severity",
               [t('count by (severity) (ALERTS{alertstate="firing"})', "{{severity}}")],
               "short", 0, 17, 24, 8,
               description="Count of firing alerts by severity over time. "
                           "Shows whether alerts are flapping or steadily "
                           "accumulating."),
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
