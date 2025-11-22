# myapp1/utils.py
import math
import re
from typing import Dict, Any

from .models import Contact


def haversine_km(lat1, lon1, lat2, lon2):
    """
    Distance in km between two lat/lng points.
    Returns None if any coordinate is missing.
    """
    if None in (lat1, lon1, lat2, lon2):
        return None
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(
        math.radians(lat2)
    ) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def _get_distinct_lower(field_name: str):
    """
    Helper: returns a dict mapping lowercase value -> original value
    for a given Contact text field (e.g. 'city', 'specialty').
    """
    values = (
        Contact.objects.exclude(**{f"{field_name}__isnull": True})
        .exclude(**{f"{field_name}__exact": ""})
        .values_list(field_name, flat=True)
        .distinct()
    )
    mapping = {}
    for v in values:
        v_str = str(v).strip()
        if not v_str:
            continue
        mapping[v_str.lower()] = v_str
    return mapping


def parse_nl_query(text: str) -> Dict[str, Any]:
    """
    Very simple, rule-based parser for natural language queries.

    Input examples:
        "cheap cardiologists in Beirut with high rating"
        "find a surgeon in Tripoli under 1000 dollars"
        "top rated pediatrician near Beirut below 2000 within 5 km"

    Output dict keys:
        specialty: str or None
        city: str or None
        max_fee: float or None
        min_rating: float or None
        max_km: float or None
    """
    text = (text or "").strip().lower()
    result: Dict[str, Any] = {
        "specialty": None,
        "city": None,
        "max_fee": None,
        "min_rating": None,
        "max_km": None,
    }

    if not text:
        return result

    # 1) Detect specialty
    specialties = _get_distinct_lower("specialty")
    for low_spec, original in specialties.items():
        if low_spec and low_spec in text:
            result["specialty"] = original
            break

    # 2) Detect city
    cities = _get_distinct_lower("city")
    for low_city, original in cities.items():
        pattern = r"\b" + re.escape(low_city) + r"\b"
        if re.search(pattern, text):
            result["city"] = original
            break

    # 3) Detect max fee
    fee_patterns = [
        r"(?:under|less than|below|up to|max(?:imum)?)\s+(\d+)",
        r"(\d+)\s*(?:usd|\$|dollars?)",
    ]
    fees_found = []
    for pat in fee_patterns:
        for m in re.finditer(pat, text):
            try:
                fees_found.append(float(m.group(1)))
            except ValueError:
                pass
    if fees_found:
        result["max_fee"] = min(fees_found)
    else:
        if any(w in text for w in ["cheap", "affordable", "low cost", "budget"]):
            result["max_fee"] = 200.0
        elif any(w in text for w in ["not too expensive", "reasonable"]):
            result["max_fee"] = 500.0
        elif "expensive" in text:
            result["max_fee"] = 2000.0

    # 4) Detect min rating
    rating_patterns = [
        r"(?:rating|score)\s*(?:above|over|greater than|>=|at least)\s*(\d(?:\.\d)?)",
        r"(\d(?:\.\d)?)\s*stars?",
    ]
    ratings_found = []
    for pat in rating_patterns:
        for m in re.finditer(pat, text):
            try:
                ratings_found.append(float(m.group(1)))
            except ValueError:
                pass
    if ratings_found:
        result["min_rating"] = max(ratings_found)
    else:
        if any(w in text for w in ["high rating", "top rated", "top-rated", "best"]):
            result["min_rating"] = 4.0

    # 5) Detect distance (max_km)
    dist_pattern = r"(\d+)\s*(?:km|kilometers?|kilometres?)"
    dists_found = []
    for m in re.finditer(dist_pattern, text):
        try:
            dists_found.append(float(m.group(1)))
        except ValueError:
            pass
    if dists_found:
        result["max_km"] = min(dists_found)
    else:
        if any(w in text for w in ["near", "close to", "nearby"]):
            result["max_km"] = 5.0

    return result
