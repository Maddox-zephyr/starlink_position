Make sure you have python installed (a quick google search should help) and allow local location access in Starlink. 
You can enable location access by clicking the two bars at the top left corner in the app, then the info mark on the bottom right. You should be able to find the Debug data section and enable it from there. You can check if it works by typing 192.168.100.1 into the url bar in any browser. It should display the Debug data and amongst it the Location. 



	Download the folder to any place you want and unzip it.
		Open PowerShell you can search for PowerShell on your computer it should be pre installed..

		Navigate into the starlink-grpc-tools-main folder:
			enter the path to the folder into powershell
			PowerShell:
			cd C:\Users\...\starlink-grpc-tools-main

		Install the dependencies:

			PowerShell:
			py -m pip install -r requirements.txt

	
	Open the most up to date Starlink_data_to_NMEA.py file
	Look for idle(python) on your pc, open it and in IDLE go to File>open and find the latest Starlink_data_to_NMEA.py version.
		check that all settings match your needs:
			Specifically check that your UDP_IP is on the right IP Submask meaning that your first three numbers are correct. You can find your ip submask in your starlinks settings. the last number should always be 255. Once completet it should look something like this 192.168.1.255


	Run the Starlink_data_to_NMEA.py file in IDLE.
		It should tell you that it sends positions

	Setup OPENCPN

		Go to settings>Connect>Add New Connection
		
		select Network
		Network Protocol: UDP
		Data Protocol: NMEA 0183
		Ip Address: 0.0.0.0
		DataPort: 30330
		Save changes

	Setup Navionics:
		1. Tap Menu
		2. Select Paired Devices
		3. Add device manually
		4. Select UDP at the Bottom
		5. host: 0.0.0.0
		6. Port Number: 30330
		

OpenCPN and navionics should now get the Starlink Locations and place your boat there.

This script sets the SOG to 0 if SOG is below 0.3 knots. this is to ensure that you dont Always have a speed and heading displayed while at anchor due to an inacurate position. you can change this in the Code.