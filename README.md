# homeassistant-fanshim
## Home Assistant integration for the Pimoroni Fan SHIM.
This custom component allows you to control the Fan SHIM directly from Home Assistant, providing an easy way to manage your cooling needs.

## Features
- Turn the Fan SHIM on and off
- Adjust the fan speed
- Monitor the fan status
- Integrate with Home Assistant automations and scripts
- Easy setup and configuration
- Supports multiple Fan SHIM devices
- Provides a user-friendly interface for controlling the fan
- Compatible with various Home Assistant versions
- Regular updates and improvements
- Open-source and community-driven development
- Detailed documentation and support
- Customizable settings and options

## Troubleshooting and GPIO Backend Setup

If the Fan SHIM controller cannot control the fan (for example: "GPIO setup error (periphery): [Errno 30] Exporting GPIO: Read-only file system" or "No usable GPIO backend available"), follow these steps:

1. **Verify device nodes are available on the host**
   - SSH into the host or use the Supervisor Terminal and run:
     - `ls -l /dev/gpiomem /dev/gpiochip0`
   - If neither exists, ensure your hardware supports GPIO and the host kernel exposes GPIO devices.

2. **Ensure the add-on exposes the GPIO devices**
   - Confirm `config.json` of the add-on includes the `devices` section listing `/dev/gpiomem` and `/dev/gpiochip0` (this project includes them by default).
   - When installing the add-on, allow access to these devices (Supervisor UI will normally prompt).

3. **Prefer libgpiod on modern systems**
   - Modern kernels expose character devices under `/dev/gpiochip*`. The recommended backend is `libgpiod` (accesses `/dev/gpiochip0`) instead of sysfs exports, which are often read-only in containerized environments.

4. **Build-time dependencies for the add-on Docker image**
   - The add-on must install the system library and Python binding for `libgpiod`. The Dockerfile should install `libgpiod2` and development headers, and the Python package `gpiod`.
   - After updating the Dockerfile, rebuild the add-on image and reinstall.

5. **Rebuild and reinstall**
   - Rebuild the add-on in the Supervisor or via CLI (or locally with `docker build`) and then restart the add-on.

6. **Logs and verification**
   - Watch add-on logs. Successful backend selection will show `HAS_LIBGPIOD = True` and not fail with sysfs export errors.
   - Verify runtime: `CPU Temp: 39.4°C | Fan is OFF` logs should change state when temperatures cross configured thresholds.

If these steps do not resolve the issue, include the add-on logs and the output of `ls -l /dev/gpiomem /dev/gpiochip0` so the problem can be further diagnosed.