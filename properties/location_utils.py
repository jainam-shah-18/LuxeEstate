"""
Location utilities using OpenStreetMap (free, no API keys required)
"""
import os
import logging
from typing import List, Dict, Tuple
import requests
import json
from django.conf import settings

logger = logging.getLogger(__name__)


class OpenStreetMapAPI:
    """
    Interface with OpenStreetMap Nominatim API for geocoding and Overpass API for places
    """

    def __init__(self):
        self.geocode_url = 'https://nominatim.openstreetmap.org/search'
        self.overpass_url = 'https://overpass-api.de/api/interpreter'
        logger.info("Using OpenStreetMap APIs (free, no API keys required)")

    def get_coordinates(self, address: str, city: str = '', state: str = '') -> Tuple[float, float]:
        """
        Convert address to latitude and longitude using OpenStreetMap Nominatim
        """
        try:
            return self._get_coordinates_nominatim(address, city, state)
        except Exception as e:
            logger.error(f"Error geocoding address: {str(e)}")
            return None, None

    def _get_coordinates_nominatim(self, address: str, city: str, state: str) -> Tuple[float, float]:
        """Get coordinates using OpenStreetMap Nominatim API"""
        # Construct search query
        query_components = []
        if address:
            query_components.append(address)
        if city:
            query_components.append(city)
        if state:
            query_components.append(state)

        if not query_components:
            logger.warning("No address, city, or state provided for geocoding.")
            return None, None

        query = ", ".join(query_components)
        params = {
            'q': query,
            'format': 'json',
            'limit': 1,
            'addressdetails': 1,
        }

        response = requests.get(
            self.geocode_url,
            params=params,
            headers={'User-Agent': 'LuxeEstate-Django-App/1.0 (https://luxeestate.example.com; contact@luxeestate.example.com)'},
            timeout=5
        )

        if response.status_code != 200:
            logger.error(f"Nominatim API returned status {response.status_code} for query: {query}")
            return None, None

        data = response.json()
        if data:
            return float(data[0]['lat']), float(data[0]['lon'])

        logger.warning(f"No results found for address: {query}")

        if address and (city or state):
            fallback_parts = [part for part in (city, state) if part]
            fallback_query = ", ".join(fallback_parts)
            if fallback_query:
                fallback_params = {
                    'q': fallback_query,
                    'format': 'json',
                    'limit': 1,
                    'addressdetails': 1,
                }
                fallback_response = requests.get(
                    self.geocode_url,
                    params=fallback_params,
                    headers={'User-Agent': 'LuxeEstate-Django-App/1.0 (https://luxeestate.example.com; contact@luxeestate.example.com)'},
                    timeout=5
                )
                if fallback_response.status_code == 200:
                    fallback_data = fallback_response.json()
                    if fallback_data:
                        logger.info(f"Falling back to city/state geocoding for query: {fallback_query}")
                        return float(fallback_data[0]['lat']), float(fallback_data[0]['lon'])
                else:
                    logger.error(f"Fallback Nominatim API returned status {fallback_response.status_code} for query: {fallback_query}")

        return None, None
    
    def find_nearby_places(self, latitude: float, longitude: float, 
                          place_type: str, radius: int = 3000) -> List[Dict]:
        """
        Find nearby places of a specific type using Overpass API
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            place_type: Type of place (hospital, railway_station, restaurant, etc)
            radius: Search radius in meters (default: 3000)
        
        Returns:
            List of nearby places
        """
        
        try:
            # Map place types to Overpass tags
            tag_mapping = {
                'hospital': ('amenity', 'hospital'),
                'railway_station': ('railway', 'station'),
                'shopping_mall': ('shop', 'mall'),
                'bus_stand': ('amenity', 'bus_station'),
                'school': ('amenity', 'school'),
                'airport': ('aeroway', 'aerodrome'),
                'park': ('leisure', 'park'),
                'supermarket': ('shop', 'supermarket'),
                'restaurant': ('amenity', 'restaurant'),
                'gym': ('leisure', 'fitness_centre'),
                'bank': ('amenity', 'bank'),
                'pharmacy': ('amenity', 'pharmacy'),
                'metro': ('railway', 'subway_entrance'),
                'university': ('amenity', 'university'),
                'theater': ('amenity', 'cinema'),
            }
            
            key, value = tag_mapping.get(place_type, ('amenity', place_type))
            
            # Overpass query
            query = f'[out:json];node(around:{radius},{latitude},{longitude})["{key}"="{value}"];out;'
            
            response = requests.post(self.overpass_url, data={'data': query}, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                places = []
                
                for element in data.get('elements', []):
                    lat = element['lat']
                    lng = element['lon']
                    tags = element.get('tags', {})
                    name = tags.get('name', f'Untitled {place_type}')
                    address = tags.get('addr:full', tags.get('addr:street', 'Unknown address'))
                    
                    place = {
                        'name': name,
                        'address': address,
                        'lat': lat,
                        'lng': lng,
                        'rating': None,  # Not available in OSM
                        'type': [place_type],
                        'open_now': None,  # Not available
                        'place_id': element['id'],
                        'distance_km': self._calculate_distance(
                            latitude, longitude, lat, lng
                        )
                    }
                    places.append(place)
                
                # Sort by distance
                places.sort(key=lambda x: x['distance_km'])
                
                return places
            
            logger.warning(f"Overpass API error: {response.status_code}")
            return []
            
        except Exception as e:
            logger.error(f"Error finding nearby places: {str(e)}")
            return []
    
    def get_all_nearby_locations(self, latitude: float, longitude: float,
                                radius: int = 3000) -> Dict[str, List[Dict]]:
        """
        Get all types of nearby locations
        """
        
        location_types = [
            'hospital',
            'railway_station',
            'shopping_mall',
            'bus_stand',
            'school',
            'airport',
            'park',
            'supermarket',
            'restaurant',
            'gym',
            'bank',
            'pharmacy',
            'metro',
            'university',
            'theater'
        ]
        
        all_locations = {}
        
        for location_type in location_types:
            places = self.find_nearby_places(latitude, longitude, location_type, radius)
            
            # Keep only top 5 places per category
            top_places = places[:5]
            
            # Format as JSON-serializable data
            all_locations[f'nearby_{location_type}'] = [
                {
                    'name': place['name'],
                    'distance_km': round(place['distance_km'], 2),
                    'address': place['address'],
                    'rating': place['rating'],
                    'open_now': place['open_now']
                }
                for place in top_places
            ]
        
        return all_locations
    
    @staticmethod
    def _calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two coordinates using Haversine formula
        Returns distance in kilometers
        """
        from math import radians, cos, sin, asin, sqrt
        
        # Convert decimal degrees to radians
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        
        # Haversine formula
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        km = 6371 * c
        
        return km


class LocationSearchService:
    """
    High-level service for searching and storing locations
    """
    
    def __init__(self):
        self.places_api = OpenStreetMapAPI()
    
    def update_property_locations(self, property_obj, latitude: float = None, 
                                 longitude: float = None, radius: int = 3000):
        """
        Fetch and update nearby locations for a property
        """
        
        try:
            # If coordinates not provided, try to geocode them
            if latitude is None or longitude is None:
                latitude, longitude = self.places_api.get_coordinates(
                    property_obj.address,
                    property_obj.city,
                    property_obj.state
                )
            
            if latitude is None or longitude is None:
                logger.warning(f"Could not get coordinates for property {property_obj.id}")
                return False
            
            # Update property coordinates
            property_obj.latitude = latitude
            property_obj.longitude = longitude
            
            # Fetch all nearby locations
            locations = self.places_api.get_all_nearby_locations(latitude, longitude, radius)
            
            # Update property fields
            for field_name, places in locations.items():
                if hasattr(property_obj, field_name):
                    setattr(property_obj, field_name, places)
            
            property_obj.save()
            logger.info(f"Updated locations for property {property_obj.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating property locations: {str(e)}")
            return False


# Initialize global service
location_service = LocationSearchService()
openstreetmap_api = OpenStreetMapAPI()
