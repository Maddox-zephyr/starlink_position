# GPS Loss Alerting Setup

GPS Loss Alerting is done by two python programs:

1. diff_starlink_gps.py detects position deviations (spoofing) and loss
of position data (jamming)
2. **Future** send_gps_status_email.py sends error-alerts and returned-to-normal
status emails.

## Signalk configuration

Add the Starlink plugin into Signalk and configure Signalk to pull location
data from Starlink, and to output it.

**TODO: how to do all this**

## diff_starlink_gps.py setup

All the following steps must be done on the computer (Windows or Linux)
that you are going to run the Loss-Alerting software on.

### Prerequisites

- signalk with the Starlink plugin running on a Windows or Linux
server that's on your network
- python installed (a quick google search should help you install it)
- location access on the Starlink antenna has been enabled by
following the steps on [this page](https://maddox-zephyr.github.io/starlink_position/starlink_setup.html)

### Download the zip file of this repo

- Send your browser to the [URL to download the repo zip file](https://github.com/Maddox-zephyr/starlink_position/releases)
- Under the most recent release, expand the Assets dropdown arrow.
- Click on the source code .zip file to
download the zip file to your computer
- Optionally move the file to any place you want on your computer
- Unzip the file. It will create a folder with a name like starlink_position-0.1

### Install dependencies

- Open up a shell or command window and cd into the GPS_loss_alerting
subdirectory and install dependencies. For example:
```
cd starlink_position-0.1
cd GPS_loss_alerting
```
- Install the dependencies by running the following command:
```
python -m pip install -r requirements.txt
```

### Run diff_starlink_gps.py

In a command window or shell, run:
```
python diff_starlink_gps.py
```
It should display something like:
```
diff_starlink_gps.py 
Starlink Position: 4° 7.294' , 73° 27.882'  GPS delta: 0.0 miles
Starlink Position: 4° 7.294' , 73° 27.882'  GPS delta: 0.0 miles
Starlink Position: 4° 7.294' , 73° 27.882'  GPS delta: 0.0 miles
Starlink Position: 4° 7.294' , 73° 27.882'  GPS delta: 0.0 miles
Starlink Position: 4° 7.294' , 73° 27.882'  GPS delta: 0.0 miles
```
Observe the delta-distance between
the location provided by Starlink and that provided by GPS.
In a normal environment, the GPS delta should be 0.0 miles.

# Future
3. Get a key for a gmail account that the system should send alerts to. (Describe
how to do that)
4. Run send_gps_status_email.py and generate an alert. Check that you receive
the alert by email
5. Configure diff_starlink_gps.py and send_gps_status_email.py to run as
services
6. Wait for an email saying GPS is wrong. Check logs to confirm. Switch
to alternate navigation. Sail on happily with good position. :-)
