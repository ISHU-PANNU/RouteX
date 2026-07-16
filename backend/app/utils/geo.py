import math
import hashlib
import httpx
from typing import List, Tuple, Dict, Any
from app.config.config import settings

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> int:
    """
    Calculate the great-circle distance between two points in meters using Haversine formula.
    """
    R = 6371000.0 # Earth radius in meters
    
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi / 2.0) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    
    return int(R * c)

def geocode_address(address: str) -> Tuple[float, float]:
    """
    Geocodes an address string to (latitude, longitude).
    If GOOGLE_MAPS_API_KEY is not defined, falls back to a deterministic hash-based generator.
    """
    if settings.GOOGLE_MAPS_API_KEY:
        try:
            url = "https://maps.googleapis.com/maps/api/geocode/json"
            params = {"address": address, "key": settings.GOOGLE_MAPS_API_KEY}
            response = httpx.get(url, params=params, timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "OK":
                    location = data["results"][0]["geometry"]["location"]
                    return float(location["lat"]), float(location["lng"])
        except Exception:
            # Fall back to mockup generation on remote API failure
            pass
            
    # Deterministic fallback coordinate generation
    h = hashlib.sha256(address.encode("utf-8")).hexdigest()
    # Map hash bits to coordinates near typical bounds (e.g. San Francisco area: lat 37.7, lng -122.4)
    lat = 37.7000 + (int(h[:8], 16) % 10000) / 100000.0
    lng = -122.4000 - (int(h[8:16], 16) % 10000) / 100000.0
    return round(lat, 8), round(lng, 8)

def get_distance_matrix(coords: List[Tuple[float, float]]) -> Tuple[List[List[int]], List[List[int]]]:
    """
    Generates a matrix of distances (meters) and durations (seconds) between list nodes.
    If GOOGLE_MAPS_API_KEY is not defined, calculates using pairwise Haversine calculations.
    """
    n = len(coords)
    # Default speed assumption: 11 m/s (approx 40 km/h or 25 mph)
    speed_m_s = 11.0
    
    distances = [[0] * n for _ in range(n)]
    durations = [[0] * n for _ in range(n)]
    
    # Check if Google Matrix API can be invoked
    if settings.GOOGLE_MAPS_API_KEY and n > 0:
        try:
            origins = "|".join([f"{c[0]},{c[1]}" for c in coords])
            destinations = "|".join([f"{c[0]},{c[1]}" for c in coords])
            url = "https://maps.googleapis.com/maps/api/distancematrix/json"
            params = {
                "origins": origins,
                "destinations": destinations,
                "key": settings.GOOGLE_MAPS_API_KEY
            }
            response = httpx.get(url, params=params, timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "OK":
                    rows = data.get("rows", [])
                    for i in range(n):
                        elements = rows[i].get("elements", [])
                        for j in range(n):
                            if elements[j].get("status") == "OK":
                                distances[i][j] = elements[j]["distance"]["value"]
                                durations[i][j] = elements[j]["duration"]["value"]
                            else:
                                # Fallback on specific element failure
                                dist = haversine_distance(coords[i][0], coords[i][1], coords[j][0], coords[j][1])
                                distances[i][j] = dist
                                durations[i][j] = int(dist / speed_m_s)
                    return distances, durations
        except Exception:
            # Fall back to pairwise distance calculation on HTTP errors
            pass

    # Mathematical pairwise calculation fallback
    for i in range(n):
        for j in range(n):
            if i == j:
                distances[i][j] = 0
                durations[i][j] = 0
            else:
                dist = haversine_distance(coords[i][0], coords[i][1], coords[j][0], coords[j][1])
                distances[i][j] = dist
                durations[i][j] = int(dist / speed_m_s)
                
    return distances, durations
