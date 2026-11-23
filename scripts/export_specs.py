# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Luca Atella

"""Regenerate checked-in JSON Schema and OpenAPI contracts deterministically."""

import json
import tempfile
from pathlib import Path

from jsonschema import Draft202012Validator

from vigilact.models import (
    CapabilityManifest, CapabilityView, CloudEvent, CommandList, CommandRequest,
    CommandResult, CommandView, ContractProposal, ContractView, EventReceipt, OutboxPage,
)
from vigilact.server import create_app

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = {
    "contract-proposal": ContractProposal,
    "contract-view": ContractView,
    "cloudevent-subset": CloudEvent,
    "event-receipt": EventReceipt,
    "capability-manifest": CapabilityManifest,
    "capability-view": CapabilityView,
    "command-request": CommandRequest,
    "command-result": CommandResult,
    "command-view": CommandView,
    "command-list": CommandList,
    "outbox-page": OutboxPage,
}


def write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    for name, model in SCHEMAS.items():
        schema = model.model_json_schema()
        Draft202012Validator.check_schema(schema)
        write_json(ROOT / "schemas" / f"{name}.schema.json", schema)

    with tempfile.TemporaryDirectory() as folder:
        app = create_app(Path(folder) / "specs.db", credentials={
            "spec-generator": {"role": "operator", "key": "local-generation-only-secret"}},
            sweep_seconds=0)
        write_json(ROOT / "api" / "openapi.json", app.openapi())
    print(f"Exported {len(SCHEMAS)} JSON Schemas and OpenAPI 3.x document")


if __name__ == "__main__":
    main()
