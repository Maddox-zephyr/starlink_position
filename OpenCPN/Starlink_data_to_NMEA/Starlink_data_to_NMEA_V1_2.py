import subprocess
import time
import socket
import math
from collections import deque
from datetime import datetime, timezone


# Settings:
# this script is able to transmit its data to all devices connected to your wifi and listening on the same port. 
REPO_SCRIPT = r"starlink-grpc-tools-main\dish_grpc_text.py"
UDP_IP = "192.168.1.255"
UDP_PORT = 30330      # Enter this Port as youre port in OpenCPN or Navionics
INTERVAL = 1.5        # Faster polling for smoother speed calculation
AVERAGE_WINDOW = 9.0  # Seconds to average cog and sog

class NavCalculator:
    def __init__(self, window_seconds):
        self.window_seconds = window_seconds
        self.history = deque() # Stores tuples: (timestamp, lat, lon)

    def add_point(self, lat, lon):
        now = time.time()
        self.history.append((now, lat, lon))
        
        # Remove old points outside the averaging window
        while self.history and (now - self.history[0][0] > self.window_seconds):
            self.history.popleft()

    def get_cog_sog(self):
        if len(self.history) < 2:
            return 0.0, 0.0

        # Compare oldest point (approx 8s ago) vs newest point
        t1, lat1, lon1 = self.history[0]
        t2, lat2, lon2 = self.history[-1]
        
        time_delta = t2 - t1
        if time_delta < 1: 
            return 0.0, 0.0

        # 1. Calculate Distance (Haversine Formula) in Meters
        R = 6371000 # Earth radius in meters
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)

        a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        dist_meters = R * c

        # 2. Calculate Speed (Knots)
        speed_mps = dist_meters / time_delta
        sog_knots = speed_mps * 1.94384

        # 3. Calculate Course (Bearing)
        y = math.sin(dlambda) * math.cos(phi2)
        x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(dlambda)
        cog_degrees = (math.degrees(math.atan2(y, x)) + 360) % 360

        # Filter: If moving extremely slowly (< 0.3 kn), output 0 speed to prevent displaying fake movements at anchor
        if sog_knots < 0.3:
            sog_knots = 0.0
            
        return cog_degrees, sog_knots

def get_location_from_repo():
    try:
        #this following part avoids the cmd window from opening
        no_cmd = 0x08000000
        cmd = ["python3", REPO_SCRIPT, "location"]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', creationflags=no_cmd)

        if result.returncode != 0: return None

        line = result.stdout.strip()
        parts = line.split(',')
        
        if len(parts) >= 4:
            return {
                'lat': float(parts[1]),
                'lon': float(parts[2]),
                'alt': float(parts[3])
            }
        return None
    except Exception:
        return None

def format_nmea_coord(decimal_degree, is_lat):
    absolute = abs(decimal_degree)
    degrees = int(absolute)
    minutes = (absolute - degrees) * 60
    val = f"{degrees * 100 + minutes:.4f}"
    
    if is_lat:
        direction = 'N' if decimal_degree >= 0 else 'S'
    else:
        direction = 'E' if decimal_degree >= 0 else 'W'
        if degrees < 100: val = "0" + val
    return val, direction

def create_nmea_msg(payload):
    checksum = 0
    for char in payload:
        checksum ^= ord(char)
    return f"${payload}*{checksum:02X}\r\n"

def main():
    print(f"--- Starlink Smart Nav (Window: {AVERAGE_WINDOW}s) ---")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    nav_calc = NavCalculator(window_seconds=AVERAGE_WINDOW)

    while True:
        data = get_location_from_repo()
        
        if data:
            # 1. Update Calculator
            nav_calc.add_point(data['lat'], data['lon'])
            cog, sog = nav_calc.get_cog_sog()

            # 2. Prepare Data for NMEA
            now = datetime.now(timezone.utc)
            utc_time = now.strftime("%H%M%S")
            lat_str, lat_dir = format_nmea_coord(data['lat'], True)
            lon_str, lon_dir = format_nmea_coord(data['lon'], False)

            # 3. Create GPGGA (Position)
            # Format: Time, Lat, Dir, Lon, Dir, Quality, Sats, HDOP, Alt, Units...
            gpgga_payload = f"GPGGA,{utc_time},{lat_str},{lat_dir},{lon_str},{lon_dir},1,08,1.0,{data['alt']:.1f},M,0.0,M,,"
            sock.sendto(create_nmea_msg(gpgga_payload).encode('utf-8'), (UDP_IP, UDP_PORT))

            # 4. Create GPVTG (Velocity/Course)
            # Format: Course(True), T, Course(Mag), M, Speed(Knots), N, Speed(KPH), K, Mode
            # We don't have magnetic variation, so we leave the magnetic field empty
            gpvtg_payload = f"GPVTG,{cog:.1f},T,,M,{sog:.2f},N,{sog*1.852:.1f},K,A"
            sock.sendto(create_nmea_msg(gpvtg_payload).encode('utf-8'), (UDP_IP, UDP_PORT))

            print(f"Sent: Pos {data['lat']:.4f}/{data['lon']:.4f} | COG: {cog:.1f}° SOG: {sog:.2f}kn")
        
        time.sleep(INTERVAL)

if __name__ == "__main__":
    main()