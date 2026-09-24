"""
Stocke un cache temporaire des places disponibles 
but : éviter de recalculer trop souvent.

"""

places_cache = None
places_cache_time = 0

CACHE_TTL = 3


def invalidate_places_cache():

    global places_cache
    global places_cache_time

    places_cache = None
    places_cache_time = 0