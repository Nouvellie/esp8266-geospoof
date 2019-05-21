from os.path import join
import json
from pathlib import Path

import requests

from app.models.data_types import WiFiNet
from app.utils import logger_utils, geo_utils
from app.settings import app_cfg as cfg


class WigleAPI:

    def __init__(self, api_name, api_token):
        self.log = logger_utils.Logger.getLogger()
        self.api_name = api_name
        self.api_token = api_token

    def build_url(self, lat, lon, radius_scale, opt_since):
        radius_inc_lat = 0.00944
        radius_inc_lon = 0.00944

        lat_range = (lat - (radius_inc_lat / 2 * radius_scale),
                     lat + (radius_inc_lat / 2 * radius_scale))
        lon_range = (lon - (radius_inc_lon / 2 * radius_scale),
                     lon + (radius_inc_lon / 2 * radius_scale))

        url = 'https://api.wigle.net/api/v2/network/search?'
        url += 'onlymine=false&'
        url += 'latrange1=' + str(lat_range[0]) + '&'
        url += 'latrange2=' + str(lat_range[1]) + '&'
        url += 'longrange1=' + str(lon_range[0]) + '&'
        url += 'longrange2=' + str(lon_range[1]) + '&'
        url += 'lastupdt=' + str(opt_since) + '&'
        url += 'freenet=false&'
        url += 'paynet=false'
        return url

    def fetch(self, url, lat, lon):
        networks = []
        target = (lat, lon)
        wigle_data = requests.get(url,
                                  headers={'Authentication': 'Basic'},
                                  auth=(self.api_name, self.api_token))

        try:
            wigle_data = wigle_data.json()['results']
        except:
            self.log.error('could not parse data: {}'.format(wigle_data))
            return []

        for n in wigle_data:
            actual = (n['trilat'], n['trilong'])
            rssi_estimated = geo_utils.calc_geo_rssi(actual, target)
            wifi_net = WiFiNet(
                n['ssid'],
                n['netid'],
                n['channel'],
                rssi=rssi_estimated,
                qos=n['qos'],
                lat=n['trilat'],
                lon=n['trilong'],
                lat_target=lat,
                lon_target=lon)
            networks.append(wifi_net)
        networks = [n.serialize() for n in networks]
        return networks
