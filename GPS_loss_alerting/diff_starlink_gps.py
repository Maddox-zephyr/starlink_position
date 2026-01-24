#!env /usr/bin/python3

import asyncio
import websockets
import json
import dict_digger
from math import radians, cos, sin, asin, sqrt

def haversine(lat1, lon1, lat2, lon2):
    R = 3959.87433 # this is in miles. For Earth radius in kilometers use 6372.8 km
    dLat = radians(lat2 - lat1)
    dLon = radians(lon2 - lon1)
    lat1 = radians(lat1)
    lat2 = radians(lat2)
    a = sin(dLat/2)**2 + cos(lat1)*cos(lat2)*sin(dLon/2)**2
    c = 2*asin(sqrt(a))
    return R * c

def dd_to_dm(deg):
    d = int(deg)
    m = (deg - d) * 60
    return d, m

async def subscribe_with_source():
    # URI for your specific server address
    uri = "ws://192.168.1.116:80/signalk/v1/stream?subscribe=none"

    async with websockets.connect(uri) as websocket:
        # Subscribe to position with instant updates
        msg = {
            "context": "vessels.self",
            "subscribe": [{"path": "navigation.position",
                           "policy": "instant"}]
            #               "minPeriod": 1000}]
        }
        await websocket.send(json.dumps(msg))

        gps_lat = None
        gps_lon = None
        starlink_lat = None
        starlink_lon = None
        lat_hemisphere = 'N'
        lon_hemisphere = 'E'

        while True:
            try:
                message = await websocket.recv()
                data = json.loads(message)

                if "updates" in data:
                    for update in data["updates"]:
                        # print (update)

                        if (dict_digger.dig(update, "source", "type") == "NMEA2000"):
                            gps_lat = dict_digger.dig(update, "values", 0, "value", "latitude")
                            gps_lon = dict_digger.dig(update, "values", 0, "value", "longitude")
                        elif (dict_digger.dig(update, "$source") == "signalk-starlink"):
                            starlink_lat = dict_digger.dig(update, "values", 0, "value", "latitude")
                            starlink_lon = dict_digger.dig(update, "values", 0, "value", "longitude")

                            if (starlink_lat is not None and starlink_lon is not None
                                and gps_lat is not None and gps_lon is not None):

                                if starlink_lat < 0.0:
                                    lat_hemisphere = 'S'
                                else:
                                    lat_hemisphere = 'N'
                                if starlink_lon < 0.0:
                                    lon_hemisphere = 'W'
                                else:
                                    lon_hemisphere = 'E'

                                slink_gps_delta = haversine(gps_lat, gps_lon, starlink_lat, starlink_lon)
                                slink_lat_deg, slink_lat_min = dd_to_dm(starlink_lat)
                                slink_lon_deg, slink_lon_min = dd_to_dm(starlink_lon)

                                print(f'Starlink Position: {slink_lat_deg}° {slink_lat_min:.3f}\' , {slink_lon_deg}° {slink_lon_min:.3f}\'  GPS delta: {slink_gps_delta:.2f} miles')

                                #print ("Starlink Lat: ", starlink_lat, "Lon: ", starlink_lon)
                                #print ("GPS Lat: ", gps_lat, "Lon: ", gps_lon)
                                #print("Distance between GPS and Starlink: ", distance, "miles\n")
                            else:
                                #print("Incomplete position data:")
                                #print("GPS Lat: ", gps_lat, "Lon: ", gps_lon)
                                #print("Starlink Lat: ", starlink_lat, "Lon: ", starlink_lon)
                                pass
                        else:
                            print("Failed to parse source info: ",)
                            print (update)

            except Exception as e:
                print(f"Error: {e}")
                break

if __name__ == "__main__":
    asyncio.run(subscribe_with_source())

