# No-Admin Quick Start

This demo runs locally and does not install packages, drivers, phone tools, or
drone tools. It does not command real hardware.

## Windows

1. Unzip the project.
2. Double-click `Launch DroneOps Demo.cmd`.
3. Keep the terminal window open.
4. The browser should open to the local demo.

If Python is missing, the launcher opens the Python download page. Install
Python 3.10 or newer and tick `Add python.exe to PATH`, then double-click the
launcher again.

## macOS

1. Unzip the project.
2. Double-click `Launch DroneOps Demo.command`.
3. Keep the Terminal window open.
4. The browser should open to the local demo.

If macOS says the file cannot be opened because it is not executable, open
Terminal in the project folder and run:

```bash
chmod +x "Launch DroneOps Demo.command"
./"Launch DroneOps Demo.command"
```

If Python is missing, the launcher opens the Python download page. Install
Python 3.10 or newer, then run the launcher again.

## Google Maps

The demo works without a Google Maps key by using a built-in fallback map.

For Google Maps, copy `demo_config.env.example` to `demo_config.env` and set:

```text
GOOGLE_MAPS_API_KEY=your-key
```

Then run the launcher again.

## Stop The Demo

Press `Ctrl+C` in the launcher terminal window.
