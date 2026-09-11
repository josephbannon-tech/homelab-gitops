# JBDNS01 — Pi-hole DNS + DHCP + Tailscale / Debian 12 LXC (VMID 105)
resource "proxmox_virtual_environment_container" "jbdns01" {
  node_name   = "JBSRV01"
  vm_id       = 105
  description = <<-EOT
    ## JBDNS01 — DNS & DHCP
    - 0.205 · admin@/admin · ssh root@ · pct enter 105
  EOT

  unprivileged = true

  cpu {
    cores = 4
  }

  memory {
    dedicated = 1024
    swap      = 512
  }

  features {
    nesting = true
  }

  disk {
    datastore_id = "local-lvm"
    size         = 4
  }

  network_interface {
    name   = "eth0"
    bridge = "vmbr0"
  }

  # template_file_id is consumed at creation time only; ignore drift on import.
  operating_system {
    template_file_id = "local:vztmpl/debian-12-standard_12.7-1_amd64.tar.zst"
    type             = "debian"
  }

  startup {
    order    = 1
    up_delay = 30
  }

  start_on_boot = true
  started       = true

  lifecycle {
    ignore_changes = [
      operating_system, initialization, console,
      start_on_boot, vm_id, tags,
      timeout_clone, timeout_create, timeout_delete, timeout_start, timeout_update,
    ]
  }
}

# JBVM04 — Satisfactory dedicated server / Debian 13 LXC (VMID 107)
# Imported 2026-09-04: the last hand-made guest. The two raw lxc.* lines that
# pass /dev/net/tun through for Tailscale (lxc.cgroup2.devices.allow c 10:200,
# lxc.mount.entry /dev/net/tun) have no provider attribute and stay a manual
# step in the rebuild procedure (docs/jbvm04.md in the private knowledge base).
import {
  to = proxmox_virtual_environment_container.jbvm04
  id = "JBSRV01/107"
}

resource "proxmox_virtual_environment_container" "jbvm04" {
  node_name   = "JBSRV01"
  vm_id       = 107
  description = <<-EOT
    ## JBVM04 — Satisfactory
    - 0.70 (DHCP) · tailscale@:7777+8888 · pct enter 107
  EOT

  unprivileged = true

  cpu {
    cores = 4
  }

  memory {
    dedicated = 12288
    swap      = 2048
  }

  features {
    nesting = true
  }

  disk {
    datastore_id = "local-lvm"
    size         = 30
  }

  network_interface {
    name   = "eth0"
    bridge = "vmbr0"
  }

  # template_file_id is consumed at creation time only; ignore drift on import.
  operating_system {
    template_file_id = "local:vztmpl/debian-13-standard_13.1-2_amd64.tar.zst"
    type             = "debian"
  }

  # Boot order 3 with the other consumers (after JBDNS01 order 1 and JBNAS01
  # order 2): the save-backup cron needs the NAS mount and every player joins by
  # name via Pi-hole. Was undeclared until 2026-09-09 (docs audit), so a host
  # reboot started it whenever Proxmox got round to it.
  startup {
    order = 3
  }

  start_on_boot = true
  started       = true

  lifecycle {
    ignore_changes = [
      operating_system, initialization, console,
      start_on_boot, vm_id, tags,
      timeout_clone, timeout_create, timeout_delete, timeout_start, timeout_update,
    ]
  }
}
