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

# Purpose

Many new members of the Cruiser Connect community, and especially the
Starlink Datahub GPS positioning discussion have joined and likely missed
some of the earlier messages. This website is intended as a reference
to bring them up to speed.

# Using Starlink position data

Here are the four major approaches to using Starlink location data.

### PredictWind Datahub -> Chartplotter or OpenCPN

PredictWind is finalizing a plugin release for their Datahub that can read
starlink position information and provide that as a source on a NMEA
2000 network (or SeatalkNG network). (The Datahub also publishes NMEA0183
over UDP and TCP on a wifi network.)

The Datahub converts Starlink location data to NMEA messages and you pipe
them into a Raymarine chartplotter or OpenCPN.  Use the chartplotter or
OpenCPN for navigation based on Starlink location. This should bypass GPS,
and should help if GPS is unavailable or spoofed.

Bruce (Wild Orchid) has tested it on a Raymarine Axiom Pro. Rui (Anne
Charlotte) has tested it on an older Raymarine E120 (Wide) Classic,
and also with OpenCPN.

### Starlink -> Signalk -> OpenCPN

The original configuration that spawned all the others.  Using SignalK +
Signalk-Starlink plugin allows you to easily (no programming at all)
broadcast your position to OpenCPN (which already has a connection
specific for SignalK). It's very easy to setup, and usable in an
emergency.  It's easy enough for most (even non-techy users) that
don’t have a DataHub. A downside is the position updates are not very
smooth.  Signalk uses its plugin that reads Starlink location data and
re-publishes it.

### Finn's Starlink -> OpenCPN project

Finn (member of the Starlink datahub positioning discussion WhatsApp
group) has shared a GitHub archive that will allow a computer (laptop,
raspberry pi, etc.) to run a program that extracts the starlink position
and provides it to other Nav programs (OpenCPN for example). This does not
require a PredictWind Datahub or Signalk, so would be a useful option for
cruisers who do not have a Datahub or Signalk. It does require getting
your hands a bit dirty with python configuration.

Finn's python scripts convert Starlink location data to NMEA messages,
and you pipe them into OpenCPN.  You then use OpenCPN for navigation
based on Starlink location. This should bypass GPS, and should help if
GPS is unavailable or spoofed.

### GPS loss-alerting project

A krafty kiwi krew member on Wild Orchid is working on a program that can
pull starlink and NMEA positions from signalk and compare them and send
an alert when the two gps sources disagree by a significant amount. This
alert could trigger you to switch from your standard chartplotter gps
source to an alternate way of getting location data into your
chartplotter or OpenCPN. This program requires
a computer that runs signalk and has access to your NMEA network.

It will also detect when Starlink or GPS location becomes unavailable
(data timeout). It will send an email alert. This should help warn a
cruiser that they need to switch to alternate navigation solution. This project
is a work in progress - as of now there is a program which compares the
Starlink position to the GPS position and prints the Starlink position
and offset from GPS.

# Starlink setup

All these capabilities that use Starlink position data rely 
on the Starlink antenna making its position
data available on the local network. Depending on the capability, other
configuration or software installation may be needed.

Follow the instructions at [this page](starlink_setup.html) to configure your
Starlink antenna to make its data available on the local network.

On the Starlink location data page in the app, it is crucial to also
select the option “Use Starlink Positioning Exclusively”, when
switching to navigate using Starlink position data, otherwise it will
also be (or could be) affected by the GPS jamming

# Starlink->PredictWind Datahub->Chartplotter or OpenCPN setup

Follow the instructions at [this page](pw_datahub_setup.html) to configure your
Starlink location data to be forwarded via PredictWind's Datahub to your
chartplotter or OpenCPN

# Starlink->Signalk->OpenCPN setup

Follow the instructions at [this page](signalk_opencpn_setup.html)
to configure Signalk and OpenCPN to use Starlink data.

# Starlink->Finn's python scripts -> OpenCPN setup

Follow the instructions at [this page](opencpn_setup.html) to configure the
python scripts to forward Starlink location data to OpenCPN

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
