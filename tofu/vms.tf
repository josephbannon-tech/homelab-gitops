# JBNAS01 — TrueNAS SCALE 25.04 (VMID 101)
resource "proxmox_virtual_environment_vm" "jbnas01" {
  node_name   = "JBSRV01"
  vm_id       = 101
  name        = "JBNAS01"
  description = <<-EOT
    ## JBNAS01 — TrueNAS
    - 0.201 · web@:443 · ssh nas
  EOT

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
      initialization,
      agent, machine, keyboard_layout,
    ]
  }
}

# JBVM01 — Jump box / Debian 13 desktop (VMID 102)
resource "proxmox_virtual_environment_vm" "jbvm01" {
  node_name   = "JBSRV01"
  vm_id       = 102
  name        = "JBVM01"
  description = <<-EOT
    ## JBVM01 — Jumpbox
    - 0.206 · ssh claude@
  EOT

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

  # Torrent staging tier: qBittorrent's *incomplete* directory. Torrent writes
  # are 16 KB random pieces; landing them straight on the NAS RAIDZ over CIFS
  # fragments every file for the life of the pool (OpenZFS tuning guide,
  # BitTorrent section). Incomplete downloads live here on NVMe instead, and
  # qBittorrent moves the finished content to the CIFS dropbox in one
  # sequential copy. Sized for one 4K remux (largest in the library is 141 GB)
  # plus a season pack. On the chipset NVMe (`local-lvm-m2`), never the boot
  # drive: sustained torrent churn is not for an unmirrored OS disk. Contents
  # are in-flight downloads, re-acquirable by definition, so backup = false.
  # discard/ssd are load-bearing on LVM-thin, see scsi0 above.
  disk {
    datastore_id = "local-lvm-m2"
    interface    = "scsi1"
    size         = 200
    discard      = "on"
    ssd          = true
    iothread     = true
    backup       = false
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
      operating_system, serial_device, initialization,
      agent, machine, keyboard_layout,
    ]
  }
}

# JBVM02 — Claude Code / Ubuntu 24.04 (VMID 103)
resource "proxmox_virtual_environment_vm" "jbvm02" {
  node_name   = "JBSRV01"
  vm_id       = 103
  name        = "JBVM02"
  description = <<-EOT
    ## JBVM02 — LLM Admin
    - 0.203 · code-server@:8080 · llm-router@:9081 · ssh jbannon@ · API token root@pam!claude → KB
  EOT

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
      operating_system, serial_device, initialization,
      agent, machine, keyboard_layout,
    ]
  }
}

# JBVM03 — Production server / Ubuntu 24.04 (VMID 104)
resource "proxmox_virtual_environment_vm" "jbvm03" {
  node_name   = "JBSRV01"
  vm_id       = 104
  name        = "JBVM03"
  description = <<-EOT
    ## JBVM03 — Minecraft
    - 0.204 · tailscale@:25565 · ssh jbvm03
  EOT

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
      operating_system, serial_device, initialization,
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
  node_name   = "JBSRV01"
  vm_id       = 106
  name        = "JBK8S01"
  description = <<-EOT
    ## JBK8S01 — k3s
    - 0.207 · Grafana@:30300 · Prometheus@:30900 · ArgoCD@:30808 · Open WebUI@:30081 · ssh jbk8s01
  EOT

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
    dedicated = 16384
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

  # PV data disk (added 2026-09-05): mounted in-guest at
  # /var/lib/rancher/k3s/storage, the local-path provisioner's root. Moves all
  # PersistentVolumes off the 40 G OS disk (root hit 84% with the Prometheus
  # TSDB at 11 G and growing) onto the P34A60 NVMe pool (838 G, ~7% used),
  # which was earmarked for PV-class data ahead of Immich. Hot-plugged; the
  # in-guest move is a short full-cluster stop (runbook in the private KB:
  # scripts/jbk8s01-move-pv-disk.sh, docs/jbk8s01.md).
  disk {
    datastore_id = "local-lvm-m2"
    interface    = "scsi1"
    size         = 100
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
      operating_system, serial_device, initialization,
      agent, machine, keyboard_layout,
    ]
  }
}

# JBLLM01 — Server LLM tier (VMID 108): Qwen3.6-35B-A3B on CPU, 32 GB RAM,
# ALWAYS-ON since 2026-09-05. Same weights as the desktop fast tier, so it is
# the fallback when JBPC004 is asleep/in gaming mode, and the tool-calling
# backend for the phone chat when the desktop is unavailable. ~6-8 t/s expected.
# History: built 2026-09-04 as a 72 GB gpt-oss-120b VM; the always-on attempt
# on 2026-09-05 hit host 125/125 GiB within 3 minutes (a guest touches its
# WHOLE allocation once page cache fills). The 120B is retired on this host.
# Capacity rule (private KB memory feedback_vm_memory_is_allocation_not_working_set):
# host 125 - 3 (hypervisor) - 71 (other guests' allocations) - 32 = 19 GiB
# worst-case spare. Re-run this sum before raising ANY guest's memory.
# First net-new VM born in Tofu (all others were imported). Disk lives on
# local-lvm-m2 (SP P34A60 NVMe) for fast model loads. Design: docs/inference.md
# in the private knowledge base; big tier gated on-demand per the toy-service rule.
resource "proxmox_virtual_environment_vm" "jbllm01" {
  node_name   = "JBSRV01"
  vm_id       = 108
  name        = "JBLLM01"
  description = <<-EOT
    ## JBLLM01 — Local LLM Resources
    - 0.208 · llama-swap@:8080 · ssh jbannon@
  EOT

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
    # CPU shares (cgroup v2 cpu.weight; Proxmox default 100). Half weight so a
    # 12-thread generation burst yields to the game servers and k3s under
    # contention instead of starving them. Not a cap: full speed when idle host.
    units = 50
  }

  memory {
    dedicated = 32768 # 22 GB Q4 weights + KV cache + guest; page cache fills the rest
  }

  disk {
    datastore_id = "local-lvm-m2"
    interface    = "scsi0"
    size         = 100
    discard      = "on"
    ssd          = true
    # Excluded from vzdump: ~63 GB of model weights are re-downloadable and the
    # VM is a Tofu clone of template 9000. The weekly job still captures the
    # VM config (backup=1 on no disks = config-only archive). Set 2026-09-05.
    backup = false
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

  # Always-on (see header). cpu.units=50 keeps generation bursts below the game
  # servers under contention; disk backup=false because the weights are a
  # hash-pinned re-download and the VM is a Tofu clone of template 9000.
  on_boot = true
  started = true
}
