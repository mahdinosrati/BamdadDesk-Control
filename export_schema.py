"""Refresh the schema embedded by the Rust client after catalog changes."""
import json
from pathlib import Path
from control.catalog import catalog

Path(__file__).with_name("policy-schema.json").write_text(
    json.dumps(catalog(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
