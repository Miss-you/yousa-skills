from functools import partial
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
import unittest
from unittest.mock import patch

from scripts import build_skill_site, serve_skill_site


class SkillSiteTests(unittest.TestCase):
    def test_public_release_excludes_unlisted_assets_and_preserves_live_on_failure(self):
        with TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            assets = root / "site"
            assets.mkdir(parents=True)
            (assets / "registry.js").write_text("// public")
            (assets / "registry.css").write_text("/* public */")
            (assets / "local-config.txt").write_text("local-only")
            inventory_path = root / "docs/readme/skills.json"
            inventory_path.parent.mkdir(parents=True)
            inventory_path.write_text(json.dumps([{
                "name": "test-skill", "path": "skills/test-skill",
                "description_en": "A <sample> skill", "description_zh": "测试 skill",
            }]))
            skill = root / "skills/test-skill/SKILL.md"
            skill.parent.mkdir(parents=True)
            skill.write_text("---\nname: test-skill\ndescription: Test.\n---\n")
            deploy = Path(temp) / "deploy"

            with patch.object(build_skill_site, "repo_root", return_value=root):
                self.assertEqual(build_skill_site.publish(deploy), 1)
                current = deploy / "current"
                first_release = current.resolve()
                self.assertEqual({path.name for path in (current / "assets").iterdir()}, {
                    "registry.css", "registry.js",
                })
                page = current / "en/skills/test-skill/index.html"
                self.assertIn("A &lt;sample&gt; skill", page.read_text())
                (assets / "registry.js").unlink()
                (assets / "registry.js").symlink_to(assets / "local-config.txt")
                with self.assertRaisesRegex(ValueError, "Public asset must be a regular file"):
                    build_skill_site.publish(deploy)
                self.assertEqual(current.resolve(), first_release)
                self.assertEqual(list((deploy / "releases").resolve().iterdir()), [first_release])

    def test_share_links_preserve_locale_and_404s_are_branded(self):
        with TemporaryDirectory() as temp:
            site = Path(temp)
            build_skill_site.build(site)
            handler = partial(serve_skill_site.RegistryHandler, directory=site)
            with ThreadingHTTPServer(("127.0.0.1", 0), handler) as server:
                worker = Thread(target=server.serve_forever, daemon=True)
                worker.start()
                connection = HTTPConnection("127.0.0.1", server.server_port, timeout=5)
                try:
                    skill = build_skill_site.load_manifest(build_skill_site.repo_root())[0]["name"]
                    connection.request("GET", f"/en/?skill={skill}")
                    response = connection.getresponse()
                    self.assertEqual(response.status, 302)
                    self.assertEqual(response.getheader("Location"), f"/en/skills/{skill}/")
                    self.assertEqual(response.getheader("Cache-Control"), "no-store")
                    response.read()

                    for path in ("/en/?skill=missing", "/en/?skill=", "/en/skills/missing/"):
                        connection.request("GET", path)
                        response = connection.getresponse()
                        self.assertEqual(response.status, 404)
                        self.assertIn(b'Browse all skills', response.read())

                    for path in ("/assets/", "/.git/config", "/%2e%2e/tunnel.yml"):
                        connection.request("GET", path)
                        response = connection.getresponse()
                        self.assertEqual(response.status, 404)
                        response.read()
                finally:
                    connection.close()
                    server.shutdown()
                    worker.join()
