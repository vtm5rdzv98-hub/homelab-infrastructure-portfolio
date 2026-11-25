PYTHON ?= python3
ANSIBLE_PLAYBOOK ?= ansible-playbook
DOCKER ?= docker

export ANSIBLE_PLAYBOOK RECOVERY_RUN RECOVERY_INVENTORY RECOVERY_TARGET
export RECOVERY_HOSTNAME RECOVERY_MODE RECOVERY_APPROVED RECOVERY_ORIGINAL_APPROVED
export RECOVERY_BACKUP_ROOT RECOVERY_WINDOW_SECONDS RECOVERY_ASK_BECOME_PASS

.PHONY: validate validate-live test-recovery

validate:
	$(PYTHON) -m unittest discover -s tests
	@set -e; for script in scripts/*.sh; do bash -n "$$script"; done
	@command -v "$(ANSIBLE_PLAYBOOK)" >/dev/null || { echo "Install the Ansible controller dependencies in docs/BUILD_GUIDE.md." >&2; exit 1; }
	@set -e; for playbook in ansible/playbooks/*.yml; do \
		case "$$playbook" in *bootstrap-fresh.yml) inventory=ansible/inventory/fresh.example.ini ;; *) inventory=ansible/inventory/hosts.ini ;; esac; \
		"$(ANSIBLE_PLAYBOOK)" -i "$$inventory" --syntax-check "$$playbook"; \
	done
	@command -v "$(DOCKER)" >/dev/null || { echo "Install the Docker CLI and Compose plugin." >&2; exit 1; }
	$(DOCKER) compose -f services/portal/compose.yaml config --quiet
	$(DOCKER) compose -f services/monitoring/compose.yaml -f services/monitoring/compose.grafana.yaml -f services/monitoring/compose.alerts.yaml config --quiet
	$(DOCKER) compose --env-file infra/docker/.env.example -f infra/docker/compose.yaml config --quiet

validate-live:
	bash scripts/verify-lab.sh

test-recovery:
	bash scripts/test-recovery.sh
