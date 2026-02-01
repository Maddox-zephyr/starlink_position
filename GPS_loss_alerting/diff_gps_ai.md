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
$HOME/logs/alert_logs.txt.

I intend another program, to be developed later, to read alert_logs.txt
and send email alerts.

This program should run on Windows and Linux.

I also want a test capability added, where the various alerting conditions
are generated if the program is started with a -t option.

Add comments to the code as needed to explain it.

# Low-level objectives
