import sys
from unittest.mock import patch

# Import the repo's package first, otherwise the test plugin's own
# testing_config/custom_components shadows it and the integration isn't found.
import custom_components  # noqa: F401
import pytest

if sys.platform == "win32":
    import pytest_socket

    # The Windows event loop needs a local socket pair, which the plugin blocks.
    pytest_socket.disable_socket = lambda *args, **kwargs: None


@pytest.fixture(autouse=True)
def _setup(enable_custom_integrations, mock_network):
    # The Bluetooth and USB stacks need real hardware, and the flow tests
    # should not set up the sensor platform.
    with (
        patch("homeassistant.components.bluetooth.async_setup", return_value=True),
        patch("homeassistant.components.usb.async_setup", return_value=True),
        patch("custom_components.watts_live.async_setup_entry", return_value=True),
    ):
        yield


@pytest.fixture
def expected_lingering_timers():
    # The mocked MQTT client leaves a periodic timer behind.
    return True
