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
  disk {
    datastore_id = "local-lvm"
    interface    = "scsi0"
    size         = 32
  }

  network_device = [{
    bridge       = "vmbr0"
    model        = "virtio"
    enabled      = true  # deprecated but still required by provider schema
    disconnected = false
    firewall     = true
    mac_address  = null
    mtu          = null
    queues       = null
    rate_limit   = null
    trunks       = null
    vlan_id      = null
  }]

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

  memory {
    dedicated = 2048
  }

  disk {
    datastore_id = "local-lvm"
    interface    = "scsi0"
    size         = 50
    iothread     = true
  }

  network_device = [{
    bridge       = "vmbr0"
    model        = "virtio"
    enabled      = true  # deprecated but still required by provider schema
    disconnected = false
    firewall     = true
    mac_address  = null
    mtu          = null
    queues       = null
    rate_limit   = null
    trunks       = null
    vlan_id      = null
  }]

  on_boot = false
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

  memory {
    dedicated = 8192
  }

  disk {
    datastore_id = "local-lvm"
    interface    = "scsi0"
    size         = 32
    iothread     = true
  }

  network_device = [{
    bridge       = "vmbr0"
    model        = "virtio"
    enabled      = true  # deprecated but still required by provider schema
    disconnected = false
    firewall     = true
    mac_address  = null
    mtu          = null
    queues       = null
    rate_limit   = null
    trunks       = null
    vlan_id      = null
  }]

  on_boot = false
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

  disk {
    datastore_id = "local-lvm"
    interface    = "scsi0"
    size         = 40
    discard      = "on"
  }

  network_device = [{
    bridge       = "vmbr0"
    model        = "virtio"
    enabled      = true  # deprecated but still required by provider schema
    disconnected = false
    firewall     = false
    mac_address  = null
    mtu          = null
    queues       = null
    rate_limit   = null
    trunks       = null
    vlan_id      = null
  }]

  on_boot = false
  started = true

  lifecycle {
    ignore_changes = [
      operating_system, serial_device, description, initialization,
      agent, machine, keyboard_layout,
    ]
  }
}
