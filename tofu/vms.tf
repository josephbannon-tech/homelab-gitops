# JBNAS01 — TrueNAS SCALE 25.04 (VMID 101)
resource "proxmox_virtual_environment_vm" "jbnas01" {
  node_name = "JBSRV01"
  vm_id     = 101
  name      = "JBNAS01"

  machine = "q35"
  bios    = "ovmf"

  scsi_hardware = "virtio-scsi-single"

  agent {
    enabled = false
  }

  cpu {
    cores = 4
    type  = "host"
  }

  memory {
    dedicated = 12048
  }

  # OS disk only; SATA passthrough disks (JBNAS_MEDIA HDDs, JBNAS_SSD SSDs)
  # are managed outside Tofu — ignore_changes prevents drift detection on them.
  #
  # NOTE: because `disk` is in ignore_changes below, this block documents the
  # live configuration rather than enforcing it. Kept accurate deliberately so
  # the file is not misleading about how the guest is actually configured.
  # discard/ssd are required for LVM-thin block reclaim; see the discard note
  # on jbvm01 below.
  disk {
    datastore_id = "local-lvm"
    interface    = "scsi0"
    size         = 32
    discard      = "on"
    ssd          = true
    iothread     = true
  }

  network_device = [{
    bridge       = "vmbr0"
    model        = "virtio"
    enabled      = true # deprecated but still required by provider schema
    disconnected = false
    firewall     = true
    mac_address  = null
    mtu          = null
    queues       = null
    rate_limit   = null
    trunks       = null
    vlan_id      = null
  }]

  startup {
    order    = 2
    up_delay = 10
  }

  on_boot = true
  started = true

  lifecycle {
    ignore_changes = [
      disk, efi_disk, operating_system, serial_device,
      description, initialization,
      agent, machine, keyboard_layout,
    ]
  }
}

# JBVM01 — Jump box / Debian 13 desktop (VMID 102)
resource "proxmox_virtual_environment_vm" "jbvm01" {
  node_name = "JBSRV01"
  vm_id     = 102
  name      = "JBVM01"

  machine       = "q35"
  bios          = "seabios"
  scsi_hardware = "virtio-scsi-single"

  agent {
    enabled = true
  }

  cpu {
    cores = 2
    type  = "x86-64-v2-AES"
  }

  # Raised 2048 -> 4096 on 2026-06-02 after NodeIOThrottled fired (PSI io full
  # ~54%): not a disk fault but swap thrash, with qBittorrent plus a full XFCE
  # desktop overrunning the 2 GB box. Do not lower without re-testing that.
  # balloon stays 0 and there is no memory hotplug, so changes need a stop/start.
  memory {
    dedicated = 4096
  }

  # discard = "on" is load-bearing, not a tuning knob. `local-lvm` is an
  # LVM-thin pool: without it QEMU accepts the guest's SCSI UNMAP and silently
  # drops it, so the thin volume grows to 100% of its provisioned size and
  # never shrinks, however much the guest deletes. This guest sat at 95.95%
  # against a pool at 87.83% before it was set. ssd = true advertises
  # non-rotational so the guest issues discards in the first place.
  # Removing either line re-opens the 2026-08-08 thin-pool overcommit incident.
  disk {
    datastore_id = "local-lvm"
    interface    = "scsi0"
    size         = 50
    discard      = "on"
    ssd          = true
    iothread     = true
  }

  network_device = [{
    bridge       = "vmbr0"
    model        = "virtio"
    enabled      = true # deprecated but still required by provider schema
    disconnected = false
    firewall     = true
    mac_address  = null
    mtu          = null
    queues       = null
    rate_limit   = null
    trunks       = null
    vlan_id      = null
  }]

  startup {
    order = 3
  }

  on_boot = true
  started = true

  lifecycle {
    ignore_changes = [
      operating_system, serial_device, description, initialization,
      agent, machine, keyboard_layout,
    ]
  }
}

# JBVM02 — Claude Code / Ubuntu 24.04 (VMID 103)
resource "proxmox_virtual_environment_vm" "jbvm02" {
  node_name = "JBSRV01"
  vm_id     = 103
  name      = "JBVM02"

  machine       = "q35"
  bios          = "seabios"
  scsi_hardware = "virtio-scsi-single"

  agent {
    enabled = true
  }

  cpu {
    cores = 2
    type  = "x86-64-v2-AES"
  }

  # Raised 8192 -> 12288 on 2026-07-28 after a runaway Claude Code process hit
  # ~7.5 GB anon RSS and was OOM-killed three times, with the resulting thrash
  # starving sshd. No memory hotplug (numa: 0, i440FX), so changes need a
  # stop/start. Do not lower without addressing the sshd guardrail first.
  memory {
    dedicated = 12288
  }

  # discard/ssd required for LVM-thin reclaim; see the note on jbvm01.
  disk {
    datastore_id = "local-lvm"
    interface    = "scsi0"
    size         = 32
    discard      = "on"
    ssd          = true
    iothread     = true
  }

  network_device = [{
    bridge       = "vmbr0"
    model        = "virtio"
    enabled      = true # deprecated but still required by provider schema
    disconnected = false
    firewall     = true
    mac_address  = null
    mtu          = null
    queues       = null
    rate_limit   = null
    trunks       = null
    vlan_id      = null
  }]

  startup {
    order = 3
  }

  on_boot = true
  started = true

  lifecycle {
    ignore_changes = [
      operating_system, serial_device, description, initialization,
      agent, machine, keyboard_layout,
    ]
  }
}

# JBVM03 — Production server / Ubuntu 24.04 (VMID 104)
resource "proxmox_virtual_environment_vm" "jbvm03" {
  node_name = "JBSRV01"
  vm_id     = 104
  name      = "JBVM03"

  machine       = "q35"
  bios          = "seabios"
  scsi_hardware = "virtio-scsi-pci"

  agent {
    enabled = true
  }

  cpu {
    cores = 6
    type  = "host"
  }

  memory {
    dedicated = 14336
  }

  # discard = "on" was already set here, which is why this was the only guest
  # not badly overgrown in the 2026-08-08 thin-pool incident (49.36% vs 94-98%
  # on its siblings). No ssd/iothread: matches the live config, and
  # virtio-scsi-pci does not support iothread.
  disk {
    datastore_id = "local-lvm"
    interface    = "scsi0"
    size         = 40
    discard      = "on"
  }

  network_device = [{
    bridge       = "vmbr0"
    model        = "virtio"
    enabled      = true # deprecated but still required by provider schema
    disconnected = false
    firewall     = false
    mac_address  = null
    mtu          = null
    queues       = null
    rate_limit   = null
    trunks       = null
    vlan_id      = null
  }]

  startup {
    order = 3
  }

  on_boot = true
  started = true

  lifecycle {
    ignore_changes = [
      operating_system, serial_device, description, initialization,
      agent, machine, keyboard_layout,
    ]
  }
}

# JBK8S01 — k3s + observability stack / Ubuntu 24.04 (VMID 106)
import {
  to = proxmox_virtual_environment_vm.jbk8s01
  id = "JBSRV01/106"
}

resource "proxmox_virtual_environment_vm" "jbk8s01" {
  node_name = "JBSRV01"
  vm_id     = 106
  name      = "JBK8S01"

  machine       = "q35"
  bios          = "seabios"
  scsi_hardware = "virtio-scsi-pci"

  agent {
    enabled = true
  }

  cpu {
    cores = 4
    type  = "x86-64-v2-AES"
  }

  memory {
    dedicated = 8192
  }

  # discard/ssd required for LVM-thin reclaim; see the note on jbvm01.
  # No iothread: scsi_hardware is virtio-scsi-pci, which does not support it.
  disk {
    datastore_id = "local-lvm"
    interface    = "scsi0"
    size         = 40
    discard      = "on"
    ssd          = true
  }

  network_device = [{
    bridge       = "vmbr0"
    model        = "virtio"
    enabled      = true # deprecated but still required by provider schema
    disconnected = false
    firewall     = false
    mac_address  = null
    mtu          = null
    queues       = null
    rate_limit   = null
    trunks       = null
    vlan_id      = null
  }]

  startup {
    order = 3
  }

  on_boot = true
  started = true

  lifecycle {
    ignore_changes = [
      operating_system, serial_device, description, initialization,
      agent, machine, keyboard_layout,
    ]
  }
}

# JBLLM01 — Big-tier LLM VM (VMID 108): gpt-oss-120b on CPU + 72 GB RAM.
# ON-DEMAND posture: parked (stopped) when idle; started for sessions/benches.
# First net-new VM born in Tofu (all others were imported). Disk lives on
# local-lvm-m2 (SP P34A60 NVMe) for fast model loads. Design: docs/inference.md
# in the private knowledge base; big tier gated on-demand per the toy-service rule.
resource "proxmox_virtual_environment_vm" "jbllm01" {
  node_name = "JBSRV01"
  vm_id     = 108
  name      = "JBLLM01"

  machine       = "q35"
  bios          = "seabios"
  scsi_hardware = "virtio-scsi-pci"

  clone {
    vm_id        = 9000
    full         = true
    datastore_id = "local-lvm-m2"
  }

  # qemu-guest-agent installed 2026-09-04; safe to enable (plan-hang rule).
  agent {
    enabled = true
  }

  cpu {
    cores = 12
    type  = "host"
  }

  memory {
    dedicated = 73728
  }

  disk {
    datastore_id = "local-lvm-m2"
    interface    = "scsi0"
    size         = 100
    discard      = "on"
    ssd          = true
  }

  network_device {
    bridge   = "vmbr0"
    model    = "virtio"
    firewall = true
  }

  operating_system {
    type = "l26"
  }

  serial_device {}

  initialization {
    datastore_id = "local-lvm-m2"

    ip_config {
      ipv4 {
        address = "192.168.0.208/24"
        gateway = "192.168.0.1"
      }
    }

    dns {
      servers = ["192.168.0.205"]
    }

    user_account {
      username = "jbannon"
      keys     = ["ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIJlpd8F6RDP/YXHj2rRWAAF8f94gjowFOimxsGgrKuyt jbannon@jbvm02"]
    }
  }

  # PARKED (on-demand posture): zero host RAM while stopped. Wake with
  # `qm start 108` (~1 min boot + ~2 min model load); benches recorded
  # 2026-09-04 in the private KB (inference.md): tg 3.8-4.0 t/s, pp512 18 t/s.
  on_boot = false
  started = false
}
