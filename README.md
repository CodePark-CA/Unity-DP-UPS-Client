# Unity DP Python Library

Python library for communicating with Unity DP UPS management cards (IS-UNITY-DP).

## Compatibility

This library provides communication with Unity DP cards installed in compatible UPS units.

**Tested with:**
- Card Model: IS-UNITY-DP
- Card Firmware: 8.4.3.1
- UPS Model: GXT3-1500RT120
- UPS Firmware: U027D024

## Installation

### From GitLab
```bash
pip install git+https://gitlab.com/codepark-ca/unity-dp-ups-client
```

### From source
```bash
git clone https://gitlab.com/codepark-ca/unity-dp-ups-client
cd python-unity-dp
pip install .
```

## Quick Start
```python
from unity_dp import UPSLibrary

# Connect to your UPS Unity DP card
ups = UPSLibrary("http://192.168.1.100", "admin", "password")

# Read status
print(f"Battery Charge: {ups.battery.charge}%")
print(f"Load: {ups.output.load_percent}%")
print(f"Input Voltage: {ups.input.voltage_ln}V")

# Get all status at once
status = ups.get_all_status()

# Control the UPS
ups.battery_test()
ups.silence_alarm()
```

## Disclaimer

This is an unofficial third-party library for communicating with Unity DP cards.
It is not affiliated with or endorsed by any UPS manufacturer.

## License

MIT