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
DISTANCE_THRESHOLD_NM = 1.0
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

    # Specific alert handler (console and main log only, file opened on-demand)
    alert_logger = logging.getLogger('alerter')
    alert_logger.setLevel(logging.INFO)
    alert_formatter = logging.Formatter('%(asctime)s - %(message)s')

    # Also log alerts to the main log
    alert_logger.addHandler(file_handler)
    alert_logger.addHandler(stream_handler)
    # Prevent alert logs from propagating to the root logger's handlers
    alert_logger.propagate = False

    return logger, alert_logger


class CsvLogHandler(logging.Handler):
    """Logging handler that appends a CSV row for each emitted log record.

    The handler calls a provided callback to get an object with attributes
    `start_time`, `starlink_lat`, `starlink_lon`, `chartplotter_gps_lat`, 
        'chartplotter_gps_lon`.

        src 5 is chart plotter
        src 22 is AIS
        src 178 is DataHub
    """
    def __init__(self, csv_path, get_context):
        super().__init__()
        self.csv_path = Path(csv_path)
        self.get_context = get_context

        # Ensure parent dir exists and create CSV header if missing
        try:
            self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

        if not self.csv_path.exists():
            try:
                with open(self.csv_path, 'a') as f:
                    f.write('date-time,slink_lat_minutes,slink_lon_minutes,chplot_lat_minutes,chplot_lon_minutes,datahub_lat_minutes,datahub_lon_minutes,chplot_datahub_diff_nm,diff_nm,sog\n')
            except Exception:
                pass

    def emit(self, record):
        try:
            from datetime import datetime
            ctx = None
            try:
                ctx = self.get_context()
            except Exception:
                ctx = None

            timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
            def get_minutes(val):
                try:
                    if val is None or val == '':
                        return ''
                    d = int(float(val))
                    m = abs(float(val) - d) * 60
                    return f"{m:.2f}"
                except Exception:
                    return ''

            slat = get_minutes(getattr(ctx, 'starlink_lat', None))
            slon = get_minutes(getattr(ctx, 'starlink_lon', None))
            glat = get_minutes(getattr(ctx, 'gps_chartplotter_lat', None))
            glon = get_minutes(getattr(ctx, 'gps_chartplogger_lon', None))
            dhlat = get_minutes(getattr(ctx, 'datahub_lat', None))
            dhlon = get_minutes(getattr(ctx, 'datahub_lon', None))

            # Try to get the current distance_nm from the context (GpsAlerter)
            diff_nm = ''
            ch_dh_diff = ''
            if ctx is not None:
                try:
                    # If distance_nm is not a property, recompute if possible
                    diff_nm_val = getattr(ctx, 'distance_nm', None)
                    if diff_nm_val is None:
                        # Try to compute if all values present for starlink vs chartplotter
                        if all([getattr(ctx, 'gps_chartplotter_lat', None), getattr(ctx, 'gps_chartplogger_lon', None), getattr(ctx, 'starlink_lat', None), getattr(ctx, 'starlink_lon', None)]):
                            diff_nm_val = haversine(ctx.gps_chartplotter_lat, ctx.gps_chartplogger_lon, ctx.starlink_lat, ctx.starlink_lon)
                    if diff_nm_val is not None:
                        diff_nm = f"{diff_nm_val:.3f}"

                    # Compute chartplotter <-> DataHub difference if possible
                    try:
                        if all([getattr(ctx, 'gps_chartplotter_lat', None), getattr(ctx, 'gps_chartplogger_lon', None), getattr(ctx, 'datahub_lat', None), getattr(ctx, 'datahub_lon', None)]):
                            chdh_val = haversine(ctx.gps_chartplotter_lat, ctx.gps_chartplogger_lon, ctx.datahub_lat, ctx.datahub_lon)
                            ch_dh_diff = f"{chdh_val:.3f}"
                    except Exception:
                        ch_dh_diff = ''
                except Exception:
                    pass

            sog = getattr(ctx, 'sog', '') if ctx is not None else ''
            sog = f"{sog:.1f}" if isinstance(sog, (int, float)) else ''
            line = f"{timestamp},{slat},{slon},{glat},{glon},{dhlat},{dhlon},{ch_dh_diff},{diff_nm},{sog}\n"
            with open(self.csv_path, 'a') as f:
                f.write(line)
        except Exception:
            self.handleError(record)


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

        # Record application start time for CSV logging (seconds since start)
        self.start_time = time.monotonic()

        # CSV log path and handler: append a row for every log entry
        try:
            from datetime import datetime
            today_str = datetime.now().strftime("%Y-%m-%d")
            csv_filename = f"position_log_data_{today_str}.csv"
            csv_path = Path.home() / "logs" / csv_filename
            csv_handler = CsvLogHandler(csv_path, lambda: self)
            # Add the CSV handler to both loggers so any emitted record appends a CSV row
            self.logger.addHandler(csv_handler)
            self.alert_logger.addHandler(csv_handler)
        except Exception as e:
            # Fail gracefully if CSV handler can't be created
            self.logger.error(f"Could not initialize CSV log handler: {e}")

        # Alert file path
        self.alert_file = Path.home() / "logs" / "starlink_gps_alerts.txt"

        # Position data
        self.gps_chartplotter_lat = None
        self.gps_chartplogger_lon = None
        self.datahub_lat = None
        self.datahub_lon = None
        self.starlink_lat = None
        self.starlink_lon = None
        self.max_distance_nm = 0.0
        # Speed Over Ground (SOG)
        self.sog = 0.0

        # Timestamps for data loss detection
        self.last_gps_update_time = None
        self.last_starlink_update_time = None

        # Timestamp for position logging throttle
        self.last_position_log_time = None

        # State flags
        self.starlink_gps_big_diff = False
        self.gps_data_lost = False
        self.starlink_data_lost = False

        # Test mode state
        if self.test_mode:
            self.test_state = "IDLE" # e.g., RAMP_LAT_UP, SUPPRESS_GPS
            self.gps_lat_offset = 0.0
            self.gps_lon_offset = 0.0
            # Offset increment to achieve ~4/600 degree change in 2 minutes at 14Hz
            self.offset_increment = (4.0 / 600.0) / (120.0 * 14.0)


        self.logger.info("GpsAlerter initialized.")
        if self.test_mode:
            self.logger.warning("TEST MODE ENABLED.")

    def _write_alert_to_file(self, message):
        """Writes an alert message to the alert file, opening and closing it immediately."""
        try:
            with open(self.alert_file, 'a') as f:
                from datetime import datetime
                timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
                f.write(f'{timestamp} - {message}\n')
        except Exception as e:
            self.logger.error(f"Error writing to alert file: {e}", exc_info=True)

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
            "subscribe": [{"path": "navigation.position", "policy": "instant"},
                          {"path": "navigation.speedOverGround", "policy": "instant"}]
        }
        await websocket.send(json.dumps(msg))
        self.logger.info("Subscribed to navigation.position updates.")

    def _process_message(self, message):
        """Parses a JSON message from the websocket.
        src 5 is chart plotter
        src 22 is AIS
        src 178 is DataHub
        """
        debug_print = False
        try:
            data = json.loads(message)
            # print(f"Received message: {data}")  # Debug print for incoming messages
            if "updates" not in data:
                return

            for update in data["updates"]:
                # print(f"Received message: {update}")  # Debug print for incoming messages

                # GPS data from NMEA2000
                if dict_digger.dig(update, "source", "type") == "NMEA2000":
                    # Check for PGN 129025 (position) and src 5 (chart plotter)
                    pgn = dict_digger.dig(update, "source", "pgn")
                    src = dict_digger.dig(update, "source", "src")
                    
                    # Handle position data (PGN 129025)
                    if pgn == 129025 and src == '5':
                        values = update.get("values", [])
                        if not values:
                            continue
                        # Check for navigation.position
                        if values[0].get("path") == "navigation.position":
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
                                if (debug_print):
                                    print(f"Received message: {data}")  # Debug print for incoming messages
                                    print("Values:", values)  # Debug print for values in the update
                    
                    # Handle Speed Over Ground (PGN 129026)
                    elif pgn == 129026 and src == '5':
                        values = update.get("values", [])
                        if values and values[0].get("path") == "navigation.speedOverGround":
                            sog = float(values[0].get("value")) * 1.94384 # Convert m/s to knots
                            self._update_sog(sog)
                            if (debug_print):
                                print(f"Received message: {data}")  # Debug print for incoming messages
                                print("SOG updated:", sog)  # Debug print for SOG updates

                    # Handle DataHub position (PGN 129025 from src 178)
                    elif pgn == 129025 and src == '178':
                        values = update.get("values", [])
                        if not values:
                            continue
                        if values[0].get("path") == "navigation.position":
                            lat = dict_digger.dig(update, "values", 0, "value", "latitude")
                            lon = dict_digger.dig(update, "values", 0, "value", "longitude")
                            if lat is not None and lon is not None:
                                self.datahub_lat = lat
                                self.datahub_lon = lon
                                if (debug_print):
                                    print(f"Received message: {data}")
                                    print("DataHub Values:", values)
                # Starlink data
                elif dict_digger.dig(update, "$source") == "signalk-starlink":
                    if self.test_mode and self.test_state == "SUPPRESS_STARLINK":
                        continue # Skip processing this update

                    lat = dict_digger.dig(update, "values", 0, "value", "latitude")
                    lon = dict_digger.dig(update, "values", 0, "value", "longitude")
                    if lat is not None and lon is not None:
                        self._update_starlink_position(lat, lon)
                        if (debug_print):
                            print(f"Received message: {data}")  # Debug print for incoming messages
                            print(f"Starlink position updated: lat={lat}, lon={lon}")  # Debug print for Starlink updates

        except json.JSONDecodeError:
            self.logger.warning(f"Could not decode JSON message: {message}")
        except Exception as e:
            self.logger.error(f"Error processing message: {e}", exc_info=True)

    def _update_sog(self, sog):
        """Updates the state with a new Speed Over Ground value."""
        self.sog = sog

    def _update_gps_position(self, lat, lon):
        """Updates the state with a new GPS position."""
        if self.gps_data_lost:
            msg = "OK: GPS data stream has resumed."
            self.alert_logger.warning(msg)
            self._write_alert_to_file(msg)
            self.gps_data_lost = False

        self.gps_chartplotter_lat = lat
        self.gps_chartplogger_lon = lon
        self.last_gps_update_time = time.monotonic()

    def _update_starlink_position(self, lat, lon):
        """Updates the state with a new Starlink position and triggers checks."""
        if self.starlink_data_lost:
            msg = "OK: Starlink data stream has resumed."
            self.alert_logger.warning(msg)
            self._write_alert_to_file(msg)
            self.starlink_data_lost = False

        self.starlink_lat = lat
        self.starlink_lon = lon
        self.last_starlink_update_time = time.monotonic()
        # Log to CSV every time a Starlink position report comes in
        for handler in self.logger.handlers:
            if hasattr(handler, 'emit') and handler.__class__.__name__ == 'CsvLogHandler':
                import logging
                handler.emit(logging.LogRecord(
                    name=self.logger.name,
                    level=logging.INFO,
                    pathname=__file__,
                    lineno=0,
                    msg='',
                    args=(),
                    exc_info=None
                ))

        # Still only log to text file and check for alerts no more often than every minute
        self._check_position_difference()

    def _check_position_difference(self):
        """Checks for position differences and logs/alerts if the state changes."""
        if not all([self.gps_chartplotter_lat, self.gps_chartplogger_lon, self.starlink_lat, self.starlink_lon]):
            return  # Not enough data to compare

        distance_nm = haversine(self.gps_chartplotter_lat, self.gps_chartplogger_lon, self.starlink_lat, self.starlink_lon)

        slink_lat_deg, slink_lat_min = dd_to_dm(self.starlink_lat)
        slink_lon_deg, slink_lon_min = dd_to_dm(self.starlink_lon)
        lat_hemisphere = 'N' if self.starlink_lat >= 0 else 'S'
        lon_hemisphere = 'W' if self.starlink_lon < 0 else 'E'

        # Log the current status to the main log file only if a minute or more has passed
        now = time.monotonic()
        if self.last_position_log_time is None or (now - self.last_position_log_time) >= 60:
            # Update maximum distance seen
            self.max_distance_nm = max(self.max_distance_nm, distance_nm)
            sog_str = f", SOG: {self.sog:.1f}" if self.sog is not None else ""
            log_msg = (
                f"Starlink Position: {abs(slink_lat_deg)}° {slink_lat_min:.3f}' {lat_hemisphere}, "
                f"{abs(slink_lon_deg)}° {slink_lon_min:.3f}' {lon_hemisphere}. "
                f"GPS delta: {distance_nm:.3f} NM (max: {self.max_distance_nm:.3f} NM){sog_str}"
            )
            self.logger.info(log_msg)
            self.last_position_log_time = now

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
                self._write_alert_to_file(alert_msg)
            else:
                alert_msg = (
                    f"OK: GPS/Starlink position difference is back within "
                    f"{DISTANCE_THRESHOLD_NM} NM tolerance. Current difference is {distance_nm:.3f} NM."
                )
                self.alert_logger.warning(alert_msg)
                self._write_alert_to_file(alert_msg)
                self.max_distance_nm = 0.0 # Reset max distance after returning to normal

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
                    msg = "ALERT: No GPS data received for 1 minute."
                    self.alert_logger.warning(msg)
                    self._write_alert_to_file(msg)
            else: # No data ever received
                if not self.gps_data_lost:
                    self.gps_data_lost = True
                    msg = "ALERT: No GPS data ever received after startup period."
                    self.alert_logger.warning(msg)
                    self._write_alert_to_file(msg)


            # Check for Starlink data loss
            if self.last_starlink_update_time:
                if now - self.last_starlink_update_time > DATA_LOSS_TIMEOUT_S and not self.starlink_data_lost:
                    self.starlink_data_lost = True
                    msg = "ALERT: No Starlink data received for 1 minute."
                    self.alert_logger.warning(msg)
                    self._write_alert_to_file(msg)
            else: # No data ever received
                if not self.starlink_data_lost:
                    self.starlink_data_lost = True
                    msg = "ALERT: No Starlink data ever received after startup period."
                    self.alert_logger.warning(msg)
                    self._write_alert_to_file(msg)


            await asyncio.sleep(10) # Check every 10 seconds

    async def _test_runner_loop(self):
        """Runs a sequence of test scenarios to trigger alerts."""
        # Wait for the system to receive initial data from both sources
        self.logger.info("Test runner waiting for initial GPS and Starlink data...")
        while not all([self.gps_chartplotter_lat, self.starlink_lat]):
            await asyncio.sleep(1)
        self.logger.info("Test runner detected initial data. Starting test sequence in 5 seconds.")
        await asyncio.sleep(5)

        # --- GPS Offset Test ---
        self.logger.warning("STARTING GPS OFFSET TEST")

        # Ramp latitude up from 0 to +8/600 deg (4 mins total)
        self.logger.info("Test: Ramping latitude offset up to +8/600 deg over 4 mins...")
        self.test_state = "RAMP_LAT_UP"
        await asyncio.sleep(240) # 4 minutes

        # Ramp latitude down from +8/600 to -8/600 deg (8 mins total)
        self.logger.info("Test: Ramping latitude offset down to -8/600 deg over 8 mins...")
        self.test_state = "RAMP_LAT_DOWN"
        await asyncio.sleep(480) # 8 minutes

        # Ramp latitude up from -8/600 to 0 deg (4 mins total)
        self.logger.info("Test: Ramping latitude offset up to 0 deg over 4 mins...")
        self.test_state = "RAMP_LAT_UP"
        await asyncio.sleep(240) # 4 minutes
        self.gps_lat_offset = 0.0 # Reset to exactly zero

        self.logger.info("Test: Latitude offset test complete.")
        await asyncio.sleep(2)

        # Ramp longitude up from 0 to +8/600 deg (4 mins total)
        self.logger.info("Test: Ramping longitude offset up to +8/600 deg over 4 mins...")
        self.test_state = "RAMP_LON_UP"
        await asyncio.sleep(240) # 4 minutes

        # Ramp longitude down from +8/600 to -8/600 deg (8 mins total)
        self.logger.info("Test: Ramping longitude offset down to -8/600 deg over 8 mins...")
        self.test_state = "RAMP_LON_DOWN"
        await asyncio.sleep(480) # 8 minutes

        # Ramp longitude up from -8/600 to 0 deg (4 mins total)
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