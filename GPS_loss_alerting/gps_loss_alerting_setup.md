# Setup

1. Install dependencies for diff_starlink_gps.py
2. Run diff_starlink_gps.py to test it. Observe the delta-distance between
the location provided by Starlink and that provided by GPS
3. Get a key for a gmail account that the system should send alerts to. (Describe
how to do that)
4. Run send_gps_status_email.py and generate an alert. Check that you receive
the alert by email
5. Configure diff_starlink_gps.py and send_gps_status_email.py to run as
services
6. Wait for an email saying GPS is wrong. Check logs to confirm. Switch
to alternate navigation. Sail on happily. :-)