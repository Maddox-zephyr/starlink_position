# Starlink_fix overview

These pages describe various ways to use Starlink for obtaining a position fix in GPS-denied environments. The page and programs are oriented toward cruising
sailboats.

# Background
Audrey's writeup

# The GitHub repo
The capabilities described below are supported by various software and documentation
which is stored on Github at https://github.com/Maddox-zephyr/starlink_fix.That
repo also has tabs for various purposes:

- A wiki tab. The wiki is open and can be read and updated by anyone with a GitHub
account, and is intended for documenting user-findings that are not in the
documentation.
- An issues tab, used for reporting bugs
- A discussion tab, used for asking questions, making suggestions, etc

## Capabilities

Two main capabilities are described:

1. OpenCPN: Convert Starlink location data to NMEA messages and pipe them into OpenCPN. Use OpenCPN for navigation based on Starlink location. This should bypass
GPS, and should help if GPS is unavailable or spoofed.
2. Alerting: Detect when Starlink location differs from the GPS location, or when
Starlink or GPS location becomes unavailable (data timeout). Send an email alert.
This should help warn a cruiser that they need to switch to alternate location
source, such as using option 1.
3. Future: PredictWind is said to be working on a plugin that takes Starlink
position data and emits it as a NMEA data source intended to feed a RayMarine
chart plotter. Bruce (Wild Orchid) is lead on testing this if/when it becomes available.

All these capabilities rely on the Starlink antenna making its position data available
on the local network. Depending on the flow, other configuration or software
installation may be needed.

# Starlink setup

Follow the instructions at [this page](starlink_setup.html) to configure your
Starlink antenna to make its data available on the local network.

1. Starlink setup
2. Signalk setup
3. diff_starlink_gps setup
4. send_gps_status_email setup
5. system operation
6. FAQ

Give the