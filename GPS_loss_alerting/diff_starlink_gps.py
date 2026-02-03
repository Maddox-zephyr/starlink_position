#!/usr/bin/python3

import asyncio
import websockets
import json
import dict_digger
from math import radians, cos, sin, asin, sqrt
import time
import os
import sys
import argparse
import logging
from pathlib import Path

# --- Constants ---
# Distance threshold for alerts, in nautical miles
DISTANCE_THRESHOLD_NM = 0.1
# Time threshold for data loss, in seconds
DATA_LOSS_TIMEOUT_S = 60.0
# Websocket URI for Signal K server
SIGNALK_URI = "ws://192.168.1.116:80/signalk/v1/stream?subscribe=none"

def setup_logging():
    """Configures logging to screen and files."""
    log_dir = Path.home() / "logs"
    try:
        log_dir.mkdir(exist_ok=True)
    except OSError as e:
        print(f"Error creating log directory {log_dir}: {e}")
        sys.exit(1)

    log_file = log_dir / "starlink_gps_logs.txt"
    alert_file = log_dir / "starlink_gps_alerts.txt"

    # Get the root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # General log handler (console and file)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Specific alert handler
    alert_logger = logging.getLogger('alerter')
    alert_logger.setLevel(logging.INFO)
    alert_formatter = logging.Formatter('%(asctime)s - %(message)s')

    alert_file_handler = logging.FileHandler(alert_file)
    alert_file_handler.setFormatter(alert_formatter)
    alert_logger.addHandler(alert_file_handler)
    # Also log alerts to the main log
    alert_logger.addHandler(file_handler)
    alert_logger.addHandler(stream_handler)
    # Prevent alert logs from propagating to the root logger's handlers
    alert_logger.propagate = False

    return logger, alert_logger


def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance in nautical miles between two points
    on the earth (specified in decimal degrees).
    """
    # Earth radius in nautical miles
    R = 3440.065
    dLat = radians(lat2 - lat1)
    dLon = radians(lon2 - lon1)
    lat1 = radians(lat1)
    lat2 = radians(lat2)
    a = sin(dLat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dLon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return R * c

def dd_to_dm(deg):
    """Convert decimal degrees to degrees and decimal minutes."""
    d = int(deg)
    m = abs(deg - d) * 60
    return d, m

class GpsAlerter:
    """
    Monitors GPS and Starlink position data, logs it, and generates alerts
    for position discrepancies or data loss.
    """
    def __init__(self, test_mode=False):
        self.test_mode = test_mode
        self.logger, self.alert_logger = setup_logging()

        # Position data
        self.gps_lat = None
        self.gps_lon = None
        self.starlink_lat = None
        self.starlink_lon = None

        # Timestamps for data loss detection
        self.last_gps_update_time = None
        self.last_starlink_update_time = None

        # State flags
        self.starlink_gps_big_diff = False
        self.gps_data_lost = False
        self.starlink_data_lost = False

        # Test mode state
        if self.test_mode:
            self.test_state = "IDLE" # e.g., RAMP_LAT_UP, SUPPRESS_GPS
            self.gps_lat_offset = 0.0
            self.gps_lon_offset = 0.0
            # Offset increment to achieve ~1/600 degree change in 2 minutes at 14Hz
            self.offset_increment = (1.0 / 600.0) / (120.0 * 14.0)


        self.logger.info("GpsAlerter initialized.")
        if self.test_mode:
            self.logger.warning("TEST MODE ENABLED.")

    async def run(self):
        """Main entry point. Runs all monitoring tasks."""
        self.logger.info("Starting GPS Alerter...")
        try:
            websocket_task = asyncio.create_task(self._websocket_loop())
            data_loss_task = asyncio.create_task(self._data_loss_checker_loop())

            tasks = [websocket_task, data_loss_task]
            if self.test_mode:
                test_runner_task = asyncio.create_task(self._test_runner_loop())
                tasks.append(test_runner_task)

            await asyncio.gather(*tasks)
        except Exception as e:
            self.logger.error(f"A critical error occurred: {e}", exc_info=True)
        finally:
            self.logger.info("GpsAlerter shut down.")

    async def _websocket_loop(self):
        """The main loop for connecting to the websocket and processing messages."""
        while True:
            try:
                async with websockets.connect(SIGNALK_URI) as websocket:
                    self.logger.info(f"Connected to Signal K websocket at {SIGNALK_URI}")
                    await self._subscribe_to_position(websocket)
                    while True:
                        message = await websocket.recv()
                        self._process_message(message)
            except (websockets.exceptions.ConnectionClosed, ConnectionRefusedError) as e:
                self.logger.warning(f"Websocket connection error: {e}. Reconnecting in 30 seconds...")
                await asyncio.sleep(30)
            except Exception as e:
                self.logger.error(f"An unexpected error occurred in the websocket loop: {e}", exc_info=True)
                self.logger.warning("Attempting to reconnect in 30 seconds...")
                await asyncio.sleep(30)

    async def _subscribe_to_position(self, websocket):
        """Sends the subscription message to the Signal K server."""
        msg = {
            "context": "vessels.self",
            "subscribe": [{"path": "navigation.position", "policy": "instant"}]
        }
        await websocket.send(json.dumps(msg))
        self.logger.info("Subscribed to navigation.position updates.")

    def _process_message(self, message):
        """Parses a JSON message from the websocket."""
        try:
            data = json.loads(message)
            if "updates" not in data:
                return

            for update in data["updates"]:
                # GPS data from NMEA2000
                if dict_digger.dig(update, "source", "type") == "NMEA2000":
                    if self.test_mode and self.test_state == "SUPPRESS_GPS":
                        continue # Skip processing this update
                    
                    lat = dict_digger.dig(update, "values", 0, "value", "latitude")
                    lon = dict_digger.dig(update, "values", 0, "value", "longitude")

                    if lat is not None and lon is not None:
                        if self.test_mode:
                            # Apply offsets during test mode
                            if self.test_state == "RAMP_LAT_UP":
                                self.gps_lat_offset += self.offset_increment
                            elif self.test_state == "RAMP_LAT_DOWN":
                                self.gps_lat_offset -= self.offset_increment
                            elif self.test_state == "RAMP_LON_UP":
                                self.gps_lon_offset += self.offset_increment
                            elif self.test_state == "RAMP_LON_DOWN":
                                self.gps_lon_offset -= self.offset_increment
                            lat += self.gps_lat_offset
                            lon += self.gps_lon_offset
                        
                        self._update_gps_position(lat, lon)

                # Starlink data
                elif dict_digger.dig(update, "$source") == "signalk-starlink":
                    if self.test_mode and self.test_state == "SUPPRESS_STARLINK":
                        continue # Skip processing this update

                    lat = dict_digger.dig(update, "values", 0, "value", "latitude")
                    lon = dict_digger.dig(update, "values", 0, "value", "longitude")
                    if lat is not None and lon is not None:
                        self._update_starlink_position(lat, lon)

        except json.JSONDecodeError:
            self.logger.warning(f"Could not decode JSON message: {message}")
        except Exception as e:
            self.logger.error(f"Error processing message: {e}", exc_info=True)

    def _update_gps_position(self, lat, lon):
        """Updates the state with a new GPS position."""
        if self.gps_data_lost:
            self.alert_logger.warning("OK: GPS data stream has resumed.")
            self.gps_data_lost = False

        self.gps_lat = lat
        self.gps_lon = lon
        self.last_gps_update_time = time.monotonic()

    def _update_starlink_position(self, lat, lon):
        """Updates the state with a new Starlink position and triggers checks."""
        if self.starlink_data_lost:
            self.alert_logger.warning("OK: Starlink data stream has resumed.")
            self.starlink_data_lost = False

        self.starlink_lat = lat
        self.starlink_lon = lon
        self.last_starlink_update_time = time.monotonic()
        self._check_position_difference()

    def _check_position_difference(self):
        """Checks for position differences and logs/alerts if the state changes."""
        if not all([self.gps_lat, self.gps_lon, self.starlink_lat, self.starlink_lon]):
            return  # Not enough data to compare

        distance_nm = haversine(self.gps_lat, self.gps_lon, self.starlink_lat, self.starlink_lon)

        slink_lat_deg, slink_lat_min = dd_to_dm(self.starlink_lat)
        slink_lon_deg, slink_lon_min = dd_to_dm(self.starlink_lon)
        lat_hemisphere = 'N' if self.starlink_lat >= 0 else 'S'
        lon_hemisphere = 'W' if self.starlink_lon < 0 else 'E'

        # Log the current status to the main log file
        log_msg = (
            f"Starlink Position: {abs(slink_lat_deg)}° {slink_lat_min:.3f}' {lat_hemisphere}, "
            f"{abs(slink_lon_deg)}° {slink_lon_min:.3f}' {lon_hemisphere}. "
            f"GPS delta: {distance_nm:.3f} NM"
        )
        self.logger.info(log_msg)

        # Check if the difference state has changed
        is_different = distance_nm > DISTANCE_THRESHOLD_NM
        if is_different != self.starlink_gps_big_diff:
            self.starlink_gps_big_diff = is_different
            if is_different:
                alert_msg = (
                    f"ALERT: GPS/Starlink position difference exceeds {DISTANCE_THRESHOLD_NM} NM. "
                    f"Current difference is {distance_nm:.3f} NM."
                )
                self.alert_logger.warning(alert_msg)
            else:
                alert_msg = (
                    f"OK: GPS/Starlink position difference is back within "
                    f"{DISTANCE_THRESHOLD_NM} NM tolerance. Current difference is {distance_nm:.3f} NM."
                )
                self.alert_logger.warning(alert_msg)

    async def _data_loss_checker_loop(self):
        """Periodically checks if data sources have timed out."""
        # Wait a moment for the first messages to arrive
        await asyncio.sleep(DATA_LOSS_TIMEOUT_S)

        while True:
            now = time.monotonic()

            # Check for GPS data loss
            if self.last_gps_update_time:
                if now - self.last_gps_update_time > DATA_LOSS_TIMEOUT_S and not self.gps_data_lost:
                    self.gps_data_lost = True
                    self.alert_logger.warning("ALERT: No GPS data received for 1 minute.")
            else: # No data ever received
                if not self.gps_data_lost:
                    self.gps_data_lost = True
                    self.alert_logger.warning("ALERT: No GPS data ever received after startup period.")


            # Check for Starlink data loss
            if self.last_starlink_update_time:
                if now - self.last_starlink_update_time > DATA_LOSS_TIMEOUT_S and not self.starlink_data_lost:
                    self.starlink_data_lost = True
                    self.alert_logger.warning("ALERT: No Starlink data received for 1 minute.")
            else: # No data ever received
                if not self.starlink_data_lost:
                    self.starlink_data_lost = True
                    self.alert_logger.warning("ALERT: No Starlink data ever received after startup period.")


            await asyncio.sleep(10) # Check every 10 seconds

    async def _test_runner_loop(self):
        """Runs a sequence of test scenarios to trigger alerts."""
        # Wait for the system to receive initial data from both sources
        self.logger.info("Test runner waiting for initial GPS and Starlink data...")
        while not all([self.gps_lat, self.starlink_lat]):
            await asyncio.sleep(1)
        self.logger.info("Test runner detected initial data. Starting test sequence in 5 seconds.")
        await asyncio.sleep(5)

        # --- GPS Offset Test ---
        self.logger.warning("STARTING GPS OFFSET TEST")

        # Ramp latitude up from 0 to +2/600 deg (4 mins total)
        self.logger.info("Test: Ramping latitude offset up to +2/600 deg over 4 mins...")
        self.test_state = "RAMP_LAT_UP"
        await asyncio.sleep(240) # 4 minutes

        # Ramp latitude down from +2/600 to -2/600 deg (8 mins total)
        self.logger.info("Test: Ramping latitude offset down to -2/600 deg over 8 mins...")
        self.test_state = "RAMP_LAT_DOWN"
        await asyncio.sleep(480) # 8 minutes

        # Ramp latitude up from -2/600 to 0 deg (4 mins total)
        self.logger.info("Test: Ramping latitude offset up to 0 deg over 4 mins...")
        self.test_state = "RAMP_LAT_UP"
        await asyncio.sleep(240) # 4 minutes
        self.gps_lat_offset = 0.0 # Reset to exactly zero

        self.logger.info("Test: Latitude offset test complete.")
        await asyncio.sleep(2)

        # Ramp longitude up from 0 to +2/600 deg (4 mins total)
        self.logger.info("Test: Ramping longitude offset up to +2/600 deg over 4 mins...")
        self.test_state = "RAMP_LON_UP"
        await asyncio.sleep(240) # 4 minutes

        # Ramp longitude down from +2/600 to -2/600 deg (8 mins total)
        self.logger.info("Test: Ramping longitude offset down to -2/600 deg over 8 mins...")
        self.test_state = "RAMP_LON_DOWN"
        await asyncio.sleep(480) # 8 minutes

        # Ramp longitude up from -2/600 to 0 deg (4 mins total)
        self.logger.info("Test: Ramping longitude offset up to 0 deg over 4 mins...")
        self.test_state = "RAMP_LON_UP"
        await asyncio.sleep(240) # 4 minutes
        self.gps_lon_offset = 0.0 # Reset to exactly zero

        self.logger.warning("GPS OFFSET TEST COMPLETE.")
        await asyncio.sleep(5)

        # --- Data Loss Test ---
        self.logger.warning("STARTING DATA LOSS TEST")

        # Suppress GPS for 2 minutes
        self.logger.info("Test: Suppressing GPS data for 2 minutes...")
        self.test_state = "SUPPRESS_GPS"
        await asyncio.sleep(120)

        # Restore GPS for 2 minutes
        self.logger.info("Test: Restoring GPS data for 2 minutes...")
        self.test_state = "IDLE"
        await asyncio.sleep(120)

        # Suppress Starlink for 2 minutes
        self.logger.info("Test: Suppressing Starlink data for 2 minutes...")
        self.test_state = "SUPPRESS_STARLINK"
        await asyncio.sleep(120)

        # Restore Starlink
        self.logger.info("Test: Restoring Starlink data...")
        self.test_state = "IDLE"

        self.logger.warning("TEST SEQUENCE COMPLETE. Resuming normal operation.")



async def main():
    """Main function to run the alerter."""
    parser = argparse.ArgumentParser(description="Monitor Starlink and GPS position data.")
    parser.add_argument("-t", "--test", action="store_true",
                        help="Enable test mode to generate alert conditions.")
    args = parser.parse_args()

    alerter = GpsAlerter(test_mode=args.test)
    await alerter.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProgram interrupted by user. Exiting.")