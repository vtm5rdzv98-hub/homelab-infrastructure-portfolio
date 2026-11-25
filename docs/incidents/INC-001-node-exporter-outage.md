# INC-001 — Storage Node Monitoring Failure

Date: 2026-11-23
Environment: HomeLab Infrastructure
Affected service: Node Exporter on lab-storage
Severity: Critical (test classification)
Type: Controlled failure simulation

## Objective
Verify that Prometheus detects a sustained metrics
collection failure and triggers the NodeDown alert.

## Test Procedure
1. Stop Node Exporter on lab-storage.
2. Observe Prometheus target health.
3. Confirm NodeDown enters the Firing state.
4. Restart Node Exporter.
5. Confirm both monitoring targets return to UP.

## Observed Results
- NodeDown entered the Firing state.
- Prometheus displayed FIRING (1).
- Both monitored Linux nodes subsequently reported up = 1.
- The final Prometheus API response listed zero active alerts.

## Findings
The monitoring stack detects loss of a metrics endpoint.
The test does not establish automatic service recovery
or complete host-failure detection.

See the [evidence index](../../evidence/README.md) for the firing and cleared alert captures. The exercise established detection in Prometheus. External alert delivery remains untested.
