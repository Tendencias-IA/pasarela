"""Contract surface for HU-01."""

from pathlib import Path

import yaml


def test_accounts_contract_defines_required_responses() -> None:
    """HU-01 CA-1–CA-6."""
    contract = yaml.safe_load(
        (Path(__file__).parents[2] / "openapi.yaml").read_text(encoding="utf-8")
    )
    responses = contract["paths"]["/api/v1/accounts"]["post"]["responses"]
    assert set(responses) == {"201", "400", "409", "413", "422", "500"}
