"""Offline regressions for backup integrity, SSH trust, and documentation links."""
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from hashlib import sha256
from io import StringIO
import importlib.util
import json
from pathlib import Path
import re
import shlex
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / f'{name}.py')
    script = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(script)
    return script


backup = load_script('copy-backup')
vbox = load_script('provision-vbox')


class BackupVerification(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.run_dir = Path(directory.name) / '20261125T010002Z'
        self.run_dir.mkdir()
        self.archive = self.run_dir / 'files.tar.gz'
        self.manifest = self.run_dir / 'files.tar.gz.sha256'
        self.archive.write_bytes(b'sample backup fixture')
        self.digest = sha256(self.archive.read_bytes()).hexdigest()
        self.manifest.write_text(f'{self.digest}  {self.archive.name}\n')

    def test_checksums_and_same_filesystem_guard(self):
        self.assertEqual(backup.verify(self.run_dir, 'storage'), {self.archive.name: self.digest})
        destination = self.run_dir.parent / 'private'
        destination.mkdir(mode=0o700)
        root = next(path for path in destination.resolve().parents if path.is_mount())
        with self.assertRaisesRegex(ValueError, 'same filesystem'):
            backup.copy_backup(self.run_dir, destination, 'storage', root)
        self.assertFalse(list(destination.iterdir()))
        self.assertTrue(self.archive.is_file())

    def test_checksum_failure_leaves_source_in_place(self):
        self.archive.write_bytes(b'changed fixture')
        with self.assertRaisesRegex(ValueError, 'SHA-256 mismatch'):
            backup.verify(self.run_dir, 'storage')
        self.assertEqual(self.archive.read_bytes(), b'changed fixture')

    def test_manifest_cannot_alias_files_or_include_paths(self):
        for name in ['../files.tar.gz', '/files.tar.gz', 'other.tar.gz']:
            with self.subTest(name=name):
                self.manifest.write_text(f'{self.digest}  {name}\n')
                with self.assertRaisesRegex(ValueError, 'Invalid entry'):
                    backup.verify(self.run_dir, 'storage')

    def test_symlink_is_refused(self):
        target = self.run_dir / 'original'
        self.archive.rename(target)
        self.archive.symlink_to(target)
        with self.assertRaisesRegex(ValueError, 'regular file'):
            backup.verify(self.run_dir, 'storage')


class RecurringReplication(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.source = self.root / 'source'
        self.destination = self.root / 'target'
        self.source.mkdir()
        self.destination.mkdir(mode=0o700)
        self.old = self.fixture('20261125T010001Z')
        self.new = self.fixture('20261125T010002Z')
        (self.source / '20261125T010003Z').mkdir()

    def fixture(self, name):
        run = self.source / name
        run.mkdir()
        payload = name.encode()
        (run / 'files.tar.gz').write_bytes(payload)
        (run / 'files.tar.gz.sha256').write_text(f'{sha256(payload).hexdigest()}  files.tar.gz\n')
        return run

    def replicate(self, reserve=0):
        @contextmanager
        def destination_lock(destination, mount, source):
            yield destination

        stdout, stderr = StringIO(), StringIO()
        mount = next(path for path in self.source.resolve().parents if path.is_mount())
        with (patch.object(backup, 'locked_destination', destination_lock),
              redirect_stdout(stdout), redirect_stderr(stderr)):
            status = backup.replicate(self.source, mount, self.destination, mount, 'storage', reserve, 1)
        return status, stdout.getvalue(), stderr.getvalue()

    def test_copy_retry_and_retention_preview_preserve_backups(self):
        code, log, errors = self.replicate()
        self.assertEqual((code, errors), (0, ''))
        self.assertIn('copied=2 already_verified=0 deferred=1 failed=0', log)
        self.assertIn('preview only: storage-20261125T010001Z', log)
        code, log, errors = self.replicate()
        self.assertEqual((code, errors), (0, ''))
        self.assertIn('copied=0 already_verified=2 deferred=1 failed=0', log)
        for run in (self.old, self.new):
            self.assertEqual(backup.verify(run, 'storage'),
                             backup.verify(self.destination / f'storage-{run.name}', 'storage'))

    def test_insufficient_space_and_corrupt_existing_copy_fail_closed(self):
        code, log, errors = self.replicate(reserve=10**30)
        self.assertEqual(code, 1)
        self.assertIn('insufficient space', errors)
        self.assertIn('preview withheld', log)
        self.assertEqual(list(self.destination.iterdir()), [])
        self.assertEqual(self.replicate()[0], 0)
        archive = self.destination / f'storage-{self.old.name}' / 'files.tar.gz'
        archive.write_bytes(b'corrupt copy')
        code, log, errors = self.replicate()
        self.assertEqual(code, 1)
        self.assertIn('SHA-256 mismatch', errors)
        self.assertIn('preview withheld', log)
        self.assertEqual(archive.read_bytes(), b'corrupt copy')
        self.assertTrue((self.old / 'files.tar.gz').is_file())


class FreshProvisioning(unittest.TestCase):
    def test_vm_names_require_fresh_prefix(self):
        self.assertEqual(vbox.names('homelab-fresh-ci'),
                         ('homelab-fresh-ci-gw', 'homelab-fresh-ci-storage'))
        for unsafe in ['lab-gw', 'lab-storage', 'homelab-fresh-../another']:
            with self.subTest(name=unsafe), self.assertRaises(ValueError):
                vbox.names(unsafe)


    def test_host_keys_are_pinned_and_proxy_supports_quoted_paths(self):
        with TemporaryDirectory(prefix="HomeLab's test ") as directory:
            run_dir = Path(directory)
            prefix = 'homelab-fresh-ci'
            gateway, storage = vbox.names(prefix)
            identity = run_dir / 'client-key'
            config = {
                'name': prefix, 'key': str(identity), 'port': 3222,
                'gateway_ip': '10.21.0.10', 'storage_ip': '10.21.0.11',
            }
            (run_dir / 'connection.json').write_text(json.dumps(config))
            for host, key in [(gateway, 'YWJj'), (storage, 'ZGVm')]:
                (run_dir / host).mkdir()
                (run_dir / host / 'console.log').write_text('HOMELAB_HOST_KEY ssh-ed25519 ' + key + '\n')

            with redirect_stdout(StringIO()):
                vbox.trust(SimpleNamespace(run_dir=run_dir))
            line = next(line for line in (run_dir / 'ssh.conf').read_text().splitlines()
                        if 'ProxyCommand' in line)
            self.assertEqual(shlex.split(line)[1:4],
                             ['ssh', '-F', str(run_dir.resolve() / 'ssh.conf')])
            (run_dir / storage / 'console.log').write_text('HOMELAB_HOST_KEY ssh-ed25519 bmV3\n')
            with self.assertRaisesRegex(ValueError, 'existing trusted keys'):
                vbox.trust(SimpleNamespace(run_dir=run_dir))


class MarkdownLinks(unittest.TestCase):
    def test_relative_targets_exist_inside_repository(self):
        markdown = [*ROOT.glob('*.md'), *ROOT.glob('docs/**/*.md'),
                    *ROOT.glob('evidence/**/*.md'), *ROOT.glob('infra/**/*.md')]
        for document in markdown:
            content = document.read_text()
            content = re.sub(r'(?ms)^(`{3,}|~{3,})[^\n]*\n.*?^\1\s*$', '', content)
            for link in re.findall(r'\]\(<?([^\s)>]+)>?(?:\s+"[^"]*")?\)', content):
                parts = urlsplit(link)
                if parts.scheme or parts.netloc or not parts.path:
                    continue
                with self.subTest(document=document.relative_to(ROOT), href=link):
                    target = (document.parent / unquote(parts.path)).resolve()
                    self.assertTrue(target.is_relative_to(ROOT) and target.exists())


if __name__ == '__main__':
    unittest.main()
