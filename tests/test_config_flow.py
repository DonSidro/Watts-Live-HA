import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.data_entry_flow import FlowResultType

DOMAIN = "watts_live"
FLOW = "custom_components.watts_live.config_flow"
TRANSLATIONS = Path(__file__).parents[1] / "custom_components" / DOMAIN / "translations"

ADDRESS = "F3:E1:D0:27:B1:29"
SERIAL = "0123456789012345"
PROVISION_INPUT = {
    "address": ADDRESS,
    "serial": SERIAL,
    "host": "192.168.1.10",
    "port": 1883,
    "username": "user",
    "password": "pass",
}


def wait_returns(errors):
    return patch(
        f"{FLOW}.WattsLiveConfigFlow._async_wait_for_measurement",
        AsyncMock(return_value=errors),
    )


async def start(hass, option):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    return await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": option}
    )


async def choose(hass, result, option):
    return await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": option}
    )


async def test_manual_with_data_creates_entry(hass, mqtt_mock):
    result = await start(hass, "manual")
    with wait_returns({}):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"name": "123"}
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {"serial": "123"}


async def test_manual_timeout_offers_add_anyway(hass, mqtt_mock):
    result = await start(hass, "manual")
    with patch(f"{FLOW}.MEASUREMENT_TIMEOUT", 0.05):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"name": "123"}
        )

    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "no_data"
    assert result["menu_options"] == ["add_anyway", "manual"]
    assert result["description_placeholders"]["serial"] == "123"

    result = await choose(hass, result, "add_anyway")
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "123"
    assert result["data"] == {"serial": "123"}


async def test_manual_retry_returns_to_form(hass, mqtt_mock):
    result = await start(hass, "manual")
    with wait_returns({"base": "no_data"}):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"name": "123"}
        )

    result = await choose(hass, result, "manual")
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "manual"
    assert not result["errors"]


async def provision_without_data(hass, status):
    """Run the Bluetooth setup up to the point where no measurement arrived."""
    with (
        patch(
            f"{FLOW}.async_discovered_devices",
            return_value={ADDRESS: f"Watts Live ({ADDRESS})"},
        ),
        patch(f"{FLOW}.async_provision", AsyncMock(return_value={"firmware": "2.6.1"})),
        patch(f"{FLOW}.async_read_status", AsyncMock(return_value=status)),
        wait_returns({"base": "no_data"}),
    ):
        result = await start(hass, "provision")
        assert result["step_id"] == "provision"
        return await hass.config_entries.flow.async_configure(
            result["flow_id"], PROVISION_INPUT
        )


@pytest.mark.parametrize("status", [0x00, None])
async def test_provision_connected_or_unknown_offers_add_anyway(
    hass, mqtt_mock, status
):
    result = await provision_without_data(hass, status)
    assert result["type"] is FlowResultType.MENU
    assert result["menu_options"] == ["add_anyway", "provision"]

    result = await choose(hass, result, "add_anyway")
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        "serial": SERIAL,
        "address": ADDRESS,
        "firmware": "2.6.1",
    }


@pytest.mark.parametrize(
    ("status", "error"),
    [
        (0x01, "status_disconnected"),
        (0x10, "status_dns_error"),
        (0x20, "status_tcp_error"),
        (0x30, "status_mqtt_error"),
    ],
)
async def test_provision_status_error(hass, mqtt_mock, status, error):
    result = await provision_without_data(hass, status)
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": error}


async def test_provision_retry_keeps_input(hass, mqtt_mock):
    result = await provision_without_data(hass, 0x00)
    with patch(f"{FLOW}.async_discovered_devices", return_value={ADDRESS: "x"}):
        result = await choose(hass, result, "provision")

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "provision"
    fields = {str(key): key for key in result["data_schema"].schema}
    assert fields["serial"].description["suggested_value"] == SERIAL
    assert fields["host"].description["suggested_value"] == "192.168.1.10"


@pytest.mark.parametrize("language", ["en", "da"])
def test_translations_cover_no_data_step(language):
    strings = json.loads((TRANSLATIONS / f"{language}.json").read_text(encoding="utf-8"))
    step = strings["config"]["step"]["no_data"]
    assert "{serial}" in step["description"]
    assert "{timeout}" in step["description"]
    assert set(step["menu_options"]) == {"add_anyway", "manual", "provision"}
