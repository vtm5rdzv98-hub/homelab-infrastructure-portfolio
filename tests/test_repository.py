"""Static repository checks. Does NOT validate any live server or network."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class RepositoryChecks(unittest.TestCase):
    def test_expected_documents_exist(self):
        for relative in ('MASTER_PLAN.md', 'docs/ARCHITECTURE.md', 'docs/BUILD_GUIDE.md',
                         'docs/TEST_PLAN.md', 'docs/RUNBOOK.md', 'docs/SECURITY.md'):
            with self.subTest(relative=relative):
                self.assertTrue((ROOT / relative).is_file())

    def test_dashboard_schema_and_real_queries(self):
        dashboard = json.loads((ROOT / 'services/monitoring/grafana/dashboards/homelab-overview.json').read_text())
        self.assertGreaterEqual(len(dashboard['panels']), 3)
        self.assertTrue(all(panel['targets'][0]['expr'] for panel in dashboard['panels']))
        self.assertTrue(any('node_memory_' in p['targets'][0]['expr'] for p in dashboard['panels']))

    def test_deployed_compose_publishes_only_on_loopback(self):
        expected = {
            'services/portal/compose.yaml': ['127.0.0.1:8080:80'],
            'services/monitoring/compose.yaml': ['127.0.0.1:9090:9090'],
            'services/monitoring/compose.grafana.yaml': ['127.0.0.1:3000:3000'],
            'services/monitoring/compose.alerts.yaml': [],
        }
        for relative, ports in expected.items():
            with self.subTest(relative=relative):
                content = (ROOT / relative).read_text()
                port_lists = re.findall(r'^    ports:\n((?:^      - [^\n]+\n)+)', content, re.MULTILINE)
                bindings = [
                    line.strip().removeprefix('- ').strip('"').strip("'")
                    for port_list in port_lists
                    for line in port_list.splitlines()
                ]
                self.assertEqual(bindings, ports)

    def test_ignore_secrets_and_backups(self):
        ignored = (ROOT / '.gitignore').read_text()
        self.assertIn('.env', ignored)
        self.assertIn('backups/', ignored)
        self.assertIn('*.vdi', ignored)
        self.assertIn('/docs/evidence/', ignored)
        self.assertIn('**/secrets/*', ignored)
        self.assertIn('SHA256SUMS', ignored)

if __name__ == '__main__':
    unittest.main()
