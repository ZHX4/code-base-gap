from __future__ import annotations

import json
import tempfile
from pathlib import Path

from code_base_gap.phase2.models import AuditInput
from code_base_gap.phase2.pipeline import run_phase2


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="code-base-gap-smoke-") as temp:
        root = Path(temp)
        (root / "src").mkdir()
        (root / "tests").mkdir()
        (root / "src" / "main.py").write_text("def main():\n    return 0\n", encoding="utf-8")
        (root / "tests" / "test_main.py").write_text("def test_main():\n    assert True\n", encoding="utf-8")
        (root / "pyproject.toml").write_text("[project]\nname='smoke'\n", encoding="utf-8")
        result = run_phase2(AuditInput(str(root)))
        payload = result.to_dict()
        assert payload["manifest"]["repository_revision"] == "unversioned"
        assert payload["manifest"]["stats"]["source_files"] == 1
        assert "Python" in payload["reconnaissance"]["languages"]
        assert payload["manifest"]["repository_metadata"]["execution_policy"]["tests_executed"] is False
        json.dumps(payload)
    print("Code Base Gap Phase 2 smoke test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
