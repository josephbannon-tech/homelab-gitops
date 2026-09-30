# pim-tools

Deterministic tool server over the Radicale CalDAV store for Open WebUI
(source and design: https://github.com/josephbannon-tech/homelab-pim-tools).
Step 2 of the personal data layer plan in the private homelab docs.

- Image: GHCR, digest-pinned in `deployment.yaml`; Renovate tracks it.
- Credentials: SealedSecret `pim-tools-radicale` (`RADICALE_USER`,
  `RADICALE_PASSWORD`), the same htpasswd identity the operator's phone uses.
- Reaches Radicale in-cluster (`radicale.pim.svc:5232`), never via the NodePort.
- ClusterIP only; consumed by Open WebUI's backend as an external OpenAPI tool
  server. No NodePort until the tools carry their own auth.
- Stateless: nothing to back up. Radicale holds the data.
