#!/usr/bin/env python3
"""Tests for `tools/check-symbols.py`'s extraction: `from rbt… import`
and `import rbt…` lines in code blocks are collected beside the
`reboot…` ones, so a wrong generated-code import is checked too; a
name that only starts with rbt or reboot is not.

    python3 tests/tools/check_symbols_test.py
"""

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
spec = importlib.util.spec_from_file_location("check_symbols", ROOT / "tools" / "check-symbols.py")
cs = importlib.util.module_from_spec(spec)
sys.modules["check_symbols"] = cs
spec.loader.exec_module(cs)

DOC = """# Example

```python
from reboot.aio.contexts import WriterContext
from rbt.v1alpha1.errors_pb2 import StateNotConstructed
import rbt.std.oauth.v1.oauth_rbt
from rbtx.thing import Other
import rebooted
```
"""


class ExtractTest(unittest.TestCase):
    def test_rbt_imports_are_collected(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            path = Path(tmp) / "doc.md"
            path.write_text(DOC)
            items = cs.extract(path)
        got = {(i["module"], tuple(i["attrs"])) for i in items}
        self.assertIn(("reboot.aio.contexts", ("WriterContext",)), got)
        self.assertIn(("rbt.v1alpha1.errors_pb2", ("StateNotConstructed",)), got)
        self.assertIn(("rbt.std.oauth.v1.oauth_rbt", ()), got)
        self.assertEqual(len(items), 3, items)

    def test_patterns(self) -> None:
        self.assertIsNotNone(cs.FROM_IMPORT.match("from rbt.v1alpha1 import errors_pb2"))
        self.assertIsNotNone(cs.IMPORT.match("import rbt.v1alpha1.errors_pb2"))
        self.assertIsNone(cs.IMPORT.match("import rbtx"))
        self.assertIsNone(cs.IMPORT.match("import rebooted"))


if __name__ == "__main__":
    unittest.main()
