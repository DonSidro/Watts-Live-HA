# 🔌 Watts Live - Home Assistant Integration

A custom [Home Assistant](https://www.home-assistant.io/) integration for the **Watts Live** energy monitoring device.  
It connects via MQTT and exposes real-time power, voltage, current, and energy metrics as sensors.

---

## 📦 Features

- MQTT-based auto-updating sensors
- Sensor grouping under a device entity
- Supports 3-phase current, voltage, and power
- Optional sensor name prefix
- Energy-compatible (works with Energy Dashboard)
---

## 🛠️ Installation

This integration can be installed using [HACS](https://hacs.xyz/)

1. Open the Home Assistant web interface.
2. Navigate to **Settings** > **Devices & Services** > **Integrations**.
3. Click the 3 dots in the top right corner and select **Custom repositories**.
4. In the "Add custom repository" dialog:
   - **Repository**: `https://github.com/DonSidro/Watts-Live-HA`
   - **Category**: Select **Integration**
   - Click **ADD**
5. Close the custom repositories dialog.
6. Click the "+" button in the bottom right corner to add a new integration.
7. Search for **Watts Live** and select it from the list.
8. Follow the prompts to complete the setup:
   - Enter the **serial number** of your Watts Live device.
   - The integration will wait for live MQTT data before completing.
9. Restart Home Assistant to apply the changes.

> **Note**: If you encounter any issues, please ensure that HACS is properly installed and MQTT is configured in your Home Assistant instance.

---

## ⚙️ Configuration via UI

1. Navigate to:  
   **Settings → Devices & Services → Integrations → Add Integration**

2. Search for `Watts Live`.

3. Enter:
   - **Serial Number**: The unique serial number of your Watts device
     
4. The system will wait up to **10 seconds** for the first MQTT message to validate the device is online.

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

## 📊 Sensor Examples

Once connected, the following sensors will appear:

- `watts_live_positive_active_power` → Unit: W
- `watts_live_positive_active_energy` → Unit: kWh
- `watts_live_voltage_l1` → Unit: V
- `watts_live_current_l3` → Unit: A
- `watts_live_frequency` → Unit: Hz

---

## 🔧 Troubleshooting

- **“No data received” error during setup**  
  Ensure your device is online and publishing MQTT data. Try subscribing manually:

  ```bash
  mosquitto_sub -t 'watts/123456/measurement' -v
  ```

- **Sensors not showing units**  
  Ensure you're using the latest version of this integration and have restarted HA after installation.

- **Changes not taking effect**  
  Remove the integration via UI and re-add it. Some sensor metadata is cached by HA.

---

## 🙌 Contributing

Feel free to open issues or submit pull requests!

---
