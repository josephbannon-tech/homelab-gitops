# JBDNS01 — Pi-hole DNS + DHCP + Tailscale / Debian 12 LXC (VMID 105)
resource "proxmox_virtual_environment_container" "jbdns01" {
  node_name   = "JBSRV01"
  vm_id       = 105
  description = "Pi-hole DNS + DHCP + Tailscale subnet router"

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
      operating_system, initialization, description, console,
      start_on_boot, vm_id, tags,
      timeout_clone, timeout_create, timeout_delete, timeout_start, timeout_update,
    ]
  }
}
