# Grafana provisioning

Grafana 13.3.1 is an overlay of the gateway monitoring Compose project. The data source points to `http://prometheus:9090` on the Compose network. The versioned dashboard and provisioning files live under [services/monitoring/grafana](../services/monitoring/grafana/). Grafana's SQLite database and other live state reside on the named Grafana volume.

Follow the [build guide](BUILD_GUIDE.md#3-deploy-the-services-on-a-fresh-gateway) for bootstrap and the [runbook](RUNBOOK.md#health-checks-and-web-access) for web access. In Grafana, open **Dashboards → HomeLab → HomeLab Infrastructure Overview**. If a panel is empty, query its expression in Prometheus to verify series and labels.

The [recovery exercise](tests/TEST-003-monitoring-application-recovery.md) established startup and database health after restore. The [completion recovery drill](tests/TEST-004-engineering-completion.md) retrieved the archived dashboard and panels through the versioned API. Authenticated restored login and visual rendering of the restored panels remain unverified.
