import sys
import json
import os
from os.path import join
from pathlib import Path
import random
import datetime
from enum import Enum
import math
from pprint import pprint
from string import ascii_uppercase

import click
import pandas as pd
import numpy as np
import requests

from app.models.data_types import WiFiNet
from app.utils import file_utils, logger_utils, geo_utils
from app.settings import app_cfg as cfg


class NetParser:

    def __init__(self):
        self.log = logger_utils.Logger.getLogger()

    def sort_distance(self, networks, scan_type):

        if scan_type == 'wigle':
            return sorted(networks, key=lambda x: abs(x['distance_xy']), reverse=False)
        elif scan_type == 'ios' or scan_type == 'wigle_export':
            return sorted(networks, key=lambda x: x['rssi'], reverse=True)
        else:
            self.log.error('{} is not a valid type'.format(scan_type))

    def filter_rssi(self, networks, rssi_min=None, rssi_max=None):
        if not rssi_min and not rssi_max:
            return networks
        if rssi_min:
            networks = [n for n in networks if float(n['rssi']) > rssi_min]
        if rssi_max:
            networks = [n for n in networks if float(n['rssi']) < rssi_max]
        return networks

    def filter_channel(self, networks, channel_min=None, channel_max=None):
        if not channel_min and not channel_max:
            return networks
        if channel_min:
            networks = [n for n in networks if float(
                n['channel']) > channel_min]
        if channel_max:
            networks = [n for n in networks if float(
                n['channel']) < channel_max]
        return networks

    def filter_quality(self, network_data, qos_min=None, qos_max=None):
        if not qos_min and not qos_max:
            return networks
        if qos_min:
            networks = [n for n in networks if float(n['qos']) > qos_min]
        if qos_max:
            networks = [n for n in networks if float(n['qos']) < qos_max]
        return networks

    def ios_to_networks(self, fp_in, lat, lon):
        self.log.info('opening: {}'.format(fp_in))
        location = pd.read_csv(
            fp_in, comment='#', skipinitialspace=True, quotechar='"')

        location['SSID'] = location['SSID'].fillna('')

        networks = {}
        for i, scan in location.iterrows():
            bssid = scan['BSSID']
            ssid = str(scan['SSID'])
            if not ssid or ssid == '':
                ssid = str(''.join(random.choice(ascii_uppercase)
                                   for i in range(6)))
            rssi = int(scan['RSSI'])
            if bssid in networks.keys():
                networks[bssid].rssi = max(networks[bssid].rssi, rssi)
            else:
                net = WiFiNet(ssid, bssid, scan['Channel'], rssi, lat, lon)
                networks[bssid] = net

        networks_list = [v.serialize() for k, v in networks.items()]
        return networks_list

    def wigle_export_to_networks(self, fp_in, fp_out, comment):
        df_scan = pd.read_csv(fp_in, skiprows=(1))
        df_scan['SSID'] = df_scan['SSID'].fillna('')

        networks = {}
        for i, scan in df_scan.iterrows():
            bssid = scan['MAC']
            if not len(bssid) == 17:
                continue
            ssid = str(scan['SSID'])
            lat = scan['CurrentLatitude']
            lon = scan['CurrentLongitude']
            if not ssid or ssid == '':
                ssid = str(''.join(random.choice(ascii_uppercase)
                                   for i in range(6)))
            rssi = int(scan['RSSI'])
            if bssid in networks.keys():
                networks[bssid].rssi = max(
                    networks[bssid].rssi, rssi)
            else:
                net = WiFiNet(ssid, bssid, scan['Channel'], rssi, lat, lon)
                networks[bssid] = net

        networks_list = [v.serialize() for k, v in networks.items()]
        return networks_list

    def summarize_locations(self, locations):

        t = []
        num_nets = sum([len(loc['networks']) for loc in locations])
        t.append('')
        t.append('// Globals')
        t.append('extern const unsigned int NNETS;')
        t.append('extern const unsigned int NPLACES;')
        t.append('extern char* ssids[NNETS];')
        t.append('extern byte bssids[NNETS][6];')
        t.append('extern byte channels[NNETS];')
        t.append('extern byte rssis[NNETS];')
        t.append('extern unsigned int idx_offsets[NPLACES];')
        t.append('extern String place_names[NPLACES];')
        t.append('extern String place_cities[NPLACES];')
        t.append('extern unsigned int place_idx_cur;')
        t.append('extern boolean wifi_tx_status;')

        t.append('')
        t.append('')
        t.append('// --------------------------------------------------------')
        t.append('// Include all networks here')
        t.append('// all networks should be included in the "networks/" subdirectory')
        t.append('// --------------------------------------------------------')
        t.append('')
        for location in locations:
            meta = location['meta']
            networks = location['networks']

            nn_name = Path(meta['filepath']).stem.lower()
            nn_name_upper = '{}'.format(nn_name.upper())

            t.append('#include "networks/{}.h"'.format(nn_name))
            t.append('extern const byte NN_{};'.format(nn_name_upper))
            t.append('extern char* ssids_{}[];'.format(nn_name))
            t.append('extern byte bssids_{}[][6];'.format(nn_name))
            t.append('extern byte rssis_{}[];'.format(nn_name))
            t.append('extern byte channels_{}[];'.format(nn_name))
            t.append('extern String name_{};'.format(nn_name))
            t.append('extern String city_{};'.format(nn_name))
            t.append('')

        t.append('')
        t.append('void setup_networks() {')
        t.append('')

        t.append('// Names')
        for idx, location in enumerate(locations):
            nn_name = Path(location['meta']['filepath']).stem.lower()
            t.append('place_names[{}] = name_{};'.format(idx, nn_name))

        t.append('')
        t.append('// Cities')
        for idx, location in enumerate(locations):
            nn_name = Path(location['meta']['filepath']).stem.lower()
            t.append('place_cities[{}] = city_{};'.format(idx, nn_name))

        t.append('')
        t.append('// concatenate networks into one array for each attribute')
        t.append('unsigned int idx_offset = 0;')
        t.append('unsigned int idx = 0;')
        t.append('idx_offsets[0] = 0;')

        for idx, location in enumerate(locations):
            nn_name = Path(location['meta']['filepath']).stem.lower()
            nn_name_upper = nn_name.upper()

            t.append('')
            t.append('// ------------------------------------------------------')
            t.append('// {}'.format(nn_name_upper))
            t.append('// ------------------------------------------------------')
            t.append('')

            # fix {
            t.append(
                'for(unsigned int i = 0; i < NN_{}; i++){}'.format(nn_name_upper, '{'))
            t.append('\tssids[i + idx_offset] = ssids_{}[i];'.format(nn_name))
            t.append('\tfor (byte j = 0; j < 6; j++){}'.format('{'))  # fix {
            t.append(
                '\t\tbssids[i + idx_offset][j] = bssids_{}[i][j];'.format(nn_name))
            t.append('\t}')
            t.append(
                '\tchannels[i + idx_offset] = channels_{}[i];'.format(nn_name))
            t.append('\trssis[i + idx_offset] = rssis_{}[i];'.format(nn_name))
            t.append('}')
            t.append('idx_offset += NN_{};'.format(nn_name_upper))
            t.append('idx++;')
            t.append('idx_offsets[idx] = idx_offset;')
            t.append('')

        t.append('')
        t.append('}')

        return t

    def networks_to_arduino(self, data, name, location):
        meta = data['meta']
        networks = data['networks']
        num_nets = len(networks)

        t = []
        nn_name = Path(meta['filepath']).stem.lower()
        nn_name_upper = 'NN_{}'.format(nn_name.upper())
        t.append('/*')
        t.append(' Scan type: {}'.format(meta.get('type', '')))
        t.append(' Networks: {}'.format(num_nets))
        t.append(' Target lat, lon: {}, {}'.format(
            meta.get('lat', ''), meta.get('lon', '')))
        t.append(' Comment: {}'.format(meta.get('comment', '')))
        t.append(' Generated: {:%b %d, %Y %H:%M:%m}'.format(
            datetime.datetime.now()))
        t.append(' (open + close this sketch to reload changes)')
        t.append('*/')
        t.append('')
        t.append('// Copy and paste this to the networks.h file')
        t.append('/*')
        t.append('#include "networks/{}.h"'.format(nn_name))
        t.append('extern const byte NN_{};'.format(nn_name_upper))
        t.append('extern char* ssids_{}[];'.format(nn_name))
        t.append('extern byte bssids_[][6];'.format(nn_name))
        t.append('extern byte rssis_[]'.format(nn_name))
        t.append('extern byte channels_{}[];'.format(nn_name))
        t.append('extern String name_{};'.format(nn_name))
        t.append('extern String city_{};'.format(nn_name))
        t.append('*/')
        t.append('')

        t.append('// Number of networks')
        t.append('const byte {} = {};'.format(nn_name_upper, num_nets))
        t.append('')
        t.append('// Name and location for OLED')
        t.append('String name_{} = "{}";'.format(nn_name, name))
        t.append('String city_{} = "{}";'.format(nn_name, location))
        t.append('')

        t.append('// SSIDs for display on OLED')
        t.append('char* ssids_{}[{}] = {{'.format(nn_name, nn_name_upper))

        for i, net in enumerate(networks):
            ssid_str = str(net['ssid'])
            ssid_str = ssid_str[0:min(6, len(ssid_str))]
            ssid_str = ssid_str.replace('"', '')
            ssid = '\t"{}"'.format(ssid_str)
            if i < num_nets - 1:
                ssid += ','
            t.append(ssid)
        t.append('};')
        t.append('')

        t.append('// BSSIDs (MAC addresses)')
        t.append('byte bssids_{}[{}][6] = {{'.format(nn_name, nn_name_upper))
        for i, net in enumerate(networks):
            bssid = [('0x{}'.format(v)) for v in net['bssid'].split(':')]
            bssid = ', '.join(bssid)
            bssid = '\t{{{}}}'.format(bssid)
            if i < num_nets - 1:
                bssid += ','
            t.append(bssid)
        t.append('};')
        t.append('')

        t.append('// RSSIs, experimental')
        t.append('byte rssis_{}[{}] = {{'.format(nn_name, nn_name_upper))
        rssis = [n['rssi'] for n in networks]
        rssi_min, rssi_max = tuple(map(int, (min(rssis), max(rssis))))

        rssi_vals = ''
        for i, net in enumerate(networks):
            rx = [-95, rssi_max]
            tx = [cfg.ESP_MIN_OP_TX, cfg.ESP_MAX_TX]
            rssi_val = int(np.interp(int(net['rssi']), rx, tx))
            if i == 0:
                rssi_vals += '{}'.format(rssi_val)
            else:
                rssi_vals += ', {}'.format(rssi_val)
        t.append(rssi_vals)
        t.append('};')
        t.append('')

        lin_sp_ch = np.linspace(1, 11, num=num_nets, dtype=np.uint8)
        channels = ", ".join([str(c) for c in lin_sp_ch])
        channels = 'byte channels_{}[{}] = {{\n {}  \n}};'.format(
            nn_name, nn_name_upper, channels)
        t.append(channels)

        return t
