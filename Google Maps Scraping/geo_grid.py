"""Geographic Grid and U.S. Spatial Partitioning Engine.

Overcomes Google Maps' strict 120-result per query limitation by subdividing
regions into spatial matrices (coordinate grids, bounding boxes, or administrative
city/state/zip units).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, Generator, List, Optional, Tuple

from models import SearchJob


@dataclass
class BoundingBox:
    min_lat: float
    min_lng: float
    max_lat: float
    max_lng: float

    def subdivide_quadrants(self) -> List["BoundingBox"]:
        """Subdivides a bounding box into 4 equal quadrants (Quadtree step)."""
        mid_lat = (self.min_lat + self.max_lat) / 2.0
        mid_lng = (self.min_lng + self.max_lng) / 2.0
        return [
            BoundingBox(self.min_lat, self.min_lng, mid_lat, mid_lng),      # SW
            BoundingBox(self.min_lat, mid_lng, mid_lat, self.max_lng),      # SE
            BoundingBox(mid_lat, self.min_lng, self.max_lat, mid_lng),      # NW
            BoundingBox(mid_lat, mid_lng, self.max_lat, self.max_lng),      # NE
        ]

    @property
    def center(self) -> Tuple[float, float]:
        return (self.min_lat + self.max_lat) / 2.0, (self.min_lng + self.max_lng) / 2.0


# Bounding boxes for all 50 U.S. States + DC
US_STATE_BOUNDS: Dict[str, BoundingBox] = {
    "AL": BoundingBox(30.223, -88.473, 35.008, -84.889),
    "AK": BoundingBox(51.214, -179.148, 71.365, -129.980),
    "AZ": BoundingBox(31.332, -114.816, 37.004, -109.045),
    "AR": BoundingBox(33.004, -94.617, 36.499, -89.644),
    "CA": BoundingBox(32.534, -124.409, 42.009, -114.131),
    "CO": BoundingBox(36.992, -109.060, 41.003, -102.041),
    "CT": BoundingBox(40.980, -73.727, 42.050, -71.786),
    "DE": BoundingBox(38.451, -75.788, 39.839, -75.048),
    "DC": BoundingBox(38.791, -77.119, 38.995, -76.909),
    "FL": BoundingBox(24.523, -87.634, 31.000, -80.031),
    "GA": BoundingBox(30.357, -85.605, 35.000, -80.839),
    "HI": BoundingBox(18.910, -160.247, 22.235, -154.806),
    "ID": BoundingBox(41.988, -117.243, 49.001, -111.043),
    "IL": BoundingBox(36.970, -91.513, 42.508, -87.494),
    "IN": BoundingBox(37.771, -88.097, 41.760, -84.784),
    "IA": BoundingBox(40.375, -96.639, 43.501, -90.140),
    "KS": BoundingBox(36.993, -102.051, 40.003, -94.588),
    "KY": BoundingBox(36.497, -89.571, 39.147, -81.964),
    "LA": BoundingBox(28.928, -94.043, 33.019, -88.817),
    "ME": BoundingBox(43.059, -71.083, 47.459, -66.949),
    "MD": BoundingBox(37.911, -79.487, 39.723, -75.048),
    "MA": BoundingBox(41.237, -73.508, 42.886, -69.928),
    "MI": BoundingBox(41.696, -90.418, 48.261, -82.413),
    "MN": BoundingBox(43.499, -97.239, 49.384, -89.491),
    "MS": BoundingBox(30.175, -91.655, 34.996, -88.097),
    "MO": BoundingBox(35.995, -95.774, 40.613, -89.098),
    "MT": BoundingBox(44.358, -116.050, 49.001, -104.039),
    "NE": BoundingBox(39.999, -104.053, 43.001, -95.308),
    "NV": BoundingBox(35.001, -120.005, 42.002, -114.039),
    "NH": BoundingBox(42.697, -72.557, 45.305, -70.713),
    "NJ": BoundingBox(38.928, -75.559, 41.357, -73.893),
    "NM": BoundingBox(31.332, -109.050, 37.000, -103.001),
    "NY": BoundingBox(40.496, -79.762, 45.015, -71.856),
    "NC": BoundingBox(33.842, -84.321, 36.588, -75.460),
    "ND": BoundingBox(45.935, -104.048, 49.000, -96.554),
    "OH": BoundingBox(38.403, -84.820, 41.977, -80.518),
    "OK": BoundingBox(33.615, -103.002, 37.002, -94.431),
    "OR": BoundingBox(41.991, -124.566, 46.292, -116.463),
    "PA": BoundingBox(39.719, -80.519, 42.269, -74.689),
    "RI": BoundingBox(41.146, -71.862, 42.018, -71.120),
    "SC": BoundingBox(32.046, -83.353, 35.215, -78.542),
    "SD": BoundingBox(42.479, -104.057, 45.945, -96.436),
    "TN": BoundingBox(34.982, -90.310, 36.678, -81.646),
    "TX": BoundingBox(25.837, -106.645, 36.500, -93.508),
    "UT": BoundingBox(36.997, -114.052, 42.001, -109.041),
    "VT": BoundingBox(42.726, -73.437, 45.016, -71.464),
    "VA": BoundingBox(36.540, -83.675, 39.466, -75.242),
    "WA": BoundingBox(45.543, -124.763, 49.002, -116.915),
    "WV": BoundingBox(37.201, -82.644, 40.638, -77.719),
    "WI": BoundingBox(42.491, -92.888, 47.080, -86.805),
    "WY": BoundingBox(40.994, -111.056, 45.005, -104.052),
}

# Curated dataset of major US Metropolitan cities across all 50 states
TOP_US_CITIES = [
    # Top Tier Metro Areas
    {"city": "New York", "state": "NY", "lat": 40.7128, "lng": -74.0060},
    {"city": "Los Angeles", "state": "CA", "lat": 34.0522, "lng": -118.2437},
    {"city": "Chicago", "state": "IL", "lat": 41.8781, "lng": -87.6298},
    {"city": "Houston", "state": "TX", "lat": 29.7604, "lng": -95.3698},
    {"city": "Phoenix", "state": "AZ", "lat": 33.4484, "lng": -112.0740},
    {"city": "Philadelphia", "state": "PA", "lat": 39.9526, "lng": -75.1652},
    {"city": "San Antonio", "state": "TX", "lat": 29.4241, "lng": -98.4936},
    {"city": "San Diego", "state": "CA", "lat": 32.7157, "lng": -117.1611},
    {"city": "Dallas", "state": "TX", "lat": 32.7767, "lng": -96.7970},
    {"city": "Austin", "state": "TX", "lat": 30.2672, "lng": -97.7431},
    {"city": "Jacksonville", "state": "FL", "lat": 30.3322, "lng": -81.6557},
    {"city": "Fort Worth", "state": "TX", "lat": 32.7555, "lng": -97.3308},
    {"city": "San Jose", "state": "CA", "lat": 37.3382, "lng": -121.8863},
    {"city": "Columbus", "state": "OH", "lat": 39.9612, "lng": -82.9988},
    {"city": "Charlotte", "state": "NC", "lat": 35.2271, "lng": -80.8431},
    {"city": "Indianapolis", "state": "IN", "lat": 39.7684, "lng": -86.1581},
    {"city": "San Francisco", "state": "CA", "lat": 37.7749, "lng": -122.4194},
    {"city": "Seattle", "state": "WA", "lat": 47.6062, "lng": -122.3321},
    {"city": "Denver", "state": "CO", "lat": 39.7392, "lng": -104.9903},
    {"city": "Nashville", "state": "TN", "lat": 36.1627, "lng": -86.7816},
    {"city": "Oklahoma City", "state": "OK", "lat": 35.4676, "lng": -97.5164},
    {"city": "El Paso", "state": "TX", "lat": 31.7619, "lng": -106.4850},
    {"city": "Washington", "state": "DC", "lat": 38.9072, "lng": -77.0369},
    {"city": "Boston", "state": "MA", "lat": 42.3601, "lng": -71.0589},
    {"city": "Las Vegas", "state": "NV", "lat": 36.1699, "lng": -115.1398},
    {"city": "Portland", "state": "OR", "lat": 45.5152, "lng": -122.6784},
    {"city": "Detroit", "state": "MI", "lat": 42.3314, "lng": -83.0458},
    {"city": "Louisville", "state": "KY", "lat": 38.2527, "lng": -85.7585},
    {"city": "Memphis", "state": "TN", "lat": 35.1495, "lng": -90.0490},
    {"city": "Baltimore", "state": "MD", "lat": 39.2904, "lng": -76.6122},
    {"city": "Milwaukee", "state": "WI", "lat": 43.0389, "lng": -87.9065},
    {"city": "Albuquerque", "state": "NM", "lat": 35.0844, "lng": -106.6504},
    {"city": "Tucson", "state": "AZ", "lat": 32.2226, "lng": -110.9747},
    {"city": "Fresno", "state": "CA", "lat": 36.7468, "lng": -119.7726},
    {"city": "Sacramento", "state": "CA", "lat": 38.5816, "lng": -121.4944},
    {"city": "Mesa", "state": "AZ", "lat": 33.4152, "lng": -111.8315},
    {"city": "Kansas City", "state": "MO", "lat": 39.0997, "lng": -94.5786},
    {"city": "Atlanta", "state": "GA", "lat": 33.7490, "lng": -84.3880},
    {"city": "Omaha", "state": "NE", "lat": 41.2565, "lng": -95.9345},
    {"city": "Colorado Springs", "state": "CO", "lat": 38.8339, "lng": -104.8214},
    {"city": "Raleigh", "state": "NC", "lat": 35.7796, "lng": -78.6382},
    {"city": "Miami", "state": "FL", "lat": 25.7617, "lng": -80.1918},
    {"city": "Long Beach", "state": "CA", "lat": 33.7701, "lng": -118.1937},
    {"city": "Virginia Beach", "state": "VA", "lat": 36.8529, "lng": -75.9780},
    {"city": "Oakland", "state": "CA", "lat": 37.8044, "lng": -122.2712},
    {"city": "Minneapolis", "state": "MN", "lat": 44.9778, "lng": -93.2650},
    {"city": "Tampa", "state": "FL", "lat": 27.9506, "lng": -82.4572},
    {"city": "Tulsa", "state": "OK", "lat": 36.1540, "lng": -95.9928},
    {"city": "Arlington", "state": "TX", "lat": 32.7357, "lng": -97.1081},
    {"city": "New Orleans", "state": "LA", "lat": 29.9511, "lng": -90.0715},
    {"city": "Wichita", "state": "KS", "lat": 37.6872, "lng": -97.3301},
    {"city": "Cleveland", "state": "OH", "lat": 41.4993, "lng": -81.6944},
    {"city": "Bakersfield", "state": "CA", "lat": 35.3733, "lng": -119.0187},
    {"city": "Aurora", "state": "CO", "lat": 39.7294, "lng": -104.8319},
    {"city": "Anaheim", "state": "CA", "lat": 33.8366, "lng": -117.9143},
    {"city": "Honolulu", "state": "HI", "lat": 21.3069, "lng": -157.8583},
    {"city": "Santa Ana", "state": "CA", "lat": 33.7455, "lng": -117.8677},
    {"city": "Riverside", "state": "CA", "lat": 33.9533, "lng": -117.3962},
    {"city": "Corpus Christi", "state": "TX", "lat": 27.8006, "lng": -97.3964},
    {"city": "Lexington", "state": "KY", "lat": 38.0406, "lng": -84.5037},
    {"city": "Stockton", "state": "CA", "lat": 37.9577, "lng": -121.2908},
    {"city": "Henderson", "state": "NV", "lat": 36.0395, "lng": -114.9817},
    {"city": "Saint Paul", "state": "MN", "lat": 44.9537, "lng": -93.0900},
    {"city": "St. Louis", "state": "MO", "lat": 38.6270, "lng": -90.1994},
    {"city": "Cincinnati", "state": "OH", "lat": 39.1031, "lng": -84.5120},
    {"city": "Pittsburgh", "state": "PA", "lat": 40.4406, "lng": -79.9959},
    {"city": "Greensboro", "state": "NC", "lat": 36.0726, "lng": -79.7920},
    {"city": "Anchorage", "state": "AK", "lat": 61.2181, "lng": -149.9003},
    {"city": "Plano", "state": "TX", "lat": 33.0198, "lng": -96.6989},
    {"city": "Lincoln", "state": "NE", "lat": 40.8136, "lng": -96.7026},
    {"city": "Orlando", "state": "FL", "lat": 28.5383, "lng": -81.3792},
    {"city": "Irvine", "state": "CA", "lat": 33.6846, "lng": -117.8265},
    {"city": "Newark", "state": "NJ", "lat": 40.7357, "lng": -74.1724},
    {"city": "Toledo", "state": "OH", "lat": 41.6528, "lng": -83.5379},
    {"city": "Durham", "state": "NC", "lat": 35.9940, "lng": -78.8986},
    {"city": "Chula Vista", "state": "CA", "lat": 32.6401, "lng": -117.0842},
    {"city": "Fort Wayne", "state": "IN", "lat": 41.0793, "lng": -85.1394},
    {"city": "Jersey City", "state": "NJ", "lat": 40.7178, "lng": -74.0431},
    {"city": "St. Petersburg", "state": "FL", "lat": 27.7676, "lng": -82.6403},
    {"city": "Laredo", "state": "TX", "lat": 27.5036, "lng": -99.5076},
    {"city": "Madison", "state": "WI", "lat": 43.0731, "lng": -89.4012},
    {"city": "Chandler", "state": "AZ", "lat": 33.3062, "lng": -111.8413},
    {"city": "Buffalo", "state": "NY", "lat": 42.8864, "lng": -78.8784},
    {"city": "Lubbock", "state": "TX", "lat": 33.5779, "lng": -101.8552},
    {"city": "Scottsdale", "state": "AZ", "lat": 33.4942, "lng": -111.9261},
    {"city": "Reno", "state": "NV", "lat": 39.5296, "lng": -119.8138},
    {"city": "Glendale", "state": "AZ", "lat": 33.5387, "lng": -112.1860},
    {"city": "Gilbert", "state": "AZ", "lat": 33.3528, "lng": -111.7890},
    {"city": "Winston-Salem", "state": "NC", "lat": 36.0999, "lng": -80.2442},
    {"city": "North Las Vegas", "state": "NV", "lat": 36.1989, "lng": -115.1175},
    {"city": "Norfolk", "state": "VA", "lat": 36.8508, "lng": -76.2859},
    {"city": "Chesapeake", "state": "VA", "lat": 36.7682, "lng": -76.2875},
    {"city": "Garland", "state": "TX", "lat": 32.9126, "lng": -96.6389},
    {"city": "Irving", "state": "TX", "lat": 32.8140, "lng": -96.9489},
    {"city": "Hialeah", "state": "FL", "lat": 25.8576, "lng": -80.2781},
    {"city": "Fremont", "state": "CA", "lat": 37.5485, "lng": -121.9886},
    {"city": "Boise", "state": "ID", "lat": 43.6150, "lng": -116.2023},
    {"city": "Richmond", "state": "VA", "lat": 37.5407, "lng": -77.4360},
    {"city": "Baton Rouge", "state": "LA", "lat": 30.4515, "lng": -91.1871},
    {"city": "Spokane", "state": "WA", "lat": 47.6588, "lng": -117.4260},
    {"city": "Des Moines", "state": "IA", "lat": 41.5868, "lng": -93.6250},
    {"city": "Tacoma", "state": "WA", "lat": 47.2529, "lng": -122.4443},
    {"city": "San Bernardino", "state": "CA", "lat": 34.1083, "lng": -117.2898},
    {"city": "Modesto", "state": "CA", "lat": 37.6391, "lng": -120.9969},
    {"city": "Fontana", "state": "CA", "lat": 34.0922, "lng": -117.4350},
    {"city": "Santa Clarita", "state": "CA", "lat": 34.3917, "lng": -118.5426},
    {"city": "Birmingham", "state": "AL", "lat": 33.5186, "lng": -86.8104},
    {"city": "Oxnard", "state": "CA", "lat": 34.1975, "lng": -119.1771},
    {"city": "Fayetteville", "state": "NC", "lat": 35.0527, "lng": -78.8784},
    {"city": "Moreno Valley", "state": "CA", "lat": 33.9425, "lng": -117.2297},
    {"city": "Rochester", "state": "NY", "lat": 43.1566, "lng": -77.6088},
    {"city": "Glendale", "state": "CA", "lat": 34.1425, "lng": -118.2551},
    {"city": "Huntington Beach", "state": "CA", "lat": 33.6595, "lng": -117.9988},
    {"city": "Salt Lake City", "state": "UT", "lat": 40.7608, "lng": -111.8910},
    {"city": "Grand Rapids", "state": "MI", "lat": 42.9634, "lng": -85.6681},
    {"city": "Amarillo", "state": "TX", "lat": 35.2220, "lng": -101.8313},
    {"city": "Yonkers", "state": "NY", "lat": 40.9312, "lng": -73.8987},
    {"city": "Montgomery", "state": "AL", "lat": 32.3792, "lng": -86.3077},
    {"city": "Akron", "state": "OH", "lat": 41.0814, "lng": -81.5190},
    {"city": "Little Rock", "state": "AR", "lat": 34.7465, "lng": -92.2896},
    {"city": "Huntsville", "state": "AL", "lat": 34.7304, "lng": -86.5861},
    {"city": "Augusta", "state": "GA", "lat": 33.4735, "lng": -82.0105},
    {"city": "Port St. Lucie", "state": "FL", "lat": 27.2730, "lng": -80.3582},
    {"city": "Grand Prairie", "state": "TX", "lat": 32.7460, "lng": -96.9978},
    {"city": "Columbus", "state": "GA", "lat": 32.4610, "lng": -84.9877},
    {"city": "Tallahassee", "state": "FL", "lat": 30.4383, "lng": -84.2807},
    {"city": "Overland Park", "state": "KS", "lat": 38.9822, "lng": -94.6708},
    {"city": "Tempe", "state": "AZ", "lat": 33.4255, "lng": -111.9400},
    {"city": "McKinney", "state": "TX", "lat": 33.1972, "lng": -96.6398},
    {"city": "Mobile", "state": "AL", "lat": 30.6954, "lng": -88.0399},
    {"city": "Cape Coral", "state": "FL", "lat": 26.5629, "lng": -81.9495},
    {"city": "Shreveport", "state": "LA", "lat": 32.5252, "lng": -93.7502},
    {"city": "Frisco", "state": "TX", "lat": 33.1507, "lng": -96.8236},
    {"city": "Knoxville", "state": "TN", "lat": 35.9606, "lng": -83.9207},
    {"city": "Worcester", "state": "MA", "lat": 42.2626, "lng": -71.8023},
    {"city": "Brownsville", "state": "TX", "lat": 25.9017, "lng": -97.4975},
    {"city": "Vancouver", "state": "WA", "lat": 45.6387, "lng": -122.6615},
    {"city": "Fort Lauderdale", "state": "FL", "lat": 26.1224, "lng": -80.1373},
    {"city": "Sioux Falls", "state": "SD", "lat": 43.5460, "lng": -96.7313},
    {"city": "Ontario", "state": "CA", "lat": 34.0633, "lng": -117.6509},
    {"city": "Chattanooga", "state": "TN", "lat": 35.0456, "lng": -85.3097},
    {"city": "Providence", "state": "RI", "lat": 41.8240, "lng": -71.4128},
    {"city": "Newport News", "state": "VA", "lat": 36.9786, "lng": -76.4280},
    {"city": "Rancho Cucamonga", "state": "CA", "lat": 34.1064, "lng": -117.5931},
    {"city": "Santa Rosa", "state": "CA", "lat": 38.4404, "lng": -122.7141},
    {"city": "Oceanside", "state": "CA", "lat": 33.1959, "lng": -117.3795},
    {"city": "Salem", "state": "OR", "lat": 44.9429, "lng": -123.0351},
    {"city": "Elk Grove", "state": "CA", "lat": 38.4088, "lng": -121.3716},
    {"city": "Garden Grove", "state": "CA", "lat": 33.7743, "lng": -117.9380},
    {"city": "Pembroke Pines", "state": "FL", "lat": 26.0078, "lng": -80.2259},
    {"city": "Peoria", "state": "AZ", "lat": 33.5806, "lng": -112.2374},
    {"city": "Eugene", "state": "OR", "lat": 44.0521, "lng": -123.0868},
    {"city": "Corona", "state": "CA", "lat": 33.8753, "lng": -117.5664},
    {"city": "Cary", "state": "NC", "lat": 35.7915, "lng": -78.7811},
    {"city": "Springfield", "state": "MO", "lat": 37.2089, "lng": -93.2923},
    {"city": "Fort Collins", "state": "CO", "lat": 40.5853, "lng": -105.0844},
    {"city": "Jackson", "state": "MS", "lat": 32.2988, "lng": -90.1848},
    {"city": "Alexandria", "state": "VA", "lat": 38.8048, "lng": -77.0469},
    {"city": "Hayward", "state": "CA", "lat": 37.6688, "lng": -122.0808},
    {"city": "Lancaster", "state": "CA", "lat": 34.6868, "lng": -118.1542},
    {"city": "Lakewood", "state": "CO", "lat": 39.7047, "lng": -105.0814},
    {"city": "Clarksville", "state": "TN", "lat": 36.5298, "lng": -87.3595},
    {"city": "Palmdale", "state": "CA", "lat": 34.5794, "lng": -118.1165},
    {"city": "Salinas", "state": "CA", "lat": 36.6777, "lng": -121.6555},
    {"city": "Springfield", "state": "MA", "lat": 42.1015, "lng": -72.5898},
    {"city": "Hollywood", "state": "FL", "lat": 26.0112, "lng": -80.1495},
    {"city": "Pasadena", "state": "TX", "lat": 29.6911, "lng": -95.2091},
    {"city": "Sunnyvale", "state": "CA", "lat": 37.3688, "lng": -122.0363},
    {"city": "Macon", "state": "GA", "lat": 32.8407, "lng": -83.6324},
    {"city": "Kansas City", "state": "KS", "lat": 39.1155, "lng": -94.6268},
    {"city": "Pomona", "state": "CA", "lat": 34.0551, "lng": -117.7499},
    {"city": "Escondido", "state": "CA", "lat": 33.1192, "lng": -117.0864},
    {"city": "Killeen", "state": "TX", "lat": 31.1171, "lng": -97.7278},
    {"city": "Naperville", "state": "IL", "lat": 41.7508, "lng": -88.1535},
    {"city": "Bellevue", "state": "WA", "lat": 47.6101, "lng": -122.2015},
    {"city": "Joliet", "state": "IL", "lat": 41.5250, "lng": -88.0817},
    {"city": "Murfreesboro", "state": "TN", "lat": 35.8456, "lng": -86.3903},
    {"city": "Midland", "state": "TX", "lat": 31.9973, "lng": -102.0779},
    {"city": "Rockford", "state": "IL", "lat": 42.2711, "lng": -89.0940},
    {"city": "Paterson", "state": "NJ", "lat": 40.9168, "lng": -74.1718},
    {"city": "Savannah", "state": "GA", "lat": 32.0809, "lng": -81.0912},
    {"city": "Bridgeport", "state": "CT", "lat": 41.1792, "lng": -73.1894},
    {"city": "Torrance", "state": "CA", "lat": 33.8358, "lng": -118.3406},
    {"city": "McAllen", "state": "TX", "lat": 26.2034, "lng": -98.2300},
    {"city": "Syracuse", "state": "NY", "lat": 43.0481, "lng": -76.1474},
    {"city": "Surprise", "state": "AZ", "lat": 33.6298, "lng": -112.3679},
    {"city": "Denton", "state": "TX", "lat": 33.2148, "lng": -97.1331},
    {"city": "Roseville", "state": "CA", "lat": 38.7521, "lng": -121.2880},
    {"city": "Thornton", "state": "CO", "lat": 39.8680, "lng": -104.9719},
    {"city": "Miramar", "state": "FL", "lat": 25.9860, "lng": -80.2323},
    {"city": "Pasadena", "state": "CA", "lat": 34.1478, "lng": -118.1445},
    {"city": "Mesquite", "state": "TX", "lat": 32.7668, "lng": -96.5992},
    {"city": "Olathe", "state": "KS", "lat": 38.8814, "lng": -94.8191},
    {"city": "Dayton", "state": "OH", "lat": 39.7589, "lng": -84.1916},
    {"city": "Carrollton", "state": "TX", "lat": 32.9746, "lng": -96.8899},
    {"city": "Waco", "state": "TX", "lat": 31.5493, "lng": -97.1467},
    {"city": "Orange", "state": "CA", "lat": 33.7879, "lng": -117.8531},
    {"city": "Fullerton", "state": "CA", "lat": 33.8704, "lng": -117.9242},
    {"city": "Charleston", "state": "SC", "lat": 32.7765, "lng": -79.9311},
    {"city": "West Valley City", "state": "UT", "lat": 40.6916, "lng": -111.9891},
    {"city": "Visalia", "state": "CA", "lat": 36.3302, "lng": -119.2921},
    {"city": "Hampton", "state": "VA", "lat": 37.0299, "lng": -76.3452},
    {"city": "Gainesville", "state": "FL", "lat": 29.6516, "lng": -82.3248},
    {"city": "Warren", "state": "MI", "lat": 42.5145, "lng": -83.0147},
    {"city": "Coral Springs", "state": "FL", "lat": 26.2712, "lng": -80.2706},
    {"city": "Round Rock", "state": "TX", "lat": 30.5083, "lng": -97.6789},
    {"city": "Sterling Heights", "state": "MI", "lat": 42.5803, "lng": -83.0302},
    {"city": "Kent", "state": "WA", "lat": 47.3809, "lng": -122.2348},
    {"city": "Columbia", "state": "SC", "lat": 34.0007, "lng": -81.0348},
    {"city": "Santa Clara", "state": "CA", "lat": 37.3541, "lng": -121.9552},
    {"city": "New Haven", "state": "CT", "lat": 41.3083, "lng": -72.9279},
    {"city": "Stamford", "state": "CT", "lat": 41.0534, "lng": -73.5387},
    {"city": "Concord", "state": "CA", "lat": 37.9780, "lng": -122.0311},
    {"city": "Elizabeth", "state": "NJ", "lat": 40.6640, "lng": -74.2107},
    {"city": "Athens", "state": "GA", "lat": 33.9519, "lng": -83.3576},
    {"city": "Thousand Oaks", "state": "CA", "lat": 34.1706, "lng": -118.8376},
    {"city": "Lafayette", "state": "LA", "lat": 30.2241, "lng": -92.0198},
    {"city": "Simi Valley", "state": "CA", "lat": 34.2694, "lng": -118.7815},
    {"city": "Topeka", "state": "KS", "lat": 39.0558, "lng": -95.6890},
    {"city": "Norman", "state": "OK", "lat": 35.2226, "lng": -97.4395},
    {"city": "Fargo", "state": "ND", "lat": 46.8772, "lng": -96.7898},
    {"city": "Wilmington", "state": "NC", "lat": 34.2257, "lng": -77.9447},
    {"city": "Abilene", "state": "TX", "lat": 32.4487, "lng": -99.7331},
    {"city": "Odessa", "state": "TX", "lat": 31.8457, "lng": -102.3676},
    {"city": "Pearland", "state": "TX", "lat": 29.5636, "lng": -95.2860},
    {"city": "Victorville", "state": "CA", "lat": 34.5362, "lng": -117.2928},
    {"city": "Hartford", "state": "CT", "lat": 41.7658, "lng": -72.6734},
    {"city": "Vallejo", "state": "CA", "lat": 38.1041, "lng": -122.2566},
    {"city": "Allentown", "state": "PA", "lat": 40.6084, "lng": -75.4902},
    {"city": "Berkeley", "state": "CA", "lat": 37.8715, "lng": -122.2730},
    {"city": "Richardson", "state": "TX", "lat": 32.9483, "lng": -96.7299},
    {"city": "Arvada", "state": "CO", "lat": 39.8028, "lng": -105.0875},
    {"city": "Ann Arbor", "state": "MI", "lat": 42.2808, "lng": -83.7430},
    {"city": "Rochester", "state": "MN", "lat": 44.0121, "lng": -92.4802},
    {"city": "Cambridge", "state": "MA", "lat": 42.3736, "lng": -71.1097},
    {"city": "Sugar Land", "state": "TX", "lat": 29.6197, "lng": -95.6349},
    {"city": "Lansing", "state": "MI", "lat": 42.7325, "lng": -84.5555},
    {"city": "Evansville", "state": "IN", "lat": 37.9716, "lng": -87.5711},
    {"city": "College Station", "state": "TX", "lat": 30.6280, "lng": -96.3344},
    {"city": "Fairfield", "state": "CA", "lat": 38.2494, "lng": -122.0400},
    {"city": "Clearwater", "state": "FL", "lat": 27.9659, "lng": -82.8001},
    {"city": "Beaumont", "state": "TX", "lat": 30.0802, "lng": -94.1266},
    {"city": "Independence", "state": "MO", "lat": 39.0911, "lng": -94.4155},
    {"city": "Provo", "state": "UT", "lat": 40.2338, "lng": -111.6585},
    {"city": "West Jordan", "state": "UT", "lat": 40.6097, "lng": -111.9391},
    {"city": "Murrieta", "state": "CA", "lat": 33.5539, "lng": -117.2139},
    {"city": "Palm Bay", "state": "FL", "lat": 28.0345, "lng": -80.5887},
    {"city": "El Paso de Robles", "state": "CA", "lat": 35.6266, "lng": -120.6910},
    {"city": "Carlsbad", "state": "CA", "lat": 33.1581, "lng": -117.3506},
    {"city": "Temecula", "state": "CA", "lat": 33.4936, "lng": -117.1484},
    {"city": "Costa Mesa", "state": "CA", "lat": 33.6411, "lng": -117.9187},
    {"city": "Westminster", "state": "CO", "lat": 39.8367, "lng": -105.0372},
    {"city": "North Charleston", "state": "SC", "lat": 32.8546, "lng": -79.9748},
    {"city": "Manchester", "state": "NH", "lat": 42.9956, "lng": -71.4548},
    {"city": "Hillsboro", "state": "OR", "lat": 45.5229, "lng": -122.9898},
    {"city": "Gresham", "state": "OR", "lat": 45.4998, "lng": -122.4310},
    {"city": "Billings", "state": "MT", "lat": 45.7833, "lng": -108.5007},
    {"city": "Greeley", "state": "CO", "lat": 40.4233, "lng": -104.7091},
    {"city": "Downey", "state": "CA", "lat": 33.9401, "lng": -118.1332},
    {"city": "Waterbury", "state": "CT", "lat": 41.5582, "lng": -73.0515},
    {"city": "League City", "state": "TX", "lat": 29.5075, "lng": -95.0949},
    {"city": "Pueblo", "state": "CO", "lat": 38.2544, "lng": -104.6091},
    {"city": "Santa Maria", "state": "CA", "lat": 34.9530, "lng": -120.4357},
    {"city": "El Monte", "state": "CA", "lat": 34.0686, "lng": -118.0276},
]


def generate_grid_jobs(
    keyword: str,
    bbox: BoundingBox,
    step_deg: float = 0.08,  # ~5.5 miles / 9 km grid spacing (optimal for zoom 14z)
    zoom_level: int = 14,
) -> List[SearchJob]:
    """Generates a matrix of coordinate search jobs covering a bounding box."""
    jobs: List[SearchJob] = []

    lat = bbox.min_lat + (step_deg / 2.0)
    row = 0
    while lat <= bbox.max_lat:
        lng = bbox.min_lng + (step_deg / 2.0)
        col = 0
        while lng <= bbox.max_lng:
            location_label = f"Grid ({lat:.4f}, {lng:.4f})"
            jobs.append(
                SearchJob(
                    keyword=keyword,
                    location_name=location_label,
                    latitude=round(lat, 5),
                    longitude=round(lng, 5),
                    zoom_level=zoom_level,
                    bounding_box=f"{bbox.min_lat:.4f},{bbox.min_lng:.4f},{bbox.max_lat:.4f},{bbox.max_lng:.4f}",
                )
            )
            lng += step_deg
            col += 1
        lat += step_deg
        row += 1

    return jobs


def generate_city_jobs(
    keyword: str,
    state_filter: Optional[str] = None,
    custom_cities: Optional[List[str]] = None,
) -> List[SearchJob]:
    """Generates search jobs targeting designated U.S. cities."""
    jobs: List[SearchJob] = []

    if custom_cities:
        for item in custom_cities:
            jobs.append(
                SearchJob(
                    keyword=keyword,
                    location_name=item,
                    zoom_level=13,
                )
            )
        return jobs

    for city_data in TOP_US_CITIES:
        if state_filter and city_data["state"].upper() != state_filter.upper():
            continue

        label = f"{city_data['city']}, {city_data['state']}"
        jobs.append(
            SearchJob(
                keyword=keyword,
                location_name=label,
                latitude=city_data["lat"],
                longitude=city_data["lng"],
                zoom_level=13,
            )
        )

    return jobs


def generate_state_grid_jobs(
    keyword: str,
    state_code: str,
    step_deg: float = 0.10,
) -> List[SearchJob]:
    """Generates a coordinate grid of search jobs for an entire U.S. State."""
    state_code = state_code.upper().strip()
    if state_code not in US_STATE_BOUNDS:
        raise ValueError(f"Unknown state code '{state_code}'. Must be valid 2-letter US State abbreviation.")

    bbox = US_STATE_BOUNDS[state_code]
    return generate_grid_jobs(keyword=keyword, bbox=bbox, step_deg=step_deg, zoom_level=14)


def generate_multi_category_city_jobs(
    keywords: List[str],
    state_filter: Optional[str] = None,
    custom_cities: Optional[List[str]] = None,
    limit_jobs: Optional[int] = None,
) -> List[SearchJob]:
    """Generates Cartesian product of (Keywords × Cities) up to an optional limit."""
    all_jobs: List[SearchJob] = []
    for kw in keywords:
        city_jobs = generate_city_jobs(keyword=kw, state_filter=state_filter, custom_cities=custom_cities)
        for j in city_jobs:
            all_jobs.append(j)
            if limit_jobs and len(all_jobs) >= limit_jobs:
                return all_jobs
    return all_jobs


def generate_multi_category_state_jobs(
    keywords: List[str],
    state_code: str,
    step_deg: float = 0.10,
    limit_jobs: Optional[int] = None,
) -> List[SearchJob]:
    """Generates Cartesian product of (Keywords × State Coordinate Matrix)."""
    all_jobs: List[SearchJob] = []
    for kw in keywords:
        grid_jobs = generate_state_grid_jobs(keyword=kw, state_code=state_code, step_deg=step_deg)
        for j in grid_jobs:
            all_jobs.append(j)
            if limit_jobs and len(all_jobs) >= limit_jobs:
                return all_jobs
    return all_jobs
