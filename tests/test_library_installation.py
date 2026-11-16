import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from crit_launcher.minecraft.libraries import (
    collect_library_entries,
    download_urls,
    ensure_file,
)


class LibraryInstallationTests(unittest.TestCase):
    def test_forge_installer_keeps_multiple_versions(self):
        libraries = [
            {"name": "net.sf.jopt-simple:jopt-simple:5.0.4"},
            {"name": "net.sf.jopt-simple:jopt-simple:6.0-alpha-3"},
        ]
        game_entries, _ = collect_library_entries(libraries)
        installer_entries, _ = collect_library_entries(libraries, keep_versions=True)

        self.assertEqual(len(game_entries), 1)
        self.assertEqual(len(installer_entries), 2)
        self.assertEqual(
            installer_entries[1]["path"],
            "net/sf/jopt-simple/jopt-simple/6.0-alpha-3/jopt-simple-6.0-alpha-3.jar",
        )

    def test_jopt_simple_maven_fallback(self):
        entry = {
            "path": "net/sf/jopt-simple/jopt-simple/6.0-alpha-3/jopt-simple-6.0-alpha-3.jar",
            "url": "https://maven.minecraftforge.net/net/sf/jopt-simple/jopt-simple/6.0-alpha-3/jopt-simple-6.0-alpha-3.jar",
        }
        self.assertEqual(
            download_urls(entry),
            [
                entry["url"],
                "https://repo.maven.apache.org/maven2/" + entry["path"],
            ],
        )

    def test_download_uses_fallback(self):
        entry = {
            "path": "net/sf/jopt-simple/jopt-simple/6.0-alpha-3/jopt-simple-6.0-alpha-3.jar",
            "url": "https://maven.minecraftforge.net/" + "net/sf/jopt-simple/jopt-simple/6.0-alpha-3/jopt-simple-6.0-alpha-3.jar",
        }
        calls = []

        def download(url, dest, size, sha1, callback):
            calls.append(url)
            if len(calls) == 1:
                raise OSError("Download failed")
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(b"jar")

        with tempfile.TemporaryDirectory() as directory:
            with patch("crit_launcher.minecraft.libraries.http_download", side_effect=download):
                result = ensure_file(entry, Path(directory), None, retries=1)
            self.assertEqual(result.read_bytes(), b"jar")

        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[1], "https://repo.maven.apache.org/maven2/" + entry["path"])


if __name__ == "__main__":
    unittest.main()
