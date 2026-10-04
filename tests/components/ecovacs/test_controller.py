"""Test persistence of renewable Ecovacs account credentials."""

from typing import Any
from unittest.mock import Mock, patch

from deebot_client.models import AccountCredentials
import pytest

from homeassistant.components.ecovacs.const import CONF_CREDENTIALS
from homeassistant.components.ecovacs.controller import _stored_account_credentials
from homeassistant.const import CONF_DEVICE_ID
from homeassistant.core import HomeAssistant

from .const import CLOUD_DEVICE_ID, STORED_ENTRY_DATA_CLOUD

from tests.common import MockConfigEntry


@pytest.mark.parametrize(
    "stored",
    [
        None,
        {},
        [],
        "invalid",
        {"access_token": "token"},
        {"user_id": "uid"},
        {"access_token": None, "user_id": "uid"},
        {"access_token": "", "user_id": "uid"},
        {"access_token": "token", "user_id": None},
        {"access_token": "token", "user_id": ""},
        {"access_token": 123, "user_id": "uid"},
        {"access_token": "token", "user_id": 123},
    ],
)
def test_incomplete_account_credentials_are_ignored(stored: Any) -> None:
    """An incomplete stored token must fall back to normal authentication."""
    assert _stored_account_credentials({CONF_CREDENTIALS: stored}) is None


@pytest.mark.parametrize(
    "mock_config_entry_data",
    [
        STORED_ENTRY_DATA_CLOUD
        | {CONF_CREDENTIALS: {"access_token": "stored-token", "user_id": "stored-uid"}}
    ],
)
async def test_controller_restores_account_credentials(
    init_integration: MockConfigEntry,
    mock_authenticator_constructor: Mock,
) -> None:
    """Loading an existing entry seeds the account and the same device ID."""
    call = mock_authenticator_constructor.call_args
    assert call.kwargs["account_credentials"] == AccountCredentials(
        access_token="stored-token", user_id="stored-uid"
    )
    assert call.args[0].device_id == CLOUD_DEVICE_ID


async def test_controller_persists_credentials_and_reloads(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_authenticator: Mock,
    mock_authenticator_constructor: Mock,
) -> None:
    """A refreshed account is stored once and restored by the next controller."""
    original = dict(init_integration.data)
    account = AccountCredentials(
        access_token="replacement-token", user_id="replacement-uid"
    )
    callback = mock_authenticator.subscribe_account_credentials.call_args.args[0]
    with patch.object(
        hass.config_entries,
        "async_update_entry",
        wraps=hass.config_entries.async_update_entry,
    ) as update:
        await callback(account)
        update.assert_called_once()
        await callback(account)
        update.assert_called_once()
    assert init_integration.data == original | {
        CONF_CREDENTIALS: {
            "access_token": account.access_token,
            "user_id": account.user_id,
        }
    }
    assert init_integration.data[CONF_DEVICE_ID] == CLOUD_DEVICE_ID
    unsubscribe = mock_authenticator.subscribe_account_credentials.return_value
    assert await hass.config_entries.async_reload(init_integration.entry_id)
    await hass.async_block_till_done()
    unsubscribe.assert_called_once()
    assert (
        mock_authenticator_constructor.call_args.kwargs["account_credentials"]
        == account
    )
    assert mock_authenticator_constructor.call_args.args[0].device_id == CLOUD_DEVICE_ID
