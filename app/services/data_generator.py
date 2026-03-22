import math
import random
from datetime import date, datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Airport, Airline, Flight


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


AIRPORTS = [
    {"iata": "JFK", "name": "John F. Kennedy International", "city": "New York", "country": "US", "lat": 40.6413, "lon": -73.7781, "tz": "America/New_York"},
    {"iata": "LAX", "name": "Los Angeles International", "city": "Los Angeles", "country": "US", "lat": 33.9425, "lon": -118.4081, "tz": "America/Los_Angeles"},
    {"iata": "ORD", "name": "O'Hare International", "city": "Chicago", "country": "US", "lat": 41.9742, "lon": -87.9073, "tz": "America/Chicago"},
    {"iata": "ATL", "name": "Hartsfield-Jackson Atlanta International", "city": "Atlanta", "country": "US", "lat": 33.6407, "lon": -84.4277, "tz": "America/New_York"},
    {"iata": "DFW", "name": "Dallas/Fort Worth International", "city": "Dallas", "country": "US", "lat": 32.8998, "lon": -97.0403, "tz": "America/Chicago"},
    {"iata": "DEN", "name": "Denver International", "city": "Denver", "country": "US", "lat": 39.8561, "lon": -104.6737, "tz": "America/Denver"},
    {"iata": "SFO", "name": "San Francisco International", "city": "San Francisco", "country": "US", "lat": 37.6213, "lon": -122.379, "tz": "America/Los_Angeles"},
    {"iata": "SEA", "name": "Seattle-Tacoma International", "city": "Seattle", "country": "US", "lat": 47.4502, "lon": -122.3088, "tz": "America/Los_Angeles"},
    {"iata": "MIA", "name": "Miami International", "city": "Miami", "country": "US", "lat": 25.7959, "lon": -80.287, "tz": "America/New_York"},
    {"iata": "BOS", "name": "Logan International", "city": "Boston", "country": "US", "lat": 42.3656, "lon": -71.0096, "tz": "America/New_York"},
    {"iata": "LAS", "name": "Harry Reid International", "city": "Las Vegas", "country": "US", "lat": 36.084, "lon": -115.1537, "tz": "America/Los_Angeles"},
    {"iata": "PHX", "name": "Phoenix Sky Harbor International", "city": "Phoenix", "country": "US", "lat": 33.4373, "lon": -112.0078, "tz": "America/Phoenix"},
    {"iata": "MCO", "name": "Orlando International", "city": "Orlando", "country": "US", "lat": 28.4294, "lon": -81.309, "tz": "America/New_York"},
    {"iata": "EWR", "name": "Newark Liberty International", "city": "Newark", "country": "US", "lat": 40.6895, "lon": -74.1745, "tz": "America/New_York"},
    {"iata": "YYZ", "name": "Toronto Pearson International", "city": "Toronto", "country": "CA", "lat": 43.6777, "lon": -79.6248, "tz": "America/Toronto"},
    {"iata": "YVR", "name": "Vancouver International", "city": "Vancouver", "country": "CA", "lat": 49.1947, "lon": -123.1792, "tz": "America/Vancouver"},
    {"iata": "MEX", "name": "Benito Juarez International", "city": "Mexico City", "country": "MX", "lat": 19.4363, "lon": -99.0721, "tz": "America/Mexico_City"},
    {"iata": "GRU", "name": "Guarulhos International", "city": "Sao Paulo", "country": "BR", "lat": -23.4356, "lon": -46.4731, "tz": "America/Sao_Paulo"},
    {"iata": "EZE", "name": "Ministro Pistarini International", "city": "Buenos Aires", "country": "AR", "lat": -34.8222, "lon": -58.5358, "tz": "America/Argentina/Buenos_Aires"},
    {"iata": "LHR", "name": "Heathrow Airport", "city": "London", "country": "GB", "lat": 51.477, "lon": -0.4613, "tz": "Europe/London"},
    {"iata": "CDG", "name": "Charles de Gaulle Airport", "city": "Paris", "country": "FR", "lat": 49.0097, "lon": 2.5479, "tz": "Europe/Paris"},
    {"iata": "FRA", "name": "Frankfurt Airport", "city": "Frankfurt", "country": "DE", "lat": 50.0379, "lon": 8.5622, "tz": "Europe/Berlin"},
    {"iata": "AMS", "name": "Amsterdam Schiphol", "city": "Amsterdam", "country": "NL", "lat": 52.3105, "lon": 4.7683, "tz": "Europe/Amsterdam"},
    {"iata": "MAD", "name": "Adolfo Suarez Madrid-Barajas", "city": "Madrid", "country": "ES", "lat": 40.4936, "lon": -3.5668, "tz": "Europe/Madrid"},
    {"iata": "FCO", "name": "Leonardo da Vinci International", "city": "Rome", "country": "IT", "lat": 41.8003, "lon": 12.2389, "tz": "Europe/Rome"},
    {"iata": "IST", "name": "Istanbul Airport", "city": "Istanbul", "country": "TR", "lat": 41.2753, "lon": 28.7519, "tz": "Europe/Istanbul"},
    {"iata": "ZRH", "name": "Zurich Airport", "city": "Zurich", "country": "CH", "lat": 47.4647, "lon": 8.5492, "tz": "Europe/Zurich"},
    {"iata": "BCN", "name": "Barcelona El Prat", "city": "Barcelona", "country": "ES", "lat": 41.2974, "lon": 2.0833, "tz": "Europe/Madrid"},
    {"iata": "MUC", "name": "Munich Airport", "city": "Munich", "country": "DE", "lat": 48.3538, "lon": 11.7861, "tz": "Europe/Berlin"},
    {"iata": "CPH", "name": "Copenhagen Airport", "city": "Copenhagen", "country": "DK", "lat": 55.6180, "lon": 12.6508, "tz": "Europe/Copenhagen"},
    {"iata": "DXB", "name": "Dubai International", "city": "Dubai", "country": "AE", "lat": 25.2532, "lon": 55.3657, "tz": "Asia/Dubai"},
    {"iata": "AUH", "name": "Abu Dhabi International", "city": "Abu Dhabi", "country": "AE", "lat": 24.4430, "lon": 54.6511, "tz": "Asia/Dubai"},
    {"iata": "DOH", "name": "Hamad International", "city": "Doha", "country": "QA", "lat": 25.2731, "lon": 51.6080, "tz": "Asia/Qatar"},
    {"iata": "JNB", "name": "O.R. Tambo International", "city": "Johannesburg", "country": "ZA", "lat": -26.1336, "lon": 28.2420, "tz": "Africa/Johannesburg"},
    {"iata": "CAI", "name": "Cairo International", "city": "Cairo", "country": "EG", "lat": 30.1219, "lon": 31.4056, "tz": "Africa/Cairo"},
    {"iata": "NBO", "name": "Jomo Kenyatta International", "city": "Nairobi", "country": "KE", "lat": -1.3192, "lon": 36.9275, "tz": "Africa/Nairobi"},
    {"iata": "NRT", "name": "Narita International", "city": "Tokyo", "country": "JP", "lat": 35.7647, "lon": 140.3864, "tz": "Asia/Tokyo"},
    {"iata": "HND", "name": "Haneda Airport", "city": "Tokyo", "country": "JP", "lat": 35.5494, "lon": 139.7798, "tz": "Asia/Tokyo"},
    {"iata": "ICN", "name": "Incheon International", "city": "Seoul", "country": "KR", "lat": 37.4602, "lon": 126.4407, "tz": "Asia/Seoul"},
    {"iata": "PEK", "name": "Beijing Capital International", "city": "Beijing", "country": "CN", "lat": 40.0799, "lon": 116.6031, "tz": "Asia/Shanghai"},
    {"iata": "PVG", "name": "Shanghai Pudong International", "city": "Shanghai", "country": "CN", "lat": 31.1443, "lon": 121.8083, "tz": "Asia/Shanghai"},
    {"iata": "HKG", "name": "Hong Kong International", "city": "Hong Kong", "country": "HK", "lat": 22.3080, "lon": 113.9185, "tz": "Asia/Hong_Kong"},
    {"iata": "SIN", "name": "Changi Airport", "city": "Singapore", "country": "SG", "lat": 1.3644, "lon": 103.9915, "tz": "Asia/Singapore"},
    {"iata": "BKK", "name": "Suvarnabhumi Airport", "city": "Bangkok", "country": "TH", "lat": 13.6900, "lon": 100.7501, "tz": "Asia/Bangkok"},
    {"iata": "KUL", "name": "Kuala Lumpur International", "city": "Kuala Lumpur", "country": "MY", "lat": 2.7456, "lon": 101.7099, "tz": "Asia/Kuala_Lumpur"},
    {"iata": "CGK", "name": "Soekarno-Hatta International", "city": "Jakarta", "country": "ID", "lat": -6.1275, "lon": 106.6537, "tz": "Asia/Jakarta"},
    {"iata": "DEL", "name": "Indira Gandhi International", "city": "New Delhi", "country": "IN", "lat": 28.5562, "lon": 77.1000, "tz": "Asia/Kolkata"},
    {"iata": "BOM", "name": "Chhatrapati Shivaji International", "city": "Mumbai", "country": "IN", "lat": 19.0896, "lon": 72.8656, "tz": "Asia/Kolkata"},
    {"iata": "BLR", "name": "Kempegowda International", "city": "Bengaluru", "country": "IN", "lat": 13.1986, "lon": 77.7066, "tz": "Asia/Kolkata"},
    {"iata": "HYD", "name": "Rajiv Gandhi International", "city": "Hyderabad", "country": "IN", "lat": 17.2403, "lon": 78.4294, "tz": "Asia/Kolkata"},
    {"iata": "MAA", "name": "Chennai International", "city": "Chennai", "country": "IN", "lat": 12.9941, "lon": 80.1709, "tz": "Asia/Kolkata"},
    {"iata": "CCU", "name": "Netaji Subhas Chandra Bose International", "city": "Kolkata", "country": "IN", "lat": 22.6520, "lon": 88.4463, "tz": "Asia/Kolkata"},
    {"iata": "GOI", "name": "Goa International (Manohar Parrikar)", "city": "Goa", "country": "IN", "lat": 15.3808, "lon": 73.8314, "tz": "Asia/Kolkata"},
    {"iata": "COK", "name": "Cochin International", "city": "Kochi", "country": "IN", "lat": 10.1520, "lon": 76.4019, "tz": "Asia/Kolkata"},
    {"iata": "PNQ", "name": "Pune Airport", "city": "Pune", "country": "IN", "lat": 18.5822, "lon": 73.9197, "tz": "Asia/Kolkata"},
    {"iata": "AMD", "name": "Sardar Vallabhbhai Patel International", "city": "Ahmedabad", "country": "IN", "lat": 23.0772, "lon": 72.6347, "tz": "Asia/Kolkata"},
    {"iata": "JAI", "name": "Jaipur International", "city": "Jaipur", "country": "IN", "lat": 26.8242, "lon": 75.8122, "tz": "Asia/Kolkata"},
    {"iata": "GAU", "name": "Lokpriya Gopinath Bordoloi International", "city": "Guwahati", "country": "IN", "lat": 26.1061, "lon": 91.5859, "tz": "Asia/Kolkata"},
    {"iata": "IXC", "name": "Chandigarh International", "city": "Chandigarh", "country": "IN", "lat": 30.6735, "lon": 76.7885, "tz": "Asia/Kolkata"},
    {"iata": "SYD", "name": "Sydney Kingsford Smith", "city": "Sydney", "country": "AU", "lat": -33.9399, "lon": 151.1753, "tz": "Australia/Sydney"},
    {"iata": "MEL", "name": "Melbourne Airport", "city": "Melbourne", "country": "AU", "lat": -37.6690, "lon": 144.8410, "tz": "Australia/Melbourne"},
    {"iata": "AKL", "name": "Auckland Airport", "city": "Auckland", "country": "NZ", "lat": -37.0082, "lon": 174.7850, "tz": "Pacific/Auckland"},
    {"iata": "MNL", "name": "Ninoy Aquino International", "city": "Manila", "country": "PH", "lat": 14.5086, "lon": 121.0197, "tz": "Asia/Manila"},
]

AIRLINES = [
    {"iata": "AA", "name": "American Airlines", "color": "#0078D2", "country": "US"},
    {"iata": "UA", "name": "United Airlines", "color": "#0056A3", "country": "US"},
    {"iata": "DL", "name": "Delta Air Lines", "color": "#E01933", "country": "US"},
    {"iata": "WN", "name": "Southwest Airlines", "color": "#304CB2", "country": "US"},
    {"iata": "AS", "name": "Alaska Airlines", "color": "#00577B", "country": "US"},
    {"iata": "B6", "name": "JetBlue Airways", "color": "#003876", "country": "US"},
    {"iata": "F9", "name": "Frontier Airlines", "color": "#008F00", "country": "US"},
    {"iata": "NK", "name": "Spirit Airlines", "color": "#FFD700", "country": "US"},
    {"iata": "BA", "name": "British Airways", "color": "#075AAA", "country": "GB"},
    {"iata": "LH", "name": "Lufthansa", "color": "#0066B3", "country": "DE"},
    {"iata": "AF", "name": "Air France", "color": "#002395", "country": "FR"},
    {"iata": "KL", "name": "KLM Royal Dutch Airlines", "color": "#009FDF", "country": "NL"},
    {"iata": "IB", "name": "Iberia", "color": "#CC0000", "country": "ES"},
    {"iata": "AZ", "name": "ITA Airways", "color": "#006DB7", "country": "IT"},
    {"iata": "TK", "name": "Turkish Airlines", "color": "#C70A0A", "country": "TR"},
    {"iata": "LX", "name": "Swiss International Air Lines", "color": "#B22222", "country": "CH"},
    {"iata": "SK", "name": "Scandinavian Airlines", "color": "#0C3C8E", "country": "SE"},
    {"iata": "EK", "name": "Emirates", "color": "#D71921", "country": "AE"},
    {"iata": "EY", "name": "Etihad Airways", "color": "#BD8B13", "country": "AE"},
    {"iata": "QR", "name": "Qatar Airways", "color": "#5C0632", "country": "QA"},
    {"iata": "SQ", "name": "Singapore Airlines", "color": "#0A3A69", "country": "SG"},
    {"iata": "CX", "name": "Cathay Pacific", "color": "#006564", "country": "HK"},
    {"iata": "NH", "name": "All Nippon Airways", "color": "#1B2E8C", "country": "JP"},
    {"iata": "JL", "name": "Japan Airlines", "color": "#CC0000", "country": "JP"},
    {"iata": "KE", "name": "Korean Air", "color": "#00235C", "country": "KR"},
    {"iata": "CA", "name": "Air China", "color": "#CC0000", "country": "CN"},
    {"iata": "MH", "name": "Malaysia Airlines", "color": "#CC0000", "country": "MY"},
    {"iata": "TG", "name": "Thai Airways", "color": "#8B008B", "country": "TH"},
    {"iata": "AI", "name": "Air India", "color": "#FF6B00", "country": "IN"},
    {"iata": "6E", "name": "IndiGo", "color": "#0033A0", "country": "IN"},
    {"iata": "SG", "name": "SpiceJet", "color": "#FF0000", "country": "IN"},
    {"iata": "UK", "name": "Vistara", "color": "#4A154B", "country": "IN"},
    {"iata": "QP", "name": "Akasa Air", "color": "#FF6F00", "country": "IN"},
    {"iata": "IX", "name": "Air India Express", "color": "#E53935", "country": "IN"},
    {"iata": "QF", "name": "Qantas", "color": "#E40000", "country": "AU"},
    {"iata": "AC", "name": "Air Canada", "color": "#CC0000", "country": "CA"},
    {"iata": "AM", "name": "Aeromexico", "color": "#006BB6", "country": "MX"},
    {"iata": "LA", "name": "LATAM Airlines", "color": "#E3051B", "country": "CL"},
]

ROUTES = [
    # US domestic
    ("JFK", "LAX", "AA"), ("LAX", "JFK", "AA"),
    ("JFK", "SFO", "UA"), ("SFO", "JFK", "UA"),
    ("JFK", "ORD", "AA"), ("ORD", "JFK", "AA"),
    ("JFK", "MIA", "AA"), ("MIA", "JFK", "AA"),
    ("JFK", "BOS", "B6"), ("BOS", "JFK", "B6"),
    ("JFK", "ATL", "DL"), ("ATL", "JFK", "DL"),
    ("LAX", "SFO", "AS"), ("SFO", "LAX", "AS"),
    ("LAX", "ORD", "UA"), ("ORD", "LAX", "UA"),
    ("LAX", "LAS", "WN"), ("LAS", "LAX", "WN"),
    ("LAX", "SEA", "AS"), ("SEA", "LAX", "AS"),
    ("LAX", "DEN", "F9"), ("DEN", "LAX", "F9"),
    ("LAX", "PHX", "WN"), ("PHX", "LAX", "WN"),
    ("LAX", "ATL", "DL"), ("ATL", "LAX", "DL"),
    ("ORD", "ATL", "UA"), ("ATL", "ORD", "UA"),
    ("ORD", "MIA", "AA"), ("MIA", "ORD", "AA"),
    ("ORD", "DFW", "AA"), ("DFW", "ORD", "AA"),
    ("ATL", "MIA", "DL"), ("MIA", "ATL", "DL"),
    ("ATL", "DFW", "AA"), ("DFW", "ATL", "AA"),
    ("SFO", "SEA", "AS"), ("SEA", "SFO", "AS"),
    ("SFO", "ORD", "UA"), ("ORD", "SFO", "UA"),
    ("BOS", "MIA", "B6"), ("MIA", "BOS", "B6"),
    ("BOS", "ORD", "AA"), ("ORD", "BOS", "AA"),
    ("DFW", "LAX", "AA"), ("LAX", "DFW", "AA"),
    ("DFW", "DEN", "UA"), ("DEN", "DFW", "UA"),
    ("MCO", "JFK", "B6"), ("JFK", "MCO", "B6"),
    ("MCO", "BOS", "B6"), ("BOS", "MCO", "B6"),
    ("MCO", "ATL", "DL"), ("ATL", "MCO", "DL"),
    ("LAS", "JFK", "B6"), ("JFK", "LAS", "B6"),
    ("LAS", "ORD", "WN"), ("ORD", "LAS", "WN"),
    ("EWR", "LAX", "UA"), ("LAX", "EWR", "UA"),
    ("EWR", "MIA", "UA"), ("MIA", "EWR", "UA"),
    # US-Canada
    ("JFK", "YYZ", "AC"), ("YYZ", "JFK", "AC"),
    ("LAX", "YVR", "AC"), ("YVR", "LAX", "AC"),
    ("ORD", "YYZ", "AC"), ("YYZ", "ORD", "AC"),
    # US-Europe transatlantic
    ("JFK", "LHR", "BA"), ("LHR", "JFK", "BA"),
    ("JFK", "CDG", "AF"), ("CDG", "JFK", "AF"),
    ("JFK", "FRA", "LH"), ("FRA", "JFK", "LH"),
    ("JFK", "AMS", "KL"), ("AMS", "JFK", "KL"),
    ("JFK", "MAD", "IB"), ("MAD", "JFK", "IB"),
    ("JFK", "IST", "TK"), ("IST", "JFK", "TK"),
    ("LAX", "LHR", "BA"), ("LHR", "LAX", "BA"),
    ("LAX", "CDG", "AF"), ("CDG", "LAX", "AF"),
    ("LAX", "FRA", "LH"), ("FRA", "LAX", "LH"),
    ("BOS", "LHR", "BA"), ("LHR", "BOS", "BA"),
    ("ORD", "LHR", "BA"), ("LHR", "ORD", "BA"),
    ("ORD", "FRA", "LH"), ("FRA", "ORD", "LH"),
    ("MIA", "LHR", "BA"), ("LHR", "MIA", "BA"),
    ("EWR", "LHR", "UA"), ("LHR", "EWR", "UA"),
    # Intra-Europe
    ("LHR", "CDG", "BA"), ("CDG", "LHR", "AF"),
    ("LHR", "FRA", "BA"), ("FRA", "LHR", "LH"),
    ("LHR", "AMS", "BA"), ("AMS", "LHR", "KL"),
    ("LHR", "MAD", "IB"), ("MAD", "LHR", "IB"),
    ("LHR", "FCO", "BA"), ("FCO", "LHR", "AZ"),
    ("LHR", "ZRH", "LX"), ("ZRH", "LHR", "LX"),
    ("CDG", "FRA", "AF"), ("FRA", "CDG", "LH"),
    ("CDG", "AMS", "AF"), ("AMS", "CDG", "KL"),
    ("CDG", "MAD", "AF"), ("MAD", "CDG", "IB"),
    ("CDG", "FCO", "AF"), ("FCO", "CDG", "AZ"),
    ("CDG", "BCN", "AF"), ("BCN", "CDG", "IB"),
    ("FRA", "AMS", "LH"), ("AMS", "FRA", "KL"),
    ("FRA", "MAD", "LH"), ("MAD", "FRA", "IB"),
    ("FRA", "FCO", "LH"), ("FCO", "FRA", "AZ"),
    ("FRA", "IST", "TK"), ("IST", "FRA", "TK"),
    ("FRA", "MUC", "LH"), ("MUC", "FRA", "LH"),
    ("AMS", "BCN", "KL"), ("BCN", "AMS", "IB"),
    ("MAD", "BCN", "IB"), ("BCN", "MAD", "IB"),
    ("MAD", "FCO", "IB"), ("FCO", "MAD", "AZ"),
    ("LHR", "IST", "BA"), ("IST", "LHR", "TK"),
    ("LHR", "MUC", "BA"), ("MUC", "LHR", "LH"),
    ("LHR", "CPH", "BA"), ("CPH", "LHR", "SK"),
    # Middle East
    ("DXB", "LHR", "EK"), ("LHR", "DXB", "EK"),
    ("DXB", "JFK", "EK"), ("JFK", "DXB", "EK"),
    ("DXB", "LAX", "EK"), ("LAX", "DXB", "EK"),
    ("DXB", "SIN", "EK"), ("SIN", "DXB", "EK"),
    ("DXB", "BKK", "EK"), ("BKK", "DXB", "EK"),
    ("DXB", "SYD", "EK"), ("SYD", "DXB", "EK"),
    ("DXB", "NRT", "EK"), ("NRT", "DXB", "EK"),
    ("DXB", "DEL", "EK"), ("DEL", "DXB", "EK"),
    ("DOH", "LHR", "QR"), ("LHR", "DOH", "QR"),
    ("DOH", "JFK", "QR"), ("JFK", "DOH", "QR"),
    ("DOH", "SIN", "QR"), ("SIN", "DOH", "QR"),
    ("DOH", "SYD", "QR"), ("SYD", "DOH", "QR"),
    ("AUH", "LHR", "EY"), ("LHR", "AUH", "EY"),
    ("AUH", "JFK", "EY"), ("JFK", "AUH", "EY"),
    ("IST", "DXB", "TK"), ("DXB", "IST", "TK"),
    # Asia
    ("SIN", "LHR", "SQ"), ("LHR", "SIN", "SQ"),
    ("SIN", "JFK", "SQ"), ("JFK", "SIN", "SQ"),
    ("SIN", "LAX", "SQ"), ("LAX", "SIN", "SQ"),
    ("SIN", "NRT", "SQ"), ("NRT", "SIN", "SQ"),
    ("SIN", "HKG", "SQ"), ("HKG", "SIN", "CX"),
    ("SIN", "BKK", "SQ"), ("BKK", "SIN", "TG"),
    ("SIN", "KUL", "SQ"), ("KUL", "SIN", "MH"),
    ("SIN", "CGK", "SQ"), ("CGK", "SIN", "MH"),
    ("SIN", "DEL", "SQ"), ("DEL", "SIN", "AI"),
    ("SIN", "SYD", "SQ"), ("SYD", "SIN", "QF"),
    ("HKG", "LHR", "CX"), ("LHR", "HKG", "CX"),
    ("HKG", "JFK", "CX"), ("JFK", "HKG", "CX"),
    ("HKG", "LAX", "CX"), ("LAX", "HKG", "CX"),
    ("HKG", "NRT", "CX"), ("NRT", "HKG", "NH"),
    ("HKG", "ICN", "CX"), ("ICN", "HKG", "KE"),
    ("HKG", "SYD", "CX"), ("SYD", "HKG", "QF"),
    ("NRT", "LAX", "NH"), ("LAX", "NRT", "NH"),
    ("NRT", "JFK", "NH"), ("JFK", "NRT", "JL"),
    ("NRT", "LHR", "JL"), ("LHR", "NRT", "JL"),
    ("NRT", "SFO", "NH"), ("SFO", "NRT", "UA"),
    ("NRT", "ICN", "JL"), ("ICN", "NRT", "KE"),
    ("NRT", "PEK", "JL"), ("PEK", "NRT", "CA"),
    ("ICN", "LAX", "KE"), ("LAX", "ICN", "KE"),
    ("ICN", "JFK", "KE"), ("JFK", "ICN", "KE"),
    ("ICN", "LHR", "KE"), ("LHR", "ICN", "BA"),
    ("PEK", "JFK", "CA"), ("JFK", "PEK", "UA"),
    ("PEK", "LAX", "CA"), ("LAX", "PEK", "CA"),
    ("PEK", "LHR", "CA"), ("LHR", "PEK", "BA"),
    ("PVG", "LAX", "CA"), ("LAX", "PVG", "UA"),
    ("PVG", "JFK", "CA"), ("JFK", "PVG", "DL"),
    ("DEL", "LHR", "AI"), ("LHR", "DEL", "BA"),
    ("DEL", "JFK", "AI"), ("JFK", "DEL", "UA"),
    ("BOM", "LHR", "AI"), ("LHR", "BOM", "BA"),
    ("BOM", "DXB", "EK"), ("DXB", "BOM", "EK"),
    ("BOM", "SIN", "SQ"), ("SIN", "BOM", "SQ"),
    ("BLR", "SIN", "SQ"), ("SIN", "BLR", "SQ"),
    # Australia/Pacific
    ("SYD", "LAX", "QF"), ("LAX", "SYD", "QF"),
    ("SYD", "JFK", "QF"), ("JFK", "SYD", "AA"),
    ("SYD", "LHR", "QF"), ("LHR", "SYD", "BA"),
    ("SYD", "MEL", "QF"), ("MEL", "SYD", "QF"),
    ("SYD", "AKL", "QF"), ("AKL", "SYD", "QF"),
    ("MEL", "LAX", "QF"), ("LAX", "MEL", "QF"),
    ("MEL", "AKL", "QF"), ("AKL", "MEL", "QF"),
    # Africa/Americas
    ("JNB", "LHR", "BA"), ("LHR", "JNB", "BA"),
    ("JNB", "DXB", "EK"), ("DXB", "JNB", "EK"),
    ("NBO", "LHR", "BA"), ("LHR", "NBO", "BA"),
    ("CAI", "LHR", "BA"), ("LHR", "CAI", "BA"),
    ("CAI", "DXB", "EK"), ("DXB", "CAI", "EK"),
    ("GRU", "JFK", "LA"), ("JFK", "GRU", "AA"),
    ("GRU", "LHR", "LA"), ("LHR", "GRU", "BA"),
    ("EZE", "JFK", "LA"), ("JFK", "EZE", "AA"),
    ("MEX", "JFK", "AM"), ("JFK", "MEX", "AA"),
    ("MEX", "LAX", "AM"), ("LAX", "MEX", "AA"),
    # Canada
    ("YYZ", "LHR", "AC"), ("LHR", "YYZ", "AC"),
    ("YVR", "LHR", "AC"), ("LHR", "YVR", "AC"),
    ("YYZ", "CDG", "AC"), ("CDG", "YYZ", "AC"),
    # Indian domestic - DEL routes
    ("DEL", "BOM", "6E"), ("BOM", "DEL", "6E"),
    ("DEL", "BOM", "AI"), ("BOM", "DEL", "AI"),
    ("DEL", "BOM", "SG"), ("BOM", "DEL", "SG"),
    ("DEL", "BOM", "QP"), ("BOM", "DEL", "QP"),
    ("DEL", "BLR", "6E"), ("BLR", "DEL", "6E"),
    ("DEL", "BLR", "AI"), ("BLR", "DEL", "AI"),
    ("DEL", "BLR", "SG"), ("BLR", "DEL", "SG"),
    ("DEL", "HYD", "6E"), ("HYD", "DEL", "6E"),
    ("DEL", "HYD", "AI"), ("HYD", "DEL", "AI"),
    ("DEL", "HYD", "SG"), ("HYD", "DEL", "SG"),
    ("DEL", "MAA", "6E"), ("MAA", "DEL", "6E"),
    ("DEL", "MAA", "AI"), ("MAA", "DEL", "AI"),
    ("DEL", "MAA", "SG"), ("MAA", "DEL", "SG"),
    ("DEL", "CCU", "6E"), ("CCU", "DEL", "6E"),
    ("DEL", "CCU", "AI"), ("CCU", "DEL", "AI"),
    ("DEL", "CCU", "SG"), ("CCU", "DEL", "SG"),
    ("DEL", "GOI", "6E"), ("GOI", "DEL", "6E"),
    ("DEL", "GOI", "SG"), ("GOI", "DEL", "SG"),
    ("DEL", "GOI", "QP"), ("GOI", "DEL", "QP"),
    ("DEL", "COK", "6E"), ("COK", "DEL", "6E"),
    ("DEL", "COK", "AI"), ("COK", "DEL", "AI"),
    ("DEL", "PNQ", "6E"), ("PNQ", "DEL", "6E"),
    ("DEL", "PNQ", "SG"), ("PNQ", "DEL", "SG"),
    ("DEL", "AMD", "6E"), ("AMD", "DEL", "6E"),
    ("DEL", "AMD", "SG"), ("AMD", "DEL", "SG"),
    ("DEL", "AMD", "QP"), ("AMD", "DEL", "QP"),
    ("DEL", "JAI", "6E"), ("JAI", "DEL", "6E"),
    ("DEL", "JAI", "SG"), ("JAI", "DEL", "SG"),
    ("DEL", "GAU", "6E"), ("GAU", "DEL", "6E"),
    ("DEL", "GAU", "AI"), ("GAU", "DEL", "AI"),
    ("DEL", "IXC", "6E"), ("IXC", "DEL", "6E"),
    ("DEL", "IXC", "SG"), ("IXC", "DEL", "SG"),
    # Indian domestic - BOM routes
    ("BOM", "BLR", "6E"), ("BLR", "BOM", "6E"),
    ("BOM", "BLR", "AI"), ("BLR", "BOM", "AI"),
    ("BOM", "BLR", "SG"), ("BLR", "BOM", "SG"),
    ("BOM", "BLR", "QP"), ("BLR", "BOM", "QP"),
    ("BOM", "HYD", "6E"), ("HYD", "BOM", "6E"),
    ("BOM", "HYD", "AI"), ("HYD", "BOM", "AI"),
    ("BOM", "HYD", "SG"), ("HYD", "BOM", "SG"),
    ("BOM", "MAA", "6E"), ("MAA", "BOM", "6E"),
    ("BOM", "MAA", "AI"), ("MAA", "BOM", "AI"),
    ("BOM", "MAA", "SG"), ("MAA", "BOM", "SG"),
    ("BOM", "CCU", "6E"), ("CCU", "BOM", "6E"),
    ("BOM", "CCU", "AI"), ("CCU", "BOM", "AI"),
    ("BOM", "GOI", "6E"), ("GOI", "BOM", "6E"),
    ("BOM", "GOI", "SG"), ("GOI", "BOM", "SG"),
    ("BOM", "GOI", "QP"), ("GOI", "BOM", "QP"),
    ("BOM", "GOI", "IX"), ("GOI", "BOM", "IX"),
    ("BOM", "COK", "6E"), ("COK", "BOM", "6E"),
    ("BOM", "COK", "AI"), ("COK", "BOM", "AI"),
    ("BOM", "COK", "IX"), ("COK", "BOM", "IX"),
    ("BOM", "PNQ", "6E"), ("PNQ", "BOM", "6E"),
    ("BOM", "PNQ", "SG"), ("PNQ", "BOM", "SG"),
    ("BOM", "AMD", "6E"), ("AMD", "BOM", "6E"),
    ("BOM", "AMD", "SG"), ("AMD", "BOM", "SG"),
    ("BOM", "JAI", "6E"), ("JAI", "BOM", "6E"),
    ("BOM", "JAI", "SG"), ("JAI", "BOM", "SG"),
    # Indian domestic - BLR routes
    ("BLR", "HYD", "6E"), ("HYD", "BLR", "6E"),
    ("BLR", "HYD", "SG"), ("HYD", "BLR", "SG"),
    ("BLR", "MAA", "6E"), ("MAA", "BLR", "6E"),
    ("BLR", "MAA", "SG"), ("MAA", "BLR", "SG"),
    ("BLR", "MAA", "AI"), ("MAA", "BLR", "AI"),
    ("BLR", "CCU", "6E"), ("CCU", "BLR", "6E"),
    ("BLR", "CCU", "AI"), ("CCU", "BLR", "AI"),
    ("BLR", "GOI", "6E"), ("GOI", "BLR", "6E"),
    ("BLR", "GOI", "SG"), ("GOI", "BLR", "SG"),
    ("BLR", "COK", "6E"), ("COK", "BLR", "6E"),
    ("BLR", "COK", "AI"), ("COK", "BLR", "AI"),
    ("BLR", "COK", "IX"), ("COK", "BLR", "IX"),
    ("BLR", "PNQ", "6E"), ("PNQ", "BLR", "6E"),
    ("BLR", "PNQ", "SG"), ("PNQ", "BLR", "SG"),
    # Indian domestic - other city pairs
    ("HYD", "MAA", "6E"), ("MAA", "HYD", "6E"),
    ("HYD", "MAA", "SG"), ("MAA", "HYD", "SG"),
    ("HYD", "CCU", "6E"), ("CCU", "HYD", "6E"),
    ("HYD", "CCU", "AI"), ("CCU", "HYD", "AI"),
    ("HYD", "GOI", "6E"), ("GOI", "HYD", "6E"),
    ("HYD", "GOI", "SG"), ("GOI", "HYD", "SG"),
    ("MAA", "CCU", "6E"), ("CCU", "MAA", "6E"),
    ("MAA", "CCU", "AI"), ("CCU", "MAA", "AI"),
    ("MAA", "COK", "6E"), ("COK", "MAA", "6E"),
    ("MAA", "COK", "SG"), ("COK", "MAA", "SG"),
    ("CCU", "GAU", "6E"), ("GAU", "CCU", "6E"),
    ("CCU", "GAU", "SG"), ("GAU", "CCU", "SG"),
]

BUDGET_AIRLINES = {"WN", "F9", "NK", "6E", "SG", "QP", "IX"}
PREMIUM_AIRLINES = {"EK", "QR", "SQ", "CX", "EY", "BA", "LH", "AF"}

DEPARTURE_HOURS = [6, 8, 11, 14, 17, 20]

_rng = random.Random(42)


def _economy_price(dist_km: float, airline_iata: str = "", origin_country: str = "", dest_country: str = "", day_offset: int = 0, dep_hour: int = 12) -> tuple[float, bool]:
    is_indian_domestic = (origin_country == "IN" and dest_country == "IN")

    if is_indian_domestic:
        if dist_km < 500:
            base = 30.0   # ~₹2,500
        elif dist_km < 1000:
            base = 42.0   # ~₹3,500
        elif dist_km < 2000:
            base = 55.0   # ~₹4,500
        else:
            base = 72.0   # ~₹6,000
    elif dist_km < 5000:
        base = _rng.uniform(150, 250)
    else:
        base = _rng.uniform(350, 600)

    # Airline tier multiplier
    if airline_iata in BUDGET_AIRLINES:
        base *= 0.65
    elif airline_iata in PREMIUM_AIRLINES:
        base *= 1.4

    # Weekend surcharge (0=Mon … 6=Sun; Fri=4, Sat=5, Sun=6)
    dep_date = date.today() + timedelta(days=day_offset)
    if dep_date.weekday() in (4, 5, 6):
        base *= 1.15

    # Time-of-day discounts
    if 0 <= dep_hour < 6:
        base *= 0.85   # red-eye discount
    elif 6 <= dep_hour < 8:
        base *= 0.90   # early morning discount

    # Advance booking discount / last-minute surge
    if day_offset >= 45:
        base *= 0.85
    elif day_offset >= 30:
        base *= 0.90
    elif 7 <= day_offset <= 14:
        base *= 1.10
    elif day_offset < 7:
        base *= 1.25

    # Deal probability 20%
    is_deal = _rng.random() < 0.20
    if is_deal:
        base *= 0.70

    return round(base, 2), is_deal


async def generate_all_data(session: AsyncSession):
    """Idempotent: only runs if airports table is empty."""
    result = await session.execute(select(Airport).limit(1))
    if result.scalars().first():
        return

    airport_map = {}
    for ap in AIRPORTS:
        obj = Airport(
            iata_code=ap["iata"],
            name=ap["name"],
            city=ap["city"],
            country=ap["country"],
            latitude=ap["lat"],
            longitude=ap["lon"],
            timezone=ap["tz"],
        )
        session.add(obj)
        airport_map[ap["iata"]] = obj

    airline_map = {}
    for al in AIRLINES:
        obj = Airline(
            iata_code=al["iata"],
            name=al["name"],
            color=al["color"],
            country=al["country"],
        )
        session.add(obj)
        airline_map[al["iata"]] = obj

    await session.flush()

    iata_info = {ap["iata"]: ap for ap in AIRPORTS}
    today = date.today()
    flight_num_counter = {}
    flights_to_add = []

    for (orig_iata, dest_iata, airline_iata) in ROUTES:
        if orig_iata not in airport_map or dest_iata not in airport_map:
            continue
        if airline_iata not in airline_map:
            continue

        orig_info = iata_info[orig_iata]
        dest_info = iata_info[dest_iata]
        dist = haversine_km(orig_info["lat"], orig_info["lon"], dest_info["lat"], dest_info["lon"])
        duration_min = max(45, int(dist / 800 * 60))
        bags = 0 if airline_iata in BUDGET_AIRLINES else (2 if airline_iata in PREMIUM_AIRLINES else 1)

        prefix = airline_iata
        if prefix not in flight_num_counter:
            flight_num_counter[prefix] = _rng.randint(100, 999)

        n_flights = _rng.randint(3, 6)
        dep_hours = _rng.sample(DEPARTURE_HOURS, min(n_flights, len(DEPARTURE_HOURS)))

        for day_offset in range(90):
            dep_date = today + timedelta(days=day_offset)
            for hour in dep_hours:
                dep_dt = datetime(dep_date.year, dep_date.month, dep_date.day, hour, _rng.choice([0, 15, 30, 45]))
                arr_dt = dep_dt + timedelta(minutes=duration_min)

                flight_num_counter[prefix] += 1
                fn = f"{prefix}{flight_num_counter[prefix]}"

                ep, is_deal = _economy_price(
                    dist,
                    airline_iata=airline_iata,
                    origin_country=orig_info["country"],
                    dest_country=dest_info["country"],
                    day_offset=day_offset,
                    dep_hour=hour,
                )
                bp = round(ep * 3.0, 2)
                fp = round(ep * 6.0, 2)

                f = Flight(
                    flight_number=fn,
                    airline_id=airline_map[airline_iata].id,
                    origin_id=airport_map[orig_iata].id,
                    destination_id=airport_map[dest_iata].id,
                    departure_time=dep_dt,
                    arrival_time=arr_dt,
                    duration_minutes=duration_min,
                    price_economy=ep,
                    price_business=bp,
                    price_first=fp,
                    stops=0,
                    layover_airports="",
                    bags_included=bags,
                    is_deal=is_deal,
                    seats_available=_rng.randint(1, 200),
                )
                flights_to_add.append(f)

    CONNECT_ROUTES = [
        ("BOS", "LAX", "JFK", "AA"),
        ("SEA", "JFK", "LAX", "AS"),
        ("MCO", "LAX", "ATL", "DL"),
        ("DEN", "JFK", "ORD", "UA"),
        ("MIA", "LAX", "ATL", "AA"),
        ("LAS", "JFK", "LAX", "WN"),
        ("SYD", "JFK", "LAX", "QF"),
        ("MEL", "JFK", "LAX", "QF"),
        ("BOM", "LHR", "DXB", "EK"),
        ("DEL", "SIN", "DXB", "EK"),
        ("NRT", "LAX", "HND", "NH"),
        ("NBO", "DXB", "JNB", "EK"),
        ("CAI", "LHR", "DXB", "EK"),
        ("GRU", "LHR", "JFK", "LA"),
        ("EZE", "LHR", "GRU", "LA"),
        ("MEX", "ORD", "DFW", "AM"),
        ("YVR", "JFK", "YYZ", "AC"),
        ("AKL", "LAX", "SYD", "QF"),
        ("MNL", "LHR", "SIN", "SQ"),
        ("BLR", "LHR", "DXB", "EK"),
        # Indian connecting routes
        ("DEL", "BOM", "BLR", "6E"),
        ("CCU", "BLR", "DEL", "6E"),
        ("GOI", "DEL", "BOM", "6E"),
        ("MAA", "DEL", "BLR", "AI"),
        ("COK", "DEL", "BOM", "AI"),
        ("GAU", "BOM", "DEL", "6E"),
        ("AMD", "BLR", "BOM", "6E"),
    ]

    for (orig_iata, dest_iata, hub_iata, airline_iata) in CONNECT_ROUTES:
        if orig_iata not in airport_map or dest_iata not in airport_map or hub_iata not in airport_map:
            continue
        if airline_iata not in airline_map:
            continue

        orig_info = iata_info[orig_iata]
        dest_info = iata_info[dest_iata]
        hub_info = iata_info[hub_iata]
        dist1 = haversine_km(orig_info["lat"], orig_info["lon"], hub_info["lat"], hub_info["lon"])
        dist2 = haversine_km(hub_info["lat"], hub_info["lon"], dest_info["lat"], dest_info["lon"])
        total_dist = dist1 + dist2
        duration_min = max(90, int(total_dist / 800 * 60) + 90)
        bags = 0 if airline_iata in BUDGET_AIRLINES else 1

        prefix = airline_iata
        if prefix not in flight_num_counter:
            flight_num_counter[prefix] = _rng.randint(100, 999)

        dep_hours_connect = _rng.sample([7, 10, 15, 19], 2)
        for day_offset in range(90):
            dep_date = today + timedelta(days=day_offset)
            for hour in dep_hours_connect:
                dep_dt = datetime(dep_date.year, dep_date.month, dep_date.day, hour, 0)
                arr_dt = dep_dt + timedelta(minutes=duration_min)

                flight_num_counter[prefix] += 1
                fn = f"{prefix}{flight_num_counter[prefix]}"

                ep, is_deal = _economy_price(
                    total_dist * 1.1,
                    airline_iata=airline_iata,
                    origin_country=orig_info["country"],
                    dest_country=dest_info["country"],
                    day_offset=day_offset,
                    dep_hour=hour,
                )
                bp = round(ep * 3.0, 2)
                fp = round(ep * 6.0, 2)

                f = Flight(
                    flight_number=fn,
                    airline_id=airline_map[airline_iata].id,
                    origin_id=airport_map[orig_iata].id,
                    destination_id=airport_map[dest_iata].id,
                    departure_time=dep_dt,
                    arrival_time=arr_dt,
                    duration_minutes=duration_min,
                    price_economy=ep,
                    price_business=bp,
                    price_first=fp,
                    stops=1,
                    layover_airports=hub_iata,
                    bags_included=bags,
                    is_deal=is_deal,
                    seats_available=_rng.randint(1, 150),
                )
                flights_to_add.append(f)

    BATCH = 500
    for i in range(0, len(flights_to_add), BATCH):
        session.add_all(flights_to_add[i:i + BATCH])
        await session.flush()

    await session.commit()
