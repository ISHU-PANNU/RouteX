import urllib.parse
from typing import List, Tuple
from app.utils.geo import geocode_address

class MapsService:
    def geocode(self, address: str) -> Tuple[float, float]:
        """
        Geocode an address to a (latitude, longitude) coordinate pair.
        """
        return geocode_address(address)

    def get_navigation_url(
        self, 
        origin: Tuple[float, float], 
        destination: Tuple[float, float], 
        waypoints: List[Tuple[float, float]]
    ) -> str:
        """
        Generate a Google Maps navigation deep-link with origin, destination, 
        and ordered waypoint stops for the delivery agent.
        """
        base_url = "https://www.google.com/maps/dir/?api=1"
        
        origin_str = f"{origin[0]},{origin[1]}"
        dest_str = f"{destination[0]},{destination[1]}"
        
        params = {
            "origin": origin_str,
            "destination": dest_str,
            "travelmode": "driving"
        }
        
        if waypoints:
            waypoints_str = "|".join([f"{w[0]},{w[1]}" for w in waypoints])
            params["waypoints"] = waypoints_str
            
        query_string = urllib.parse.urlencode(params)
        return f"{base_url}&{query_string}"

maps_service = MapsService()
