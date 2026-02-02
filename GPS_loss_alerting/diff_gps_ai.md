# Background

This directory contains a file called diff_starlink_gps.py. It currently reads boat position from gps, and from starlink, via a signalk websocket connection.
It compares the two position sources and prints the difference between them,
along with the current Starlink position.

# High-level objectives

I want to add an alerting capability, which will write a log entry
when starlink and gps positions differ by more than 0.1 mile, and also
when they were different and become the same within 0.1 miles tolerance.

I also want log entries if no updates have been received from starlink or
from gps for 1 minute.

Logs are to be printed to the screen, and also appended to a logfile called
$HOME/logs/starlink_gps_logs.txt. If the directory $HOME/logs doesn't exist, it should
be created. Alerts are to be appended to an alert file called $HOME/logs/starlink_gps_alerts.txt.

I intend another program, to be developed later, to read alert_logs.txt
and send the contents as WhatsApp messages.

This program should run on Windows and Linux.

I also want a test capability added, where the various alerting conditions
are generated if the program is started with a -t option.

Add comments to the code as needed to explain it.

# Low-level objectives

Follow these steps in order.

## GPS / Starlink difference detection

1. On startup, open the logfile and alert file for appending.
2. Each time a new Starlink location is received, the current code compares the
Starlink location to the GPS location. Write the current printed output
to the logfile.
3. Add a flag called starlink_gps_big_diff.
When true, the flag means the difference between Starlink and GPS location is
greater than 0.1 nautical miles. Initialize it to false
4.  When a new Starlink location is received, compare it to GPS and determine
if the flag state needs to change. If so, print a log to the log file and the alert file.
Change the flag state as appropriate.

## Lost data detection

1. If either starlink or GPS doesn't report a new location for 1 minute, print a log to the log file
and to the alert file. Print again if the source which stopped reporting starts receiving locations again

## Test capability

1. Detect if the program is started with the -t flag. If so, enable logic which can modify
the GPS position, or suppress GPS or starlink data from reaching the detection logic.

### Test GPS offset from Starlink

GPS measurements are received at approximately 14 Hz. Testing for Starlink-GPS difference is
to be done by adding to latitude an offset that increases with each new GPS measurement.
It should take about two minutes for latitude to become offset by
1/600th of a degree above the actual received latitude.
(This is approximately 0.1 nautical mile at the equator). The offset should continue to
be added until the offset is about 2/600 degrees, then the offset should ramp down
at the same rate until it is about -2/600 degrees, then ramp back up to zero.
Then the same should be done for longitude.

I expect to see an alert for 0.1 nautical miles offset caused by GPS latitude high after two minutes, then
a return to normal after another 4 minutes, then an alert caused by GPS latitude low
after another 4 minutes then a return to normal alert after another 4 minutes.

The test should start with the current starlink and gps positions. It should add an
offset to GPS latitude then longitude as specified above. It should print to the log
when it starts adding or subtracting from the offset for both latitude and longitude.

The test itself is not required to verify that an alert was sent at appropriate
times - this will be done manually by checking alerts are issued.

### Test data loss

After completing the test for GPS offset from Starlink, the test should suppress GPS data
for 2 minutes, then restore it for 2 minutes, then suppress Starlink location for 2
minutes, then restore it.

The test should print a log when it is complete, and resume normal operation (no more
testing).