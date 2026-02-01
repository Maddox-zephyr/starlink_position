# GPS Loss Alerting Setup

GPS Loss Alerting is done by two python programs:

1. diff_starlink_gps.py detects position deviations (spoofing) and loss
of position data (jamming)
2. **Future** send_gps_status_email.py sends error-alerts and returned-to-normal
status emails.

## Signalk configuration

Note: signalk standard/default convention is to have 192.168.1.xxx:3000 as the path to 
control/view signalk. Port 3000 was already taken on my server with a grafana page, so I changed 
the default to port 80 for my signalk.

To add the signalk-starlink plugin to your signalk, login to signalk (top right hand three 
horizontal lines) [view login image](images/Signalk_login.png), then click on Appstore, then 
Available [view_applications](images/signalk_available.png).  You will find the plugin here.

Next step is to configure the signalk-starlink plugin by going to Server, then Plugin Config, and 
look for Starlink. You will want to enable it, then check the option for "Use Starlink as a GPS
source (requires enabling access on local network)." 

Restart signalk, and then using the Data Browser for siganlk, look for the path 
navigation.position.  You probably have multiple of these, but one should have 
signalk-starlink in the far right Source column. Note the path for the other "navigation.position" 
source that you want to use to compare against stalink position. 

**TODO: how to use these source paths in the program

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
