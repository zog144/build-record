import importlib.util
from pathlib import Path
import re
import unittest

import zog.build_record
from zog.build_record.cli import main


ROOT = Path(__file__).resolve().parents[1]


class NamespaceMigrationTests(unittest.TestCase):
    def test_canonical_namespace_and_version(self):
        self.assertEqual(zog.build_record.__version__, "0.8.2")
        self.assertTrue(callable(main))
        self.assertIsNone(importlib.util.find_spec("build_record"))

    def test_source_tree_is_directly_assemblable(self):
        component = ROOT / "src" / "zog" / "build_record"
        self.assertTrue((component / "__init__.py").is_file())
        self.assertFalse((ROOT / "src" / "zog" / "__init__.py").exists())
        self.assertFalse((ROOT / "build_record").exists())

    def test_legacy_python_module_paths_do_not_return(self):
        patterns = (
            re.compile(r"\bfrom\s+build_record\b"),
            re.compile(r"\bimport\s+build_record\b"),
            re.compile(r"\bpython(?:3)?\s+-m\s+build_record\b"),
            re.compile(r"['\"]build_record\.(?:cli|model|store|graph|audit|image_build|snapshot)"),
        )
        offenders = []
        for path in ROOT.rglob("*"):
            if not path.is_file() or ".git" in path.parts:
                continue
            if path.suffix not in {".py", ".toml", ".yml", ".yaml", ".md"}:
                continue
            text = path.read_text(encoding="utf-8")
            if any(pattern.search(text) for pattern in patterns):
                offenders.append(str(path.relative_to(ROOT)))
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
