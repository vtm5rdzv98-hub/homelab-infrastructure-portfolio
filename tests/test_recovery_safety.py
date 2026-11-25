"""Regression checks for explicit recovery selection and scratch-only extraction."""

import importlib.util
import io
import os
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    'extract_recovery_archive', ROOT / 'ansible/files/extract-recovery-archive.py')
extractor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(extractor)


class RecoveryCommand(unittest.TestCase):
    def run_wrapper(self, **settings):
        environment = {key: value for key, value in os.environ.items()
                       if not key.startswith('RECOVERY_')}
        environment.update(ANSIBLE_PLAYBOOK='/usr/bin/true', **settings)
        return subprocess.run(['bash', 'scripts/test-recovery.sh'], cwd=ROOT,
                              env=environment, capture_output=True, text=True)

    def test_no_default_inventory_or_host(self):
        result = self.run_wrapper(RECOVERY_MODE='isolated')
        self.assertEqual(result.returncode, 2)
        self.assertIn('explicit readable inventory', result.stderr)

    def test_original_gateway_requires_host_named_approval(self):
        settings = dict(RECOVERY_MODE='original', RECOVERY_INVENTORY='ansible/inventory/hosts.ini',
                        RECOVERY_TARGET='lab-gw', RECOVERY_HOSTNAME='lab-gw',
                        RECOVERY_APPROVED='yes', RECOVERY_RUN='20261124T050335Z')
        result = self.run_wrapper(**settings)
        self.assertEqual(result.returncode, 2)
        self.assertIn('RECOVERY_ORIGINAL_APPROVED=lab-gw', result.stderr)
        result = self.run_wrapper(**settings, RECOVERY_ORIGINAL_APPROVED='lab-gw')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Recovery host lab-gw (inventory host lab-gw, mode original)', result.stdout)

    def test_original_cannot_be_named_as_isolated(self):
        result = self.run_wrapper(RECOVERY_MODE='isolated', RECOVERY_INVENTORY='ansible/inventory/hosts.ini',
                                  RECOVERY_TARGET='lab-gw', RECOVERY_HOSTNAME='lab-gw',
                                  RECOVERY_APPROVED='yes', RECOVERY_RUN='20261124T050335Z')
        self.assertEqual(result.returncode, 2)
        self.assertIn('isolated gateway hostname', result.stderr)


class ArchiveExtraction(unittest.TestCase):
    def setup_archive(self, member):
        work = tempfile.TemporaryDirectory()
        self.addCleanup(work.cleanup)
        parent = Path(work.name)
        archive = parent / 'archive.tar.gz'
        destination = parent / 'scratch'
        destination.mkdir(mode=0o700)
        with tarfile.open(archive, 'w:gz') as output:
            sample = tarfile.TarInfo('sample')
            sample.size = 4
            output.addfile(sample, io.BytesIO(b'data'))
            if member:
                output.addfile(member)
        return archive, destination

    def test_extracts_regular_files_into_scratch(self):
        archive, destination = self.setup_archive(None)
        extractor.extract(archive, destination)
        self.assertEqual((destination / 'sample').read_bytes(), b'data')

    def test_rejects_links_and_traversal_before_any_extraction(self):
        symlink = tarfile.TarInfo('redirect')
        symlink.type = tarfile.SYMTYPE
        symlink.linkname = '../outside'
        hardlink = tarfile.TarInfo('hardlink')
        hardlink.type = tarfile.LNKTYPE
        hardlink.linkname = 'sample'
        for entry in (tarfile.TarInfo('../outside'), tarfile.TarInfo('/absolute'), symlink, hardlink):
            with self.subTest(entry=entry.name):
                archive, destination = self.setup_archive(entry)
                with self.assertRaises(ValueError):
                    extractor.extract(archive, destination)
                self.assertEqual(list(destination.iterdir()), [])
