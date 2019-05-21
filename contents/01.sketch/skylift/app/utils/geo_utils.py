import geopy.distance


def get_signed_distance(p1, p2):
    d = geopy.distance.vincenty(p1, p2).m
    return -d if (p2[0] < p1[0] or p2[1] > p1[1]) else d


def get_geo_distance(p1, p2, signed=False):
    d = geopy.distance.vincenty(p1, p2).m
    return -d if (p2[0] < p1[0] or p2[1] > p1[1]) else d


def calc_geo_rssi(p1, p2):
    m = geopy.distance.vincenty(p1, p2).m
    if m > 1000:
        rssi = -90
    elif m > 500:
        rssi = -80
    elif m > 250:
        rssi = -75
    elif m > 125:
        rssi = -65
    elif m > 50:
        rssi = -55
    else:
        rssi = -50
    return rssi
