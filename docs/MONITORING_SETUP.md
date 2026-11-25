# Monitoring configuration

The gateway runs Prometheus, Grafana and Node Exporter. Use the base Compose file and the Grafana and alerts overlays together. The storage Node Exporter is a systemd service. Prometheus sees three jobs in the reference deployment: `prometheus`, `lab-gw` and `lab-storage`.

For first deployment, see the [build guide](BUILD_GUIDE.md#3-deploy-the-services-on-a-fresh-gateway). To check an existing stack, use the [operations runbook](RUNBOOK.md#health-checks-and-web-access). Prometheus evaluates the NodeDown alert after a one-minute sustained exporter outage. See the [controlled outage report](incidents/INC-001-node-exporter-outage.md).

Node Exporter uses the gateway PID namespace and a read-only root mount. The dashboard relies on the labels configured in [prometheus.yml](../services/monitoring/prometheus.yml). Review these settings when changing host names or metrics scope.
