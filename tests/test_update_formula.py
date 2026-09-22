"""Exercise release verification and refusal to publish unchecked hashes."""

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import update_formula as updater


class UpdateTests(unittest.TestCase):
    def setUp(self):
        self.original = updater.FORMULA.read_text()
        self.current = updater.formula_version(self.original)
        major, minor, patch_number = map(int, self.current.split("."))
        self.next_version = f"{major}.{minor}.{patch_number + 1}"
        self.payloads = {"arm64": b"arm archive", "x64": b"intel archive"}
        self.hashes = {arch: hashlib.sha256(data).hexdigest() for arch, data in self.payloads.items()}
        self.draft = False
        self.prerelease = False
        self.corrupt = False
        self.duplicate = False
        self.missing = False

    def fake_gh(self, *arguments):
        if arguments[1] == "view":
            return json.dumps({"tagName": f"v{self.next_version}", "isDraft": self.draft,
                               "isPrerelease": self.prerelease})
        directory = Path(arguments[arguments.index("--dir") + 1])
        lines = []
        for arch, data in self.payloads.items():
            name = f"omnivox-{self.next_version}-macos-{arch}.tar.gz"
            (directory / name).write_bytes(b"corrupted" if self.corrupt and arch == "x64" else data)
            if not (self.missing and arch == "x64"):
                lines.append(f"{self.hashes[arch]}  {name}\n")
        if self.duplicate:
            lines.append(lines[0])
        (directory / "sha256sums.txt").write_text("".join(lines))
        return ""

    def test_verified_update_preserves_install_and_tests(self):
        with patch.object(updater, "gh", side_effect=self.fake_gh):
            hashes = updater.release_hashes(self.next_version)
        result = updater.render_formula(self.original, self.next_version, hashes)
        self.assertEqual(updater.formula_version(result), self.next_version)
        self.assertEqual(result.count(f"/v{self.next_version}/omnivox-{self.next_version}-macos-"), 2)
        for digest in hashes.values():
            self.assertIn(digest, result)
        self.assertEqual(self.original.split("  def install", 1)[1], result.split("  def install", 1)[1])

    def test_failed_release_leaves_formula_untouched(self):
        for failure in ("draft", "prerelease", "corrupt", "duplicate", "missing"):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as temporary:
                setattr(self, failure, True)
                path = Path(temporary) / "omnivox.rb"
                path.write_text(self.original)
                with patch.object(updater, "gh", side_effect=self.fake_gh), self.assertRaises(ValueError):
                    updater.update_formula(path, self.next_version)
                self.assertEqual(path.read_text(), self.original)
                setattr(self, failure, False)

    def test_check_does_not_edit_outdated_formula(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "omnivox.rb"
            path.write_text(self.original)
            with patch.object(updater, "gh", side_effect=self.fake_gh), self.assertRaises(ValueError):
                updater.update_formula(path, self.next_version, check=True)
            self.assertEqual(path.read_text(), self.original)

    def test_rejects_replaced_release_and_downgrade(self):
        for version in (self.current, "0.0.1"):
            with self.subTest(version=version), self.assertRaises(ValueError):
                updater.render_formula(self.original, version, self.hashes)

    def test_upstream_upgrade_resets_packaging_revision(self):
        revised = self.original.replace("  depends_on :macos", "  revision 3\n\n  depends_on :macos")
        result = updater.render_formula(revised, self.next_version, self.hashes)
        self.assertNotIn("  revision ", result)

    def test_rejects_inconsistent_url_versions(self):
        changed = self.original.replace(f"omnivox-{self.current}-macos-x64", "omnivox-0.0.1-macos-x64")
        with self.assertRaises(ValueError):
            updater.render_formula(changed, self.next_version, self.hashes)

    def test_stable_version_validation(self):
        self.assertEqual(updater.version_number("v1.12.0"), "1.12.0")
        for value in ("1.12.0-rc1", "main", "../1.12.0", "1.12.0\n", "1.12"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                updater.version_number(value)


if __name__ == "__main__":
    unittest.main()
