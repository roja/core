"""Tests for diagnostics data."""

import pytest
from syrupy.assertion import SnapshotAssertion
from syrupy.filters import props

from homeassistant.components.diagnostics import REDACTED
from homeassistant.components.ecovacs.const import CONF_CREDENTIALS
from homeassistant.const import CONF_USERNAME
from homeassistant.core import HomeAssistant

from .const import STORED_ENTRY_DATA_CLOUD, STORED_ENTRY_DATA_SELF_HOSTED

from tests.common import MockConfigEntry
from tests.components.diagnostics import get_diagnostics_for_config_entry
from tests.typing import ClientSessionGenerator


@pytest.mark.parametrize(
    "mock_config_entry_data",
    [STORED_ENTRY_DATA_CLOUD, STORED_ENTRY_DATA_SELF_HOSTED],
    ids=lambda data: data[CONF_USERNAME],
)
async def test_diagnostics(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    init_integration: MockConfigEntry,
    snapshot: SnapshotAssertion,
) -> None:
    """Test diagnostics."""
    assert await get_diagnostics_for_config_entry(
        hass, hass_client, init_integration
    ) == snapshot(exclude=props("entry_id", "created_at", "modified_at"))


@pytest.mark.parametrize(
    "mock_config_entry_data",
    [
        data
        | {
            CONF_CREDENTIALS: {
                "access_token": "secret-account-token",
                "user_id": "secret-user-id",
            }
        }
        for data in (STORED_ENTRY_DATA_CLOUD, STORED_ENTRY_DATA_SELF_HOSTED)
    ],
    ids=["cloud", "self_hosted"],
)
async def test_account_credentials_are_redacted(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    init_integration: MockConfigEntry,
) -> None:
    """Renewable tokens must never appear in a downloaded diagnostic report."""
    diagnostics = await get_diagnostics_for_config_entry(
        hass, hass_client, init_integration
    )
    assert diagnostics["config"]["data"][CONF_CREDENTIALS] == REDACTED
    assert "secret-account-token" not in str(diagnostics)
    assert "secret-user-id" not in str(diagnostics)
