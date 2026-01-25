# Starlink->OpenCPN setup

Using OpenCPN with Starlink involves setting up a bridge
that forwards Starlink's location data to OpenCPN.
Here is a step by step guide for configuring the Starlink->OpenCPN
bridge.

All the following steps must be done on the computer (Windows or Linux)
that you are going to run the OpenCPN-Starlink software on.

## Prerequisites

Make sure you have python installed (a quick google search should help)
and allow local location access in Starlink. 

Make sure you have enabled location access on the Starlink antenna by
following the steps on [this page](https://maddox-zephyr.github.io/starlink_fix/starlink_setup.html)

## Get the OpenCPN-Starlink zip file

- Send your browser to the [URL to download the OpenCPN-Starlink zip file](https://github.com/Maddox-zephyr/starlink_fix/blob/main/OpenCPN/Starlink_data_to_NMEA.zip)
- Click the three dots to the right of the file name and select **Download** to
download the zip file to your computer
- Move the folder to any place you want and unzip it.

## Configure the Starlink->OpenCPN bridge software

- Open PowerShell. (You can search for PowerShell on your
computer - it should be pre-installed.)
- **cd** into the starlink-grpc-tools-main folder that is inside
the Starlink_data_to_NMEA folder by entering the path
to the folder into powershell like so:
```
cd C:\Users\...Starlink_data_to_NMEA\starlink-grpc-tools-main
```
- Install the dependencies by entering the following command into Powershell:
```
py -m pip install -r requirements.txt
```
- Open the Starlink_data_to_NMEA.py file using any editor (e.g. Notepad, IDLE, etc)
- Check that all settings match your needs. Specifically check that your UDP_IP
is on the right IP Submask. Your first three numbers are correct.
You can find your ip submask in your starlinks settings.
The last number should always be 255.
Once complete it should look something like 192.168.1.255

## Run the Starlink->OpenCPN bridge

- **FIXME** Run the Starlink_data_to_NMEA.py file.
You can do this if you opened it
in IDLE. It should tell you that it sends positions

# Setup OPENCPN

- In OpenCPN, go to settings>Connect>Add New Connection
- Configure the new connection as follows:		
    - select Network
    - Network Protocol: UDP
    - Data Protocol: NMEA 0183
    - Ip Address: 0.0.0.0
    - DataPort: 30330
- Save your changes

# Setup Navionics:

1. Tap Menu
2. Select Paired Devices
3. Add device manually
4. Select UDP at the Bottom
5. host: 0.0.0.0
6. Port Number: 30330

# Run the system

OpenCPN and navionics should now get the Starlink Locations and place
your boat there.
 
This script sets the SOG to 0 if SOG is below 0.3
knots. This is to ensure that you dont have a speed and heading
displayed while at anchor. You can change this in the code.