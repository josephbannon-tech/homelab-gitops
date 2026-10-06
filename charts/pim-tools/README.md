# pim-tools

Deterministic tool server over the Radicale CalDAV store for Open WebUI
(source and design: https://github.com/josephbannon-tech/homelab-pim-tools).
Step 2 of the personal data layer plan in the private homelab docs.

- Image: GHCR, digest-pinned in `deployment.yaml`; Renovate tracks it.
- Credentials: SealedSecret `pim-tools-radicale` (`RADICALE_USER`,
  `RADICALE_PASSWORD`), the same htpasswd identity the operator's phone uses.
- Caller auth: SealedSecret `pim-tools-token` (`PIM_TOOLS_TOKEN`, v0.3.0). A
  shared-secret bearer on every route except `/health` and `/openapi.json`;
  trust, not identity. Open WebUI's tool-server registration carries it.
- Reaches Radicale in-cluster (`radicale.pim.svc:5232`), never via the NodePort.
- Two doors, one definition: OpenAPI for Open WebUI's backend (in-cluster,
  `pim-tools.pim.svc:8000`) and MCP (Streamable HTTP at `/mcp`) for headless
  Claude Code on JBVM02 via NodePort 30800. The NodePort exists because the
  MCP client is outside the cluster; it was withheld until the token landed.
- Stateless: nothing to back up. Radicale holds the data.
