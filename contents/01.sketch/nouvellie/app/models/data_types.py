from app.utils import geo_utils


class WiFiNet:

    def __init__(self, ssid, bssid, channel, rssi,
                 lat, lon, vendor=None, qos=0, lat_target=None, lon_target=None):
        self.ssid = ssid
        self.bssid = bssid
        self.channel = int(channel)
        self.rssi = int(rssi) if rssi is not None else rssi
        self.qos = qos
        self.lat = lat
        self.lon = lon
        self.vendor = vendor
        self.lat_target = lat if not lat_target else lat_target
        self.lon_target = lon if not lon_target else lon_target

        p_targ = (self.lat_target, self.lon_target)
        p_actual = (self.lat, self.lon)
        p_y = (self.lat, self.lon_target)
        p_x = (self.lat_target, self.lon)
        self.distance_x = geo_utils.get_geo_distance(p_targ, p_x, signed=True)
        self.distance_y = geo_utils.get_geo_distance(p_targ, p_y, signed=True)
        self.distance_xy = geo_utils.get_geo_distance(
            p_targ, p_actual, signed=True)

    def serialize(self):
        return {'ssid': self.ssid,
                'bssid': self.bssid,
                'channel': self.channel,
                'rssi': self.rssi,
                'qos': self.qos,
                'lat': self.lat,
                'lon': self.lon,
                'distance_x': self.distance_x,
                'distance_y': self.distance_y,
                'distance_xy': self.distance_xy,
                }

    def __repr__(self):
        return str(self.serialize())
