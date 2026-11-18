import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

COLLECTOR = Path(__file__).with_name('collect_review_scope.py')


class ScopeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.git('init', '-q')
        self.git('config', 'user.name', 'Scope Test')
        self.git('config', 'user.email', 'scope@example.invalid')
        self.write('go/handler.go', 'old\n')
        self.write('php/producer.php', 'old\n')
        self.write('old name.go', 'old\n')
        self.git('add', '.')
        self.git('commit', '-qm', 'base')
        self.base = self.git('rev-parse', 'HEAD').strip()

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.root), *args], text=True)

    def write(self, name, content):
        dest = self.root / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content)

    def collect(self, *args):
        result = subprocess.run([sys.executable, str(COLLECTOR), *args],
                                cwd=self.root / 'go', text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_workspace_includes_sibling_untracked_and_deleted(self):
        self.write('go/handler.go', 'new\n')
        self.write('php/producer.php', 'new\n')
        self.write('go/new consumer.go', 'new\n')
        self.write('spec/feature.md', 'requirements\n')
        self.write('README.md', 'unrelated, classification belongs to reviewer\n')
        self.git('rm', '-q', 'old name.go')
        data = self.collect()
        paths = {f['path'] for f in data['candidates']}
        self.assertEqual(paths, {'go/handler.go', 'php/producer.php',
                                'go/new consumer.go', 'spec/feature.md', 'README.md', 'old name.go'})
        self.assertEqual(data['mode'], 'workspace')
        self.assertFalse(data['empty'])
        self.assertFalse(data['acceptance_proven'])

    def test_staged_does_not_claim_worktree_test_evidence(self):
        self.write('go/handler.go', 'staged\n')
        self.git('add', 'go/handler.go')
        self.write('go/handler.go', 'unstaged fix\n')
        self.write('php/producer.php', 'unstaged\n')
        data = self.collect('--mode', 'staged')
        self.assertEqual([f['path'] for f in data['candidates']], ['go/handler.go'])
        self.assertFalse(data['worktree_matches_target'])
        self.assertIn('go/handler.go', data['worktree_drift'])

    def test_empty_is_not_acceptance(self):
        data = self.collect('--mode', 'staged')
        self.assertTrue(data['empty'])
        self.assertFalse(data['acceptance_proven'])

    def test_range_excludes_uncommitted_and_keeps_rename(self):
        self.git('mv', 'old name.go', 'new name.go')
        self.git('commit', '-qm', 'rename')
        self.write('go/handler.go', 'worktree only\n')
        data = self.collect('--mode', 'range', '--base', self.base, '--head', 'HEAD')
        self.assertEqual([f['path'] for f in data['candidates']], ['new name.go'])
        self.assertEqual(data['candidates'][0]['old_path'], 'old name.go')
        self.assertFalse(data['worktree_matches_target'])

    def test_staged_only_add_does_not_create_unstaged_candidate(self):
        self.write('go/new.go', 'new\n')
        self.git('add', 'go/new.go')
        data = self.collect()
        self.assertEqual([f['path'] for f in data['candidates']], ['go/new.go'])
        self.assertEqual(data['candidates'][0]['sources'], ['staged'])

    def test_mode_change_alters_fingerprint(self):
        self.write('go/handler.go', 'changed\n')
        before = self.collect()['candidates'][0]
        (self.root / 'go/handler.go').chmod(0o755)
        after = self.collect()['candidates'][0]
        self.assertNotEqual(before, after)


if __name__ == '__main__':
    unittest.main()
