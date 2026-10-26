# 🔌 Watts Live - Home Assistant Integration

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)
[![hacs][hacsbadge]][hacs]
![Project Maintenance][maintenance-shield]

<a href="https://buymeacoffee.com/sidon" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 40px !important;width: 145px !important;" ></a>

A custom [Home Assistant](https://www.home-assistant.io/) integration for the **Watts Live** energy monitoring device.  
It connects via MQTT and exposes real-time power, voltage, current, and energy metrics as sensors.

---

## 📦 Features

- Set up a new device over Bluetooth: the integration sends it your MQTT broker settings, so you don't need the Watts app for that
- Or add a device that is already sending data to your broker, by serial number
- MQTT-based auto-updating sensors, grouped under one device per Watts Live
- Supports 3-phase current, voltage, and power, for both consumption and returned energy
- Energy-compatible (works with Energy Dashboard)
- Shows the device's firmware version when it was set up over Bluetooth
---

## ⚠️ Prerequisites

- **MQTT** set up in Home Assistant, with a broker the Watts Live device can reach over your network (for example the Mosquitto broker add-on).
- To set up a device over Bluetooth: a Bluetooth adapter on Home Assistant, or an [ESPHome Bluetooth proxy](https://esphome.io/components/bluetooth_proxy.html), within range of the device. The device must already be connected to your Wi-Fi with the Watts On app, since the integration only sends it the MQTT settings.

If you configure the device yourself (with the Watts app) instead, make sure that:
- MQTT is enabled in your Watts Live module settings.
- The broker address, topic, and credentials (if applicable) are configured correctly.

### 🎥 Video Guide

Need help setting it up? Watch the step-by-step video tutorial here:  
[📺 How to Configure Watts Live for MQTT](https://www.youtube.com/watch?v=7gwUCLs2p1w)  

---

## 🛠️ Installation

This integration can be installed using [HACS](https://hacs.xyz/)

1. Open the Home Assistant web interface.
2. Open **HACS**, click the 3 dots in the top right corner and select **Custom repositories**.
3. In the "Add custom repository" dialog:
   - **Repository**: `https://github.com/DonSidro/Watts-Live-HA`
   - **Category**: Select **Integration**
   - Click **ADD**
4. Close the custom repositories dialog, search for **Watts Live** in HACS and download it.
5. Restart Home Assistant.
6. Add the integration as described below.

> **Note**: If you encounter any issues, please ensure that HACS is properly installed and MQTT is configured in your Home Assistant instance.

---

## ⚙️ Configuration via UI

Go to **Settings → Devices & Services → Add Integration** and search for `Watts Live`. You can then choose how to add your device.

### Set up a new device over Bluetooth

The device only has Bluetooth on for **30 minutes after it starts** (and again whenever it loses Wi-Fi). If it has been running longer, restart it first by pulling it out of the meter until it stops blinking, then plug it back in.

Home Assistant may also find the device by itself and show it under **Discovered**.

1. Pick your device from the list.
2. Enter its **serial number**. This is the number used in the MQTT topic, `watts/<serial_number>/measurement`.
3. Check the **MQTT broker** settings. They are filled in from Home Assistant's own MQTT setup. The address must be reachable from the device, so use Home Assistant's IP address, not `localhost` or `core-mosquitto`.
4. Optionally set the **sampling interval**: how often the device sends a reading, 5 to 3600 seconds. Leave it empty to keep the device's current setting.
5. Submit. The integration writes the settings to the device and waits for its first reading.

The device only loads new MQTT settings when it starts. If no reading arrives, restart it as described above and try again. If the device can tell why it is not connected (it can't resolve the broker address, can't reach it, or the broker refused the login), the setup shows that reason.

### Add a device that is already sending data

1. Enter the device's **serial number**.
2. The integration waits up to **30 seconds** for a reading on `watts/<serial_number>/measurement`.

### No reading within 30 seconds

If the device sends readings less often than every 30 seconds, setup can't see one in time. You can then choose **Add the device anyway**: its sensors fill in when the first reading arrives. Check the serial number first, though. With a wrong serial number, the sensors never get any data.

---

## 📡 MQTT Requirements

Ensure your Watts Live device publishes MQTT messages to this topic format:

```
watts/<serial_number>/measurement
```

With payloads like:

```json
{
  "positive_active_energy": 1198712,
  "positive_active_power": 3104,
  "voltage_l1": 380,
  "current_l3": 5.42
}
```

---

## 📊 Sensors

Once connected, the following sensors appear on the device, with entity IDs like `sensor.watts_live_power` and `sensor.watts_live_energy_consumption`:

| Sensor | Payload field | Unit |
| --- | --- | --- |
| Energy consumption | `positive_active_energy` | Wh |
| Power | `positive_active_power` | W |
| L1 / L2 / L3 power | `positive_active_power_l1` … `_l3` | W |
| Returned energy | `negative_active_energy` | Wh |
| Returned power | `negative_active_power` | W |
| L1 / L2 / L3 returned power | `negative_active_power_l1` … `_l3` | W |
| L1 / L2 / L3 voltage | `voltage_l1` … `_l3` | V |
| L1 / L2 / L3 current | `current_l1` … `_l3` | A |

---

## ⬆️ Upgrading from 1.0.x

- **Energy consumption is now in Wh.** The device has always sent Wh, but earlier versions labelled the value kWh, so it showed 1000 times too high. Your Energy dashboard may show a one-time jump where the unit changes. If you worked around this by overriding the unit yourself, remove that override.
- Sensors now belong to their own device, so you can add more than one Watts Live. Existing sensors are moved over automatically and keep their entity IDs.

---

## 🔧 Troubleshooting

- **No reading arrives during setup**  
  Ensure your device is online and publishing MQTT data. Try subscribing manually, with your own serial number:

  ```bash
  mosquitto_sub -t 'watts/123456/measurement' -v
  ```

- **The device isn't listed for Bluetooth setup**  
  Bluetooth turns off 30 minutes after the device starts. Restart it by pulling it out of the meter until it stops blinking, and make sure it is in range of Home Assistant's Bluetooth adapter or a Bluetooth proxy.

- **"The device could not resolve the broker address"**  
  Use the broker's IP address instead of a hostname.

- **Sensors not showing units**  
  Ensure you're using the latest version of this integration and have restarted HA after installation.

- **Changes not taking effect**  
  Remove the integration via UI and re-add it. Some sensor metadata is cached by HA.

---

## 🙌 Contributing

Feel free to open issues or submit pull requests!

To run the tests (Home Assistant needs Linux or macOS):

```bash
pip install -r requirements_test.txt
pytest
```

---


[commits-shield]: https://img.shields.io/github/commit-activity/y/DonSidro/Watts-Live-HA.svg?style=flat-square
[commits]: https://github.com/DonSidro/Watts-Live-HA/commits/main
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=flat-square
[license-shield]: https://img.shields.io/github/license/DonSidro/Watts-Live-HA.svg?style=flat-square
[maintenance-shield]: https://img.shields.io/badge/maintainer-%40DonSidro-blue.svg?style=flat-square
[releases-shield]: https://img.shields.io/github/release/DonSidro/Watts-Live-HA.svg?include_prereleases&style=flat-square&style=flat-square
[releases]: https://github.com/DonSidro/Watts-Live-HA/releases
