# cloudnative-pg

The CloudNativePG operator (chart 0.29.1 / operator 1.30.1), deployed once in
`cnpg-system` ahead of any consumer (sync wave -1). Postgres instances are then
declared as `Cluster` CRs beside the app that owns them; the first is Immich's
(`charts/immich/templates/postgres.yaml`).

Why an operator rather than a StatefulSet (decided 2026-09-30): the chart
maintainers' path for Immich, declarative bootstrap (`initdb` + extensions),
built-in logical/physical backup CRDs that will target Backblaze B2 once the
account exists, and the pattern a platform role expects. The cost is one more
Application and CRDs large enough to need `ServerSideApply=true`.
