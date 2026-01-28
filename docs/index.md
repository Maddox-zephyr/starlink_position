# Starlink_position overview

These pages describe various ways to use Starlink for obtaining a
position fix in GPS-denied environments. The pages and programs are
oriented toward cruising sailboats.

This site and associated GitHub repo is NOT intended to replace the
WhatsApp group. WhatsApp is a useful discussion forum for general
communication on this topic. Rather, this site is intended to be a
repository for important documentation and software that will not be visible
to those who join the WhatsApp group after some post has been made. It
is a place for anyone to get the relevant info at any time.

# Background

Many new members of the Cruiser Connect community, and especially the
Starlink Datahub GPS positioning discussion have joined and likely missed
some of the earlier messages. This website is intended as a reference
to bring them up to speed.

### PredictWind Datahub

PredictWind is finalizing a plugin release for their Datahub that can read
starlink position information and provide that as a source on a NMEA
2000 network (or SeatalkNG network). This gives us a choice to use that
with our chartplotters in the event we encounter denial of standard GPS
due to jamming or spoofing or any other GPS outage. Bruce (Wild Orchid)
has tested it on a Raymarine Axiom Pro. Rui (Anne Charlotte) has tested
it on an older Raymarine E120 (Wide) Classic, and also with OpenCPN.

### Finn's Starlink -> OpenCPN project

Finn (member of the Starlink datahub positioning discussion WhatsApp
group) has shared a GitHub archive that will allow a computer (laptop,
raspberry pi, etc.) to run a program that extracts the starlink position
and provides it to other Nav programs (OpenCPN for example). This does
not require a PredictWind Datahub, so would be a useful option for
cruisers who do not have a Datahub.

### GPS loss-alerting project

A krafty kiwi krew member on Wild Orchid is working on a program that can
pull starlink and NMEA positions from signalk and compare them and send
an alert when the two gps sources disagree by a significant amount. This
alert could trigger you to switch from your standard chartplotter gps
source to either a datahub with starlink or OpenCPN. This program requires
a computer that runs signalk and has access to your NMEA network.

# Capabilities

Three main capabilities are described in these pages:

1. **Starlink->PredictWind Datahub->Raymarine chartplotter or OpenCPN:** 
Convert Starlink location data to NMEA messages and pipe them into
a Raymarine chartplotter or OpenCPN.
Use the chartplotter or OpenCPN for navigation based on
Starlink location. This should bypass
GPS, and should help if GPS is unavailable or spoofed.

2. **Starlink->OpenCPN:** Convert Starlink location data to NMEA messages
using a python program, and pipe them into OpenCPN.
Use OpenCPN for navigation based on
Starlink location. This should bypass
GPS, and should help if GPS is unavailable or spoofed.

3. **GPS Loss-Alerting:** Detect when Starlink location differs from the
GPS location, or when Starlink or GPS location becomes unavailable (data
timeout). Send an email alert.  This should help warn a cruiser that they
need to switch to alternate location source, such as using option 1. This
is a work in progress - as of now there is a program which compares the
Starlink position to the GPS position and prints the Starlink position
and offset from GPS.

# Starlink setup

All these capabilities rely on the Starlink antenna making its position
data available on the local network. Depending on the flow, other
configuration or software installation may be needed.

Follow the instructions at [this page](starlink_setup.html) to configure your
Starlink antenna to make its data available on the local network.

# Starlink->PredictWind Datahub->Chartplotter or OpenCPN setup

Follow the instructions at [this page](pw_datahub_setup.html) to configure your
Starlink location data to be forwarded via PredictWind's Datahub to your
chartplotter or OpenCPN

# Starlink->OpenCPN setup

Follow the instructions at [this page](opencpn_setup.html) to configure your
Starlink location data to be forwarded to OpenCPN

# GPS Loss-Alerting setup

Follow the instructions at [this page](gps_loss_alerting_setup.html) to configure
your Starlink location to be compared to GPS, and the comparison results printed
and sent to email if they don't match.

# The GitHub repo

The capabilities described above are supported by various software and documentation
which is stored on Github at [Maddox-zephyr/starlink_position](https://github.com/Maddox-zephyr/starlink_position).
That repo also has tabs for various purposes:

- A wiki tab. The wiki is open and can be read and updated by anyone with a GitHub
account, and is intended for documenting user-findings that are not in the
documentation.
- An issues tab, used for reporting bugs
- A discussion tab, used for asking questions, making suggestions, etc

Generally, you can browse the repo, look at the issues list etc without
logging into GitHub. If you wish to create discussions or issues, modify the wiki,
or other activities that modify the repo contents you must be logged into GitHub.
Create an account if you don't have one at https://github.com and log in, and
you'll be more powerful, and be able to contribute to the happiness of your
fellow cruisers.

# Future sections

1. Signalk setup
2. FAQ
